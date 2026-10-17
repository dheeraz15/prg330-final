"""Module 5 - Matplotlib charts (pandas + matplotlib + numpy).

Covers every requested variable:
  Release year, Rating, Vote count, Popularity, Runtime,
  Genre, Original language, Release date, Revenue, Budget,
  Cast count, Crew count
Legacy chart functions kept for compatibility.
"""

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


def _prepare_bar_data(data_dict, top_n=10):
    # Sort biggest first and keep the top_n. Returns labels + values.
    items = list(data_dict.items())
    ordered = sorted(items, key=_sort_key, reverse=True)
    top = ordered[:top_n]
    labels = []
    values = []
    for key, value in top:
        labels.append(str(key))
        values.append(value)
    return labels, values


def _sort_key(item):
    return item[1]


def _save(fig, savepath):
    if savepath:
        fig.savefig(savepath, bbox_inches="tight")
    return fig


# ---------- legacy ----------
def plot_boxoffice_by_genre(genre_totals, savepath=None, top_n=8):
    labels, values = _prepare_bar_data(genre_totals, top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title(f"Total Global Box Office by Genre (Top {top_n})")
    ax.set_xlabel("Genre")
    ax.set_ylabel("USD")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax


def plot_count_by_genre(genre_counts, savepath=None):
    labels, values = _prepare_bar_data(genre_counts, top_n=10)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title("Number of Movies by Genre")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Count")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax


def plot_boxoffice_class_pie(class_counts, savepath=None):
    labels = list(class_counts.keys())
    values = list(class_counts.values())
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Movies by Box Office Class")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax


def plot_rating_class_pie(rating_counts, savepath=None):
    labels = list(rating_counts.keys())
    values = list(rating_counts.values())
    fig, ax = plt.subplots(figsize=(6, 6))
    ax.pie(values, labels=labels, autopct="%1.1f%%", startangle=90)
    ax.set_title("Movies by IMDb Rating Class")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax


def plot_yearly_trend(df, savepath=None):
    """Line chart: total global box office + movie count per ReleaseYear."""
    yearly = df.groupby("ReleaseYear").agg(
        total_global=("Global_BoxOfficeUSD", "sum"),
        movie_count=("MovieID", "count"),
    ).reset_index().sort_values("ReleaseYear")

    fig, ax1 = plt.subplots(figsize=(12, 5))
    ax1.plot(yearly["ReleaseYear"].tolist(), yearly["total_global"].tolist())
    ax1.set_xlabel("Release Year")
    ax1.set_ylabel("Total Global Box Office (USD)")
    ax1.set_title("Yearly Trend: Total Global Box Office")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax1


def plot_top_countries(counts, savepath=None, top_n=10):
    labels, values = _prepare_bar_data(counts, top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.barh(labels[::-1], values[::-1])  # biggest on top
    ax.set_title(f"Top {top_n} Countries by Movie Count")
    ax.set_xlabel("Count")
    plt.tight_layout()
    if savepath:
        fig.savefig(savepath)
    return fig, ax


# ---------- TMDB charts (1 per requested variable) ----------
def plot_movies_per_year(year_counts, savepath=None):
    years = sorted(year_counts)
    vals = [year_counts[y] for y in years]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.bar(years, vals)
    ax.set_title("Movies Released per Year")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Movies")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_rating_distribution(ratings, savepath=None):
    # Histogram of ratings with mean and median lines.
    nums = []
    for r in list(ratings):
        if pd.isna(r):
            continue
        nums.append(float(r))
    mean_val = float(np.mean(nums))
    median_val = float(np.median(nums))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(nums, bins=20)
    ax.axvline(mean_val, linestyle="--", label="mean " + str(round(mean_val, 2)))
    ax.axvline(median_val, linestyle=":", label="median " + str(round(median_val, 2)))
    ax.set_title("Rating Distribution (vote_average 0-10)")
    ax.set_xlabel("Rating")
    ax.set_ylabel("Movies")
    ax.legend()
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_votes_vs_rating(df, savepath=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(df["Vote_Count"], df["Rating"], alpha=0.6, s=18)
    ax.set_xscale("log")
    ax.set_title("Votes vs Rating (log x-scale)")
    ax.set_xlabel("Vote count (log)")
    ax.set_ylabel("Rating")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_popularity_by_year(avg_pop_by_year, savepath=None):
    years = sorted(avg_pop_by_year)
    vals = [avg_pop_by_year[y] for y in years]
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(years, vals, marker="o")
    ax.set_title("Average Popularity by Year")
    ax.set_xlabel("Release year")
    ax.set_ylabel("Mean popularity")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_runtime_distribution(runtimes, savepath=None):
    # Histogram of runtimes (skips 0 / missing).
    nums = []
    for r in list(runtimes):
        number = pd.to_numeric(pd.Series([r]), errors="coerce").iloc[0]
        if pd.isna(number):
            continue
        if number <= 0:
            continue
        nums.append(float(number))
    median_val = float(np.median(nums))
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(nums, bins=20)
    ax.axvline(median_val, linestyle="--", label="median " + str(int(median_val)) + " min")
    ax.set_title("Runtime Distribution (minutes)")
    ax.set_xlabel("Runtime (min)")
    ax.set_ylabel("Movies")
    ax.legend()
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_movies_by_genre(genre_counts, savepath=None, top_n=12):
    labels, values = _prepare_bar_data(genre_counts, top_n)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(labels, values)
    ax.set_title(f"Movies by Genre (Top {top_n}, multi-counted)")
    ax.set_xlabel("Genre")
    ax.set_ylabel("Movies")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_movies_by_language(lang_counts, savepath=None, top_n=10):
    labels, values = _prepare_bar_data(lang_counts, top_n)
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(labels, values)
    ax.set_title(f"Movies by Original Language (Top {top_n})")
    ax.set_xlabel("Language")
    ax.set_ylabel("Movies")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_releases_over_time(df, savepath=None):
    # Line chart of release counts per year.
    dates = pd.to_datetime(df["ReleaseDate"], errors="coerce")
    dates = dates.dropna()
    if len(dates) == 0:
        fig, ax = plt.subplots(figsize=(10, 4))
        ax.text(0.5, 0.5, "No valid release dates", ha="center")
        return _save(fig, savepath), ax
    per_year = dates.dt.year.value_counts()
    per_year = per_year.sort_index()
    xs = list(per_year.index)
    ys = list(per_year.values)
    fig, ax = plt.subplots(figsize=(12, 5))
    ax.plot(xs, ys, marker="o")
    ax.set_title("Releases Over Time (by release date)")
    ax.set_xlabel("Release date (year)")
    ax.set_ylabel("Movies")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_revenue_by_genre(revenue_by_genre, savepath=None, top_n=12):
    labels, values = _prepare_bar_data(revenue_by_genre, top_n)
    fig, ax = plt.subplots(figsize=(11, 5))
    ax.bar(labels, values)
    ax.set_title(f"Total Revenue by Genre (Top {top_n})")
    ax.set_xlabel("Genre")
    ax.set_ylabel("USD")
    plt.xticks(rotation=30, ha="right")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_budget_vs_revenue(df, savepath=None):
    sub = df[(df["Budget"] > 0) & (df["Revenue"] > 0)]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(sub["Budget"], sub["Revenue"], alpha=0.6, s=20)
    ax.set_xscale("log")
    ax.set_yscale("log")
    # break-even line
    lims = [max(sub["Budget"].min(), 1), sub["Budget"].max()]
    ax.plot(lims, lims, linestyle="--", label="break-even")
    ax.plot(lims, [v * 2 for v in lims], linestyle=":", label="2x (profitable)")
    ax.set_title("Budget vs Revenue (log-log)")
    ax.set_xlabel("Budget USD (log)")
    ax.set_ylabel("Revenue USD (log)")
    ax.legend()
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_cast_vs_rating(df, savepath=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(df["Cast_Count"], df["Rating"], alpha=0.6, s=20)
    ax.set_title("Cast Size vs Rating")
    ax.set_xlabel("Cast count")
    ax.set_ylabel("Rating")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_crew_vs_rating(df, savepath=None):
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(df["Crew_Count"], df["Rating"], alpha=0.6, s=20)
    ax.set_title("Crew Size vs Rating")
    ax.set_xlabel("Crew count")
    ax.set_ylabel("Rating")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_correlation_bars(names, r_values, savepath=None):
    # Simple bar chart of correlation numbers (r from -1 to 1).
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(names, r_values)
    ax.set_title("How strongly each pair moves together (r)")
    ax.set_xlabel("Pair")
    ax.set_ylabel("r")
    plt.xticks(rotation=20, ha="right")
    plt.tight_layout()
    return _save(fig, savepath), ax


def plot_simple_scatter(xs, ys, x_name, y_name, title, savepath=None):
    # Plain x-y scatter. No log scale, no colours, no sizes.
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.scatter(xs, ys, alpha=0.6, s=20)
    ax.set_title(title)
    ax.set_xlabel(x_name)
    ax.set_ylabel(y_name)
    plt.tight_layout()
    return _save(fig, savepath), ax
