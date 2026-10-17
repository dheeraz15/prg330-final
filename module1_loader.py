"""Module 1 - Data loading and cleaning (pandas + numpy).

Supports BOTH:
  (a) legacy synthetic CSV (movies_dataset.csv) and
  (b) TMDB API dump (data/tmdb_movies.csv) — the current default.

TMDB columns:
  MovieID, Title, ReleaseDate, ReleaseYear, Original_Language,
  Rating, Vote_Count, Popularity, Runtime, Budget, Revenue,
  Cast_Count, Crew_Count, Genres, Primary_Genre
"""

import numpy as np
import pandas as pd

MOVIE_COLUMNS = [
    "MovieID", "Title", "Genre", "ReleaseYear", "ReleaseDate", "Country",
    "BudgetUSD", "US_BoxOfficeUSD", "Global_BoxOfficeUSD",
    "Opening_Day_SalesUSD", "One_Week_SalesUSD",
    "IMDbRating", "RottenTomatoesScore", "NumVotesIMDb", "NumVotesRT",
    "Director", "LeadActor",
]

TMDB_COLUMNS = [
    "MovieID", "Title", "ReleaseDate", "ReleaseYear", "Original_Language",
    "Rating", "Vote_Count", "Popularity", "Runtime", "Budget", "Revenue",
    "Cast_Count", "Crew_Count", "Genres", "Primary_Genre",
]

TMDB_NUMERIC = ["ReleaseYear", "Rating", "Vote_Count", "Popularity",
                "Runtime", "Budget", "Revenue", "Cast_Count", "Crew_Count"]
TMDB_TEXT = ["Title", "ReleaseDate", "Original_Language", "Genres", "Primary_Genre"]


def load_data(filepath, nrows=None):
    # Read a CSV file into a DataFrame.
    df = pd.read_csv(filepath, nrows=nrows)
    return df


def load_tmdb(filepath="data/tmdb_movies.csv"):
    # Shortcut for the TMDB file.
    return load_data(filepath)


def clean_data(df):
    # Clean legacy OR TMDB tables.
    # Steps: tidy text, turn numbers into numbers,
    # fill missing years from the date, add Profit and ROI.
    df = df.copy()

    # TMDB table has Rating and Revenue columns.
    is_tmdb = "Rating" in df.columns and "Revenue" in df.columns

    if is_tmdb:
        # 1. Tidy text columns.
        for col in TMDB_TEXT:
            if col in df.columns:
                df[col] = df[col].astype(str)
                df[col] = df[col].str.strip()

        # 2. Empty genre becomes Unknown.
        if "Genres" in df.columns:
            df["Genres"] = df["Genres"].replace("", "Unknown")
            df["Primary_Genre"] = df["Primary_Genre"].replace("", "Unknown")

        # 3. Turn number columns into numbers.
        for col in TMDB_NUMERIC:
            if col in df.columns:
                df[col] = pd.to_numeric(df[col], errors="coerce")
                df[col] = df[col].fillna(0)

        # 4. If ReleaseYear is 0, take the year from ReleaseDate.
        # Example: "2019-07-20" -> 2019.
        if "ReleaseDate" in df.columns:
            years = []
            for value in df["ReleaseDate"]:
                year = 0
                text = str(value)
                if len(text) >= 4:
                    part = text[:4]
                    if part.isdigit():
                        year = int(part)
                years.append(year)
            new_years = []
            for old_year, new_year in zip(df["ReleaseYear"], years):
                if old_year == 0:
                    new_years.append(new_year)
                else:
                    new_years.append(int(old_year))
            df["ReleaseYear"] = new_years

        # 5. Profit = Revenue - Budget. ROI = Revenue / Budget.
        profits = []
        rois = []
        for budget, revenue in zip(df["Budget"], df["Revenue"]):
            profits.append(revenue - budget)
            if budget > 0:
                rois.append(revenue / budget)
            else:
                rois.append(float("nan"))
        df["Profit"] = profits
        df["ROI"] = rois

        df = df.drop_duplicates()
        df = df.reset_index(drop=True)
        return df

    # Legacy table cleaning.
    for col in ["Title", "Genre", "Country", "Director", "LeadActor"]:
        if col in df.columns:
            df[col] = df[col].astype(str)
            df[col] = df[col].str.strip()

    numeric_cols = [
        "BudgetUSD", "US_BoxOfficeUSD", "Global_BoxOfficeUSD",
        "Opening_Day_SalesUSD", "One_Week_SalesUSD",
        "IMDbRating", "RottenTomatoesScore",
        "NumVotesIMDb", "NumVotesRT", "ReleaseYear",
    ]
    for col in numeric_cols:
        if col in df.columns:
            df[col] = pd.to_numeric(df[col], errors="coerce")
            df[col] = df[col].fillna(0)

    df = df.drop_duplicates()
    df = df.reset_index(drop=True)
    return df


def get_summary(df):
    # Return row count, column names and column types.
    types = {}
    for col in df.columns:
        types[col] = str(df[col].dtype)
    return len(df), list(df.columns), types


def tmdb_completeness(df):
    # Count rows that have Budget, Revenue and Runtime.
    good = 0
    for i in range(len(df)):
        row = df.iloc[i]
        if row["Budget"] > 0 and row["Revenue"] > 0 and row["Runtime"] > 0:
            good = good + 1
    return good, len(df)
