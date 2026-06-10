# 简历真实性与背调风险报告

> 风险等级说明：
> - **safe**：Git 证据充分，可直接使用
> - **needs_confirmation**：需要本人确认（业务指标、线上效果、团队角色等仓库无法佐证的内容）
> - **risky**：不建议使用，证据不足或可能冒领他人贡献

## 总览

- 共评估表述：6 条
- safe：6 条
- needs_confirmation：0 条
- risky：0 条

## 逐条评估

### 1. 参与 service 模块的开发与维护，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 0a8f8b6（performance）：src/service/order_service.js
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit b8b8865（feature）：src/service/order_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### 2. 参与 controller 模块的开发与维护，工作包括 功能开发（2 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### 3. 深度参与 service 模块，基于 Express、MySQL、Redis，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 0a8f8b6（performance）：src/service/order_service.js
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit b8b8865（feature）：src/service/order_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### 4. 参与 controller 模块，基于 Express、MySQL、Redis，工作包括 功能开发（2 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### 5. 深度参与 service 模块开发，基于 Express、MySQL、Redis，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 0a8f8b6（performance）：src/service/order_service.js
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit b8b8865（feature）：src/service/order_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### 6. 参与 controller 模块，基于 Express、MySQL、Redis，工作包括 功能开发（2 次提交）

- 风险等级：**safe**
- 需要本人确认：否
- 证据：
  - commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
  - commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js


## 通用背调提醒

1. 量化指标（性能提升 X%、支撑 X 并发）没有压测/监控数据就不要写。
2. 「主导」「从 0 到 1」「独立负责」只有在 Git 证据强支撑时才可使用。
3. 他人主要贡献的模块，最多写「参与」或「协助」。
4. 项目性质（上线 / 课程 / 练习）如实呈现，背调或追问极易暴露。
5. 面试时所有表述都应能落到具体 commit 与文件，这是最硬的证据。