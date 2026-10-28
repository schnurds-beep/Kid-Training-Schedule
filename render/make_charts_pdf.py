#!/usr/bin/env python3
"""Combine each kid's chart into one landscape PDF, one kid per page.

    python3 render/make_charts_pdf.py son daughter --blank --week 2026-W45
    → output/charts-blank-2026-W45.pdf

Charts are rendered with make_chart.py; the PDF is printed by headless Chromium
(set CHROME=/path/to/chrome if it isn't found automatically).
"""
import argparse
import glob
import os
import pathlib
import re
import subprocess
import sys

ROOT = pathlib.Path(__file__).resolve().parent.parent


def find_chrome():
    env = os.environ.get("CHROME")
    candidates = [env] if env else []
    candidates += glob.glob("/opt/pw-browsers/chromium*/chrome-linux*/chrome")
    candidates += ["/usr/bin/chromium", "/usr/bin/chromium-browser", "/usr/bin/google-chrome",
                   "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome"]
    for c in candidates:
        if c and os.path.exists(c):
            return c
    sys.exit("no Chromium found; set CHROME=/path/to/chrome")


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("kids", nargs="+")
    ap.add_argument("--week")
    ap.add_argument("--blank", action="store_true")
    ap.add_argument("--out")
    args = ap.parse_args()

    pages = []
    for kid in args.kids:
        html_path = ROOT / "output" / kid / "page.html"
        cmd = [sys.executable, str(ROOT / "render" / "make_chart.py"), kid, "--out", str(html_path)]
        if args.week:
            cmd += ["--week", args.week]
        if args.blank:
            cmd.append("--blank")
        subprocess.run(cmd, check=True, stdout=subprocess.DEVNULL)
        html = html_path.read_text()
        html_path.unlink()
        if not pages:
            head = re.search(r"<head>.*?</head>", html, re.S).group(0)
        body = re.search(r"<body>(.*?)</body>", html, re.S).group(1)
        pages.append(f'<section class="page">{body}</section>')

    combined = (
        "<!doctype html><html lang='en'>" + head.replace("</style>",
        ".page { page-break-after: always; break-after: page; } .page:last-child { page-break-after: auto; }</style>")
        + "<body>" + "".join(pages) + "</body></html>"
    )
    tag = ("charts-blank" if args.blank else "charts") + (f"-{args.week}" if args.week else "")
    out = pathlib.Path(args.out) if args.out else ROOT / "output" / f"{tag}.pdf"
    out.parent.mkdir(parents=True, exist_ok=True)
    tmp_html = out.with_suffix(".html")
    tmp_html.write_text(combined)

    subprocess.run([find_chrome(), "--headless=new", "--no-sandbox", "--disable-gpu",
                    "--no-pdf-header-footer", f"--print-to-pdf={out}", f"file://{tmp_html}"],
                   check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    tmp_html.unlink()
    print(out.relative_to(ROOT))


if __name__ == "__main__":
    main()
