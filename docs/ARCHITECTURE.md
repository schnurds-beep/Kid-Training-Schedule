# Architecture — Phase 1 proposal

This is the proposal you asked for: language/tooling, folder tree, schemas, generator
interface, CLI surface. Everything below is reflected in example files in the repo so you
can read the schemas with real values rather than field lists. Nothing is code yet;
the five choices that are hard to reverse are collected in `DECISIONS.md` and wait for you.

## 1. Language and tooling (proposed)

**Python 3.11+, with three small dependencies.**

| Need                    | Choice            | Why                                                              |
|-------------------------|-------------------|------------------------------------------------------------------|
| Data files              | YAML (PyYAML)     | Readable and hand-editable; comments allowed, which JSON forbids. |
| Content items           | Markdown + YAML frontmatter | A passage should read like a document in any editor.   |
| Templates               | Jinja2            | HTML charts/packets from templates; the de facto Python standard. |
| CLI                     | stdlib `argparse` | One parent maintains this; no framework to learn.                 |
| LLM calls (Phase 2)     | `anthropic` SDK   | Behind an interface; Phase 1 uses a stub.                         |
| PDF (optional)          | browser print, or `weasyprint` if installed | No hard PDF dependency.         |
| Tests                   | `pytest`          | Mostly schema validation and the planner's rule checks.           |

Why Python over TypeScript: the work is "read YAML, apply rules, call an LLM, fill a
template". Python does that with the least ceremony, and the LLM tooling is strongest there.
TypeScript is a fine alternative if you live in Node; the data layer and templates would not
change at all, which is why this is listed as reversible-ish in `DECISIONS.md`.

Install: `pip install -e .` gives you a `kp` command (name is a placeholder).

## 2. Folder tree

```
.
├── config/
│   └── rules.yaml                 # house rules: budget, pairing, day modes, adaptation thresholds
├── profiles/<kid>/
│   ├── profile.yaml               # who the kid is: interests, constraints, areas (what + how)
│   └── difficulty.yaml            # versioned difficulty state per content type, with history
├── schedules/<kid>/
│   ├── rotation.yaml              # rules: which areas on which days (the "when")
│   └── weeks/<YYYY-Www>.yaml      # generated weekly plan; committed; item ids are stable
├── content/<kid>/<type>/
│   └── <week>[-<slot>].md|yaml    # generated items + the params that produced them
├── results/<kid>/
│   └── <YYYY-Www>.yaml            # parent-entered sessions: done, score, missed, notes
├── output/<kid>/<week>/           # chart.html, packet.html, [.pdf] — gitignored
├── generators/                    # reading.py, handwriting.py, math.py, baseball.py, registry.py
├── render/
│   ├── templates/                 # chart.html.j2, packet.html.j2, review.md.j2, base.css
│   └── render.py
├── kp/                            # CLI package: cli.py, plan.py, record.py, review.py, io.py
├── tests/
└── docs/
```

**Kids are data.** `profiles/<kid>/` + `schedules/<kid>/rotation.yaml` is the entire definition
of a kid. The daughter already exists as a draft under exactly that rule.

**Separation of "what/how" from "when".** The profile says handwriting is 5 minutes,
self-running, fed by the handwriting generator. The rotation says it happens Mon–Thu + Sat/Sun.
Changing days after the review touches one file.

**Git is the audit trail.** Weekly plans, content, results, and difficulty history are all
committed text. `git log -p profiles/son/difficulty.yaml` is the difficulty timeline.

## 3. Schemas

Each schema has a filled example in the repo; this section says what the fields mean and
which program owns them.

### 3.1 Profile — `profiles/<kid>/profile.yaml` (hand-edited)

| field | notes |
|---|---|
| `id`, `name`, `age`, `grade`, `status` | `id` == folder name. `status: draft` plans but warns on TBDs. |
| `interests[]` | Topic seeds for every generator. |
| `reading.likes/avoid` | Extra steer for the reading generator. |
| `constraints.weekday.*` | Times. `block` is the practice window. |
| `constraints.budget_minutes` | Per-kid cap; may be lower than `config`, never higher. |
| `constraints.weekend.fixed/seasonal` | Lesson, skiing. Informational for the planner's warnings. |
| `areas.<name>` | `minutes`, `mode: self\|parent`, `content_type` (generator), `outside_block`, `notes`. |

### 3.2 Rotation — `schedules/<kid>/rotation.yaml` (hand-edited, versioned)

| field | notes |
|---|---|
| `version`, `effective_from` | Bumped after each review; plans record which version made them. |
| `rows[]` | One chart row each: `area`, `days[]`, optional `label`, `minutes`, `external`, `outside_block`, `unless: skiing`, `role: anchor`. |
| `day_modes` | Default mode per day (`fri: free`). |
| `seasons` | Date-ranged switches (indoor baseball, skiing day). |
| `validate` | Which rule checks are `error` vs `warn`. |

### 3.3 Weekly plan — `schedules/<kid>/weeks/<week>.yaml` (written by `plan-week`)

| field | notes |
|---|---|
| `week`, `starts`, `ends`, `generated_at`, `rotation_version`, `rules_version`, `season` | Provenance. |
| `overrides` | What the parent passed: `homework_heavy: [tue]`, `skiing: sun`, `off: [thu]`. |
| `days.<d>.mode` | `normal \| homework_heavy \| free \| off`. |
| `days.<d>.items[]` | `id` (`<day>-<n>`, stable), `area`, `minutes`, `mode`, `content` (ref, filled by `generate`), `external`, `outside_block`. |
| `days.<d>.in_block_minutes` | Sum the budget rule checked. |
| `validation.errors/warnings` | Output of the rule checks, kept with the plan. |

### 3.4 Content item — `content/<kid>/<type>/…` (written by `generate`)

Markdown with YAML frontmatter when there is prose (reading, math sheets); pure YAML when it
is structured (handwriting prompts, drills). Shared header:

| field | notes |
|---|---|
| `id`, `kid`, `type`, `week`, `slot` | `id` is the path; `slot` is the plan item id. |
| `generator.name/version/backend` | `backend: stub` or `llm:<model>`. |
| `params` | The exact inputs: `difficulty_version`, level fields, topic, interests used, question mix, seed, topics avoided. Regeneration is reproducible from this. |
| `status` | `generated → printed → used`, advanced by `build-packet` and `record`. |
| `questions[]` (reading/math) | `n`, `type` in order, so `record --missed 3,5` resolves to types. |

### 3.5 Result — `results/<kid>/<week>.yaml` (written by `record`, or edited directly)

| field | notes |
|---|---|
| `sessions[].item` | Plan item id. Absent item = not recorded; `done: false` = skipped. |
| `done` | The timer ran. Independent of score. |
| `minutes`, `score.correct/total`, `missed[]`, `notes` | All optional. `missed` holds question numbers (reading/math) or skill names (drills). |
| `adaptation` | Appended by `record`: before/after difficulty version and the reason. |

Because this file is the source of truth and already readable, "enter via CLI" and "edit a
file" are the same path. No separate checklist parser is needed (open question 2 resolved
unless you want a different shape).

### 3.6 Difficulty state — `profiles/<kid>/difficulty.yaml` (written by `record`)

| field | notes |
|---|---|
| `areas.<type>.version` | Bumps on every change. Content items pin the version they were built at. |
| `areas.<type>.level` | Per-type shape: reading `{grade_equiv, passage_words, questions}`, math `{track, skill, stage}`, baseball `{hitting, throwing, fielding}`. The generator defines its own unit of "one step". |
| `areas.<type>.question_mix` | Weights; the missed-type rule bumps these. |
| `areas.<type>.history[]` | Append-only `{version, at, reason}`. |

Adaptation rule (defaults in `config/rules.yaml#adaptation`, applied by each generator's `adapt()`):
- scored: ratio ≥ 0.83 (5/6) → step up; ≤ 0.50 (3/6) → step down; same question type missed
  twice → weight 2 until two clean sessions.
- timed: 4 completions in a row → next stage; 3 skips in a row → easier variant.

## 4. Generator interface

Specified in full in `generators/README.md`. The one-paragraph version: a generator is a
named, versioned object with `generate(req, llm) -> GenResult` and
`adapt(difficulty, results, rules) -> new_entry | None`. Both are pure; the CLI does all file
I/O. `req` carries the profile, the current difficulty entry, prior items of that type, prior
results, the slots to fill, the season, and a deterministic seed. `GenResult` carries the
items plus a `difficulty_record` snapshot that gets copied into each item's `params`.
The LLM is injected via a two-method protocol so Phase 1 runs end-to-end on a `StubLLM`.

## 5. CLI surface

```
kp plan-week    <kid> [--week 2026-W44] [--homework-heavy tue,thu] [--skiing sun] [--off thu] [--season winter]
kp generate     <kid> <type|all> [--week W] [--slot tue-3] [--force]
kp record       <kid> <session> <done|score> [--missed 3,5] [--minutes 12] [notes...]
kp build-packet <kid|all> [--week W] [--pdf]
kp review       <kid> [--weeks 2]
kp validate     [kid]                  # schema + rule checks on everything, no writes
kp prep         [--week W]             # Sunday: plan-week + generate all + build-packet, both kids
```

Examples:

```
kp plan-week son --homework-heavy tue --skiing sun
kp generate son reading
kp record son tue-3 4/6 --missed 3,5 "guessed fast, didn't go back to the text"
kp record son tue-2 skipped "meltdown about the bow"
kp record son mon-2 done
kp build-packet all --pdf
kp review son
```

`<session>` is `<day>-<n>` for the current week, or `<week>/<day>-<n>` for an older one.
`record` writes the result, runs `adapt()` for scored areas, appends to `difficulty.yaml`
if the level changed, and flips the content item to `used`.

What `plan-week` enforces, from `config/rules.yaml` and the rotation's `validate` block:
- weekday `in_block_minutes` ≤ budget → `error` (no plan written);
- non-anchor in-block items ≤ `items_per_day` → `error`;
- one `self` + one `parent` among them → `warn` (Tue/Thu are cello+reading, both plausible as
  self+parent, which is why cello is `mode: self` in the profile);
- `homework_heavy` days keep the anchor + the first non-anchor row that fits;
- `free`/`off` days get no in-block items; `outside_block` rows still print.

`review` reads the last N weeks of results and plans and writes
`output/<kid>/review-<week>.md`: completion per area (scheduled vs done), score trend per
scored area, difficulty changes, and rotate-out candidates per `config.trial.rotate_out`
(≥3 scheduled, ≤50% done). It suggests; the parent edits `rotation.yaml` and bumps `version`.

## 6. The weekly loop, end to end

1. **Sunday** `kp prep` → plans both kids, generates everything scheduled, writes
   `output/*/W/chart.html` + `packet.html`. Print. Write anything by hand you want to.
2. **Weeknights** the kids tick the chart. The parent runs `kp record` the same evening or
   batches it; the results file is small enough to type by hand.
3. **After 2 weeks** `kp review son`, read it with him, edit `rotation.yaml`, bump `version`.
4. Commit after each step. The history *is* the record.

## 7. What Phase 2 builds (once decisions are signed off)

1. `kp/io.py` loaders + schema validation (`validate` command). Tests on the example files.
2. `kp/plan.py` planner with the rule checks, reproducing `schedules/son/weeks/2026-W44.yaml`.
3. `generators/*` stubs + registry; `generate` writes items with `backend: stub`.
4. `render/` chart + packet; `build-packet`.
5. `record` + `adapt()`; `review`.
6. Swap `StubLLM` for `AnthropicLLM` behind a flag.
