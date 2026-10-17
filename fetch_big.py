"""Fetch ~3000 movies in chunks with checkpoint saves (so a hiccup doesn't lose everything)."""
import os, time, pandas as pd
from module1_tmdb import discover_movies, enrich_many, TMDB_COLUMNS

PAGES = 150
OUT = "data/tmdb_movies_3000.csv"
CHUNK = 500

t0 = time.time()
brief = discover_movies(pages=PAGES, parallel=True, max_workers=10)
ids = list(dict.fromkeys(m["id"] for m in brief if m.get("id") is not None))
print(f"discovered {len(ids)} unique ids", flush=True)

done_ids, all_rows = set(), []
if os.path.exists(OUT) and os.path.getsize(OUT) > 0:
    old = pd.read_csv(OUT)
    all_rows = old.to_dict("records")
    done_ids = set(old["MovieID"].tolist())
    print(f"resuming: {len(done_ids)} already saved", flush=True)

todo = [i for i in ids if i not in done_ids]
print(f"to fetch: {len(todo)}", flush=True)
for s in range(0, len(todo), CHUNK):
    batch = todo[s:s + CHUNK]
    rows = enrich_many(batch, max_workers=15)
    all_rows.extend(rows)
    df = pd.DataFrame(all_rows, columns=TMDB_COLUMNS).drop_duplicates(subset=["MovieID"])
    all_rows = df.to_dict("records")
    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    df.to_csv(OUT, index=False)
    print(f"CHECKPOINT {s + len(batch)}/{len(todo)} -> {len(df)} rows saved "
          f"({time.time() - t0:.0f}s elapsed)", flush=True)

print(f"DONE: {OUT} ({time.time() - t0:.0f}s total)")
