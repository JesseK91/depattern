# depattern

**An AI-pattern linter for serious writing.**

`depattern` is a Python CLI that flags formulaic AI-writing patterns, explains why they weaken the draft, and helps rewrite them into clearer, more specific prose.

It is not an AI detector. It does not guess who wrote the text. It measures visible writing patterns: flat sentence rhythm, repeated openers, vague intensifiers, abstract nouns, transition scaffolding, and weak answer-first structure.

```bash
depattern analyze examples/raw.md
depattern suggest examples/raw.md
depattern process examples/raw.md --diff --answer-first
```

---

## Why this exists

AI can draft fast. The problem is that the drafts often carry the same residue:

- "Furthermore..."
- "In conclusion..."
- "It is important to note..."
- "cutting-edge solutions"
- "seamless ecosystem"
- paragraphs that sound confident but never say anything concrete

`depattern` treats that residue like lint.

---

## Quick Demo

Input:

```md
Furthermore, in today's fast-moving digital ecosystem, small businesses must
leverage cutting-edge solutions to unlock their full potential. It is important
to note that a website is no longer just a website.
```

Run:

```bash
depattern analyze examples/raw.md
```

Output:

```text
DEPATTERN LINGUISTIC AUDIT: raw.md

Overall Pattern Risk:   [HIGH RISK - Formulaic Patterning]
Pattern Artifact Score: 6/9

Linguistic Metrics:
 - Sentence Length StdDev:  7.26 (High Risk - Needs Variance)
 - Banned Transition %:     4.31 (High Risk - Over-Patterned)%
 - Abstract Noun %:         2.39%
 - AEO Answer-First Layout: [MISSING/OUTSIDE LIMITS]

Linguistic Artifact Details:
 - Banned transitions: 'furthermore', 'in conclusion', 'moreover'
 - Abstract nouns: 'synergy', 'solutions', 'paradigm', 'ecosystem'
```

Run:

```bash
depattern suggest examples/raw.md
```

Output:

```text
1. [HIGH] Replace formulaic transition language
   Cut the transition or replace it with a concrete claim.

2. [MEDIUM] Trade abstract nouns for visible actions
   Name the actual tool, action, result, or decision instead.

3. [MEDIUM] Vary sentence rhythm
   Mix short assertions with longer explanatory sentences.
```

See [`examples/before_after.md`](examples/before_after.md) for a full before/after.

---

## Features

- **Offline pattern audit**: no API key required for `analyze`
- **Offline edit suggestions**: concrete recommendations with `suggest`
- **JSON output**: scriptable `--json` mode for automation and CI
- **Risk thresholds**: fail a check with `--max-risk`
- **LLM rewrite pipeline**: optional rewrite flow through Gemini
- **Answer-first rewrite**: direct 50-80 word opening for service pages, FAQs, and strategy docs
- **JSON-LD schema export**: LocalBusiness, Person, Article, and FAQPage
- **Marp slide export**: convert markdown docs into presentation decks
- **Batch mode**: process markdown directories

---

## Installation

```bash
git clone https://github.com/JesseK91/depattern.git
cd depattern
pip install -e .
```

For development:

```bash
pip install -e ".[dev]"
python -m pytest -q
```

---

## Usage

### Analyze a draft

```bash
depattern analyze draft.md
```

Machine-readable output:

```bash
depattern analyze draft.md --json
```

Fail if a draft exceeds a threshold:

```bash
depattern analyze docs/homepage.md --max-risk medium
```

### Get offline suggestions

```bash
depattern suggest draft.md
depattern suggest draft.md --json
```

### Rewrite with Gemini

```bash
export GEMINI_API_KEY="your-key"
depattern process draft.md --diff
depattern process draft.md --out cleaned.md --answer-first
```

### Generate schema

```bash
depattern schema cleaned.md --type FAQPage --out faq_schema.json
depattern schema cleaned.md --type LocalBusiness --out business.json
```

### Generate slides

```bash
depattern slides cleaned.md --out presentation.md
```

### Batch process markdown files

```bash
depattern batch ./drafts --out ./processed --answer-first
```

---

## Configuration

Create a `depattern.toml` in your working directory:

```toml
[brand]
name = "580 Digital Infrastructure"
voice = "direct, specific, local, no hype, active voice, short paragraphs"

[llm]
provider = "gemini"
model = "gemini-2.5-flash"

[rules]
banned_phrases = [
    "furthermore",
    "in conclusion",
    "moreover",
    "it is important to note",
    "delve",
    "tapestry",
    "beacon",
    "testament",
    "game-changer",
    "seamless"
]
vague_intensifiers = [
    "very",
    "extremely",
    "incredibly",
    "highly"
]
```

---

## What the score means

`depattern` reports **pattern risk**, not "AI probability."

High-risk writing usually has:

- repeated transitional scaffolding
- flat sentence rhythm
- vague intensifiers instead of evidence
- abstract nouns instead of concrete actions
- repeated sentence openings
- no direct answer near the top

Low-risk writing can still be bad. This is a fast editorial filter, not a substitute for judgment.

---

## What this is not

`depattern` is not:

- an AI detector
- a plagiarism checker
- a guarantee of SEO rankings
- a replacement for an editor
- a claim that all AI-assisted writing is bad

It is a linter for visible writing patterns that tend to make drafts weaker.

---

## Roadmap

- [ ] `depattern compare before.md after.md`
- [ ] More schema graph types
- [ ] Ollama/local model provider
- [ ] OpenAI provider
- [ ] Markdown report export
- [ ] GitHub Action wrapper
- [ ] Voice presets for technical docs, local service pages, executive memos, and agency reports

---

## Contributing

See [`CONTRIBUTING.md`](CONTRIBUTING.md).

---

## License

MIT
