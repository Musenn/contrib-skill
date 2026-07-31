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
- **仓库上下文丰富**：联合 README、核心业务流、架构分层、依赖技术栈、commit 语义与变更文件，生成“背景 + 方案 + 个人动作 + 技术作用”完整项目表述
- **高密度三段式贡献**：项目简介压缩为 1—2 句；3—4 条编号统一使用“技术主题：问题/约束 → 方案与关键机制 → 可验证结果”，让每个技术名词都能回答为什么使用、解决什么问题
- **不冒领**：核心模块主要由他人提交时，最多生成「参与 / 协助」
- **强表述要强证据**：「主导」「从 0 到 1」「独立负责」只有在项目初始化提交、高贡献等级等证据齐备时才放行，否则判为 `risky` 并给出降级建议
- **量化指标零虚构**：仓库内没有 benchmark / 压测证据时，绝不生成「性能提升 30%」「支撑百万级并发」之类的数字，只输出「可补充真实指标」清单
- **每条建议带证据**：简历 bullet 附 commit hash、文件路径、变更类型与风险等级

## 生成结果长什么样

以下内容来自仓库内置的模拟订单项目，正文由生成器直接产出，没有手工润色：

> **项目简介**：公司内部使用的订单与支付系统，业务场景要求高可用、高并发；面向电商交易中的订单处理与支付结果衔接需求，项目聚焦订单状态流转和支付回调处理，并兼顾高频查询效率。基于 Express、MySQL、Redis 构建电商订单与支付核心链路，采用分层架构，组织核心模块与扩展边界。
>
> 1. 工程基线：针对项目持续开发中的依赖、运行约定与仓库规则一致性要求，负责工程基线建设，基于 Express + MySQL + Redis 完成工程初始化与依赖集成，统一依赖版本、仓库忽略规则和运行说明；形成一致的工程入口，支撑电商订单与支付核心业务模块持续扩展。
> 2. 订单状态建模：针对订单跨阶段状态需要统一生命周期承载与约束的问题，参与订单核心链路建设，基于 Express 组织请求接入与业务处理，实现订单创建与状态流转，并以状态驱动方式统一约束订单生命周期；形成覆盖订单创建、业务处理与状态演进的业务闭环，为跨阶段状态变化提供统一承载入口。
> 3. 支付回调链路：针对外部支付结果需要接入系统并与内部业务处理衔接的问题，参与支付核心链路建设，基于 Express 组织请求接入与业务处理，接入支付回调并统一处理返回结果；形成回调接收、支付结果处理与业务响应闭环，为外部结果与内部业务衔接提供统一入口。
> 4. 查询性能优化：针对订单查询这一高频场景存在重复读取持久化数据、核心查询路径需要收敛的问题，采用 Redis 缓存机制，将重复读取前移至缓存层；减少对 MySQL 的重复访问并收敛核心查询路径。

生成器遵循与标准技术简历一致的信息分配方式：

| 区域 | 负责表达什么 | 不应该出现什么 |
| --- | --- | --- |
| 项目简介 | 项目性质、需求背景、服务对象、系统边界、整体架构 | 过长的技术栈罗列、文件目录、commit 数量 |
| 编号贡献 | 技术主题、问题/约束、个人方案、关键机制、有依据的结果 | 名词堆砌、Controller/Service/DAO 逐层点名、无证据模式与指标 |
| 证据映射 | commit、变更文件、用户提供背景、风险等级 | 不复制进正式简历 |

完整结果见 [`docs/example-output/06_resume_bullets.md`](docs/example-output/06_resume_bullets.md)。

三段式句法、项目性质校验、技术词汇准入和指标证据规则见[高密度简历项目经历写作指南](docs/resume-writing-guide.md)；有实测数据时的完整写法见[本地压测数据示例](docs/benchmark-resume-example.md)。

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
   ├─ ProjectContextValidator 用户提供背景与仓库证据交叉校验
   ├─ BenchmarkLoader        读取并验证本地/测试/预发布环境的实测报告
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

### 作为 CLI 使用

```bash
git clone https://github.com/Musenn/contrib-skill.git
cd contrib-skill
python3 -m venv .venv && source .venv/bin/activate
pip install -e ".[dev]"
```

### 作为 Codex Skill 使用

将仓库放入 Codex skills 目录，并安装同一个 Python 包：

```bash
git clone https://github.com/Musenn/contrib-skill.git "${CODEX_HOME:-$HOME/.codex}/skills/contrib-skill"
cd "${CODEX_HOME:-$HOME/.codex}/skills/contrib-skill"
pip install -e ".[dev]"
```

之后可以直接向 Codex 描述任务，例如：

```text
分析 E:\code\order-service 中 Alice 的真实贡献。这个项目是公司内部订单系统，
请校验高可用、高并发背景是否有仓库证据，并生成可直接粘贴的 Java 后端简历项目经历。
```

需要量化数据时必须明确授权测试环境和负载范围：

```text
请在本地启动该服务，为订单查询接口编写压测脚本，以 20 并发完成 1000 次请求，
保存报告，并把成功率、QPS、P95 按 STAR 写入对应的性能贡献。不要压测生产地址。
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
  --project-context "公司内部使用的订单系统，业务场景要求高可用、高并发" \
  --output ./output

# 分析所有作者（简历材料默认生成给提交数最高的作者）
contrib-skill analyze --repo ./project --all-authors

# 严格模式：只保留 safe 等级的简历表述
contrib-skill analyze --repo ./project --author alice --strict
```

### 可选：显式压测后生成量化 STAR 成果

仅在用户明确要求压测，并确认目标是本地、测试或预发布环境后执行：

```bash
# 1. 先启动待测服务，再执行可复核的 HTTP 压测
contrib-benchmark \
  --url http://127.0.0.1:8080/api/orders \
  --scenario "订单查询接口" \
  --environment test \
  --requests 1000 \
  --concurrency 20 \
  --output ./benchmark/order-query.json

# 2. 将实测报告作为简历量化证据
contrib-skill analyze \
  --repo ./project \
  --author alice \
  --mode resume \
  --benchmark-report ./benchmark/order-query.json \
  --output ./output
```

压测脚本记录请求数、并发数、成功率、QPS 与 P50/P95/P99。没有报告时生成器不会输出这些指标；本地/测试结果会明确标注环境，不会包装成生产承载能力。若作者已有同场景性能贡献，生成器会把测试配置与结果并入对应编号，形成“技术机制 + 实测基线”的完整句子；否则生成独立 STAR 条目。默认拒绝生产环境压测，除非用户再次明确授权并显式使用 `--allow-production`。

实测数据的正确写法示例：

> 接口性能基线：针对订单查询接口缺少可复核性能基线的问题，在本地模拟服务的测试环境中编写并执行 HTTP 压测脚本，以 10 并发完成 100 次请求；实测成功率 100.00%、吞吐量 184.30 QPS、P95 延迟 11.02 ms，为后续容量评估与性能优化建立可复核基线。

以上数值来自仓库保存的本地模拟接口报告，仅用于演示数据写法，不能作为真实项目的生产性能结论。原始报告与完整说明见 [`docs/benchmark-resume-example.md`](docs/benchmark-resume-example.md)。

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
| `--project-context` | 用户确认的项目性质/使用场景；正文按此背景撰写，审计区会用仓库证据校验高可用、高并发、上线等强声明 |
| `--benchmark-report` | `contrib-benchmark` 或等价脚本生成的实测 JSON；同场景数据并入性能贡献，否则生成独立 STAR 条目 |
| `--language` | `zh` / `en`（MVP 报告与可粘贴简历主稿以中文为主） |
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
  06_resume_bullets.md       # 可直接粘贴的项目条目 + 证据映射 + 待确认增强项
  07_interview_script.md     # 30s/1m/3m 介绍、技术难点、14 条高频追问、防问穿指南
  08_claim_risk_report.md    # 逐条表述风险裁决 + 背调提醒
  full_report.md             # 汇总报告
```

> 📂 完整输出示例见 [docs/example-output/](docs/example-output/)（一个模拟电商仓库的真实运行结果，未做手工修改）。项目简介保持两句，编号按“技术主题：问题 → 方案/机制 → 结果”展开；MVC/DDD/Repository/Strategy 等词汇只在证据命中时出现。未提供压测报告时不生成量化指标，而是输出与每条贡献对应的指标建议。规则说明见[高密度简历项目经历写作指南](docs/resume-writing-guide.md)，数据写法见[本地压测数据示例](docs/benchmark-resume-example.md)。

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
