#!/usr/bin/env python3
"""Render a kid's weekly check-off chart from profile + rotation.

Prototype of the `build-packet` chart step. It goes straight from the rotation rules to
HTML, skipping the weekly plan, so it works before the planner exists.

    python3 render/make_chart.py son                 # output/son/chart.html, blank "Week of ___"
    python3 render/make_chart.py daughter --week 2026-W45
"""
import argparse
import datetime as dt
import pathlib
import sys

import yaml
from jinja2 import Environment, FileSystemLoader, select_autoescape

ROOT = pathlib.Path(__file__).resolve().parent.parent
DAYS = ["mon", "tue", "wed", "thu", "fri", "sat", "sun"]
DAY_LABELS = dict(zip(DAYS, ["Mon", "Tue", "Wed", "Thu", "Fri", "Sat", "Sun"]))


def load(path):
    with open(path) as f:
        return yaml.safe_load(f)


def week_dates(week):
    """'2026-W45' -> (monday, sunday) as dates."""
    year, w = week.split("-W")
    monday = dt.date.fromisocalendar(int(year), int(w), 1)
    return monday, monday + dt.timedelta(days=6)


def build_rows(profile, rotation):
    """Merge rotation rows by area into one chart row each, cells keyed by day."""
    areas = profile["areas"]
    rows, index = [], {}
    for r in rotation["rows"]:
        area = r["area"]
        spec = areas.get(area, {})
        if area not in index:
            index[area] = len(rows)
            rows.append({
                "area": area,
                "label": spec.get("label") or area.replace("_", " ").capitalize(),
                "icon": spec.get("icon", ""),
                "minutes": spec.get("minutes"),
                "outside_block": bool(spec.get("outside_block")),
                "cells": {},
            })
        row = rows[index[area]]
        for d in r["days"]:
            row["cells"][d] = {
                "minutes": r.get("minutes", spec.get("minutes")),
                "external": bool(r.get("external")),
                "label": r.get("label", ""),
            }
    # outside-the-block rows (bedtime reading) go last, under a divider
    rows.sort(key=lambda r: r["outside_block"])
    return rows


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kid")
    ap.add_argument("--week", help="ISO week like 2026-W45; omit for a blank 'Week of ___' line")
    ap.add_argument("--out", help="output path (default output/<kid>/chart[-<week>].html)")
    ap.add_argument("--blank", action="store_true",
                    help="discussion copy: no dates, minutes or boxes; empty grid to fill in by hand")
    args = ap.parse_args()

    profile = load(ROOT / "profiles" / args.kid / "profile.yaml")
    rotation = load(ROOT / "schedules" / args.kid / "rotation.yaml")
    profile.setdefault("chart", {}).setdefault("style", "words")

    week = None
    dates = {}
    if args.week:
        mon, sun = week_dates(args.week)
        week = {"id": args.week, "starts": mon.strftime("%b %-d"), "ends": sun.strftime("%b %-d")}
        dates = {d: (mon + dt.timedelta(days=i)).strftime("%-m/%-d") for i, d in enumerate(DAYS)}

    modes = {} if args.blank else rotation.get("day_modes", {})
    days = [{"key": d, "label": DAY_LABELS[d], "date": dates.get(d), "mode": modes.get(d, "normal")} for d in DAYS]

    rows = build_rows(profile, rotation)
    if args.blank:
        for row in rows:
            row["minutes"] = None
            row["cells"] = {}          # empty cells: days get decided on paper

    env = Environment(loader=FileSystemLoader(ROOT / "render" / "templates"), autoescape=select_autoescape(["html"]))
    html = env.get_template("chart.html.j2").render(
        kid=profile, week=week, days=days, rows=rows, blank=args.blank,
        rotation_version=rotation.get("version", "?"),
    )

    out = pathlib.Path(args.out) if args.out else ROOT / "output" / args.kid / (
        (f"chart-blank-{args.week}.html" if args.week else "chart-blank.html") if args.blank
        else (f"chart-{args.week}.html" if args.week else "chart.html"))
    out.parent.mkdir(parents=True, exist_ok=True)
    out.write_text(html)
    print(out.relative_to(ROOT))
    if profile.get("status") == "draft":
        print(f"warning: {args.kid} profile is a draft; fill in TBD fields", file=sys.stderr)


if __name__ == "__main__":
    main()
