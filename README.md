# contrib-skill

代码贡献洞察与项目包装工具。

基于本地 Git 仓库的提交历史、diff、项目结构与依赖配置，还原项目背景、架构与每个人的真实贡献，并生成**有证据链支撑、可背调**的简历表述与面试话术。

## 核心原则

- 所有结论基于 Git 证据链，区分 **事实 / 高置信推断 / 低置信假设**
- 不虚构贡献，不冒领他人产出，不鼓励简历造假
- 证据不足时使用保守表达（参与 / 协助 / 负责部分模块）
- 「主导」「从 0 到 1」等强表述只在 Git 证据足够强时放行
- 量化指标（性能提升 X% 等）无证据一律不生成，只提示「可补充真实指标」
- 每条简历建议附带 commit / 文件级证据来源与风险等级

## 安装

```bash
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

要求 Python 3.10+，且本机可执行 `git`。

## 使用

```bash
# 完整分析当前仓库中某位作者的贡献
contrib-skill analyze --repo ./project --author "Xu Yilin" --mode full

# 指定分支区间、时间窗口与目标岗位
contrib-skill analyze \
  --repo ./project \
  --author "Xu Yilin" \
  --base main \
  --branch feature/order \
  --since 2025-01-01 \
  --until 2025-06-01 \
  --mode resume \
  --target-role "Java后端开发工程师" \
  --output ./output

# 分析所有作者（简历材料默认生成给提交数最高的作者）
contrib-skill analyze --repo ./project --all-authors

# 严格模式：只保留 safe 等级的简历表述
contrib-skill analyze --repo ./project --author alice --strict
```

### 主要参数

| 参数 | 说明 |
| --- | --- |
| `--repo` | 仓库路径，默认当前目录 |
| `--author` | 目标作者名称或邮箱（子串匹配） |
| `--all-authors` | 分析所有作者 |
| `--base` / `--branch` | 分析 `base..branch` 区间 |
| `--since` / `--until` | 时间过滤 |
| `--mode` | `strict` / `resume` / `interview` / `audit` / `full` |
| `--target-role` | 目标岗位，用于简历适配建议 |
| `--language` | `zh` / `en`（MVP 报告以中文为主，简历含英文版） |
| `--output` | 输出目录，默认 `./contrib_output` |
| `--max-commits` | 最大分析 commit 数，默认 2000 |
| `--include-diff` | evidence.json 中保留逐文件 numstat |
| `--strict` | 只保留有证据支撑（safe）的简历表述 |

## 输出

```
contrib_output/
  evidence.json              # 完整证据链（Pydantic 结构化）
  metrics.json               # 量化统计
  01_project_overview.md     # 项目概览与业务背景（标注置信度）
  02_architecture_analysis.md
  03_git_history_summary.md
  04_author_contribution.md
  05_key_commits_analysis.md
  06_resume_bullets.md       # 多版本简历表述（保守/标准/强化/STAR/英文）
  07_interview_script.md     # 面试话术 + 高频追问
  08_claim_risk_report.md    # 逐条表述的背调风险评估
  full_report.md
```

## 风险等级说明

| 等级 | 含义 |
| --- | --- |
| `safe` | Git 证据充分，可直接使用 |
| `needs_confirmation` | 涉及业务指标、线上效果、团队角色等仓库无法佐证的内容，需本人确认 |
| `risky` | 证据不足或可能冒领他人贡献，不建议使用 |

## 测试

```bash
pytest
```

测试会在临时目录构造一个真实的多人 Git 仓库进行端到端验证。

## 局限（MVP）

- commit 类型判断基于 message 关键词与文件路径规则，非 AST 级语义分析
- 业务背景与架构风格为启发式推断，报告中均标注置信度
- 不接入 GitHub / Jira 等外部系统，仅依赖本地仓库
- 报告以中文为主，简历部分提供英文版

## 后续规划

- 接入 LLM 对 diff 做语义级解读（commit 动机与影响的深度还原）
- tree-sitter AST 调用图，识别核心代码路径
- 多仓库聚合（一个人的完整贡献画像）
- 输出 PDF / HTML 报告
