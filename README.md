<p align="center">
  <img src="assets/logo.svg" alt="contrib-skill" width="480">
</p>

<p align="center">
  <b>中文</b> | <a href="README.en.md">English</a>
</p>

# contrib-skill

**代码贡献洞察与项目包装工具。**

基于本地 Git 仓库的提交历史、diff、项目结构与依赖配置，还原项目背景、架构与每个人的真实贡献，并生成**有证据链支撑、经得起背调**的简历表述与面试话术。

它不是 commit 计数器，也不是简历造假器——它做的是：把你**真实做过的事**从 Git 历史里挖出来、讲清楚，并明确告诉你哪些话能写、哪些话需要确认、哪些话写了会在背调或面试追问中翻车。

## 它能回答什么问题

1. 这个项目是做什么的？业务背景和解决的问题是什么？
2. 项目的架构风格、技术栈、技术选型是什么？
3. 每个人分别提交了什么？活跃周期、主力模块是什么？
4. 关键 commit 为什么产生、起了什么作用？
5. 指定作者的真实贡献是什么？在团队中处于什么量级？
6. 这些贡献如何**安全地**写进简历？面试该怎么讲？
7. 哪些表述是 safe 的，哪些需要确认，哪些有冒领风险？

## 核心原则

- **证据链优先**：所有结论基于 Git 证据，输出严格区分 *事实* / *高置信推断* / *低置信假设*，推断一律标注置信度（高/中/低）
- **不冒领**：核心模块主要由他人提交时，最多生成「参与 / 协助」
- **强表述要强证据**：「主导」「从 0 到 1」「独立负责」只有在项目初始化提交、高贡献等级等证据齐备时才放行，否则判为 `risky` 并给出降级建议
- **量化指标零虚构**：仓库内没有 benchmark / 压测证据时，绝不生成「性能提升 30%」「支撑百万级并发」之类的数字，只输出「可补充真实指标」清单
- **每条建议带证据**：简历 bullet 附 commit hash、文件路径、变更类型与风险等级

## 工作原理

```
Git 仓库
   │
   ├─ GitAnalyzer            提交历史、numstat、作者聚合、活跃分布（事实层）
   ├─ RepoScanner            目录结构、关键目录、配置/依赖/CI 文件
   ├─ TechStackDetector      语言、框架、数据库、中间件、构建与部署方式
   ├─ DiffAnalyzer           commit 语义分类（feature/bugfix/refactor/… 14 类）
   ├─ ArchitectureAnalyzer   架构风格、分层、模块地图（推断层，带置信度）
   ├─ BusinessContextAnalyzer 业务领域、项目目标、核心流程（推断层，带置信度）
   ├─ AuthorProfiler         作者画像：角色、模块归属、贡献含金量等级
   └─ ClaimRiskChecker       每条简历表述的风险裁决：safe / needs_confirmation / risky
   │
   ▼
ResumeGenerator + InterviewGenerator + ReportGenerator
   │
   ▼
evidence.json + metrics.json + 8 份 Markdown 报告 + full_report.md
```

### 贡献含金量评分

不按代码行数线性计分。每个 commit 的得分 = **变更类型权重 × 文件路径权重**（如 architecture 1.0、feature 0.9、docs 0.4、style 0.1；service/core 路径 1.0、docs 路径 0.35），merge commit 不计分，最终与仓库内其他作者**相对比较**，输出粗粒度等级（很高/较高/中等/较低/低），不给假精度分数。

### 模块归属分级

按作者在模块内的提交占比、持续时间与变更类型，分为五级，直接决定简历用词：

| 归属等级 | 判定（简化） | 允许用词 |
| --- | --- | --- |
| owner | 占比 ≥60% 且 ≥5 次提交且 feature 类为主 | 主要负责 |
| deep | ≥4 次提交且跨度 ≥30 天 | 深度参与 |
| maintainer | ≥3 次提交 | 负责该模块部分开发与维护 |
| participant | ≥2 次提交 | 参与 |
| assistant | 1 次提交 | 协助 |

## 安装

要求 Python 3.10+，本机可执行 `git`。

```bash
git clone https://github.com/Musenn/contrib-skill.git
cd contrib-skill
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

## 快速开始

```bash
# 完整分析某位作者的贡献
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

### 参数

| 参数 | 说明 |
| --- | --- |
| `--repo` | 仓库路径，默认当前目录 |
| `--author` | 目标作者名称或邮箱（子串匹配，大小写不敏感） |
| `--all-authors` | 分析所有作者 |
| `--base` / `--branch` | 只分析 `base..branch` 区间内的提交 |
| `--since` / `--until` | 时间过滤，如 `2025-01-01` |
| `--mode` | `full`（全部）/ `resume`（简历向）/ `interview`（面试向）/ `audit`（审计向）/ `strict` |
| `--target-role` | 目标岗位，生成简历适配建议（技术栈不匹配时会如实提醒） |
| `--language` | `zh` / `en`（MVP 报告以中文为主，简历含英文版） |
| `--output` | 输出目录，默认 `./contrib_output` |
| `--max-commits` | 最大分析 commit 数，默认 2000 |
| `--include-diff` | evidence.json 中保留逐文件 numstat |
| `--strict` | 只保留有证据支撑（safe）的简历表述 |

## 输出文件

```
contrib_output/
  evidence.json              # 完整证据链（结构化，含每个 commit 的分类与推断）
  metrics.json               # 量化统计
  01_project_overview.md     # 项目概览 + 业务背景（标注置信度与待确认问题）
  02_architecture_analysis.md# 架构风格、分层、模块地图、优势与风险
  03_git_history_summary.md  # 作者概况表
  04_author_contribution.md  # 逐作者画像：模块归属、角色、活跃分布、证据 commit
  05_key_commits_analysis.md # 关键 commit 逐条解读（reason/impact 均标注为推断）
  06_resume_bullets.md       # 六版简历：保守 / 标准 / 强化 / STAR / 英文 / 岗位适配
  07_interview_script.md     # 30s/1m/3m 介绍、技术难点、14 条高频追问、防问穿指南
  08_claim_risk_report.md    # 逐条表述风险裁决 + 背调提醒
  full_report.md             # 汇总报告
```

> 📂 完整输出示例见 [docs/example-output/](docs/example-output/)（一个模拟电商仓库的真实运行结果，未做手工修改）。

## 风险分级

| 等级 | 含义 |
| --- | --- |
| `safe` | Git 证据充分，可直接使用 |
| `needs_confirmation` | 涉及业务指标、线上效果、团队角色等仓库无法佐证的内容，需本人确认 |
| `risky` | 证据不足或可能冒领他人贡献，不建议使用（附原因与降级建议） |

## 测试

```bash
pytest
```

测试会在临时目录构造一个真实的多作者 Git 仓库，对解析、分类、画像与风险裁决做端到端验证。

## 局限（MVP）

- commit 类型判断基于 message 关键词与文件路径规则，非 AST 级语义分析
- 业务背景与架构风格为启发式推断，报告中均标注置信度
- 不接入 GitHub / Jira 等外部系统，仅依赖本地仓库
- 报告以中文为主，简历部分提供英文版

## 路线图

- [ ] LLM 接入：对 diff 做语义级解读，深度还原 commit 动机与影响
- [ ] tree-sitter AST 调用图，识别核心代码路径与真实影响面
- [ ] 多仓库聚合：一个人跨项目的完整贡献画像
- [ ] HTML / PDF 报告导出
- [ ] 英文完整报告
