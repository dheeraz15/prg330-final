import csv
import gzip
import io
import time

import requests
from bs4 import BeautifulSoup


HEADERS = {"User-Agent": "CollegeMovieProject/1.0 (student data analysis project; python-requests)"}

WIKI_URL = "https://en.wikipedia.org/wiki/List_of_American_films_of_{}"
IMDB_RATINGS_URL = "https://datasets.imdbws.com/title.ratings.tsv.gz"
IMDB_BASICS_URL = "https://datasets.imdbws.com/title.basics.tsv.gz"

MOVIE_COLUMNS = ["Year", "Month", "Day", "Title", "Director", "Cast", "Genre",
                 "Studio", "Cast_Crew", "Notes", "Source_URL"]
BOX_OFFICE_COLUMNS = ["Year", "Rank", "Title", "Distributor", "Domestic_Gross"]
IMDB_COLUMNS = ["IMDb_ID", "IMDb_Title", "Original_Title", "Year", "Runtime",
                "Genres", "Rating", "Votes"]


def get_page(url):
    """Downloads a web page and returns it as BeautifulSoup (None if the request fails)"""
    try:
        response = requests.get(url, headers=HEADERS, timeout=30)
    except requests.RequestException as error:
        print("Request error:", url, error)
        return None

    if response.status_code != 200:
        print("Failed:", url, "status", response.status_code)
        return None

    return BeautifulSoup(response.text, "html.parser")


def to_int(value, default=1):
    try:
        return int(str(value).strip().rstrip(";"))
    except ValueError:
        return default


def table_to_rows(table):
    """Turns an HTML table into a list of rows (each row is a list of cell texts).
    A cell with rowspan (like the month / day column) is copied into every row it covers."""
    rows = []
    carry = {}   # column number -> [text, rows still to fill]

    for tr in table.find_all("tr"):
        cells = tr.find_all(["th", "td"], recursive=False)
        row = []
        col = 0
        next_cell = 0

        while next_cell < len(cells) or col in carry:

            if col in carry:
                text, rows_left = carry[col]
                row.append(text)

                if rows_left == 1:
                    del carry[col]
                else:
                    carry[col][1] = rows_left - 1

                col += 1
                continue

            cell = cells[next_cell]
            next_cell += 1
            text = cell.get_text(" ", strip=True)
            colspan = to_int(cell.get("colspan", 1))
            rowspan = to_int(cell.get("rowspan", 1))

            for _ in range(colspan):
                row.append(text)
                if rowspan > 1:
                    carry[col] = [text, rowspan - 1]
                col += 1

        rows.append(row)

    return rows


def make_header(header_row):
    """'Opening' spans two columns (month and day) - give them separate names"""
    header = []

    for name in header_row:
        name = name.strip()

        if name == "Opening":
            if "Month" in header:
                name = "Day"
            else:
                name = "Month"

        header.append(name)

    return header


def find_value(record, *keywords):
    """Returns the value of the first column whose name contains one of the keywords"""
    for column, value in record.items():
        for keyword in keywords:
            if keyword in column.lower():
                return value
    return ""


def scrape_year(year):
    """Scrapes one Wikipedia page -> (list of movies, list of box office rows)"""
    url = WIKI_URL.format(year)
    soup = get_page(url)
    movies = []
    box_office = []

    if soup is None:
        return movies, box_office

    for table in soup.select("table.wikitable"):
        rows = table_to_rows(table)

        if len(rows) < 2:
            continue

        header = make_header(rows[0])

        if "Title" not in header:
            continue

        is_box_office = "Rank" in header

        for row in rows[1:]:
            if row == rows[0]:                # repeated header row
                continue

            record = dict(zip(header, row))
            title = record.get("Title", "")

            if title == "":
                continue

            if is_box_office:
                box_office.append({
                    "Year": year,
                    "Rank": record.get("Rank", ""),
                    "Title": title,
                    "Distributor": find_value(record, "distributor"),
                    "Domestic_Gross": find_value(record, "gross"),
                })
            else:
                movies.append({
                    "Year": year,
                    "Month": record.get("Month", ""),
                    "Day": record.get("Day", ""),
                    "Title": title,
                    "Director": find_value(record, "director"),
                    "Cast": record.get("Cast", ""),
                    "Genre": find_value(record, "genre"),
                    "Studio": find_value(record, "production", "studio"),
                    "Cast_Crew": find_value(record, "cast and crew"),
                    "Notes": find_value(record, "note"),
                    "Source_URL": url,
                })

    return movies, box_office


def scrape_all_years(start_year, end_year, movie_file, box_office_file, delay=1.0):
    """Scrapes every year from start_year to end_year and saves two raw CSV files"""
    all_movies = []
    all_box_office = []

    for year in range(start_year, end_year + 1):
        movies, box_office = scrape_year(year)
        all_movies += movies
        all_box_office += box_office
        print(f"{year}: {len(movies):>4} movies, {len(box_office):>2} box office rows"
              f"   (total so far: {len(all_movies):,})")
        time.sleep(delay)              # be polite to Wikipedia's servers

    write_rows(movie_file, all_movies, MOVIE_COLUMNS)
    write_rows(box_office_file, all_box_office, BOX_OFFICE_COLUMNS)

    return len(all_movies), len(all_box_office)


def write_rows(filename, rows, columns):
    with open(filename, "w", newline="", encoding="utf-8") as file:
        writer = csv.DictWriter(file, fieldnames=columns)
        writer.writeheader()
        writer.writerows(rows)


def open_imdb_file(url):
    """Streams a .tsv.gz file from IMDb and returns a csv reader (no need to save the big file)"""
    response = requests.get(url, headers=HEADERS, stream=True, timeout=60)
    response.raise_for_status()
    text = io.TextIOWrapper(gzip.GzipFile(fileobj=response.raw), encoding="utf-8")
    return csv.reader(text, delimiter="\t", quoting=csv.QUOTE_NONE)


def download_imdb_data(output_file, min_votes=20):
    """Downloads IMDb's official dataset and keeps only movies that have a rating.
    IMDb blocks scrapers (bot challenge), but offers these files free for non-commercial use."""
    ratings = {}
    reader = open_imdb_file(IMDB_RATINGS_URL)
    next(reader)                       # skip header

    for imdb_id, rating, votes in reader:
        if int(votes) >= min_votes:
            ratings[imdb_id] = (rating, votes)

    print(f"Ratings loaded: {len(ratings):,} titles with {min_votes}+ votes")

    movies = []
    reader = open_imdb_file(IMDB_BASICS_URL)
    next(reader)

    for row in reader:
        imdb_id, title_type, title, original, is_adult, year, _, runtime, genres = row

        if title_type != "movie" or is_adult == "1" or imdb_id not in ratings:
            continue

        rating, votes = ratings[imdb_id]
        movies.append({
            "IMDb_ID": imdb_id,
            "IMDb_Title": title,
            "Original_Title": original,
            "Year": year,
            "Runtime": runtime,
            "Genres": genres,
            "Rating": rating,
            "Votes": votes,
        })

    write_rows(output_file, movies, IMDB_COLUMNS)
    print(f"IMDb movies saved: {len(movies):,}")

    return len(movies)
