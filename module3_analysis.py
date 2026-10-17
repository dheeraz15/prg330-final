"""Module 3 - Loop analysis with a little numpy.

Rule: use plain for-loops and if/else first,
then use numpy only for mean / median / std / correlation.
Works on the TMDB table. Old functions are kept too.
"""

import numpy as np
import pandas as pd

import module2_conditions as cond


def _rows(df):
    # Give back each row as a simple dict.
    rows = df.to_dict(orient="records")
    for row in rows:
        yield row


# ---------- legacy (synthetic CSV) ----------
def calculate_total_global(df):
    # Total Global_BoxOfficeUSD over all movies.
    total = 0
    for row in _rows(df):
        total = total + row["Global_BoxOfficeUSD"]
    return total


def calculate_total_budget(df):
    # Total BudgetUSD over all movies.
    total = 0
    for row in _rows(df):
        total = total + row["BudgetUSD"]
    return total


def count_genre(df):
    # Count movies in each genre.
    counts = {}
    for row in _rows(df):
        key = row["Genre"]
        if key in counts:
            counts[key] = counts[key] + 1
        else:
            counts[key] = 1
    return counts


def count_country(df):
    # Count movies in each country.
    counts = {}
    for row in _rows(df):
        key = row["Country"]
        if key in counts:
            counts[key] = counts[key] + 1
        else:
            counts[key] = 1
    return counts


def group_boxoffice_by(df, column):
    # Add up box office for each group.
    totals = {}
    for row in _rows(df):
        key = row[column]
        if key in totals:
            totals[key] = totals[key] + row["Global_BoxOfficeUSD"]
        else:
            totals[key] = row["Global_BoxOfficeUSD"]
    return totals


def count_by(df, column):
    # Count rows in each group.
    counts = {}
    for row in _rows(df):
        key = row[column]
        if key in counts:
            counts[key] = counts[key] + 1
        else:
            counts[key] = 1
    return counts


def count_boxoffice_classes(df):
    # Count Blockbuster / Hit / Average / Flop.
    classes = {"Blockbuster": 0, "Hit": 0, "Average": 0, "Flop": 0}
    for row in _rows(df):
        label = cond.classify_boxoffice(row["Global_BoxOfficeUSD"])
        classes[label] = classes[label] + 1
    return classes


def count_rating_classes(df):
    # Count Excellent / Good / Average / Poor.
    classes = {"Excellent": 0, "Good": 0, "Average": 0, "Poor": 0}
    for row in _rows(df):
        label = cond.classify_rating(row["IMDbRating"])
        classes[label] = classes[label] + 1
    return classes


def get_blockbusters(df):
    # Keep only Blockbuster rows.
    out = []
    for row in _rows(df):
        if cond.classify_boxoffice(row["Global_BoxOfficeUSD"]) == "Blockbuster":
            out.append(row)
    return out


def get_profitable(df):
    # Keep rows where box office is at least 2x budget.
    out = []
    for row in _rows(df):
        if cond.is_profitable(row["BudgetUSD"], row["Global_BoxOfficeUSD"]):
            out.append(row)
    return out


# ---------- TMDB (current table) ----------
def calculate_total_revenue(df):
    total = 0
    for row in _rows(df):
        value = row.get("Revenue", 0)
        if value is None:
            value = 0
        total = total + value
    return total


def calculate_total_tmdb_budget(df):
    total = 0
    for row in _rows(df):
        value = row.get("Budget", 0)
        if value is None:
            value = 0
        total = total + value
    return total


def count_genre_exploded(df):
    # Genres look like "Action|Drama". Count each part.
    counts = {}
    for row in _rows(df):
        text = row.get("Genres", "")
        if text is None:
            text = ""
        parts = str(text).split("|")
        for g in parts:
            g = g.strip()
            if g == "":
                continue
            if g in counts:
                counts[g] = counts[g] + 1
            else:
                counts[g] = 1
    return counts


def count_primary_genre(df):
    return count_by(df, "Primary_Genre")


def count_language(df):
    return count_by(df, "Original_Language")


def group_revenue_by(df, column):
    # Add up Revenue for each group.
    totals = {}
    for row in _rows(df):
        key = row.get(column, "Unknown")
        money = row.get("Revenue", 0)
        if money is None:
            money = 0
        if key in totals:
            totals[key] = totals[key] + money
        else:
            totals[key] = money
    return totals


def avg_rating_by(df, column):
    # Mean rating for each group.
    groups = {}
    for row in _rows(df):
        key = row.get(column, "Unknown")
        rating = row.get("Rating", 0)
        if rating is None:
            rating = 0
        if key in groups:
            groups[key].append(rating)
        else:
            groups[key] = [rating]
    result = {}
    for key in groups:
        result[key] = float(np.mean(groups[key]))
    return result


def avg_popularity_by_year(df):
    # Mean popularity for each year, oldest year first.
    groups = {}
    for row in _rows(df):
        year = row.get("ReleaseYear", 0)
        if year is None:
            year = 0
        if year <= 0:
            continue
        pop = row.get("Popularity", 0)
        if pop is None:
            pop = 0
        if year in groups:
            groups[year].append(pop)
        else:
            groups[year] = [pop]
    result = {}
    years = sorted(groups.keys())
    for year in years:
        result[year] = float(np.mean(groups[year]))
    return result


def count_per_year(df):
    counts = {}
    for row in _rows(df):
        year = row.get("ReleaseYear", 0)
        if year is None:
            year = 0
        if year <= 0:
            continue
        if year in counts:
            counts[year] = counts[year] + 1
        else:
            counts[year] = 1
    ordered = {}
    for year in sorted(counts.keys()):
        ordered[year] = counts[year]
    return ordered


def count_tmdb_rating_classes(df):
    classes = {"Excellent": 0, "Good": 0, "Average": 0, "Poor": 0}
    for row in _rows(df):
        rating = row.get("Rating", 0)
        if rating is None:
            rating = 0
        label = cond.classify_rating(rating)
        classes[label] = classes[label] + 1
    return classes


def count_runtime_classes(df):
    classes = {"Short (<90m)": 0, "Standard (90-120m)": 0,
               "Long (121-150m)": 0, "Epic (>150m)": 0, "Unknown": 0}
    for row in _rows(df):
        runtime = row.get("Runtime", 0)
        if runtime is None:
            runtime = 0
        label = cond.classify_runtime(runtime)
        classes[label] = classes[label] + 1
    return classes


def get_profitable_tmdb(df):
    out = []
    for row in _rows(df):
        budget = row.get("Budget", 0)
        revenue = row.get("Revenue", 0)
        if budget is None:
            budget = 0
        if revenue is None:
            revenue = 0
        if cond.is_profitable(budget, revenue):
            out.append(row)
    return out


def get_high_revenue(df, threshold=500_000_000):
    out = []
    for row in _rows(df):
        revenue = row.get("Revenue", 0)
        if revenue is None:
            revenue = 0
        if revenue >= threshold:
            out.append(row)
    return out


# ---------- small numpy helpers ----------
def numpy_describe(values):
    # Simple summary using numpy. Skips missing values.
    clean = []
    for v in list(values):
        if pd.isna(v):
            continue
        clean.append(float(v))
    if len(clean) == 0:
        return {"count": 0, "mean": 0, "median": 0, "std": 0,
                "min": 0, "p25": 0, "p75": 0, "max": 0}
    a = np.array(clean)
    result = {}
    result["count"] = len(clean)
    result["mean"] = float(np.mean(a))
    result["median"] = float(np.median(a))
    if len(clean) > 1:
        result["std"] = float(np.std(a, ddof=1))
    else:
        result["std"] = 0.0
    result["min"] = float(np.min(a))
    result["p25"] = float(np.percentile(a, 25))
    result["p75"] = float(np.percentile(a, 75))
    result["max"] = float(np.max(a))
    return result


def correlation(df, col_x, col_y):
    # How strongly do two columns move together? Returns r from -1 to 1.
    xs = []
    ys = []
    for i in range(len(df)):
        x = pd.to_numeric(pd.Series([df[col_x].iloc[i]]), errors="coerce").iloc[0]
        y = pd.to_numeric(pd.Series([df[col_y].iloc[i]]), errors="coerce").iloc[0]
        if pd.isna(x) or pd.isna(y):
            continue
        xs.append(float(x))
        ys.append(float(y))
    if len(xs) < 3:
        return float("nan")
    matrix = np.corrcoef(xs, ys)
    return float(matrix[0, 1])
