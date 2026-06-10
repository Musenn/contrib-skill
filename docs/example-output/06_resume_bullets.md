# 简历表述建议（Alice Zhang）

> 每条表述均附风险等级与 Git 证据。`safe` 可直接使用；`needs_confirmation` 须本人确认后使用；`risky` 不建议使用。

## 一、保守真实版（最稳妥，适合背调严格的公司）

- 参与 service 模块的开发与维护，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）
    - 风险等级：safe
    - 证据：commit 0a8f8b6（performance）：src/service/order_service.js
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit b8b8865（feature）：src/service/order_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js
- 参与 controller 模块的开发与维护，工作包括 功能开发（2 次提交）
    - 风险等级：safe
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

## 二、标准求职版（按模块归属等级用词）

- 深度参与 service 模块，基于 Express、MySQL、Redis，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）
    - 风险等级：safe
    - 证据：commit 0a8f8b6（performance）：src/service/order_service.js
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit b8b8865（feature）：src/service/order_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js
- 参与 controller 模块，基于 Express、MySQL、Redis，工作包括 功能开发（2 次提交）
    - 风险等级：safe
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

## 三、强化表达版（仅在证据允许的范围内加强）

- 深度参与 service 模块开发，基于 Express、MySQL、Redis，工作包括 功能开发（3 次提交）、性能相关改动（1 次提交）
    - 风险等级：safe
    - 证据：commit 0a8f8b6（performance）：src/service/order_service.js
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit b8b8865（feature）：src/service/order_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js
- 参与 controller 模块，基于 Express、MySQL、Redis，工作包括 功能开发（2 次提交）
    - 风险等级：safe
    - 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
    - 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

## 四、STAR 版

### service 模块

- **Situation**：项目需要 service 模块支撑相关业务能力（背景细节建议结合实际补充）
- **Task**：深度参与该模块的开发任务
- **Action**：基于 Express、MySQL、Redis 完成相关提交，代表性工作：feat: 接入支付回调；feat: 实现订单状态流转
- **Result**：模块按提交记录持续演进并合入主干；量化效果需补充真实指标
- 证据：commit 0a8f8b6（performance）：src/service/order_service.js
- 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
- 证据：commit b8b8865（feature）：src/service/order_service.js
- 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js

### controller 模块

- **Situation**：项目需要 controller 模块支撑相关业务能力（背景细节建议结合实际补充）
- **Task**：参与该模块的开发任务
- **Action**：基于 Express、MySQL、Redis 完成相关提交，代表性工作：feat: 接入支付回调；feat: 新增订单创建接口
- **Result**：模块按提交记录持续演进并合入主干；量化效果需补充真实指标
- 证据：commit 171ec66（feature）：src/controller/payment_controller.js, src/service/payment_service.js
- 证据：commit 1133c4f（feature）：src/controller/order_controller.js, src/service/order_service.js


## 五、英文版（English）

- Was deeply involved in the service module (Express, MySQL, Redis); work covered feature (3 commits), performance (1 commits).
    - Risk level: safe
- Contributed to the controller module (Express, MySQL, Redis); work covered feature (2 commits).
    - Risk level: safe

## 六、目标岗位适配建议

- 面向「Java后端开发工程师」：建议在简历中突出 MySQL, Redis 相关经验（仓库依赖中确有这些技术）

## 七、可补充指标建议

以下指标**仓库中没有证据**，只有你能提供真实数据后才可写入简历：

1. 接口响应时间变化（需有压测或监控数据）
2. bug 数量 / 故障率下降情况
3. 测试覆盖率提升幅度
4. 用户量 / 数据量级
5. QPS / 并发量（需有压测记录）
6. 部署环境（测试 / 预发 / 生产）
7. 线上使用情况与运行时长
