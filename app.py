"""Flask dashboard for exploring a cleaned FIFA player-data snapshot."""
from __future__ import annotations

import os
from datetime import date
from pathlib import Path
from typing import Any

import pandas as pd
from flask import Flask, jsonify, render_template, request

BASE_DIR = Path(__file__).resolve().parent
DATA_PATH = BASE_DIR / "data" / "fifa_players_cleaned.csv"
REQUIRED_COLUMNS = {
    "name", "team", "age", "ova", "pot", "value_eur_m", "wage_eur_k",
    "total_stats", "image_url", "source", "snapshot_date",
}

app = Flask(__name__)
app.config.update(JSON_SORT_KEYS=False, TEMPLATES_AUTO_RELOAD=True)


def load_players() -> pd.DataFrame:
    """Load the local snapshot only; public requests never scrape the source website."""
    if not DATA_PATH.exists():
        raise FileNotFoundError(f"Dataset not found: {DATA_PATH}")
    frame = pd.read_csv(DATA_PATH)
    missing = REQUIRED_COLUMNS - set(frame.columns)
    if missing:
        raise ValueError(f"Dataset is missing columns: {', '.join(sorted(missing))}")
    for column in ("age", "ova", "pot", "value_eur_m", "wage_eur_k", "total_stats"):
        frame[column] = pd.to_numeric(frame[column], errors="coerce")
    return frame.dropna(subset=["name", "team", "age", "ova", "pot"]).copy()


def number_arg(name: str, minimum: float, maximum: float) -> float | None:
    raw = request.args.get(name)
    if raw in (None, ""):
        return None
    try:
        value = float(raw)
    except ValueError as exc:
        raise ValueError(f"{name} must be a number") from exc
    if not minimum <= value <= maximum:
        raise ValueError(f"{name} must be between {minimum:g} and {maximum:g}")
    return value


def filtered_players(frame: pd.DataFrame) -> pd.DataFrame:
    """Apply validated query-string filters used by both API routes."""
    minimums = {
        "min_age": ("age", 14, 50), "max_age": ("age", 14, 50),
        "min_ova": ("ova", 1, 99), "min_pot": ("pot", 1, 99),
        "max_value": ("value_eur_m", 0, 1000),
    }
    result = frame
    for query_name, (column, lower, upper) in minimums.items():
        value = number_arg(query_name, lower, upper)
        if value is None:
            continue
        result = result[result[column] <= value] if query_name.startswith("max_") else result[result[column] >= value]
    team = request.args.get("team", "").strip()
    if team:
        result = result[result["team"].str.casefold() == team.casefold()]
    return result


def records(frame: pd.DataFrame) -> list[dict[str, Any]]:
    # Cast first: otherwise pandas keeps float columns as floats and serializes
    # missing values as JavaScript-invalid NaN instead of JSON null.
    safe_frame = frame.astype(object).where(pd.notna(frame), None)
    return safe_frame.to_dict(orient="records")


@app.get("/")
def index() -> str:
    players = load_players()
    return render_template("index.html", teams=sorted(players["team"].unique()))


@app.get("/players")
def players_page() -> str:
    players = load_players()
    return render_template("players.html", teams=sorted(players["team"].unique()))


@app.get("/compare")
def compare_page() -> str:
    players = load_players().sort_values("name")
    return render_template("compare.html", players=records(players))


@app.get("/about")
def about_page() -> str:
    return render_template("about.html")


@app.get("/api/players")
def api_players():
    try:
        data = filtered_players(load_players())
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    return jsonify(players=records(data), count=len(data))


@app.get("/api/dashboard")
def api_dashboard():
    try:
        data = filtered_players(load_players())
    except ValueError as exc:
        return jsonify(error=str(exc)), 400
    if data.empty:
        return jsonify(error="No players match those filters."), 404
    top_potential = data.nlargest(10, "pot")[["name", "pot"]]
    top_value = data.nlargest(10, "value_eur_m")[["name", "value_eur_m"]]
    return jsonify(
        summary={
            "count": len(data), "avg_age": round(float(data.age.mean()), 1),
            "avg_ova": round(float(data.ova.mean()), 1),
            "highest_potential": data.loc[data.pot.idxmax(), "name"],
        },
        charts={
            "ova": records(data.groupby("ova").size().rename("count").reset_index()),
            "age": records(data.groupby("age").size().rename("count").reset_index()),
            "scatter": records(data[["name", "team", "ova", "pot", "value_eur_m"]]),
            "top_potential": records(top_potential), "top_value": records(top_value),
        },
    )


@app.get("/api/wonderkids")
def api_wonderkids():
    data = load_players()
    result = data[(data.age <= 21) & (data.pot >= 85)].sort_values(["pot", "ova"], ascending=False)
    return jsonify(players=records(result), count=len(result))


@app.get("/api/compare")
def api_compare():
    first, second = request.args.get("first", "").strip(), request.args.get("second", "").strip()
    if not first or not second or first == second:
        return jsonify(error="Choose two different players."), 400
    data = load_players()
    chosen = data[data.name.isin([first, second])]
    if len(chosen) != 2:
        return jsonify(error="One or both selected players were not found."), 404
    return jsonify(players=records(chosen))


@app.get("/health")
def health():
    return jsonify(status="ok", dataset_exists=DATA_PATH.exists(), checked_on=date.today().isoformat())


if __name__ == "__main__":
    app.run(host="127.0.0.1", port=int(os.getenv("PORT", "5000")), debug=True)
