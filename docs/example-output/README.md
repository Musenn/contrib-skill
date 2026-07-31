# 输出示例 / Output Example

本目录是 contrib-skill 对一个**模拟仓库**的完整输出，未做任何手工修改。

This directory contains the complete, unedited output of contrib-skill against a **simulated repository**.

## 模拟仓库设定 / The simulated repo

`order-shop`：一个电商订单与支付后端服务（Express + MySQL + Redis），两位作者、8 个 commit、时间跨度 2025-01 ~ 2025-03。生成时额外提供背景：“公司内部使用的订单与支付系统，业务场景要求高可用、高并发”。

| # | 日期 | 作者 | Commit |
| --- | --- | --- | --- |
| 1 | 2025-01-05 | Alice Zhang | init project scaffold（package.json / README / .gitignore） |
| 2 | 2025-01-20 | Alice Zhang | feat: 新增订单创建接口 |
| 3 | 2025-02-10 | Alice Zhang | feat: 实现订单状态流转 |
| 4 | 2025-02-20 | Alice Zhang | feat: 接入支付回调 |
| 5 | 2025-02-25 | Bob Li | fix: 修复支付回调空指针（深夜提交） |
| 6 | 2025-03-05 | Alice Zhang | perf: 订单查询增加 redis 缓存 |
| 7 | 2025-03-10 | Bob Li | test: 补充订单服务单元测试 |
| 8 | 2025-03-15 | Alice Zhang | docs: update readme |

## 生成命令 / Command used

```bash
contrib-skill analyze \
  --repo /tmp/contrib_demo_repo \
  --author Alice \
  --target-role "Java后端开发工程师" \
  --project-context "公司内部使用的订单与支付系统，业务场景要求高可用、高并发" \
  --output docs/example-output
```

## 值得注意的细节 / What to look for

- `01_project_overview.md`：业务领域被推断为「支付（次要相关：电商/订单交易）」，置信度「高」——来自 README 与 commit 关键词的交叉证据
- `04_author_contribution.md`：Alice 被识别为项目初始化者、贡献等级「很高」；Bob 的深夜提交、测试角色都有体现
- `06_resume_bullets.md`：项目简介只用两句交代需求与系统方案；编号以“工程基线、订单状态建模、支付回调链路、查询性能优化”为主题，按“问题 → 方案/机制 → 结果”展开。示例未提供压测报告，所以正文不生成量化指标，而是在审计区给出订单、支付、缓存对应的指标建议
- `08_claim_risk_report.md`：每条表述的风险裁决与证据列表
- `evidence.json`：全部结论的结构化证据链（commit 级分类、置信度、推断标注）

模拟仓库可用 `tests/conftest.py` 中的 fixture 逻辑复现。

The simulated repo can be reproduced with the fixture logic in `tests/conftest.py`.
