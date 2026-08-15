# Arduino 现场试验台

## 解决什么现场问题

验证激光切割设备外围自动化改造的硬件逻辑与代码映射，为安全联锁、自动上下料等改造提供可复用模块。

## 目标

- 验证传感器与 PLC 的联动逻辑
- 测试按钮/限位/光电等硬件状态与代码的完整映射
- 为现场设备改造提供可复用的代码模块

## 硬件清单（待补充）

- Arduino 主控板
- 光电传感器 x2
- 按钮模块 x2
- 继电器模块
- 限位开关

## 核心任务：建立完整真值表

激光切割设备安全联锁的启动条件：

| 条件 | 硬件 | 常态 | 触发态 | 代码变量 | 允许启动？ |
|------|------|------|--------|---------|-----------|
| 急停 | 按钮 NC | 闭合 | 断开 | `emergency_stop = False` | 常态 ✅ 触发 ❌ |
| 安全门 | 门磁 NC | 闭合 | 断开 | `door_closed = True` | 闭合 ✅ 打开 ❌ |
| 左限位 | 开关 NC | 闭合 | 断开 | `left_limit = False` | 未触发 ✅ 触发 ❌ |
| 右限位 | 开关 NC | 闭合 | 断开 | `right_limit = False` | 未触发 ✅ 触发 ❌ |
| 启动 | 按钮 NO | 断开 | 闭合 | `start_pressed = True` | 按下 ✅（仅脉冲） |
| 气压 | 传感器 | OFF | ON | `air_pressure_ok = True` | 正常 ✅ 不足 ❌ |

**启动允许 = NOT emergency_stop AND door_closed AND NOT left_limit AND NOT right_limit AND start_pressed AND air_pressure_ok**

## 状态

搭建中。当前重点注意项（待办事项 4号）。
