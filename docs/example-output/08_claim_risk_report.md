# 简历真实性与背调风险报告

> 风险等级说明：
> - **safe**：Git 证据充分，可直接使用
> - **needs_confirmation**：需要本人确认（业务指标、线上效果、团队角色等仓库无法佐证的内容）
> - **risky**：不建议使用，证据不足或可能冒领他人贡献

## 总览

- 共评估表述：4 条
- safe：4 条
- needs_confirmation：0 条
- risky：0 条

## 逐条评估

### 1. 参与项目初始化与基础架构搭建，基于 Express + MySQL + Redis 完成项目骨架、依赖与基础配置初始化，建立 Controller/Service 分层开发基线。

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 2f052fd [architecture] init project scaffold；文件：.gitignore、README.md、package.json

### 2. 参与订单核心功能开发，在 Controller 接口层、Service 业务层新增订单创建接口、实现订单状态流转，覆盖订单创建、业务处理与状态演进流程。

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 1133c4f [feature] feat: 新增订单创建接口；文件：src/controller/order_controller.js、src/service/order_service.js
  - commit b8b8865 [feature] feat: 实现订单状态流转；文件：src/service/order_service.js

### 3. 参与支付核心功能开发，在 Controller 接口层、Service 业务层接入支付回调，补齐支付结果接收与业务处理链路。

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 171ec66 [feature] feat: 接入支付回调；文件：src/controller/payment_controller.js、src/service/payment_service.js

### 4. 围绕订单查询链路开展性能优化，在 Service 业务层引入 Redis 缓存，减少重复数据访问并优化高频查询路径。

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 0a8f8b6 [performance] perf: 订单查询增加 redis 缓存；文件：src/service/order_service.js


## 通用背调提醒

1. 量化指标（性能提升 X%、支撑 X 并发）没有压测/监控数据就不要写。
2. 「主导」「从 0 到 1」「独立负责」只有在 Git 证据强支撑时才可使用。
3. 他人主要贡献的模块，最多写「参与」或「协助」。
4. 项目性质（上线 / 课程 / 练习）如实呈现，背调或追问极易暴露。
5. 面试时所有表述都应能落到具体 commit 与文件，这是最硬的证据。