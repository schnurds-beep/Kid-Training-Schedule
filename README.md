# Kids Practice System

A home practice system for two kids. Short, frequent practice ("a bit, often"),
run by one parent, checked off by the kids on a printed chart.

**Status: Phase 1 — architecture only.** There is no runnable code yet. This
repo currently contains:

- `docs/ARCHITECTURE.md` — the proposal: tooling, folder tree, schemas,
  generator interface, CLI surface. **Read this first.**
- `docs/DECISIONS.md` — the choices that are hard to reverse, waiting on sign-off.
- Example data files under `profiles/`, `schedules/`, `content/`, `results/`
  that show every schema with real values for the son, and a placeholder
  profile for the daughter.
- `config/rules.yaml` — the operating rules as machine-readable config, not prose.

## Layout at a glance

| Folder        | What lives here                                             | Who writes it        |
|---------------|-------------------------------------------------------------|----------------------|
| `profiles/`   | Who each kid is: interests, constraints, difficulty state   | Parent (hand-edited) + `record` (difficulty) |
| `schedules/`  | Rotation rules per kid → generated weekly plans             | Parent (rules) + `plan-week` (plans) |
| `content/`    | Generated passages, prompts, drills + the params that made them | `generate`      |
| `results/`    | Parent-entered scores and notes, one file per kid per week  | `record` or text editor |
| `output/`     | Printable charts and packets (gitignored)                   | `build-packet`       |
| `generators/` | One module per content type, behind one interface           | Code                 |
| `render/`     | Templates that turn plans + content into printables         | Code + templates     |
| `config/`     | House rules: budgets, pairing, adaptation thresholds        | Parent               |

Kids are data: adding a kid is adding a folder under `profiles/` and
`schedules/`, nothing else.
