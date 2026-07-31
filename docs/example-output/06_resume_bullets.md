# 简历项目描述（Alice Zhang）
> “可直接粘贴”只收录有 Git 证据的表述。复制到简历时不要带上后面的证据映射与待确认清单。

## 可直接粘贴的项目条目

### contrib_demo_repo — 支付

**参与时间**：2025.01 — 2025.03

**个人角色**：项目初始化与核心功能开发

**技术栈**：JavaScript · Express · MySQL · Redis · npm/yarn/pnpm · Jest

**项目简介**：一个简单的电商订单与支付后端服务。

1. 参与项目初始化与基础架构搭建，完成项目骨架、依赖与基础配置初始化；基于 Express + MySQL + Redis 建立可持续迭代的工程基线。
2. 参与核心功能开发，新增订单创建接口、实现订单状态流转，完善项目关键业务链路。
3. 参与核心功能开发，接入支付回调，完善项目关键业务链路。
4. 围绕关键链路开展性能优化，订单查询增加 redis 缓存，减少重复计算或资源访问开销。

## 证据映射（不要粘贴到简历）

### 1. 参与项目初始化与基础架构搭建，完成项目骨架、依赖与基础配置初始化；基于 Express + MySQL + Redis 建立可持续迭代的工程基线。

- 风险等级：`safe`
- 证据：commit 2f052fd [architecture] init project scaffold；文件：.gitignore、README.md、package.json

### 2. 参与核心功能开发，新增订单创建接口、实现订单状态流转，完善项目关键业务链路。

- 风险等级：`safe`
- 证据：commit 1133c4f [feature] feat: 新增订单创建接口；文件：src/controller/order_controller.js、src/service/order_service.js
- 证据：commit b8b8865 [feature] feat: 实现订单状态流转；文件：src/service/order_service.js

### 3. 参与核心功能开发，接入支付回调，完善项目关键业务链路。

- 风险等级：`safe`
- 证据：commit 171ec66 [feature] feat: 接入支付回调；文件：src/controller/payment_controller.js、src/service/payment_service.js

### 4. 围绕关键链路开展性能优化，订单查询增加 redis 缓存，减少重复计算或资源访问开销。

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
