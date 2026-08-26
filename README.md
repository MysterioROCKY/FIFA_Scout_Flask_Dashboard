# FIFA Scout — Flask dashboard

A responsive football analytics dashboard built from the original FIFA web-scraping notebook. The public app reads a local, versioned CSV snapshot, so visitors never trigger a third-party scrape.

## What changed from the notebook

- Scraping is in `scraper.py`, separate from the web app.
- The scraper uses BeautifulSoup selectors, a timeout, a clear user-agent, real pagination offsets, and a polite delay.
- Numeric/currency fields are cleaned before saving. `€120.5M` becomes `120.5` in `value_eur_m`; `€50K` becomes `50` in `wage_eur_k`.
- Duplicates are removed using `name + team`, instead of dropping hundreds of rows without explanation.
- `Hits` is excluded because it represents page engagement, not football goals.
- `DataFrame.append()` is not used.

The included CSV is a small starter snapshot assembled from examples recorded in the original notebook output. It is dated 2020-12-01 and is deliberately labelled as such in the UI. Refresh it only after you review the data source's current robots.txt and Terms of Service.

## Features

- Dashboard filters, KPI cards, and five interactive Chart.js charts.
- Searchable/sortable/paginated DataTables player listing and player-detail modal.
- Wonderkids section, sortable by potential, value, or overall rating.
- Two-player radar comparison.
- JSON API: `/api/dashboard`, `/api/players`, `/api/wonderkids`, and `/api/compare`.
- Production command with Gunicorn for Render or Google Cloud Run.

## Run locally

Prerequisite: Python 3.10+. The pinned pandas release supports Python 3.14 as well.

```powershell
cd "C:\Users\sanyaagr\Documents\ChatGPT\FIFA_Dataset_Analysis--Web_Scraping"
py -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
python app.py
```

Open `http://127.0.0.1:5000`. Check Dashboard, Players, Compare, About data, then run these browser/API checks:

```powershell
Invoke-WebRequest http://127.0.0.1:5000/health
Invoke-WebRequest http://127.0.0.1:5000/api/dashboard
```

## Optional manual dataset refresh

Never expose this action through a public route. First check the source site's current permissions, then run:

```powershell
python scraper.py --pages 2 --delay 2
```

Review `data/fifa_players_cleaned.csv`, test the UI again, and commit the new snapshot only if it is correct.

## GitHub

Create an empty GitHub repository first, then from this folder:

```powershell
git add .
git commit -m "Build FIFA Scout Flask dashboard"
git branch -M main
git remote add origin https://github.com/YOUR-USERNAME/FIFA_Dataset_Analysis--Web_Scraping.git
git push -u origin main
```

If your existing GitHub repository already contains files, use its URL in `git remote add origin`, inspect the remote before pushing, and resolve any history difference rather than force-pushing.

## Render deployment

1. Push the tested project to GitHub.
2. Sign in at Render and choose **New → Web Service**.
3. Connect the repository and choose branch `main`.
4. Set Build Command to `pip install -r requirements.txt`.
5. Set Start Command to `gunicorn --bind 0.0.0.0:$PORT app:app`.
6. Choose the Free instance type and deploy.

Render deploys Flask apps from GitHub automatically. Its free web services sleep after 15 minutes of inactivity, so the first request after sleep can take around a minute. Do not store runtime uploads or a SQLite database on this free instance because its local filesystem is ephemeral.

## Google Cloud Run deployment (optional)

Cloud Run is a good next step once the local app is approved. It requires a Google Cloud project with billing enabled.

```powershell
gcloud auth login
gcloud config set project YOUR_PROJECT_ID
gcloud run deploy fifa-scout --source . --region asia-south1 --allow-unauthenticated
```

Choose the displayed service URL after deployment. Set a Cloud Billing budget alert before making the service public. Cloud Run has a usage-based free tier, but costs can occur if you exceed it.

## Project layout

```text
app.py                         Flask routes and JSON API
scraper.py                     optional manual scraper
data/fifa_players_cleaned.csv  local dataset snapshot
templates/                     Jinja/Bootstrap pages
static/                        site CSS and dashboard JavaScript
Procfile                       Gunicorn command for Render
requirements.txt               Python dependencies
```
