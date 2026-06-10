<p align="center">
  <img src="assets/logo.svg" alt="contrib-skill" width="480">
</p>

<p align="center">
  <a href="README.md">中文</a> | <b>English</b>
</p>

# contrib-skill

**Contribution intelligence: turn Git history into credible resume material.**

contrib-skill analyzes a local Git repository — commit history, diffs, project structure, and dependency manifests — to reconstruct what the project is, how it is architected, and what each contributor actually did. It then generates resume bullets and interview scripts that are **backed by an evidence chain and safe under background checks**.

It is not a commit counter, and it is not a resume fabricator. It digs out the work you **actually did**, explains it well, and tells you explicitly which statements are safe to use, which need your confirmation, and which would fall apart under a background check or a probing interviewer.

## Questions it answers

1. What does this project do? What business problem does it solve?
2. What are the architecture style, tech stack, and technology choices?
3. Who committed what? When was each person active, and in which modules?
4. Why did the key commits happen, and what role did they play?
5. What did a specific author really contribute, relative to the rest of the team?
6. How can those contributions be written into a resume **safely**? How should the project be presented in an interview?
7. Which claims are safe, which need confirmation, and which risk claiming someone else's work?

## Core principles

- **Evidence chain first**: every conclusion is grounded in Git evidence and strictly labeled as *fact*, *high-confidence inference*, or *low-confidence assumption*, with an explicit confidence level (high/medium/low)
- **No credit-stealing**: if a core module was mainly committed by others, the strongest wording generated is "contributed to / assisted with"
- **Strong claims require strong evidence**: "led", "built from scratch", "solely responsible" are only allowed when backed by project-initialization commits and a high contribution level; otherwise the claim is marked `risky` with a suggested downgrade
- **Zero fabricated metrics**: without benchmark or load-test evidence in the repository, numbers like "improved performance by 30%" or "handles millions of concurrent users" are never generated — instead you get a checklist of real metrics worth adding
- **Every suggestion carries evidence**: each resume bullet cites commit hashes, file paths, change types, and a risk level

## How it works

```
Git repository
   │
   ├─ GitAnalyzer             commit history, numstat, per-author stats, activity (facts)
   ├─ RepoScanner             directory layout, key dirs, config/dependency/CI files
   ├─ TechStackDetector       languages, frameworks, databases, middleware, deployment
   ├─ DiffAnalyzer            commit semantic classification (feature/bugfix/refactor/… 14 types)
   ├─ ArchitectureAnalyzer    architecture style, layers, module map (inference + confidence)
   ├─ BusinessContextAnalyzer business domain, project goal, core flows (inference + confidence)
   ├─ AuthorProfiler          author profile: roles, module ownership, contribution level
   └─ ClaimRiskChecker        verdict on every resume claim: safe / needs_confirmation / risky
   │
   ▼
ResumeGenerator + InterviewGenerator + ReportGenerator
   │
   ▼
evidence.json + metrics.json + 8 Markdown reports + full_report.md
```

### Contribution scoring

Not a linear line count. Each commit scores **change-type weight × file-path weight** (e.g. architecture 1.0, feature 0.9, docs 0.4, style 0.1; `service`/`core` paths 1.0, docs paths 0.35). Merge commits score zero. The total is compared **relative to other authors** in the repository and reported as a coarse level (very high / high / medium / low / minimal) — no fake-precision scores.

### Module ownership levels

Based on the author's share of commits in a module, time span, and change types — and this directly gates the wording used in resume bullets:

| Level | Criteria (simplified) | Allowed wording |
| --- | --- | --- |
| owner | ≥60% share, ≥5 commits, feature-heavy | took primary responsibility for |
| deep | ≥4 commits spanning ≥30 days | was deeply involved in |
| maintainer | ≥3 commits | developed and maintained parts of |
| participant | ≥2 commits | contributed to |
| assistant | 1 commit | assisted in |

## Installation

Requires Python 3.10+ and a working `git` executable.

```bash
git clone https://github.com/Musenn/contrib-skill.git
cd contrib-skill
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## Quick start

```bash
# Full analysis of one author's contributions
contrib-skill analyze --repo ./project --author "Xu Yilin" --mode full

# Branch range, time window, and target role
contrib-skill analyze \
  --repo ./project \
  --author "Xu Yilin" \
  --base main \
  --branch feature/order \
  --since 2025-01-01 \
  --until 2025-06-01 \
  --mode resume \
  --target-role "Backend Engineer (Java)" \
  --output ./output

# Analyze all authors (resume material defaults to the top committer)
contrib-skill analyze --repo ./project --all-authors

# Strict mode: keep only claims rated safe
contrib-skill analyze --repo ./project --author alice --strict
```

### Options

| Option | Description |
| --- | --- |
| `--repo` | Repository path, defaults to the current directory |
| `--author` | Target author name or email (case-insensitive substring match) |
| `--all-authors` | Analyze every author |
| `--base` / `--branch` | Restrict analysis to commits in `base..branch` |
| `--since` / `--until` | Date filters, e.g. `2025-01-01` |
| `--mode` | `full` / `resume` / `interview` / `audit` / `strict` |
| `--target-role` | Target job role; produces tailoring advice (and honest warnings when the stack doesn't match) |
| `--language` | `zh` / `en` (MVP reports are primarily Chinese; resume bullets include an English version) |
| `--output` | Output directory, defaults to `./contrib_output` |
| `--max-commits` | Max commits to analyze, default 2000 |
| `--include-diff` | Keep per-file numstat in evidence.json |
| `--strict` | Keep only evidence-backed (`safe`) resume claims |

## Output files

```
contrib_output/
  evidence.json              # full evidence chain (structured; per-commit classification & inference)
  metrics.json               # quantitative stats
  01_project_overview.md     # project overview + business context (with confidence levels)
  02_architecture_analysis.md# architecture style, layers, module map, strengths & risks
  03_git_history_summary.md  # author summary table
  04_author_contribution.md  # per-author profile: ownership, roles, activity, evidence commits
  05_key_commits_analysis.md # key commits explained (reason/impact explicitly marked as inference)
  06_resume_bullets.md       # six resume versions: conservative / standard / enhanced / STAR / English / role-tailored
  07_interview_script.md     # 30s/1m/3m intros, technical challenges, 14 follow-up questions, anti-grilling guide
  08_claim_risk_report.md    # per-claim risk verdicts + background-check reminders
  full_report.md             # consolidated report
```

> 📂 See [docs/example-output/](docs/example-output/) for a complete, unedited run against a simulated e-commerce repository.

## Risk levels

| Level | Meaning |
| --- | --- |
| `safe` | Sufficient Git evidence; use as-is |
| `needs_confirmation` | Involves business metrics, production impact, or team roles the repository cannot prove; confirm before using |
| `risky` | Insufficient evidence, or may claim someone else's work; not recommended (reason and downgrade suggestion included) |

## Testing

```bash
pytest
```

Tests build a real multi-author Git repository in a temp directory and verify parsing, classification, profiling, and risk verdicts end to end.

## Limitations (MVP)

- Commit classification is rule-based (message keywords + file paths), not AST-level semantics
- Business context and architecture style are heuristic inferences, always labeled with confidence
- Local repository only; no GitHub / Jira integration
- Reports are primarily in Chinese; resume bullets include an English version

## Roadmap

- [ ] LLM-powered semantic diff analysis to reconstruct commit motivation and impact in depth
- [ ] tree-sitter AST call graphs to identify core code paths and real blast radius
- [ ] Multi-repository aggregation: one person's complete contribution profile
- [ ] HTML / PDF report export
- [ ] Fully English reports
