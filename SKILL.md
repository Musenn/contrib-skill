---
name: contrib-skill
description: Analyze a local Git repository to reconstruct a contributor's evidence-backed work and generate a paste-ready Chinese resume project entry plus an interview/audit trail. Use when Codex needs to turn commit history into truthful resume bullets, inspect individual contributions, prepare project interview material, or check whether a claimed project responsibility is supported by Git evidence.
---

# Contrib Skill

Turn a local Git repository into concise resume and interview material without inventing responsibilities or metrics.

## Workflow

1. Confirm the repository path and target author name or email.
2. Install the package in an isolated Python 3.10+ environment with `pip install -e ".[dev]"` when the command is unavailable.
3. Run:

   ```bash
   contrib-skill analyze --repo <repo> --author <name-or-email> --mode resume --target-role <role> --output <output-dir>
   ```

4. Open `06_resume_bullets.md` first.
   - Copy only “可直接粘贴的项目条目” into the resume.
   - Use “证据映射” to prepare interview explanations and verify wording.
   - Ask the user to answer “待本人确认后补强” before adding team scope, production impact, or metrics.
5. Use `07_interview_script.md` for interview preparation and `08_claim_risk_report.md` for wording audits.

## Guardrails

- Keep commit hashes, file paths, risk labels, and confirmation checklists outside the resume body.
- Prefer business or technical outcomes over directory names and commit counts.
- Never fabricate percentages, QPS, user counts, production status, or team ownership.
- Treat README-derived business context as fact only when the README states it directly; label other interpretations as inferences.
- Downgrade “主导/从 0 到 1/独立负责” when the contribution evidence is insufficient.
- If the repository history is sparse, return fewer strong bullets instead of padding the entry with generic claims.
