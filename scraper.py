"""Optional, respectful SoFIFA listing scraper. Run manually, never from Flask routes."""
from __future__ import annotations

import argparse
import time
from datetime import date
from pathlib import Path

import pandas as pd
import requests
from bs4 import BeautifulSoup

BASE_DIR = Path(__file__).resolve().parent
OUTPUT = BASE_DIR / "data" / "fifa_players_cleaned.csv"
HEADERS = {"User-Agent": "FIFA-Dataset-Analysis educational project contact: repository owner"}


def money_to_millions(value: str) -> float | None:
    value = value.replace("€", "").replace(",", "").strip().upper()
    if not value or value == "-":
        return None
    multiplier = 1 if value.endswith("M") else 0.001 if value.endswith("K") else 0.000001
    try:
        return round(float(value.rstrip("MK")) * multiplier, 4)
    except ValueError:
        return None


def text(row, selector: str) -> str:
    node = row.select_one(selector)
    return node.get_text(" ", strip=True) if node else ""


def scrape_pages(pages: int, delay: float) -> pd.DataFrame:
    rows: list[dict] = []
    session = requests.Session()
    for page in range(pages):
        response = session.get("https://sofifa.com/players", params={"offset": page * 60}, headers=HEADERS, timeout=20)
        response.raise_for_status()
        soup = BeautifulSoup(response.text, "html.parser")
        for row in soup.select("table tbody tr"):
            name_link = row.select_one("a.tooltip")
            name = name_link.get_text(" ", strip=True) if name_link else ""
            if not name:
                continue
            image = row.select_one("img.player-check")
            team_links = row.select("a[title]")
            team = team_links[-1].get("title", "Unknown") if team_links else "Unknown"
            record = {
                "name": name, "team": team, "age": text(row, "td.col"),
                "ova": text(row, "td.col-oa"), "pot": text(row, "td.col-pt"),
                "value_eur_m": money_to_millions(text(row, "td.col-vl")),
                "wage_eur_k": money_to_millions(text(row, "td.col-wg")),
                "total_stats": text(row, "td.col-tt"),
                "image_url": (image.get("data-src") or image.get("data-srcset") or image.get("src", "")) if image else "",
                "source": "SoFIFA public player listing", "snapshot_date": date.today().isoformat(),
            }
            rows.append(record)
        time.sleep(delay)
    frame = pd.DataFrame(rows)
    if frame.empty:
        raise RuntimeError("No player rows were found. The source HTML may have changed; review selectors before retrying.")
    return clean_dataframe(frame)


def clean_dataframe(frame: pd.DataFrame) -> pd.DataFrame:
    numeric = ["age", "ova", "pot", "value_eur_m", "wage_eur_k", "total_stats"]
    for column in numeric:
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    frame = frame.dropna(subset=["name", "team", "age", "ova", "pot"]).copy()
    # Name + team is a transparent, stable de-duplication rule for this listing data.
    return frame.drop_duplicates(subset=["name", "team"], keep="first").sort_values("ova", ascending=False)


if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Manually refresh the local FIFA snapshot.")
    parser.add_argument("--pages", type=int, default=2, choices=range(1, 21), metavar="1-20")
    parser.add_argument("--delay", type=float, default=2.0, help="Seconds to wait between listing pages")
    args = parser.parse_args()
    OUTPUT.parent.mkdir(exist_ok=True)
    data = scrape_pages(args.pages, args.delay)
    data.to_csv(OUTPUT, index=False)
    print(f"Saved {len(data)} unique players to {OUTPUT}")
