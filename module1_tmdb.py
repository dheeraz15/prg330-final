"""Module 1b - TMDB API fetcher: API hit -> store locally -> analysis reads local CSV.

Covers all requested variables:
  Release year, Rating, Vote count, Popularity, Runtime,
  Genre, Original language, Release date, Revenue, Budget,
  Cast count, Crew count

Usage:
    from module1_tmdb import fetch_and_store
    fetch_and_store(pages=50)   # ~1000 movies (20 per page)

    # Fast parallel (default): 10-20 workers, connection reuse, rate-limited
    fetch_and_store(pages=150, output_path="data/tmdb_movies.csv", max_workers=20)

    # Resume: skip IDs already in the CSV (lets you grow 197 -> 3000+ cheaply)
    fetch_and_store(pages=150, output_path="data/tmdb_movies.csv", resume=True)

Auth: Bearer read-access token (preferred) or api_key fallback.
"""

import os
import threading
import time

import pandas as pd
import requests
from concurrent.futures import ThreadPoolExecutor, as_completed

# --- Auth (student project: token stored here for reproducibility) ---
TMDB_BEARER_TOKEN = "eyJhbGciOiJIUzI1NiJ9.eyJhdWQiOiIwODJjNDRkNTRkODk4ZDBjNDFjMzVmZjE3YTAzMTgxMSIsIm5iZiI6MTc5MDk1MTc4Mi4xOCwic3ViIjoiNmFiZmMxNjY3NDA1MTI4MTZhYWExMTUzIiwic2NvcGVzIjpbImFwaV9yZWFkIl0sInZlcnNpb24iOjF9.aswFg1IMiuLZ7GwB6Qb0OodEa17Dga-7EDxS0wDK77A"
TMDB_API_KEY = "082c44d54d898d0c41c35ff17a031811"

BASE_URL = "https://api.themoviedb.org/3"
HEADERS = {"Authorization": f"Bearer {TMDB_BEARER_TOKEN}", "accept": "application/json"}

TMDB_COLUMNS = [
    "MovieID", "Title", "ReleaseDate", "ReleaseYear", "Original_Language",
    "Rating", "Vote_Count", "Popularity", "Runtime", "Budget", "Revenue",
    "Cast_Count", "Crew_Count", "Genres", "Primary_Genre",
]

# TMDB rate limit is ~40 req / 10 s. Stay just under it to avoid 429 storms.
_RATE_MAX_CALLS = 38
_RATE_PERIOD = 10.0

_thread_local = threading.local()
_print_lock = threading.Lock()


def _log(msg):
    with _print_lock:
        print(msg, flush=True)


class _RateLimiter:
    """Thread-safe sliding-window limiter: max_calls per period (seconds)."""

    def __init__(self, max_calls=_RATE_MAX_CALLS, period=_RATE_PERIOD):
        self.max_calls = max_calls
        self.period = period
        self.lock = threading.Lock()
        self.calls = []  # timestamps of recent calls

    def wait(self):
        while True:
            with self.lock:
                now = time.monotonic()
                # drop calls outside the window
                self.calls = [t for t in self.calls if now - t < self.period]
                if len(self.calls) < self.max_calls:
                    self.calls.append(now)
                    return
                # must wait until oldest call leaves the window
                sleep_for = self.period - (now - self.calls[0]) + 0.05
            if sleep_for > 0:
                time.sleep(sleep_for)

    def reset(self, max_calls=None, period=None):
        with self.lock:
            if max_calls:
                self.max_calls = max_calls
            if period:
                self.period = period
            self.calls = []


_limiter = _RateLimiter()


def _session():
    """One reused Session per thread (connection pooling = much less overhead)."""
    sess = getattr(_thread_local, "session", None)
    if sess is None:
        sess = requests.Session()
        sess.headers.update(HEADERS)
        adapter = requests.adapters.HTTPAdapter(
            pool_connections=20, pool_maxsize=20, max_retries=0
        )
        sess.mount("https://", adapter)
        sess.mount("http://", adapter)
        _thread_local.session = sess
    return sess


def _get(url, params=None, retries=4):
    """GET with retry + backoff on 429 / transient errors (sequential path)."""
    for attempt in range(retries):
        try:
            r = requests.get(url, headers=HEADERS, params=params or {}, timeout=30)
        except requests.RequestException as e:
            print(f"  request error {e} (try {attempt + 1}/{retries})")
            time.sleep(2 * (attempt + 1))
            continue
        if r.status_code == 200:
            return r.json()
        if r.status_code in (429, 500, 502, 503, 504):
            wait = 2 * (attempt + 1)
            print(f"  HTTP {r.status_code}, retry in {wait}s (try {attempt + 1}/{retries})")
            time.sleep(wait)
            continue
        print(f"  FAILED {url} status={r.status_code} body={r.text[:200]}")
        return None
    return None


def _get_fast(url, params=None, retries=5):
    """Thread-safe GET: shared rate limiter + pooled Session + Retry-After honor."""
    params = params or {}
    for attempt in range(retries):
        _limiter.wait()
        try:
            r = _session().get(url, params=params, timeout=30)
        except requests.RequestException:
            time.sleep(1.0 * (attempt + 1))
            continue
        if r.status_code == 200:
            try:
                return r.json()
            except ValueError:
                return None
        if r.status_code == 429:
            retry_after = r.headers.get("Retry-After")
            try:
                wait = float(retry_after) + 0.5 if retry_after else 2.0 * (attempt + 1)
            except ValueError:
                wait = 2.0 * (attempt + 1)
            time.sleep(wait)
            continue
        if r.status_code in (500, 502, 503, 504):
            time.sleep(1.5 * (attempt + 1))
            continue
        return None  # 401/404/etc: don't retry
    return None


def _row_from_details(details, fallback_id=None):
    """Convert /movie/{id}?append_to_response=credits JSON -> flat row dict."""
    if not details:
        return None
    genres = [g.get("name", "") for g in (details.get("genres") or []) if g.get("name")]
    release_date = details.get("release_date") or ""
    try:
        year = int(release_date[:4]) if release_date and len(release_date) >= 4 else 0
    except ValueError:
        year = 0
    credits = details.get("credits") or {}
    cast_n = len(credits.get("cast", []))
    crew_n = len(credits.get("crew", []))
    mid = details.get("id", fallback_id)
    return {
        "MovieID": mid,
        "Title": details.get("title") or details.get("original_title") or "",
        "ReleaseDate": release_date,
        "ReleaseYear": year,
        "Original_Language": details.get("original_language") or "",
        "Rating": float(details.get("vote_average") or 0.0),
        "Vote_Count": int(details.get("vote_count") or 0),
        "Popularity": float(details.get("popularity") or 0.0),
        "Runtime": int(details.get("runtime") or 0),
        "Budget": int(details.get("budget") or 0),
        "Revenue": int(details.get("revenue") or 0),
        "Cast_Count": int(cast_n),
        "Crew_Count": int(crew_n),
        "Genres": "|".join(genres),
        "Primary_Genre": genres[0] if genres else "Unknown",
    }


def _fetch_discover_page(page, sort_by, extra_params):
    params = {"sort_by": sort_by, "page": page, "language": "en-US",
              "include_adult": "false", "include_video": "false"}
    params.update(extra_params or {})
    return page, _get_fast(f"{BASE_URL}/discover/movie", params=params)


def discover_movies(pages=50, sort_by="popularity.desc", delay=0.15, extra_params=None,
                    parallel=True, max_workers=10):
    """Hit /discover/movie for N pages (20 movies/page). Returns list of brief dicts.

    parallel=True (default) fires `max_workers` page requests at once through
    one shared rate limiter. parallel=False keeps the old sequential loop.
    """
    extra_params = extra_params or {}
    if pages > 500:
        _log(f"NOTE: TMDB /discover caps at page 500 (~10k movies); got pages={pages}.")
    if not parallel:
        all_results = []
        for page in range(1, pages + 1):
            params = {"sort_by": sort_by, "page": page, "language": "en-US",
                      "include_adult": "false", "include_video": "false"}
            params.update(extra_params)
            data = _get(f"{BASE_URL}/discover/movie", params=params)
            if not data or "results" not in data:
                print(f"page {page}: no data, stopping")
                break
            all_results.extend(data["results"])
            print(f"page {page}/{pages}: +{len(data['results'])} (total {len(all_results)})")
            time.sleep(delay)
        return _dedupe(all_results)

    # ---- parallel path ----
    t0 = time.time()
    by_page = {}
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_fetch_discover_page, p, sort_by, extra_params): p
                for p in range(1, pages + 1)}
        done = 0
        for fut in as_completed(futs):
            page, data = fut.result()
            done += 1
            if data and "results" in data:
                by_page[page] = data["results"]
            if done % 10 == 0 or done == pages:
                _log(f"discover {done}/{pages} pages ({time.time() - t0:.1f}s)")
    all_results = []
    for p in sorted(by_page):  # keep page order deterministic
        all_results.extend(by_page[p])
    _log(f"discover done: {len(all_results)} movies from {len(by_page)}/{pages} pages "
         f"in {time.time() - t0:.1f}s")
    return _dedupe(all_results)


def _dedupe(movies):
    seen, uniq = set(), []
    for m in movies:
        mid = m.get("id")
        if mid not in seen:
            seen.add(mid)
            uniq.append(m)
    return uniq


def enrich_movie(movie_id, delay=0.04):
    """Hit /movie/{id}?append_to_response=credits (1 request). Returns enriched dict or None."""
    details = _get(f"{BASE_URL}/movie/{movie_id}",
                   params={"language": "en-US", "append_to_response": "credits"})
    if not details:
        return None
    time.sleep(delay)
    return _row_from_details(details, fallback_id=movie_id)


def _enrich_one(movie_id):
    details = _get_fast(f"{BASE_URL}/movie/{movie_id}",
                        params={"language": "en-US", "append_to_response": "credits"})
    return _row_from_details(details, fallback_id=movie_id)


def enrich_many(movie_ids, max_workers=20):
    """Enrich a list of TMDB ids in parallel. Returns list of row dicts."""
    rows = []
    t0 = time.time()
    total = len(movie_ids)
    done = 0
    with ThreadPoolExecutor(max_workers=max_workers) as ex:
        futs = {ex.submit(_enrich_one, mid): mid for mid in movie_ids}
        for fut in as_completed(futs):
            done += 1
            try:
                row = fut.result()
            except Exception:
                row = None
            if row:
                rows.append(row)
            if done % 100 == 0 or done == total:
                _log(f"  enriched {done}/{total} (kept {len(rows)}, "
                     f"{time.time() - t0:.0f}s)")
    return rows


def _load_existing_ids(output_path):
    """Return set of MovieIDs already stored (for resume=True)."""
    try:
        if os.path.exists(output_path) and os.path.getsize(output_path) > 0:
            df = pd.read_csv(output_path, usecols=["MovieID"])
            return set(df["MovieID"].astype(int).tolist())
    except Exception as e:
        _log(f"  (could not read existing CSV for resume: {e})")
    return set()


def fetch_and_store(pages=50, output_path="data/tmdb_movies.csv", delay=0.05,
                    sort_by="popularity.desc", extra_params=None,
                    max_workers=20, parallel=True, resume=False,
                    discover_workers=10):
    """Full pipeline: discover -> enrich each movie -> save CSV locally.

    Args:
        pages: discover pages to pull (20 movies each). 50 => ~1000 movies.
            150 => ~3000, 250 => ~5000 (TMDB caps at 500 pages).
        output_path: local CSV path (relative to project/ or absolute).
        delay: (sequential mode only) pause between detail calls.
        max_workers: threads for the enrich phase (15-20 is the sweet spot;
            higher just hits the 40req/10s TMDB cap and 429-retries).
        parallel: True (default) = ThreadPoolExecutor + pooled Sessions +
            shared 38req/10s limiter. False = old one-by-one loop.
        resume: True = skip MovieIDs already in output_path, append new ones.
        discover_workers: threads for the discover phase (10 is plenty).
    Returns:
        pandas DataFrame of stored movies.
    """
    t_start = time.time()
    print(f"Discovering {pages} pages (~{pages * 20} movies) "
          f"[{'parallel' if parallel else 'sequential'}]...")
    brief = discover_movies(pages=pages, sort_by=sort_by, extra_params=extra_params,
                            parallel=parallel, max_workers=discover_workers)
    print(f"Discovered {len(brief)} movies. Enriching details+credits...")

    ids = [m.get("id") for m in brief if m.get("id") is not None]
    # de-dupe ids while keeping order
    ids = list(dict.fromkeys(ids))

    already = set()
    if resume:
        already = _load_existing_ids(output_path)
        before = len(ids)
        ids = [i for i in ids if i not in already]
        print(f"resume: {len(already)} already stored, {before} discovered -> "
              f"{len(ids)} new to fetch")

    if parallel:
        rows = enrich_many(ids, max_workers=max_workers)
    else:
        rows = []
        for i, mid in enumerate(ids, 1):
            row = enrich_movie(mid, delay=delay)
            if row:
                rows.append(row)
            if i % 50 == 0 or i == len(ids):
                print(f"  enriched {i}/{len(ids)} (kept {len(rows)})")

    df_new = pd.DataFrame(rows, columns=TMDB_COLUMNS)
    # store locally (append if resume, else overwrite)
    outdir = os.path.dirname(output_path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    if resume and already and os.path.exists(output_path):
        try:
            df_old = pd.read_csv(output_path)
            df = pd.concat([df_old, df_new], ignore_index=True)
            df = df.drop_duplicates(subset=["MovieID"]).reset_index(drop=True)
        except Exception:
            df = df_new
    else:
        df = df_new
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} movies ({len(df_new)} new) -> {output_path} "
          f"in {time.time() - t_start:.0f}s total")
    return df


def fetch_stratified_and_store(years=None, per_year=10, output_path="data/tmdb_movies.csv",
                               delay=0.04, min_votes=20, max_workers=20,
                               parallel=True):
    """Year-spread pipeline: top `per_year` popular movies for each year in `years`.

    Gives a balanced sample across time (good for yearly-trend charts) and
    only released movies with real budget/revenue data.
    parallel=True fetches the per-year discover calls + enrichment concurrently.
    """
    if years is None:
        years = list(range(2005, 2025))  # 20 years x 10 = 200 movies
    print(f"Stratified fetch: {len(years)} years x {per_year} = ~{len(years) * per_year} movies "
          f"[{'parallel' if parallel else 'sequential'}]")

    brief = []
    if parallel:
        def _one_year(y):
            data = _get_fast(f"{BASE_URL}/discover/movie", params={
                "sort_by": "popularity.desc", "page": 1, "language": "en-US",
                "include_adult": "false", "include_video": "false",
                "primary_release_year": y, "vote_count.gte": min_votes,
            })
            return y, (data or {}).get("results", [])[:per_year]

        with ThreadPoolExecutor(max_workers=min(10, len(years))) as ex:
            futs = {ex.submit(_one_year, y): y for y in years}
            per_year_results = {}
            for fut in as_completed(futs):
                y, res = fut.result()
                per_year_results[y] = res
        for y in years:  # deterministic year order
            res = per_year_results.get(y, [])
            print(f"  {y}: +{len(res)}")
            brief.extend(res)
    else:
        for y in years:
            data = _get(f"{BASE_URL}/discover/movie", params={
                "sort_by": "popularity.desc", "page": 1, "language": "en-US",
                "include_adult": "false", "include_video": "false",
                "primary_release_year": y, "vote_count.gte": min_votes,
            })
            time.sleep(0.12)
            results = (data or {}).get("results", [])[:per_year]
            print(f"  {y}: +{len(results)}")
            brief.extend(results)

    print(f"Discovered {len(brief)} movies. Enriching...")
    ids = list(dict.fromkeys(m.get("id") for m in brief if m.get("id") is not None))
    if parallel:
        rows_all = enrich_many(ids, max_workers=max_workers)
    else:
        rows_all = []
        for i, mid in enumerate(ids, 1):
            row = enrich_movie(mid, delay=delay)
            if row:
                rows_all.append(row)
            if i % 50 == 0 or i == len(ids):
                print(f"  enriched {i}/{len(ids)} (kept {len(rows_all)})")
    rows = [r for r in rows_all if r and r["ReleaseYear"] > 0]
    df = pd.DataFrame(rows, columns=TMDB_COLUMNS)
    outdir = os.path.dirname(output_path)
    if outdir:
        os.makedirs(outdir, exist_ok=True)
    df.to_csv(output_path, index=False)
    print(f"Saved {len(df)} movies -> {output_path}")
    return df


if __name__ == "__main__":
    import sys
    pages = int(sys.argv[1]) if len(sys.argv) > 1 else 50
    out = sys.argv[2] if len(sys.argv) > 2 else "data/tmdb_movies.csv"
    workers = int(sys.argv[3]) if len(sys.argv) > 3 else 20
    fetch_and_store(pages=pages, output_path=out, max_workers=workers)
