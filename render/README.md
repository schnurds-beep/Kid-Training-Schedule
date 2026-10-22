# render/

Turns a weekly plan + content items into printables via templates. Nothing here is
hand-built per week.

```
render/
  templates/
    chart.html.j2      # one-page check-off chart, Letter landscape, rows = areas, cols = Mon–Sun
    packet.html.j2     # cover (chart) + passages + prompts + drills, then answer keys last
    review.md.j2       # 2-week summary (markdown, not printed)
    base.css           # @page { size: letter landscape; margin: 0.5in } and print styles
  render.py            # (Phase 2) load plan + content → Jinja2 → output/<kid>/<week>/*.html [+ .pdf]
```

Chart rules the template enforces:
- A checkbox appears **only** on scheduled days (`days` in the rotation). Blank cell otherwise.
- Friday column reads "free choice" when `mode: free`.
- `external: true` rows (piano lesson) print as a note, not a checkbox.
- `outside_block: true` rows (bedtime reading) sit below a divider.
- Footer: week id, rotation version, and a blank "notes for review" line.

PDF: HTML is the primary output (print from the browser). If `weasyprint` is installed,
`build-packet --pdf` also writes a PDF. No PDF library is a hard dependency.
