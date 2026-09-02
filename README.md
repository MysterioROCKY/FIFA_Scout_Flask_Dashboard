# FIFA Scout — Flask Dashboard

A responsive football analytics dashboard built from a FIFA web-scraping notebook. It turns a Python Jupiter notebook-based analysis into an interactive Flask website with player exploration, filtering, charts, wonderkids, and player comparison.

The deployed dashboard reads a local, versioned CSV snapshot. Visitors do not trigger web scraping when they open the site.

## Live Demo

**Live Application:** https://fifa-scout-sanyam.onrender.com/

**Note:** The application is deployed on Render's free tier. If it has been inactive for some time, the service may take a short time to start when you first open the link.

## Features

- Interactive dashboard with player count, average age, average overall rating, and highest-potential player.
- Chart.js visualizations for rating and age distributions, overall vs potential, top potential, and market value.
- Searchable, sortable, paginated player table with detail modal.
- Filters for age, overall rating, potential, team, and market value.
- Wonderkids section for players aged 21 or under with a potential score of at least 85.
- Two-player radar comparison.
- JSON endpoints: `/api/dashboard`, `/api/players`, `/api/wonderkids`, `/api/compare`, and `/health`.
- Optional, manual scraper separated from the public Flask routes.

## Project structure

```text
app.py                         Flask routes and JSON API
scraper.py                     Optional manual data-refresh script
data/fifa_players_cleaned.csv  Local player-data snapshot
templates/                     Jinja and Bootstrap templates
static/                        Custom CSS and dashboard JavaScript
requirements.txt               Python dependencies
Procfile                       Gunicorn command for Render
```

## Run locally

Prerequisites: Python 3.10 or later and Git.

```powershell
git clone https://github.com/MysterioROCKY/FIFA_Scout_Flask_Dashboard.git
cd FIFA_Scout_Flask_Dashboard
py -m venv .venv
.\.venv\Scripts\python.exe -m pip install --upgrade pip
.\.venv\Scripts\python.exe -m pip install --only-binary=:all: -r requirements.txt
.\.venv\Scripts\python.exe app.py
```

Open `http://127.0.0.1:5000` in a browser.

## Data and quality improvements

The original notebook scraped player data directly into a pandas DataFrame. This project improves that workflow:

- Scraping is isolated in `scraper.py`; the website reads the prepared CSV.
- HTML is parsed using BeautifulSoup selectors rather than regular expressions.
- Requests use a timeout, a clear user-agent, pagination offsets, and a delay between source pages.
- Currency values are converted into numeric values (`€120.5M` becomes `120.5` in `value_eur_m`).
- Duplicates are removed using player name plus team.
- The original `Hits` field is not treated as goals; it represents source-site engagement.
- Deprecated `DataFrame.append()` is not used.

The bundled starter snapshot is based on examples recorded in the original notebook output and is dated `2020-12-01`. It is not current FIFA data.

## Refresh the dataset manually

Only refresh after checking the source website's current `robots.txt` and Terms of Service. Do not add the scraper to a public website route.

```powershell
.\.venv\Scripts\python.exe scraper.py --pages 2 --delay 2
```

`--pages 2` requests two source listing pages. `--delay 2` waits two seconds between source requests. The command overwrites `data/fifa_players_cleaned.csv` with cleaned, de-duplicated results.

After reviewing the CSV locally, commit and push it:

```powershell
git add data/fifa_players_cleaned.csv
git commit -m "Refresh FIFA player dataset"
git push
```
## Disclaimer

This is an educational portfolio project. FIFA and related player data belong to their respective owners. Check a data source's permissions before scraping or redistributing its data.
