# Decisions waiting on you

These are the choices that are hard to reverse. Each has a recommendation; the repo's
example files assume the recommendation. Reply with the number and "yes" or your
alternative, and Phase 2 starts from there.

## 1. Language: Python 3.11+ (recommended) vs TypeScript/Node
- **Python**: least ceremony for YAML + rules + LLM + templates; `pip install -e .`, one `kp` command.
- **TypeScript**: pick it if you already live in Node. Data files and templates stay identical.
- Cost of reversing later: rewrite of the (small) code layer; zero change to data.

## 2. Data format: YAML for state, Markdown+frontmatter for prose content (recommended)
- Alternative: JSON everywhere (no comments, worse to hand-edit) or TOML (awkward for lists of records).
- Cost of reversing: a one-off conversion script; every file is already structured the same way.

## 3. Schema shape: see `docs/ARCHITECTURE.md` §3 and the example files
The specific calls I made that you might want to overrule:
- **Profile holds "what/how" (minutes, self/parent mode, generator); rotation holds "when" (days).**
  Alternative: one file per kid with both. Recommended split because the review changes days, not areas.
- **Difficulty state lives in `profiles/<kid>/difficulty.yaml`**, with append-only history in the same
  file. Alternative: a `state/` folder. Kept under profiles because the brief lists "level" as part of who the kid is.
- **Results: one file per kid per ISO week**, sessions keyed by the plan's item id (`tue-3`).
  Alternative: one file per session (more files, better for git blame per session). Weekly is less to type.
- **Cello is `mode: self`** so Tue/Thu/Sun pair cello (self) with reading or baseball (parent).
  If cello really needs a parent in the room, Tue/Thu become two parent items and the planner will warn.
- **Content item ids are paths** (`son/reading/2026-W44-tue`). Renaming a kid's folder renames history;
  fine for a two-kid system.

## 4. `output/` gitignored (recommended)
Printables are rebuilt from committed inputs, so committing them is noise. Flip `.gitignore` if you want
the PDF you actually handed the kid in the audit trail.

## 5. Results entry: CLI *and* direct edit of the same YAML file (recommended)
This closes open question 2 without a parser: `results/<kid>/<week>.yaml` is designed to be typed by hand,
and `kp record` just appends to it. If you'd rather tick a Markdown checklist that gets parsed, say so and
the results schema gains a `checklist.md` sibling.

## Still open, not blocking
- Daughter's age and activities → fill `profiles/daughter/profile.yaml` and `schedules/daughter/rotation.yaml`;
  `status: draft` keeps her chart printing meanwhile.
- Packet generation on a schedule (Sunday cron) vs on demand (`kp prep`). Proposal: on demand first,
  cron is one line later.
- CLI name: `kp` is a placeholder.
