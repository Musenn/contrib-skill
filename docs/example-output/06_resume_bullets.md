# 简历项目描述（Alice Zhang）
> “可直接粘贴”只收录有 Git 证据的表述。复制到简历时不要带上后面的证据映射与待确认清单。

## 可直接粘贴的项目条目

### contrib_demo_repo — 电商订单与支付

**参与时间**：2025.01 — 2025.03

**个人角色**：项目初始化与核心功能开发

**技术栈**：JavaScript · Express · MySQL · Redis · npm/yarn/pnpm · Jest

**项目简介**：一个基于 Express、MySQL、Redis 的电商订单与支付后端服务，围绕订单创建与状态流转、支付与回调处理构建核心业务流程。代码按 Controller/Service 分层组织接口接入与业务逻辑；通过 Redis 缓存优化订单查询与数据访问路径；配套 Jest 单元测试形成自动化回归入口。

1. 参与项目初始化与基础架构搭建，基于 Express + MySQL + Redis 完成项目骨架、依赖与基础配置初始化，建立 Controller/Service 分层开发基线。
2. 参与订单核心功能开发，在 Controller 接口层、Service 业务层新增订单创建接口、实现订单状态流转，覆盖订单创建、业务处理与状态演进流程。
3. 参与支付核心功能开发，在 Controller 接口层、Service 业务层接入支付回调，补齐支付结果接收与业务处理链路。
4. 围绕订单查询链路开展性能优化，在 Service 业务层引入 Redis 缓存，减少重复数据访问并优化高频查询路径。

## 证据映射（不要粘贴到简历）

### 项目简介上下文

- 证据：README: README.md
- 证据：领域关键词命中：payment, pay, 支付, 回调
- 证据：业务流程（仓库语义推断）：订单创建与状态流转 → 支付与回调处理
- 证据：目录分层：Controller 层（接口/路由）、Service 层（业务逻辑）
- 证据：依赖文件：package.json → JavaScript · Express · MySQL · Redis · npm/yarn/pnpm · Jest
- 证据：技术机制：commit 0a8f8b6 perf: 订单查询增加 redis 缓存

### 1. 参与项目初始化与基础架构搭建，基于 Express + MySQL + Redis 完成项目骨架、依赖与基础配置初始化，建立 Controller/Service 分层开发基线。

- 风险等级：`safe`
- 证据：commit 2f052fd [architecture] init project scaffold；文件：.gitignore、README.md、package.json

### 2. 参与订单核心功能开发，在 Controller 接口层、Service 业务层新增订单创建接口、实现订单状态流转，覆盖订单创建、业务处理与状态演进流程。

- 风险等级：`safe`
- 证据：commit 1133c4f [feature] feat: 新增订单创建接口；文件：src/controller/order_controller.js、src/service/order_service.js
- 证据：commit b8b8865 [feature] feat: 实现订单状态流转；文件：src/service/order_service.js

### 3. 参与支付核心功能开发，在 Controller 接口层、Service 业务层接入支付回调，补齐支付结果接收与业务处理链路。

- 风险等级：`safe`
- 证据：commit 171ec66 [feature] feat: 接入支付回调；文件：src/controller/payment_controller.js、src/service/payment_service.js

### 4. 围绕订单查询链路开展性能优化，在 Service 业务层引入 Redis 缓存，减少重复数据访问并优化高频查询路径。

- 风险等级：`safe`
- 证据：commit 0a8f8b6 [performance] perf: 订单查询增加 redis 缓存；文件：src/service/order_service.js


## 待本人确认后补强

- [ ] 确认项目性质与使用场景：真实上线、公司内部使用、开源项目，还是课程/练习项目。
- [ ] 确认个人角色与团队边界：团队人数、本人负责范围，以及是否可使用“主导/主要负责”。
- [ ] 补充真实规模：用户量、数据量、QPS、运行时长或 star；没有可靠数据就不要填写。
- [ ] 如有压测或监控记录，补充性能优化前后的 P95/P99、吞吐量或资源消耗。

## 目标岗位适配

- 面向「Java后端开发工程师」：优先保留 MySQL, Redis 相关成果，并在面试中准备对应的设计取舍与问题排查过程。

## 可补充的真实指标

以下指标只有在本人能提供可靠来源时才能加入正文：

- 接口响应时间 / P95 / P99（需压测或监控数据）
- 吞吐量、QPS 或批处理耗时（需压测记录）
- 故障率、超时率或缺陷数量变化
- 测试覆盖率与自动化用例数量
- 真实用户量、数据量级与线上运行时长
