---
name: contrib-skill
description: Analyze a local Git repository to reconstruct a contributor's evidence-backed work and generate a requirement-driven, technically specific Chinese resume project entry plus an interview/audit trail. Use when Codex needs to turn repository context and commit history into truthful resume bullets, validate architecture or design-pattern claims, or—only when explicitly requested—run a safe benchmark and add measured STAR metrics.
---

# Contrib Skill

Turn a local Git repository into context-rich resume and interview material without inventing responsibilities or metrics.

## Workflow

1. Confirm the repository path and target author name or email. If the user states the project nature or use case, preserve it as user-provided context.
2. Install the package in an isolated Python 3.10+ environment with `pip install -e ".[dev]"` when the command is unavailable.
3. Run:

   ```bash
   contrib-skill analyze --repo <repo> --author <name-or-email> --mode resume --target-role <role> --project-context <confirmed-background> --output <output-dir>
   ```

4. Open `06_resume_bullets.md` first.
   - Copy only “可直接粘贴的项目条目” into the resume.
   - Keep the project summary to one or two compact sentences: state the user/requirement context first, then the system boundary and evidence-backed architecture. Put the detailed technical substance in three or four numbered contributions.
   - Start each numbered contribution with a short technical theme label, then enforce one causal sentence: problem/constraint → owned technical approach and key mechanism → evidence-backed result. Do not accept noun lists that fail to explain why the approach was used.
   - Use a measured result only when a saved benchmark, monitoring export, test report, or user-supplied source supports it. Otherwise write an observable qualitative outcome and place scenario-specific metric suggestions outside the paste-ready body.
   - Keep numbered contributions at the business capability, technical approach, mechanism, and engineering-value level. Do not enumerate Controller/Service/Repository layers or file-level implementation details in the resume body.
   - Lead the project summary with user/requirement context: target users, operational scenario, and the problem to solve. Describe the stack only after the requirement.
   - Name DDD, MVC, Repository, Strategy, Factory, Adapter, Observer, or similar patterns only when directory names, changed files, commit semantics, or dependencies provide direct evidence.
   - When user context is provided, use it in the project summary, then inspect “用户提供背景与仓库校验” for independent risk findings.
   - Use “证据映射” to prepare interview explanations and verify wording.
   - Ask the user to answer “待本人确认后补强” before adding team scope, production impact, or metrics.
5. Use `07_interview_script.md` for interview preparation and `08_claim_risk_report.md` for wording audits.

## Optional benchmark workflow

Use this workflow only when the user explicitly asks for load/performance testing.

1. Inspect how the target service starts, which endpoint represents the claimed scenario, and whether authentication or seed data is required.
2. Confirm the target is local/test/staging. Before any production benchmark, request a second explicit authorization and agree on request/concurrency limits.
3. Create or adapt a repository-local scenario script when setup, auth, payload generation, or cleanup is needed. Use `contrib-benchmark` as the measurement runner and save the JSON report.
4. Actually run the benchmark; do not draft numbers from configuration alone.
5. Re-run `contrib-skill analyze` with `--benchmark-report <report.json>`.
6. Use the generated natural-language bullet in the resume and the structured Situation/Task/Action/Result block for audit and interview preparation. If a related performance contribution exists, the measured environment, load configuration, and result are merged into that numbered item; otherwise a standalone STAR item is generated. Always retain the environment qualifier.

## Guardrails

- Keep commit hashes, file paths, risk labels, and confirmation checklists outside the resume body.
- Prefer business or technical outcomes over directory names and commit counts.
- Treat information density as causal density: every technology name must connect to a concrete constraint and an outcome. Do not add DDD, design patterns, middleware, or adjectives merely to make a sentence sound advanced.
- Keep the information ratio aligned with strong resumes: a short requirement-oriented summary and three or four technically dense numbered contributions. Do not let the summary become longer than the contribution body.
- Enrich project context only from the README, detected dependencies, architecture layers, business-flow inference, commit semantics, and changed files.
- Treat explicit user context as a separate evidence source: use it for background wording, label it as user-provided in the audit trail, and never present it as repository fact.
- Validate high-availability, high-concurrency, production, and similar strong context against visible deployment, resilience, middleware, benchmark, and monitoring evidence. Keep the supplied background in the entry, but mark unsupported overall claims `risky` with a concrete explanation.
- Use code layers and changed paths only to infer higher-level responsibilities; keep their literal names in the evidence map unless a specific component is itself the key design mechanism.
- Treat architecture and design-pattern names as claims requiring path/commit evidence. A lone `domain` directory is not enough to claim DDD.
- Never run a benchmark by default. Never benchmark a production endpoint without explicit authorization, bounded load parameters, and user awareness of impact.
- Quantify success rate, QPS, or P95/P99 only from a saved benchmark report; do not generalize local/test results into production capacity.
- Never fabricate percentages, QPS, user counts, production status, or team ownership.
- Treat README-derived business context as fact only when the README states it directly; label other interpretations as inferences.
- Downgrade “主导/从 0 到 1/独立负责” when the contribution evidence is insufficient.
- If the repository history is sparse, return fewer strong bullets instead of padding the entry with generic claims.
