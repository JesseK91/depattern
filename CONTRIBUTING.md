# Contributing

`depattern` is intentionally small: a CLI that audits formulaic writing patterns, suggests edits, rewrites drafts, and exports useful markdown/schema artifacts.

Good contributions usually improve one of these areas:

- More precise pattern checks with low false positives
- Better examples and before/after fixtures
- Safer rewrite prompts
- Provider support beyond Gemini
- CLI ergonomics for batch and CI workflows
- Schema/export improvements for real markdown documents

## Local setup

```bash
pip install -e ".[dev]"
python -m pytest -q
```

## Development rules

- Keep offline commands usable without an API key.
- Do not market `depattern` as an AI detector.
- Prefer concrete pattern names over vague scoring language.
- Add tests for scoring changes.
- Keep CLI output readable for humans and available as JSON for automation.

## Running smoke checks

```bash
depattern analyze examples/raw.md
depattern suggest examples/raw.md
depattern analyze examples/raw.md --json
depattern slides examples/raw.md --out /tmp/depattern-slides.md
```

