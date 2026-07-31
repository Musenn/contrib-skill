# 架构分析

- **架构风格**：Controller-Service 分层架构
- **置信度**：中

## 分层分析

- Controller 层（接口/路由）
- Service 层（业务逻辑）

## 模块地图

- **src**：src、src/controller、src/service
- **tests**：tests

## 依赖观察

- 主要框架：Express（来自 package.json）
- 数据存储：MySQL
- 中间件：Redis

## 架构与设计模式（仅列证据命中项）

- **分层架构**：src/controller、src/service、tests/order_service.test.js、src/service/order_service.js

## 架构优势（基于可见证据）

- 目录体现出分层意识，职责划分有迹可循
- 存在测试目录（tests）

## 架构风险

- 未发现部署/CI 配置，交付方式无法从仓库确认