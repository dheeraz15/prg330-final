"""Module 2 - Conditionals (classify one value at a time with if/elif/else).

Keeps the legacy classifiers AND adds TMDB classifiers for the new schema.
Pure Python conditions - no imports needed here.
"""


# ---------- legacy (synthetic CSV) ----------
def classify_boxoffice(global_boxoffice):
    """Classify a movie by its global box office gross."""
    if global_boxoffice >= 100_000_000:
        return "Blockbuster"
    elif global_boxoffice >= 20_000_000:
        return "Hit"
    elif global_boxoffice >= 5_000_000:
        return "Average"
    else:
        return "Flop"


def classify_rating(imdb_rating):
    """Classify a movie by its IMDb/TMDB rating (0-10 scale)."""
    if imdb_rating >= 8.0:
        return "Excellent"
    elif imdb_rating >= 6.5:
        return "Good"
    elif imdb_rating >= 5.0:
        return "Average"
    else:
        return "Poor"


def classify_budget(budget):
    """Classify a movie by its production budget (legacy thresholds)."""
    if budget >= 50_000_000:
        return "Big Budget"
    elif budget >= 10_000_000:
        return "Mid Budget"
    else:
        return "Low Budget"


def classify_era(year):
    """Classify a movie by its release era."""
    if year < 1980:
        return "Classic (before 1980)"
    elif year < 2000:
        return "Retro (1980-1999)"
    elif year < 2015:
        return "Modern (2000-2014)"
    else:
        return "Recent (2015+)"


def is_profitable(budget, global_boxoffice):
    """Returns True if box office covers at least 2x the budget."""
    if budget <= 0:
        return False
    return global_boxoffice >= 2 * budget


# ---------- TMDB additions ----------
def classify_runtime(runtime_min):
    """Bucket runtime in minutes."""
    if runtime_min <= 0:
        return "Unknown"
    if runtime_min < 90:
        return "Short (<90m)"
    elif runtime_min <= 120:
        return "Standard (90-120m)"
    elif runtime_min <= 150:
        return "Long (121-150m)"
    else:
        return "Epic (>150m)"


def classify_popularity(pop):
    """Bucket TMDB popularity score."""
    if pop < 10:
        return "Niche (<10)"
    elif pop < 40:
        return "Known (10-40)"
    elif pop < 100:
        return "Popular (40-100)"
    else:
        return "Viral (100+)"


def classify_budget_tmdb(budget):
    """Budget buckets tuned for real TMDB dollar values."""
    if budget <= 0:
        return "Unknown"
    if budget < 1_000_000:
        return "Micro (<$1M)"
    elif budget < 10_000_000:
        return "Indie ($1-10M)"
    elif budget < 100_000_000:
        return "Mid ($10-100M)"
    else:
        return "Big ($100M+)"


def classify_votes(votes):
    """Bucket vote counts (proxy for audience size)."""
    if votes < 100:
        return "Obscure (<100)"
    elif votes < 1_000:
        return "Few (100-1k)"
    elif votes < 10_000:
        return "Solid (1k-10k)"
    else:
        return "Massive (10k+)"


def classify_revenue(revenue):
    """Bucket revenue in dollars."""
    if revenue <= 0:
        return "Unknown"
    if revenue < 10_000_000:
        return "Small (<$10M)"
    elif revenue < 100_000_000:
        return "Mid ($10-100M)"
    elif revenue < 500_000_000:
        return "Big ($100-500M)"
    else:
        return "Huge ($500M+)"
