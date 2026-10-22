# generators/

One module per content type, all behind the same interface. **Phase 1: interface only;
no code until the language is confirmed (docs/DECISIONS.md #1).** The interface below is
written in Python because that is the proposed language; it ports 1:1 to TypeScript.

## Contract

A generator is a pure function of *(profile, difficulty state, history, results)* that
returns *(content items, difficulty record)*. It never writes files; the CLI does.

```python
from dataclasses import dataclass
from typing import Protocol

@dataclass
class GenRequest:
    profile: dict          # profiles/<kid>/profile.yaml
    difficulty: dict       # profiles/<kid>/difficulty.yaml#areas.<type>  (current version)
    history: list[dict]    # prior content items of this type (headers only), newest first
    results: list[dict]    # prior result sessions for this type, newest first
    week: str              # "2026-W44"
    slots: list[dict]      # plan items this call must fill, e.g. [{id: "tue-3", minutes: 10}]
    season: str
    seed: int              # derived from kid+week+slot; makes stub output deterministic

@dataclass
class ContentItem:
    id: str                # "son/reading/2026-W44-tue"
    slot: str | None       # plan item id, or None for week-level files (handwriting)
    header: dict           # becomes the YAML frontmatter / top-level keys: params, questions, ...
    body: str | None       # markdown body for .md items; None for pure-YAML items

@dataclass
class GenResult:
    items: list[ContentItem]
    difficulty_record: dict   # snapshot of the difficulty the items were built at (version + level)

class Generator(Protocol):
    name: str              # "reading" — matches profile.areas.*.content_type
    version: str           # "0.1.0" — recorded on every item it produces
    scoring: str           # "scored" | "timed" — picks the adaptation rule family in config/rules.yaml

    def generate(self, req: GenRequest, llm: "LLM") -> GenResult: ...

    def adapt(self, difficulty: dict, new_results: list[dict], rules: dict) -> dict | None:
        """Return a new difficulty entry (version+1, level, reason) or None for no change.
        Pure. `record` calls this and appends the result to difficulty.yaml#history."""
```

The LLM is injected so Phase 1 can run end-to-end with a stub:

```python
class LLM(Protocol):
    def complete(self, system: str, prompt: str, *, json: bool = False) -> str: ...

class StubLLM:      # Phase 1: returns deterministic lorem-ipsum shaped like the real thing
class AnthropicLLM: # Phase 2: reads key from .env; model name recorded in item.generator.backend
```

## Modules (one file each)

| module          | name          | scoring | fills                                 |
|-----------------|---------------|---------|---------------------------------------|
| `reading.py`    | `reading`     | scored  | one `.md` per slot: passage + questions + key |
| `handwriting.py`| `handwriting` | timed   | one `.yaml` per week: prompt per day   |
| `math.py`       | `math`        | scored  | `.md` fact sheet or `.yaml` game per slot |
| `baseball.py`   | `baseball`    | timed   | one `.yaml` drill plan per slot        |
| `registry.py`   | —             | —       | `{name: Generator}` lookup used by the CLI |

Adding a content type = one module + one `content_type:` line in a profile. Adding a kid
touches nothing here.

## Default adaptation (shared, generators may override `adapt`)

- **scored**: ratio ≥ `step_up_at` → level +1 step; ≤ `step_down_at` → −1 step; otherwise unchanged.
  Any question type missed in ≥ `after_misses` of the last N sessions gets `weight` in
  `question_mix`; decays back after `decay_after_clean_sessions`.
- **timed**: `step_up_after_done_streak` completions → next stage; `step_down_after_skips`
  consecutive skips → easier/shorter variant.

Thresholds live in `config/rules.yaml#adaptation`; the unit of one "step" is defined per area
in `profiles/<kid>/difficulty.yaml` (0.5 grade for reading, one stage for math, one level per skill for baseball).
