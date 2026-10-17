# TMDB Movies Analysis (Team README)

## 1. What is this project?
We study **real movie data from the TMDB API** (The Movie Database:
https://www.themoviedb.org). We download movies **once**, save them as
`data/tmdb_movies.csv`, then do **all analysis on that saved file**.
No internet is needed after the download, so results are repeatable.

### Outcomes we are chasing (our questions)
1. Does a bigger **budget** mean bigger **revenue**?
2. Do better **ratings** mean more money, or is quality separate from money?
3. Does TMDB **popularity** (hype) predict revenue?
4. Do bigger **cast / crew** teams get better ratings?
5. Which **genres** earn the most, and which just have the most movies?
6. How are movies spread over **years, languages, runtimes**?
7. What is the **single strongest driver** of revenue in our data?

Short answers are in section 7 (Findings).

## 2. The 12 variables we use
| # | Variable | Column name | Example |
|---|----------|-------------|---------|
| 1 | Release year | `ReleaseYear` | 2019 |
| 2 | Rating | `Rating` | 7.5 out of 10 |
| 3 | Vote count | `Vote_Count` | 2545 votes |
| 4 | Popularity | `Popularity` | 47.3 (TMDB score) |
| 5 | Runtime | `Runtime` | 112 minutes |
| 6 | Genre | `Genres` + `Primary_Genre` | "Action\|Adventure" |
| 7 | Original language | `Original_Language` | en, es, ja, ... |
| 8 | Release date | `ReleaseDate` | 2019-07-20 |
| 9 | Revenue | `Revenue` | money earned (USD) |
| 10 | Budget | `Budget` | money spent (USD) |
| 11 | Cast count | `Cast_Count` | number of actors |
| 12 | Crew count | `Crew_Count` | number of crew |

Two extra columns are **calculated** by us:
`Profit = Revenue - Budget`, `ROI = Revenue / Budget`
(ROI = how many times the budget was earned back).

## 3. How it works
```
Step 1 (once, needs internet):
  TMDB API  --(/discover/movie + /movie/{id})-->  data/tmdb_movies.csv
              module1_tmdb.py

Step 2 (every run, no internet):
  data/tmdb_movies.csv  --(load + clean)-->  clean table
                          module1_loader.py

Step 3 (every run):
  clean table --(labels)-->  classes        (module2_conditions.py)
              --(loops)--->  totals/counts  (module3_analysis.py)
              --(numpy) --->  r values      (module3_analysis.py)
              --(tables)-->  text report    (module4_stats.py)
              --(plots) --->  14 PNG charts (module5_visuals.py)

All of Step 3 runs inside main_analysis.ipynb, top to bottom.
```

API calls used (only in `module1_tmdb.py`):
- `GET /discover/movie` — list of movies (20 per page, sorted by popularity).
- `GET /movie/{id}?append_to_response=credits` — one call gives details
  (budget, revenue, runtime, ...) **plus** cast and crew in the same answer.

## 4. What we used (tech)
| Tool | Why | Where |
|------|-----|-------|
| Python 3 | main language | everything |
| pandas | read CSV, clean columns, group by year/genre | loader, notebook |
| matplotlib | all charts (bar, line, pie-style, hist, scatter) | module5, notebook |
| numpy (basic only) | `mean`, `median`, `std`, `percentile`, `corrcoef` | analysis, stats, notebook |
| requests | talk to the TMDB API | module1_tmdb only |
| Jupyter notebook | step-by-step run + inline charts | main_analysis.ipynb |
| TMDB API | real data source | fetcher |

Code style rule: plain `for` loops and `if / elif / else` first.
numpy is only used for 5 simple calls. No advanced tricks,
so a 1st-year student can read every line.

## 5. Code structure
```
project/
  module1_tmdb.py        fetch + store (API -> CSV)
  module1_loader.py      load + clean (CSV -> table)
  module2_conditions.py  label one value (if/elif)
  module3_analysis.py    totals with loops + r with numpy
  module4_stats.py       average / percent / top / text tables
  module5_visuals.py     chart functions (one per variable)
  main_analysis.ipynb    connects everything, in order
  data/tmdb_movies.csv   197 saved movies (our dataset)
  charts/tmdb_*.png      14 saved charts
  tmdb_summary_report.txt  final text report
  module1_scraper.py     OLD Wikipedia scraper, not used any more
```

What each module gives the notebook:
- `module1_tmdb.fetch_and_store(pages=10)` -> DataFrame + CSV.
  `fetch_stratified_and_store()` variant exists for a year-balanced sample.
- `module1_loader.load_tmdb()` -> raw DataFrame.
  `clean_data()` -> tidy text, numbers as numbers, year fixed from date,
  Profit/ROI added, doubles removed.
  `tmdb_completeness()` -> e.g. (142, 197): rows usable for money charts.
- `module2_conditions` -> `classify_rating / classify_runtime /
  classify_popularity / classify_budget_tmdb / classify_votes /
  classify_revenue / classify_era / is_profitable`.
- `module3_analysis` -> `calculate_total_revenue`,
  `count_genre_exploded` (splits "A|B"), `count_primary_genre`,
  `count_language`, `group_revenue_by`, `avg_rating_by`,
  `count_per_year`, `avg_popularity_by_year`, `numpy_describe`,
  `correlation(x, y)` (Pearson r from -1 to 1).
- `module4_stats` -> `calculate_average`, `calculate_percentage`,
  `find_top`, `sort_desc`, `format_money_table`, `format_count_table`,
  `np_mean / np_median / np_std`, `roi_stats`, `top_n_share`.
- `module5_visuals` -> `plot_movies_per_year`, `plot_rating_distribution`,
  `plot_votes_vs_rating`, `plot_popularity_by_year`,
  `plot_runtime_distribution`, `plot_movies_by_genre`,
  `plot_movies_by_language`, `plot_releases_over_time`,
  `plot_revenue_by_genre`, `plot_budget_vs_revenue`,
  `plot_cast_vs_rating`, `plot_crew_vs_rating`,
  plus `plot_correlation_bars` and `plot_simple_scatter` for relationships.

## 6. Outputs (what you get after Run All)
- **Notebook with inline charts**: `main_analysis.ipynb` (24 cells).
- **14 PNG files** in `charts/` (also shown inline).
- **Text report**: `tmdb_summary_report.txt` (totals + correlations + conclusion).
- **Console tables**: revenue-by-genre, count-by-genre, avg-rating-by-genre.

### Chart guide (type + file + how to read it)
| # | Chart | Type | File | Read it as |
|---|-------|------|------|------------|
| 1 | Movies released per year | bar | `tmdb_movies_per_year.png` | taller bar = more movies that year |
| 2 | Rating distribution | histogram + mean/median lines | `tmdb_rating_dist.png` | hump = where most ratings sit (median 7.51) |
| 3 | Votes vs Rating | scatter (log x) | `tmdb_votes_vs_rating.png` | dots drift up = more votes, slightly better rating |
| 4 | Average popularity by year | line + dots | `tmdb_popularity_by_year.png` | recent years much higher = recency hype |
| 5 | Runtime distribution | histogram + median line | `tmdb_runtime_dist.png` | hump near 112 min; tails = very short / epic films |
| 6 | Movies by genre | bar | `tmdb_by_genre.png` | Action (76 incl. multi-counts) is most common |
| 7 | Movies by language | bar | `tmdb_by_language.png` | en = 170/197, Hollywood-skewed sample |
| 8 | Releases over time | line | `tmdb_releases_over_time.png` | same story as chart 1, from real dates |
| 9 | Revenue by genre | bar (USD) | `tmdb_revenue_by_genre.png` | Action > Adventure > Sci-Fi > Animation |
| 10 | Budget vs Revenue | scatter log-log + break-even lines | `tmdb_budget_vs_revenue.png` | dots above dashed line made money; dotted = doubled it |
| 11 | Cast size vs Rating | scatter | `tmdb_cast_vs_rating.png` | cloud, almost flat = cast size barely matters |
| 12 | Crew size vs Rating | scatter | `tmdb_crew_vs_rating.png` | cloud, almost flat = crew size barely matters |
| R1 | Correlations side by side | bar of r values | `tmdb_corr_bars.png` | taller bar = stronger link; near 0 = no link |
| R2 | Budget vs Revenue (simple) | plain scatter | `tmdb_budget_revenue_simple.png` | dots rise left to right = money follows money |

## 7. Findings
Dataset snapshot: **197 movies, years 1970–2026** (leans recent:
API sorts by popularity). **142 rows complete**
(budget + revenue + runtime all > 0). Median rating **7.51**,
median runtime **112 min**, median ROI **~4.4x**, **110 of 197**
movies profitable (revenue >= 2x budget).

Per-chart findings:
1. Sample skews recent (popularity-sorted API) — trends use per-year averages.
2. Ratings cluster ~6.8–8.1; extremes are rare.
3. More votes go with slightly better ratings (r = +0.46).
4. Popularity is recency-driven, not a quality signal.
5. Typical film is ~2 hours; Short (<90m) and Epic (>150m) are minorities.
6. Most common genre: Action; count leader and revenue leader differ.
7. English dominates (170/197).
8. Release-date curve matches the per-year bars.
9. Revenue leader: Action (24.0%), top-3 genres take well over half of all revenue.
10. Budget–Revenue is the strongest money link (see r table).
11. Cast size vs rating r = +0.40 — weak; big casts don't buy ratings.
12. Crew size vs rating r = +0.34 — weak; big crews don't buy ratings either.
13. (R1) Budget–Revenue towers over Rating/Popularity bars.
14. (R2) Simple scatter rises left to right — same story without log tricks.

Full correlation table (numpy Pearson r):
| Pair | r | Meaning |
|------|---|---------|
| Budget vs Revenue | **+0.76** | strong — biggest driver |
| Vote_Count vs Revenue | +0.56 | medium — audience size matters |
| Rating vs Revenue | +0.31 | weak — quality helps a little |
| Popularity vs Revenue | +0.04 | ~none — hype alone means nothing here |
| Cast_Count vs Rating | +0.40 | weak |
| Crew_Count vs Rating | +0.34 | weak |
| Budget vs Rating | +0.30 | weak — spending doesn't buy ratings |

### Conclusive finding (computed from the data, not hard-coded)
> **Production scale drives commercial outcome.**
> Budget vs Revenue r = +0.76 is the strongest revenue link —
> about 2x Rating vs Revenue (+0.31) and far above
> Popularity vs Revenue (+0.04). Ratings, cast size (+0.40) and
> crew size (+0.34) barely move quality scores, and budget barely
> lifts ratings (+0.30). **Money predicts money; quality signals don't.**

Also worth saying on stage: count leader (Action, 44 primary) is also
revenue leader ($19.3B), but the **best-rated** groups
(Music 8.63, Animation 8.15, Family 8.02) are **not** the richest —
another sign that ratings and revenue live on different axes.

## 8. How to run it
1. Install what you need:
```bash
pip install pandas matplotlib numpy requests jupyter
```
2. (Optional, needs internet.) Fetch fresh data — else skip, the CSV is already there:
```python
from module1_tmdb import fetch_and_store
fetch_and_store(pages=10, output_path="data/tmdb_movies.csv")  # ~200 movies, ~1 min
```
Note: TMDB allows ~40 requests per 10 seconds. If you fetch a lot at
once you may hit rate limits and the script waits and retries —
that is normal, just let it finish.
3. Run the notebook top to bottom:
```bash
jupyter notebook main_analysis.ipynb
```
Click **Cell > Run All**. Charts appear inline and are saved to `charts/`.
The report is saved as `tmdb_summary_report.txt`.

## 9. Limits (say these if anyone asks)
- Sample leans **recent** (many 2025–2026 titles) because the API sorts
  by popularity. That is why Popularity vs Revenue is ~0: new films have
  huge popularity but $0 revenue so far.
- Money charts use only rows with Budget > 0 and Revenue > 0 (142 of 197).
- `data/movies_dataset.csv` (144 MB synthetic file) and
  `module1_scraper.py` are leftovers — the TMDB files replaced them.
- API keys live in `module1_tmdb.py` (student project shortcut).
  For real work, move them to environment variables.

## 10. How to extend it (for teammates)
Add a chart — copy this pattern into a new notebook cell:
```python
visuals.plot_simple_scatter(list(df["Runtime"]), list(df["Rating"]),
    "Runtime", "Rating", "Runtime vs Rating",
    savepath="charts/tmdb_runtime_vs_rating.png")
plt.show()
```
Add a label — put a new `classify_...` function in
`module2_conditions.py` using only `if / elif / else`, then use it with
`.apply()` like the rating classes in Cell 2.

Re-fetch with a year-balanced sample (slower, ~5 min) instead of the
quick popularity sample:
```python
from module1_tmdb import fetch_stratified_and_store
fetch_stratified_and_store(per_year=10, output_path="data/tmdb_movies.csv")
```
