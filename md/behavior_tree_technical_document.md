# 行为树系统技术文档

## 目录

1. [概述](#1-概述)
2. [架构分析](#2-架构分析)
3. [实现方法](#3-实现方法)
4. [前端操作方法](#4-前端操作方法)
5. [节点功能详解](#5-节点功能详解)
6. [附录](#6-附录)

---

## 1. 概述

### 1.1 什么是行为树

行为树（Behavior Tree）是一种用于控制决策流程的树形数据结构，广泛应用于游戏AI、机器人控制和自动化脚本等领域。本项目实现了一套完整的行为树系统，支持可视化编辑、多种节点类型、装饰器参数配置等功能。

### 1.2 系统特性

- **可视化编辑器**：提供直观的拖拽式节点编辑界面
- **丰富的节点类型**：支持组合节点、条件节点、动作节点三大类
- **装饰器机制**：内置重试、重复、超时、取反等装饰参数
- **黑板系统**：支持节点间数据共享与通信
- **多格式序列化**：支持 JSON、YAML、TEXT 三种格式
- **撤销/重做**：完整的编辑历史管理
- **自动保存与崩溃恢复**：保障数据安全

### 1.3 核心模块结构

```
modules/behavior_tree/
├── __init__.py          # 模块入口，导出核心组件
├── nodes.py             # 节点定义与实现
├── engine.py            # 执行引擎
├── context.py           # 执行上下文
├── blackboard.py        # 黑板系统
└── serializer.py        # 序列化器

modules/bt_adapters/
├── action_adapters.py   # 动作节点适配器
├── ocr_adapter.py       # OCR条件节点
├── image_adapter.py     # 图像条件节点
├── color_adapter.py     # 颜色条件节点
├── number_adapter.py    # 数字条件节点
└── variable_adapter.py  # 变量条件节点

ui/bt_editor/
├── editor.py            # 编辑器主组件
├── canvas.py            # 画布组件
├── palette.py           # 节点面板
├── property.py          # 属性面板
├── toolbar.py           # 工具栏
├── connection.py        # 连接线管理
└── undo_redo.py         # 撤销/重做系统
```

---

## 2. 架构分析

### 2.1 整体架构图

```
┌─────────────────────────────────────────────────────────────────────────┐
│                           用户界面层 (UI Layer)                          │
├─────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │   Editor    │  │   Canvas    │  │   Palette   │  │  Property   │    │
│  │   编辑器    │  │    画布     │  │  节点面板   │  │  属性面板   │    │
│  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘  └──────┬──────┘    │
│         │                │                │                │            │
│         └────────────────┴────────────────┴────────────────┘            │
│                                   │                                      │
├───────────────────────────────────┼──────────────────────────────────────┤
│                           业务逻辑层 (Business Layer)                    │
├───────────────────────────────────┼──────────────────────────────────────┤
│                                   │                                      │
│  ┌─────────────┐  ┌─────────────┐│┌─────────────┐  ┌─────────────┐     │
│  │   Engine    │  │ Serializer  │││  Undo/Redo  │  │ AutoSave    │     │
│  │  执行引擎   │  │  序列化器   │││  撤销重做   │  │  自动保存   │     │
│  └──────┬──────┘  └──────┬──────┘│└─────────────┘  └─────────────┘     │
│         │                │       │                                      │
│         └────────────────┴───────┼──────────────────────────────────────┤
│                                   │                                      │
├───────────────────────────────────┼──────────────────────────────────────┤
│                           核心节点层 (Node Layer)                        │
├───────────────────────────────────┼──────────────────────────────────────┤
│                                   │                                      │
│  ┌─────────────────────────────────────────────────────────────────┐   │
│  │                         Node (抽象基类)                          │   │
│  └───────────────────────────────┬─────────────────────────────────┘   │
│                                  │                                       │
│         ┌────────────────────────┼────────────────────────┐             │
│         │                        │                        │             │
│  ┌──────┴──────┐          ┌──────┴──────┐          ┌──────┴──────┐     │
│  │ Composite   │          │ Condition   │          │   Action    │     │
│  │ 组合节点    │          │ 条件节点    │          │  动作节点   │     │
│  └──────┬──────┘          └──────┬──────┘          └──────┬──────┘     │
│         │                        │                        │             │
│  ┌──────┴──────┐          ┌──────┴──────┐          ┌──────┴──────┐     │
│  │SequenceNode │          │OCRCondition │          │ KeyPress    │     │
│  │SelectorNode │          │ImageCond.   │          │ MouseClick  │     │
│  │ParallelNode │          │ColorCond.   │          │ MouseMove   │     │
│  └─────────────┘          │NumberCond.  │          │ Delay       │     │
│                           │VariableCond.│          │ SetVariable │     │
│                           └─────────────┘          │ Script      │     │
│                                                    │ Code        │     │
│                                                    └─────────────┘     │
│                                                                          │
├──────────────────────────────────────────────────────────────────────────┤
│                           基础设施层 (Infrastructure Layer)              │
├──────────────────────────────────────────────────────────────────────────┤
│  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐  ┌─────────────┐    │
│  │ Blackboard  │  │  Context    │  │ Screenshot  │  │   Input     │    │
│  │   黑板      │  │  执行上下文 │  │   截图      │  │   输入控制  │    │
│  └─────────────┘  └─────────────┘  └─────────────┘  └─────────────┘    │
└─────────────────────────────────────────────────────────────────────────┘
```

### 2.2 核心组件说明

#### 2.2.1 节点系统 (Node System)

节点是行为树的基本构建单元，采用面向对象设计，通过继承实现不同类型节点：

```
Node (抽象基类)
├── CompositeNode (组合节点基类)
│   ├── SequenceNode (顺序节点)
│   ├── SelectorNode (选择节点)
│   └── ParallelNode (并行节点)
├── ConditionNode (条件节点基类)
│   ├── OCRConditionNode (OCR条件)
│   ├── ImageConditionNode (图像条件)
│   ├── ColorConditionNode (颜色条件)
│   ├── NumberConditionNode (数字条件)
│   └── VariableConditionNode (变量条件)
└── ActionNode (动作节点基类)
    ├── KeyPressNode (按键动作)
    ├── MouseClickNode (点击动作)
    ├── MouseMoveNode (移动动作)
    ├── DelayNode (延时动作)
    ├── SetVariableNode (设置变量)
    ├── ScriptNode (脚本动作)
    ├── CodeNode (代码动作)
    └── AlarmNode (报警动作) ⭐ 新增
```

#### 2.2.2 执行引擎 (BehaviorTreeEngine)

执行引擎负责行为树的生命周期管理：

| 功能 | 说明 |
|------|------|
| `load_tree()` | 从字典数据加载行为树 |
| `load_from_file()` | 从文件加载行为树 |
| `save_to_file()` | 保存行为树到文件 |
| `start()` | 启动执行 |
| `stop()` | 停止执行 |
| `pause()` | 暂停执行 |
| `resume()` | 恢复执行 |
| `get_status()` | 获取执行状态 |

#### 2.2.3 执行上下文 (ExecutionContext)

执行上下文封装了执行过程中的共享资源和状态：

```python
class ExecutionContext:
    blackboard: Blackboard          # 黑板（数据共享）
    screenshot_manager              # 截图管理器
    input_controller                # 输入控制器
    logging_manager                 # 日志管理器
    
    # 状态属性
    is_running: bool               # 是否运行中
    is_paused: bool                # 是否暂停
    elapsed_time: float            # 已运行时间
    tick_count: int                # tick次数
```

#### 2.2.4 黑板系统 (Blackboard)

黑板系统提供节点间的数据共享能力：

```python
class Blackboard:
    # 内置变量
    BUILTIN_VARS = {
        "last_detection_position": None,  # 最后检测位置（OCR/图像/颜色统一使用）
        "last_number_value": None,        # 最后识别的数字值
        "execution_count": 0,             # 执行计数
    }
    
    # 核心方法
    get(key, default)      # 获取变量
    set(key, value)        # 设置变量
    increment(key, amount) # 递增变量
    subscribe(key, callback) # 订阅变化
```

**重要说明**：
- `last_detection_position`：所有检测节点（OCR/图像/颜色）检测成功后，会将检测到的位置统一保存到此变量
- 保存的是**绝对坐标**（屏幕坐标），而非相对于检测区域的坐标
- 点击节点勾选"点击最近检测点"时，会从此变量读取位置

### 2.3 数据流向

```
┌──────────────────────────────────────────────────────────────────────┐
│                          数据流向图                                   │
└──────────────────────────────────────────────────────────────────────┘

用户操作
    │
    ▼
┌─────────┐     添加节点      ┌─────────┐     更新数据     ┌─────────┐
│ Palette │ ───────────────► │ Canvas  │ ───────────────► │ Editor  │
│ 节点面板 │                  │  画布   │                  │  编辑器  │
└─────────┘                  └─────────┘                  └────┬────┘
                                                              │
                              ┌───────────────────────────────┤
                              │                               │
                              ▼                               ▼
                        ┌─────────┐                     ┌─────────┐
                        │Property │                     │Serializer│
                        │属性面板  │                     │序列化器  │
                        └─────────┘                     └────┬────┘
                                                            │
                              ┌─────────────────────────────┤
                              │                             │
                              ▼                             ▼
                        ┌─────────┐                   ┌───────────┐
                        │  JSON   │                   │   File    │
                        │  数据   │                   │   文件    │
                        └────┬────┘                   └───────────┘
                             │
                             ▼
                       ┌───────────┐
                       │  Engine   │
                       │  执行引擎  │
                       └─────┬─────┘
                             │
              ┌──────────────┼──────────────┐
              │              │              │
              ▼              ▼              ▼
        ┌─────────┐   ┌─────────┐   ┌─────────┐
        │ Context │   │Blackboard│   │  Nodes  │
        │  上下文  │   │   黑板   │   │  节点   │
        └─────────┘   └─────────┘   └─────────┘
```

### 2.4 与其他系统的交互

#### 2.4.1 与截图系统集成

```python
# 条件节点通过上下文获取截图
screenshot = context.get_screenshot(region)

# 截图管理器提供两种截图方式
screenshot_manager.get_full_screenshot()      # 全屏截图
screenshot_manager.get_region_screenshot(region)  # 区域截图
```

#### 2.4.2 与输入控制集成

```python
# 动作节点通过上下文执行输入操作
context.execute_key_press(key, action, duration)    # 按键
context.execute_mouse_click(button, position)       # 鼠标点击
context.input_controller.move_to(x, y)              # 鼠标移动
```

#### 2.4.3 与OCR识别集成

```python
# OCR条件节点调用识别器
from utils.recognition import OCRRecognizer
matched, position = OCRRecognizer.recognize(
    screenshot, keywords, language
)
```

---

## 3. 实现方法

### 3.1 核心算法

#### 3.1.1 节点执行算法 (Tick)

每个节点通过 `tick()` 方法执行，返回 `NodeStatus` 状态：

```python
class NodeStatus(Enum):
    SUCCESS = "success"    # 执行成功
    FAILURE = "failure"    # 执行失败
    RUNNING = "running"    # 正在执行
    ABORTED = "aborted"    # 被中止
```

**节点中止接口**：

每个节点都支持 `abort()` 方法，用于在外部中止节点执行：

```python
class Node(ABC):
    def abort(self, context: "ExecutionContext") -> None:
        """
        中止节点执行
        
        当节点被外部中止时调用（如并行节点完成时中止其他RUNNING子节点）。
        子类可以重写此方法以实现特定的中止逻辑。
        """
        self.reset()
        context.notify_node_status(self.node_id, "aborted")
```

**各节点类型的中止行为**：

| 节点类型 | 中止行为 |
|---------|---------|
| CodeNode | 终止外部进程（terminate/kill） |
| ScriptNode | 停止脚本执行器 |
| MouseClickNode | 停止无限点击循环 |
| DelayNode | 重置延时状态 |
| 其他节点 | 调用 reset() 重置状态 |

**执行流程**：

```
┌─────────────────────────────────────────────────────────────┐
│                     节点执行流程                             │
└─────────────────────────────────────────────────────────────┘

tick(context)
    │
    ├── 检查节点是否启用
    │   └── 未启用 → 返回 SUCCESS
    │
    ├── 检查执行上下文状态
    │   └── 已停止 → 返回 ABORTED
    │
    ├── 检查超时设置
    │   └── 已超时 → 返回 FAILURE
    │
    ├── 执行节点逻辑
    │   └── _execute_xxx(context)
    │
    ├── 处理装饰参数
    │   ├── 重试计数
    │   ├── 重复计数
    │   └── 结果取反
    │
    └── 返回最终状态
```

#### 3.1.2 顺序节点算法 (SequenceNode)

```
执行逻辑：
1. 空子节点列表时返回 SUCCESS
2. 按顺序依次执行子节点
3. 所有子节点成功才返回成功
4. 默认：任一子节点失败立即返回失败
5. 开启 continue_on_failure：失败仍继续执行，最终根据失败情况返回结果
6. 子节点返回 RUNNING 时记录位置并返回 RUNNING

伪代码：
function tick(context):
    if children is empty:
        return SUCCESS
    
    has_failure = false
    
    while current_index < children.length:
        child = children[current_index]
        
        if not child.enabled:
            current_index++
            continue
        
        status = child.tick(context)
        
        if status == RUNNING:
            return RUNNING
        
        if status == FAILURE:
            if continue_on_failure:
                has_failure = true
                current_index++
                continue
            return FAILURE
        
        current_index++
    
    current_index = 0
    
    if has_failure:
        return FAILURE
    
    return SUCCESS
```

#### 3.1.3 选择节点算法 (SelectorNode)

```
执行逻辑：
1. 空子节点列表时返回 FAILURE
2. 按顺序依次执行子节点
3. 任一子节点成功立即返回成功
4. 所有子节点失败才返回失败
5. 子节点返回 RUNNING 时记录位置并返回 RUNNING

伪代码：
function tick(context):
    if children is empty:
        return FAILURE
    
    while current_index < children.length:
        child = children[current_index]
        
        if not child.enabled:
            current_index++
            continue
        
        status = child.tick(context)
        
        if status == RUNNING:
            return RUNNING
        
        if status == SUCCESS:
            return SUCCESS
        
        current_index++
    
    return FAILURE
```

#### 3.1.4 并行节点算法 (ParallelNode)

```
执行逻辑：
1. 空子节点列表时返回 SUCCESS
2. 同时执行所有子节点
3. 已完成的子节点使用缓存状态，不会重复执行
4. 根据成功策略决定最终结果：
   - require_all: 所有启用的子节点成功才成功
   - require_one: 任一子节点成功即成功（立即返回）
5. 有子节点 RUNNING 时返回 RUNNING
6. 节点完成时中止所有 RUNNING 子节点：
   - 调用子节点的 abort() 方法
   - 子节点状态更新为 ABORTED
   - 画布状态同步更新

中止行为说明：
- 当并行节点判定成功时，会立即中止所有仍在 RUNNING 的子节点
- CodeNode：终止外部进程
- ScriptNode：停止脚本执行
- MouseClickNode（无限点击）：停止点击循环
- DelayNode：重置延时状态

伪代码：
function tick(context):
    if children is empty:
        return SUCCESS
    
    success_count = 0
    failure_count = 0
    running_count = 0
    running_children = []
    
    for i, child in enumerate(children):
        if not child.enabled:
            continue
        
        # 检查缓存状态（已完成的子节点不重复执行）
        if i in cached_statuses:
            status = cached_statuses[i]
            if status == SUCCESS:
                success_count++
                continue
            elif status == FAILURE:
                failure_count++
                continue
        
        status = child.tick(context)
        
        if status == SUCCESS:
            cached_statuses[i] = SUCCESS
            success_count++
        elif status == FAILURE:
            cached_statuses[i] = FAILURE
            failure_count++
        elif status == RUNNING:
            running_count++
            running_children.append(child)
    
    # require_one 策略：任一成功即成功，中止其他 RUNNING 子节点
    if success_policy == require_one and success_count > 0:
        abort_running_children(context, running_children)
        return SUCCESS
    
    if running_count > 0:
        return RUNNING
    
    # require_all 策略：全部成功才成功
    if success_policy == require_all:
        if success_count == enabled_count:
            abort_running_children(context, running_children)
            return SUCCESS
        else:
            return FAILURE
    else:
        if success_count > 0:
            abort_running_children(context, running_children)
            return SUCCESS
        else:
            return FAILURE

function abort_running_children(context, running_children):
    for child in running_children:
        if child.status == RUNNING:
            child.abort(context)
```

### 3.2 数据结构设计

#### 3.2.1 节点数据结构

```python
{
    "id": "node_1",                    # 节点唯一标识
    "type": "SequenceNode",            # 节点类型
    "name": "主流程",                   # 节点名称
    "description": "",                 # 节点描述
    "enabled": true,                   # 是否启用
    "config": {                        # 配置参数
        "retry_count": 0,              # 重试次数
        "repeat_count": 1,             # 重复次数
        "timeout_ms": 0                # 超时时间
    },
    "children": ["node_2", "node_3"],  # 子节点ID列表
    "position": {                      # 画布位置
        "x": 200,
        "y": 100
    }
}
```

#### 3.2.2 行为树文件格式 (v2.0)

```json
{
    "version": "2.0",
    "format_type": "behavior_tree_editor",
    "metadata": {
        "created_at": "2026-03-30T12:00:00",
        "modified_at": "2026-03-30T12:30:00",
        "app_version": "1.0.0",
        "save_type": "manual",
        "checksum": ""
    },
    "canvas": {
        "name": "示例行为树",
        "description": "",
        "viewport": {
            "zoom": 1.0,
            "offset_x": 0,
            "offset_y": 0
        },
        "grid": {
            "enabled": true,
            "size": 20
        }
    },
    "root_node": "node_1",
    "nodes": {
        "node_1": { ... },
        "node_2": { ... }
    },
    "connections": [
        {"parent_id": "node_1", "child_id": "node_2"}
    ],
    "editor_state": {
        "selected_node": null,
        "selected_connection": null,
        "clipboard": null,
        "undo_stack": [],
        "redo_stack": []
    }
}
```

### 3.3 节点注册机制

#### 3.3.1 节点类型映射表

```python
# 核心节点类型
NODE_TYPE_MAP = {
    "SequenceNode": SequenceNode,
    "SelectorNode": SelectorNode,
    "ParallelNode": ParallelNode,
    "CompositeNode": CompositeNode,
    "ConditionNode": ConditionNode,
    "ActionNode": ActionNode,
}

# 引擎初始化时注册适配器节点
def register_adapters():
    NODE_TYPE_MAP["OCRConditionNode"] = OCRConditionNode
    NODE_TYPE_MAP["ImageConditionNode"] = ImageConditionNode
    NODE_TYPE_MAP["ColorConditionNode"] = ColorConditionNode
    NODE_TYPE_MAP["NumberConditionNode"] = NumberConditionNode
    NODE_TYPE_MAP["VariableConditionNode"] = VariableConditionNode
    NODE_TYPE_MAP["KeyPressNode"] = KeyPressNode
    NODE_TYPE_MAP["MouseClickNode"] = MouseClickNode
    NODE_TYPE_MAP["MouseMoveNode"] = MouseMoveNode
    NODE_TYPE_MAP["DelayNode"] = DelayNode
    NODE_TYPE_MAP["SetVariableNode"] = SetVariableNode
    NODE_TYPE_MAP["ScriptNode"] = ScriptNode
    NODE_TYPE_MAP["CodeNode"] = CodeNode
    NODE_TYPE_MAP["AlarmNode"] = AlarmNode
```

#### 3.3.2 节点工厂创建

```python
@classmethod
def from_dict(cls, data: Dict[str, Any]) -> "Node":
    """从字典反序列化创建节点"""
    node_type = data.get("type", "")
    node_class = NODE_TYPE_MAP.get(node_type, Node)
    return node_class(
        node_id=data["id"],
        config={
            "name": data.get("name", ""),
            "description": data.get("description", ""),
            "enabled": data.get("enabled", True),
            **data.get("config", {})
        }
    )
```

### 3.4 序列化与反序列化方案

#### 3.4.1 支持的格式

| 格式 | 扩展名 | 说明 |
|------|--------|------|
| JSON | .json | 默认格式，完整支持所有特性 |
| YAML | .yaml, .yml | 需要 PyYAML 库支持 |
| TEXT | .txt, .bt | 文本脚本格式，便于阅读 |

#### 3.4.2 序列化流程

```
┌───────────────────────────────────────────────────────────────┐
│                       序列化流程                               │
└───────────────────────────────────────────────────────────────┘

节点树
    │
    ▼
┌─────────────────┐
│  to_dict()      │  递归转换为字典
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│ update_metadata │  更新元数据
└────────┬────────┘
         │
    ┌────┴────┐
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ JSON  │ │ YAML  │
└───┬───┘ └───┬───┘
    │         │
    ▼         ▼
┌───────┐ ┌───────┐
│ 文件  │ │ 文件  │
└───────┘ └───────┘
```

#### 3.4.3 文本脚本格式示例

```
; 行为树脚本 v1.0
; 名称: 自动化流程

[Sequence]
  Name: 主流程
  retry_count: 0
  [Condition:OCR]
    Name: 检测文字
    region: 100,100,300,200
    keywords: 开始
  [Action:Click]
    Name: 点击按钮
    use_blackboard: true
    position_key: last_ocr_position
  [Delay]
    duration_ms: 1000
```

### 3.5 性能优化策略

#### 3.5.1 执行优化

| 策略 | 说明 |
|------|------|
| Tick间隔控制 | 默认50ms间隔，避免CPU占用过高 |
| 懒加载模板 | 图像模板首次使用时加载并缓存 |
| 状态记忆 | RUNNING状态节点记录执行位置，下次继续 |
| 异步执行 | 执行循环在独立线程中运行 |

#### 3.5.2 UI优化

| 策略 | 说明 |
|------|------|
| 视口裁剪 | 只渲染可见区域的节点 |
| 缩放缓存 | 节点缩放时重绘，避免实时计算 |
| 批量更新 | 属性变更后批量更新UI |
| 延迟保存 | 自动保存间隔控制，避免频繁IO |

---

## 4. 前端操作方法

### 4.1 编辑器界面布局

```
┌─────────────────────────────────────────────────────────────────────────┐
│                              工具栏                                     │
│  [新建] [打开] [保存] │ [撤销] [回退] [清空] │ [运行] [停止]    状态: 就绪 │
├────────────┬───────────────────────────────────────────┬────────────────┤
│            │                                           │                │
│   节点面板  │                                           │    属性面板    │
│            │                                           │                │
│  ▼ 组合节点 │                                           │   节点属性     │
│   ◇ 顺序   │                                           │   ─────────   │
│   ◇ 选择   │              画布区域                      │   名称: ___   │
│   ◇ 并行   │                                           │   启用: [✓]   │
│            │                                           │                │
│  ▼ 条件节点 │         ┌──────────┐                      │   配置参数     │
│   ◇ OCR检测│         │  顺序    │                      │   ─────────   │
│   ◇ 图像匹配│         └────┬─────┘                      │   区域: ___   │
│   ◇ 颜色检测│              │                            │   关键词: ___ │
│   ◇ 数字比较│         ┌────┴─────┐                      │                │
│   ◇ 变量判断│         │          │                      │   装饰参数     │
│            │    ┌────┴──┐  ┌────┴───┐                   │   ─────────   │
│  ▼ 动作节点 │    │OCR检测│  │ 点击   │                   │   重试: 0     │
│   ◆ 按键   │    └───────┘  └────────┘                   │   超时: 0     │
│   ◆ 点击   │                                           │                │
│   ◆ 移动   │                                           │                │
│   ◆ 延时   │                                           │                │
│   ◆ 设变量 │                                           │                │
│   ◆ 代码   │                                           │                │
│   ◆ 脚本   │                                           │                │
│            │                                           │                │
└────────────┴───────────────────────────────────────────┴────────────────┘
```

### 4.2 行为树创建流程

#### 步骤1：新建行为树

1. 点击工具栏 **[新建]** 按钮
2. 或使用快捷键 `Ctrl + N`
3. 如果当前有未保存的更改，会提示确认

#### 步骤2：添加节点

**方法一：从节点面板添加**
1. 在左侧节点面板中找到目标节点类型
2. 点击节点按钮，节点将添加到画布中央

**方法二：搜索添加**
1. 在节点面板顶部搜索框输入关键词
2. 匹配的节点会自动显示
3. 点击即可添加

#### 步骤3：建立连接关系

1. 将鼠标移动到父节点的 **输出端口**（底部圆点）
2. 光标变为十字形状时，按住左键拖拽
3. 拖拽到子节点的 **输入端口**（顶部圆点）
4. 释放鼠标完成连接

```
连接示意：

    ┌─────────┐
    │  父节点  │
    └────┬────┘
         │ ○ 输出端口
         │
         │  拖拽连线
         │
         ○ 输入端口
    ┌────┴────┐
    │  子节点  │
    └─────────┘
```

#### 步骤4：配置节点属性

1. 单击选中节点
2. 右侧属性面板显示该节点的配置选项
3. 修改各项参数
4. 切换选中节点时自动保存

#### 步骤5：保存行为树

1. 点击工具栏 **[保存]** 按钮
2. 或使用快捷键 `Ctrl + S`
3. 首次保存会弹出文件对话框
4. 另存为使用 `Ctrl + Shift + S`

### 4.3 节点操作详解

#### 4.3.1 选择节点

| 操作 | 说明 |
|------|------|
| 单击节点 | 选中单个节点 |
| Ctrl + 单击 | 多选节点（追加/取消选择） |
| 左键拖动空白区域 | 框选多个节点 |
| Ctrl + 左键拖动 | 追加框选节点 |
| 单击空白区域 | 取消所有选中 |
| 单击连线 | 选中连线 |

#### 4.3.2 移动节点

**单节点移动**：
1. 在节点非端口区域按住左键
2. 拖拽到目标位置
3. 释放鼠标完成移动
4. 连接线会自动更新

**多节点批量移动**：
1. 选中多个节点（Ctrl+点击或框选）
2. 在任一选中的节点上按住左键
3. 拖拽到目标位置，所有选中节点同步移动
4. 释放鼠标完成移动
5. 节点间相对位置保持不变，连线自动更新

#### 4.3.3 删除节点/连线

| 方法 | 操作 |
|------|------|
| 快捷键 | 选中后按 `Delete` 或 `Backspace` |
| 右键菜单 | 右键点击 → 选择"删除" |
| 批量删除 | 选中多个节点后按 `Delete` 或右键菜单 |

**删除特性**：
- 删除节点时自动删除相关连线
- 支持撤销/重做操作
- 批量删除支持一次性撤销

#### 4.3.4 复制粘贴

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + C` | 复制选中节点（支持多选） |
| `Ctrl + V` | 粘贴节点 |
| `Ctrl + D` | 复制并粘贴（快捷复制） |

**批量复制特性**：
- 支持复制多个选中的节点
- 自动复制节点间的连线关系
- 粘贴时保持节点间相对位置
- 自动生成新的节点ID

### 4.4 画布操作

#### 4.4.1 缩放操作

| 方法 | 操作 |
|------|------|
| 鼠标滚轮 | 向上放大，向下缩小 |
| 缩放范围 | 0.25x ~ 4.0x |

#### 4.4.2 平移操作

| 方法 | 操作 |
|------|------|
| 右键拖动 | 按住右键拖动平移画布 |
| 右键点击 | 显示上下文菜单 |

**右键操作说明**：
- 右键按下时准备拖动
- 拖动距离超过阈值（5像素）时启动平移
- 未拖动时显示上下文菜单
- 支持多选节点的批量操作菜单

#### 4.4.3 视图重置

- 清空画布会重置所有节点和连线
- 缩放比例重置为 1.0

### 4.5 调试与运行控制

#### 4.5.1 运行行为树

1. 点击工具栏 **[运行]** 按钮（绿色）
2. 或使用快捷键 `空格键`
3. 运行时节点状态会实时显示：

| 状态 | 图标 | 颜色 |
|------|------|------|
| 空闲 | 无 | 默认 |
| 运行中 | ⋯ | 橙色（闪烁） |
| 成功 | ✓ | 绿色 |
| 失败 | ✗ | 红色 |
| 已中止 | ⊘ | 灰色 |

#### 4.5.2 停止执行

1. 点击工具栏 **[停止]** 按钮（红色）
2. 或使用快捷键 `Escape`
3. 停止后所有节点状态重置

### 4.6 撤销与重做

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + Z` | 撤销上一步操作 |
| `Ctrl + Y` | 重做下一步操作 |
| `Ctrl + Shift + Z` | 重做（备选） |

支持撤销的操作：
- 添加/删除节点
- 移动节点
- 添加/删除连线
- 修改属性

### 4.7 快捷键一览

| 快捷键 | 功能 |
|--------|------|
| `Ctrl + N` | 新建 |
| `Ctrl + O` | 打开文件 |
| `Ctrl + S` | 保存 |
| `Ctrl + Shift + S` | 另存为 |
| `Ctrl + Z` | 撤销 |
| `Ctrl + Y` | 重做 |
| `Ctrl + C` | 复制 |
| `Ctrl + V` | 粘贴 |
| `Ctrl + D` | 复制并粘贴 |
| `Delete` / `Backspace` | 删除选中 |
| `Space` | 运行/停止切换 |
| `Escape` | 停止执行 |

---

## 5. 节点功能详解

### 5.1 组合节点 (Composite Nodes)

组合节点用于控制子节点的执行流程，可以包含多个子节点。

#### 5.1.1 顺序节点 (SequenceNode)

**功能描述**：按顺序依次执行所有子节点，所有子节点成功才返回成功。

**执行逻辑**：
```
┌─────────────────────────────────────────────────────────────┐
│                    顺序节点执行流程                          │
└─────────────────────────────────────────────────────────────┘

开始
  │
  ▼
┌─────────────┐
│ 子节点1执行  │── FAILURE ──► 返回 FAILURE
└──────┬──────┘
       │ SUCCESS
       │
       ▼
  [子节点间隔等待] (如果配置了 child_interval)
       │
       ▼
┌─────────────┐
│ 子节点2执行  │── FAILURE ──► 返回 FAILURE
└──────┬──────┘
       │ SUCCESS
       ▼
      ...
       │
       ▼
┌─────────────┐
│ 子节点N执行  │── FAILURE ──► 返回 FAILURE
└──────┬──────┘
       │ SUCCESS
       ▼
   返回 SUCCESS
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| name | string | "" | 节点名称 |
| enabled | bool | true | 是否启用 |
| retry_count | int | 0 | 失败重试次数 |
| repeat_count | int | 1 | 重复次数（-1为无限） |
| timeout_ms | int | 0 | 超时时间（毫秒，0不限） |
| child_interval | int | 0 | 子节点执行间隔（毫秒） |
| continue_on_failure | bool | false | 失败后是否继续执行后续节点 |

**使用场景**：
- 需要按固定顺序执行的任务序列
- 流程化的自动化操作
- 前置条件检查后执行动作

**continue_on_failure 参数说明**：

默认情况下，顺序节点采用"短路失败"策略：任一子节点失败立即终止，后续节点不执行。

开启 `continue_on_failure` 后，行为变为：
1. 子节点失败时不会立即终止
2. 继续执行后续所有子节点
3. 所有子节点执行完毕后，检查是否有失败的节点
4. 如果存在失败的子节点，顺序节点返回 FAILURE
5. 如果所有子节点都成功，顺序节点返回 SUCCESS

```
示例：顺序节点 [A] → [B] → [C] → [D]，开启 continue_on_failure

情况：节点 B 执行失败

执行结果：
├── [A] 执行成功 ✓
├── [B] 执行失败 ✗ ← 记录失败，继续执行
├── [C] 执行成功 ✓ ← 仍然执行
└── [D] 执行成功 ✓ ← 仍然执行

最终结果：返回 FAILURE（因为 B 失败了）
```

适用场景：
- 需要执行所有清理操作，即使中间步骤失败
- 批量操作，需要知道每个操作的结果
- 日志记录/状态收集，不希望遗漏任何步骤

**示例配置**：
```
顺序节点: 登录流程
├── OCR条件: 检测登录按钮
├── 点击动作: 点击登录按钮
├── 延时动作: 等待2秒
└── OCR条件: 检测登录成功
```

---

#### 5.1.2 选择节点 (SelectorNode)

**功能描述**：按顺序执行子节点，任一子节点成功即返回成功。

**执行逻辑**：
```
┌─────────────────────────────────────────────────────────────┐
│                    选择节点执行流程                          │
└─────────────────────────────────────────────────────────────┘

开始
  │
  ▼
┌─────────────┐
│ 子节点1执行  │── SUCCESS ──► 返回 SUCCESS
└──────┬──────┘
       │ FAILURE
       ▼
┌─────────────┐
│ 子节点2执行  │── SUCCESS ──► 返回 SUCCESS
└──────┬──────┘
       │ FAILURE
       ▼
      ...
       │
       ▼
┌─────────────┐
│ 子节点N执行  │── SUCCESS ──► 返回 SUCCESS
└──────┬──────┘
       │ FAILURE
       ▼
   返回 FAILURE
```

**属性参数**：与顺序节点相同（包含 child_interval 子节点间隔参数）

**使用场景**：
- 多种方案尝试，任一成功即可
- 容错处理，提供备选方案
- 条件分支选择

**示例配置**：
```
选择节点: 多方式登录
├── OCR条件: 检测账号密码登录入口
│   └── 顺序节点: 账号密码登录流程
├── OCR条件: 检测扫码登录入口
│   └── 顺序节点: 扫码登录流程
└── OCR条件: 检测第三方登录入口
    └── 顺序节点: 第三方登录流程
```

---

#### 5.1.3 并行节点 (ParallelNode)

**功能描述**：同时执行所有子节点，根据成功策略决定最终结果。

**执行逻辑**：
```
┌─────────────────────────────────────────────────────────────┐
│                    并行节点执行流程                          │
└─────────────────────────────────────────────────────────────┘

              开始
                │
    ┌───────────┼───────────┐
    │           │           │
    ▼           ▼           ▼
┌───────┐  ┌───────┐  ┌───────┐
│子节点1│  │子节点2│  │子节点3│
└───┬───┘  └───┬───┘  └───┬───┘
    │           │           │
    └───────────┼───────────┘
                │
                ▼
        ┌───────────────┐
        │  汇总结果判断  │
        └───────┬───────┘
                │
    ┌───────────┴───────────┐
    │                       │
    ▼                       ▼
require_all             require_one
所有成功才成功           任一成功即成功
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| success_policy | string | "require_all" | 成功策略 |
| - require_all | - | - | 所有子节点成功才成功 |
| - require_one | - | - | 任一子节点成功即成功 |

**使用场景**：
- 需要同时监控多个条件
- 并行执行独立任务
- 多资源同时检测

**示例配置**：
```
并行节点: 多条件检测
├── OCR条件: 检测文字A
├── 图像条件: 检测图标B
└── 颜色条件: 检测颜色C
```

---

### 5.2 条件节点 (Condition Nodes)

条件节点用于检测特定条件是否满足，返回成功或失败。

**串联执行特性**：

条件节点支持子节点串联执行。当条件检测成功后，会依次执行连接的子节点：

```
┌─────────────────────────────────────────────────────────────┐
│                 条件节点串联执行流程                          │
└─────────────────────────────────────────────────────────────┘

条件检测
    │
    ├── FAILURE ──► 返回 FAILURE
    │
    └── SUCCESS
         │
         ▼
    有子节点？
         │
    ┌────┴────┐
    │         │
   否        是
    │         │
    ▼         ▼
 返回     依次执行子节点
SUCCESS   │
          ├── 任一失败 ──► 返回 FAILURE
          │
          └── 全部成功 ──► 返回 SUCCESS
```

**示例**：
```
OCR检测"开始按钮" → 点击节点 → 延时节点(500ms)
执行顺序：检测到"开始按钮" → 点击 → 延时500ms
```

#### 5.2.1 OCR条件节点 (OCRConditionNode)

**功能描述**：使用OCR识别指定区域的文字，检测是否包含目标关键词。

**执行逻辑**：
```
1. 获取指定区域截图
2. 图像预处理（灰度化→对比度增强→锐化→二值化）
3. 调用OCR识别文字
4. 检测是否包含关键词
5. 可选：保存检测位置到黑板（绝对坐标）
```

**图像预处理流程**：
```
原始截图
    │
    ▼
┌─────────────┐
│  灰度转换    │  转换为灰度图像
└──────┬──────┘
       │
       ▼
┌─────────────┐
│ 对比度增强   │  1.5倍对比度
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   锐化处理   │  增强边缘
└──────┬──────┘
       │
       ▼
┌─────────────┐
│   二值化     │  阈值128
└──────┬──────┘
       │
       ▼
  预处理完成
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| region | tuple | (0,0,100,100) | 检测区域 (x1,y1,x2,y2) |
| keywords | string | "" | 目标关键词（逗号分隔多个） |
| language | string | "eng" | OCR语言 (eng/chi_sim/jpn) |
| save_position | bool | true | 是否保存位置到黑板 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| invert | bool | false | 结果取反 |
| retry_count | int | 0 | 失败重试次数 |

**使用场景**：
- 检测界面文字内容
- 识别按钮文字
- 验证文本状态

**示例**：
```
检测区域: 100,100,300,150
关键词: 确定,确认
语言: chi_sim
匹配模式: any
```

---

#### 5.2.2 图像条件节点 (ImageConditionNode)

**功能描述**：使用模板匹配检测指定区域是否包含目标图像。

**执行逻辑**：
```
1. 加载模板图像
2. 获取指定区域截图
3. 执行模板匹配
4. 匹配度超过阈值则成功
5. 可选：保存匹配位置到黑板（绝对坐标）
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| region | tuple | (0,0,100,100) | 检测区域 |
| template_path | string | "" | 模板图像路径 |
| threshold | int | 80 | 匹配阈值（百分比 0~100） |
| save_position | bool | true | 是否保存位置 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| invert | bool | false | 结果取反 |
| retry_count | int | 0 | 失败重试次数 |

**使用场景**：
- 检测特定图标
- 识别按钮状态
- 匹配界面元素

**示例**：
```
检测区域: 100,100,300,150
模板路径: D:/images/button.png
匹配阈值: 90%
```

---

#### 5.2.3 颜色条件节点 (ColorConditionNode)

**功能描述**：检测指定区域是否包含目标颜色。

**执行逻辑**：
```
1. 获取指定区域截图
2. 扫描像素查找目标颜色
3. 匹配像素数超过阈值则成功
4. 可选：保存匹配位置到黑板（绝对坐标）
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| region | tuple | (0,0,100,100) | 检测区域 |
| target_color | tuple | (255,0,0) | 目标颜色 (R,G,B) |
| tolerance | int | 10 | 颜色容差 (0~100) |
| min_pixels | int | 1 | 最小匹配像素数 |
| save_position | bool | true | 是否保存位置 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| invert | bool | false | 结果取反 |
| retry_count | int | 0 | 失败重试次数 |

**使用场景**：
- 检测状态指示灯颜色
- 识别特定颜色区域
- 判断进度条状态

---

#### 5.2.4 数字条件节点 (NumberConditionNode)

**功能描述**：识别指定区域的数字并进行比较判断。

**执行逻辑**：
```
1. 获取指定区域截图
2. 图像预处理（灰度化→对比度增强→锐化→二值化）
3. OCR识别文字
4. 根据提取模式解析数字
5. 与阈值进行比较
6. 可选：保存数字值到黑板
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| region | tuple | (0,0,100,100) | 检测区域 |
| extract_mode | string | "无规则" | 数字提取模式 |
| extract_pattern | string | "" | 自定义提取模式 |
| compare_mode | string | "<" | 比较模式 |
| threshold | int | 0 | 比较阈值 |
| min_confidence | float | 0.5 | 最小识别置信度 |
| preprocess_mode | string | "normal" | 预处理模式 |
| save_value | bool | true | 是否保存值 |
| value_key | string | "last_number_value" | 黑板变量名 |
| position_key | string | "last_detection_position" | 位置变量名 |
| invert | bool | false | 结果取反 |
| retry_count | int | 0 | 失败重试次数 |

**预处理模式说明**：

| 模式 | 说明 | 适用场景 |
|------|------|----------|
| normal | 普通文本模式 | 常规数字识别 |
| artistic | 艺术字模式 | 游戏/艺术字体 |

**提取模式说明**：

| 模式 | 说明 | 示例 |
|------|------|------|
| 无规则 | 直接采集第一个数字 | "HP: 100" → 100 |
| x/y | 识别 x/y 格式中的 x 值 | "50/100" → 50 |
| 自定义 | 使用通配符自定义模式 | 见下方说明 |

**自定义提取模式**：
- 使用 `*` 表示要提取的数字部分
- 示例：
  - `"HP: */MAX"` → 匹配 "HP: 100/MAX" 提取 100
  - `"(*/*)"` → 匹配 "(50/100)" 提取 50
  - `"Level: *"` → 匹配 "Level: 25" 提取 25

**比较模式**：

| 模式 | 说明 |
|------|------|
| < | 小于 |
| <= | 小于等于 |
| > | 大于 |
| >= | 大于等于 |
| == | 等于 |
| != | 不等于 |

**使用场景**：
- 检测数值状态
- 判断资源数量
- 监控计数器

---

#### 5.2.5 变量条件节点 (VariableConditionNode)

**功能描述**：检测黑板变量是否满足指定条件。

**执行逻辑**：
```
1. 从黑板获取变量值
2. 与比较值进行运算
3. 返回比较结果
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variable_name | string | "" | 变量名 |
| operator | string | "==" | 比较运算符 |
| compare_value | any | - | 比较值 |
| invert | bool | false | 结果取反 |
| retry_count | int | 0 | 失败重试次数 |

**支持的运算符**：

| 运算符 | 说明 |
|--------|------|
| == | 等于 |
| != | 不等于 |
| > | 大于 |
| < | 小于 |
| >= | 大于等于 |
| <= | 小于等于 |
| exists | 变量存在 |
| not_exists | 变量不存在 |
| contains | 包含（字符串/列表） |
| not_contains | 不包含 |

**使用场景**：
- 流程控制条件
- 状态机切换
- 计数器判断

---

### 5.3 动作节点 (Action Nodes)

动作节点用于执行具体操作，如按键、点击、延时等。

**串联执行特性**：

动作节点支持子节点串联执行。当动作节点连接子节点时，执行逻辑如下：

```
┌─────────────────────────────────────────────────────────────┐
│                 动作节点串联执行流程                          │
└─────────────────────────────────────────────────────────────┘

动作节点执行
    │
    ├── FAILURE ──► 返回 FAILURE
    │
    └── SUCCESS
         │
         ▼
    有子节点？
         │
    ┌────┴────┐
    │         │
   否        是
    │         │
    ▼         ▼
 返回     依次执行子节点
SUCCESS   │
          ├── 任一失败 ──► 返回 FAILURE
          │
          └── 全部成功 ──► 返回 SUCCESS
```

**示例**：
```
延时节点(1秒) → 点击节点 → 按键节点
执行顺序：延时1秒 → 点击 → 按键，全部成功才返回成功
```

#### 5.3.1 按键动作节点 (KeyPressNode)

**功能描述**：模拟键盘按键操作。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| key | string | "" | 按键名称 |
| action | string | "press" | 动作类型 |
| duration | int | 0 | 按住时长（毫秒） |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

**动作类型**：

| 类型 | 说明 |
|------|------|
| press | 按下并释放 |
| down | 按下不释放 |
| up | 释放按键 |

**常用按键名**：
```
字母: a-z
数字: 0-9
功能: f1-f12
控制: ctrl, alt, shift, win
方向: up, down, left, right
其他: enter, space, tab, escape, backspace
```

---

#### 5.3.2 鼠标点击动作节点 (MouseClickNode)

**功能描述**：模拟鼠标点击操作，支持多次点击。

**执行逻辑**：
```
1. 确定点击位置（固定位置或黑板位置）
2. 移动鼠标到目标位置
3. 根据动作类型执行操作：
   - press: 按下 → 等待时长 → 抬起
   - down: 仅按下
   - up: 仅抬起
4. 多次点击时，重复步骤3（间隔 click_interval 毫秒）
5. 返回执行结果
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| button | string | "left" | 鼠标按钮 (left/right/middle) |
| action | string | "press" | 动作类型 (press/down/up) |
| duration | int | 0 | 按住时长（毫秒） |
| click_count | int | 1 | 点击次数（-1为无限循环点击） |
| click_interval | int | 100 | 多次点击间隔（毫秒） |
| position | tuple | null | 点击位置 (x,y) |
| use_blackboard | bool | false | 点击最近检测点 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

**动作类型说明**：

| 类型 | 说明 | 执行流程 |
|------|------|----------|
| press | 完整点击 | 按下 → 等待duration → 抬起 |
| down | 仅按下 | 鼠标按下不释放 |
| up | 仅抬起 | 释放鼠标按键 |

**鼠标按钮**：
- left: 左键
- right: 右键
- middle: 中键

**click_count 说明**：
- `click_count = 1`：单击（默认）
- `click_count = 2`：双击
- `click_count = 3`：三击
- `click_count = -1`：无限循环点击（直到行为树停止）

**使用场景**：
- 点击按钮、链接
- 拖拽操作（配合 down/up）
- 长按操作（设置 duration）
- 双击操作（设置 click_count=2）

**示例配置**：
```
普通点击:
  button: left
  action: press
  duration: 0
  click_count: 1

双击:
  button: left
  action: press
  click_count: 2
  click_interval: 100

长按500ms:
  button: left
  action: press
  duration: 500

拖拽操作:
  节点1: 鼠标点击 action=down
  节点2: 鼠标移动 relative=true position=(100,0)
  节点3: 鼠标点击 action=up
```

---

#### 5.3.3 鼠标滚轮动作节点 (MouseScrollNode)

**功能描述**：模拟鼠标滚轮滚动操作。

**执行逻辑**：
```
1. 确定滚动位置（固定位置或黑板位置）
2. 移动鼠标到目标位置（可选）
3. 执行滚轮滚动
4. 返回执行结果
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| amount | int | 1 | 滚动量（正数向上，负数向下） |
| position | tuple | null | 滚动位置 (x,y)，null则在当前位置滚动 |
| use_blackboard | bool | false | 在最近检测点滚动 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

**滚动量说明**：
- `amount > 0`：向上滚动（如 amount=3 向上滚动3格）
- `amount < 0`：向下滚动（如 amount=-3 向下滚动3格）
- 每个单位约等于鼠标滚轮的一格

**使用场景**：
- 页面滚动
- 缩放操作（配合 Ctrl 键）
- 列表导航

---

#### 5.3.4 鼠标移动动作节点 (MouseMoveNode)

**功能描述**：移动鼠标到指定位置，支持拖拽操作。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| position | tuple | null | 目标位置 (x,y) |
| use_blackboard | bool | false | 移动到最近检测点 |
| position_key | string | "last_detection_position" | 黑板变量名 |
| relative | bool | false | 相对移动 |
| smooth | bool | true | 平滑移动 |
| move_type | string | "move" | 移动类型（move/drag） |
| drag_button | string | "left" | 拖拽使用的鼠标按钮 |
| end_position | tuple | null | 拖拽终点位置 (x,y) |
| use_blackboard_end | bool | false | 使用黑板获取终点位置 |
| position_key_end | string | "last_detection_position" | 终点位置黑板变量名 |
| drag_duration | int | 500 | 拖拽持续时间（毫秒） |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

**移动类型说明**：
- `move`：普通移动，鼠标移动到目标位置
- `drag`：拖拽操作，按下鼠标按钮后移动到终点位置再释放

**拖拽操作流程**：
```
1. 按下指定鼠标按钮（drag_button）
2. 移动到终点位置（end_position 或黑板变量）
3. 等待 drag_duration 毫秒
4. 释放鼠标按钮
```

---

#### 5.3.4 延时动作节点 (DelayNode)

**功能描述**：等待指定时间。

**重要特性**：延时节点是**非阻塞**的，执行期间返回 `RUNNING` 状态，不会阻塞整个行为树的执行。

**执行逻辑**：
```
开始延时
  │
  ▼
检查已过时间 < duration_ms ── 是 ──► 返回 RUNNING（下一帧继续检查）
  │
  │ 否（时间到）
  ▼
返回 SUCCESS
```

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| duration_ms | int | 1000 | 延时时长（毫秒） |
| repeat_count | int | 1 | 重复次数 |

---

#### 5.3.5 设置变量动作节点 (SetVariableNode)

**功能描述**：设置黑板变量的值。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| variable_name | string | "" | 变量名 |
| operation | string | "set" | 操作类型 |
| value | any | - | 变量值 |
| repeat_count | int | 1 | 重复次数 |

**操作类型**：

| 操作 | 说明 |
|------|------|
| set | 设置值 |
| increment | 递增 |
| delete | 删除变量 |
| clear | 清空黑板 |

---

#### 5.3.6 脚本动作节点 (ScriptNode)

**功能描述**：执行原项目脚本格式的txt文件。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| script_path | string | "" | 脚本文件路径 |
| loop | bool | false | 循环执行 |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

---

#### 5.3.7 代码动作节点 (CodeNode)

**功能描述**：执行外部代码文件（Python/Batch/PowerShell）。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| code_path | string | "" | 代码文件路径 |
| code_type | string | "auto" | 代码类型 |
| args | list | [] | 命令行参数 |
| repeat_count | int | 1 | 重复次数 |
| timeout_ms | int | 0 | 超时时间 |

**代码类型**：
- auto: 自动识别（根据扩展名）
- python: Python脚本
- batch: 批处理文件
- powershell: PowerShell脚本

---

#### 5.3.8 报警动作节点 (AlarmNode) ⭐ 新增

**功能描述**：播放报警音效，支持自定义音频文件、音量、播放次数等参数。

**属性参数**：

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| sound_path | string | "" | 音频文件路径（留空使用全局默认） |
| volume | int | null | 音量（0-100，留空使用全局音量） |
| repeat_count | int | 1 | 播放次数 |
| interval_ms | int | 0 | 播放间隔（毫秒） |
| wait_complete | bool | true | 是否等待播放完成 |

**音频文件支持**：
- MP3、WAV、OGG、FLAC 等常见音频格式
- 留空时自动使用工具设置中的全局报警音
- 如果全局设置也无效，使用项目自带的 `voice/alarm.mp3`

**播放模式**：
- **等待播放完成**（默认）：节点等待音频播放完成才继续执行后续节点
- **异步播放**：节点立即返回成功，音频在后台播放，同时执行后续节点

**使用场景**：
- 检测到异常情况时播放报警音
- 任务完成时播放提示音
- 需要引起用户注意的场景
- 自定义成功/失败音效

**示例配置**：
```
示例1：简单报警
OCR检测"错误" → 报警节点（默认设置）→ 点击"确定"按钮

示例2：自定义报警
图像检测特定图标 → 报警节点（自定义音频，音量80%，播放3次）→ 执行脚本

示例3：异步报警
OCR检测"完成" → 报警节点（异步播放）→ 发送按键"Ctrl+S"保存
```

**技术实现**：
- 复用 `AlarmModule` 的音频播放功能
- 通过 `ExecutionContext.play_alarm()` 调用
- 支持同步/异步播放模式
- 自动处理音频文件不存在等异常情况

---

### 5.4 装饰参数详解

装饰参数是附加在节点上的特殊配置，用于改变节点的执行行为。

#### 5.4.1 组合节点装饰参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| retry_count | int | 0 | 失败后重试次数（-1无限重试，无上限） |
| repeat_count | int | 1 | 整体重复次数（1不重复，-1无限） |
| timeout_ms | int | 0 | 执行超时时间（毫秒，0不限） |

**retry_count 执行次数说明**：
- `retry_count = 0`：执行 1 次（初始执行，不重试）
- `retry_count = 1`：执行 2 次（初始执行 + 1 次重试）
- `retry_count = N`：执行 N+1 次（初始执行 + N 次重试）
- `retry_count = -1`：无限重试，直到成功或手动停止
- 总执行次数 = retry_count + 1（有限重试时）

**执行流程**：
```
┌─────────────────────────────────────────────────────────────┐
│                 组合节点装饰参数执行流程                     │
└─────────────────────────────────────────────────────────────┘

开始
  │
  ▼
检查超时 ── 超时 ──► 返回 FAILURE
  │
  │ 未超时
  ▼
执行子节点
  │
  ├── SUCCESS ──► repeat_count检查 ── 未完成 ──► 重置子节点，继续执行
  │                                    │
  │                                    └── 完成 ──► 返回 SUCCESS
  │
  └── FAILURE ──► retry_count检查 ── 有重试 ──► 重置子节点，重试
                                     │
                                     └── 无重试 ──► 返回 FAILURE
```

#### 5.4.2 条件节点装饰参数

| 参数 | 类型 | 默认值 | 说明 |
|------|------|--------|------|
| invert | bool | false | 取反检测结果 |
| retry_count | int | 0 | 失败重试次数（-1无限重试，无上限） |
| timeout_ms | int | 0 | 检测超时时间（毫秒，0不限） |
| check_interval_ms | int | 300 | 检测间隔（毫秒，最小30，用于减少CPU占用） |

**取反逻辑**：
```
原始结果    取反后
SUCCESS  →  FAILURE
FAILURE  →  SUCCESS
RUNNING  →  RUNNING
```

**检测间隔说明**：
- `check_interval_ms` 用于控制条件检测的频率
- 默认值 300ms，最小值 30ms
- 适当增加间隔可减少 CPU 占用
- 对于需要快速响应的场景，可降低间隔（最小 30ms）

**无限重试说明**：
- `retry_count = -1` 表示无限重试，直到条件满足
- 建议配合 `timeout_ms` 使用，避免无限等待
- 可通过手动停止行为树来中止无限重试

#### 5.4.3 动作节点装饰参数

| 参数 | 类型 | 说明 |
|------|------|------|
| repeat_count | int | 重复次数（1不重复，-1无限） |
| timeout_ms | int | 执行超时时间（毫秒，0不限） |

---

## 6. 附录

### 6.1 节点类型速查表

| 类型 | 类名 | 分类 | 说明 | 支持子节点 |
|------|------|------|------|------------|
| 顺序 | SequenceNode | 组合 | 按顺序执行，全成功才成功 | ✓ |
| 选择 | SelectorNode | 组合 | 按顺序执行，任一成功即成功 | ✓ |
| 并行 | ParallelNode | 组合 | 同时执行，按策略判定 | ✓ |
| OCR检测 | OCRConditionNode | 条件 | 检测文字内容 | ✓ (串联执行) |
| 图像匹配 | ImageConditionNode | 条件 | 匹配图像模板 | ✓ (串联执行) |
| 颜色检测 | ColorConditionNode | 条件 | 检测颜色值 | ✓ (串联执行) |
| 数字比较 | NumberConditionNode | 条件 | 比较数值大小 | ✓ (串联执行) |
| 变量判断 | VariableConditionNode | 条件 | 判断变量值 | ✓ (串联执行) |
| 按键 | KeyPressNode | 动作 | 模拟键盘按键 | ✓ (串联执行) |
| 点击 | MouseClickNode | 动作 | 模拟鼠标点击 | ✓ (串联执行) |
| 移动 | MouseMoveNode | 动作 | 移动鼠标位置 | ✓ (串联执行) |
| 滚轮 | MouseScrollNode | 动作 | 模拟鼠标滚轮滚动 | ✓ (串联执行) |
| 延时 | DelayNode | 动作 | 等待指定时间 | ✓ (串联执行) |
| 设变量 | SetVariableNode | 动作 | 设置变量值 | ✓ (串联执行) |
| 脚本 | ScriptNode | 动作 | 执行脚本文件 | ✓ (串联执行) |
| 代码 | CodeNode | 动作 | 执行代码文件 | ✓ (串联执行) |
| 报警 | AlarmNode | 动作 | 播放报警音频 | ✓ (串联执行) |

**说明**：
- 组合节点：子节点按节点类型定义的逻辑执行
- 条件节点：条件成功后，子节点依次串联执行
- 动作节点：动作成功后，子节点依次串联执行

### 6.2 黑板内置变量

| 变量名 | 类型 | 说明 |
|--------|------|------|
| last_detection_position | tuple | 最后检测位置（OCR/图像/颜色/数字检测统一使用） |
| last_number_value | int/float | 最后识别的数字值 |
| execution_count | int | 执行计数 |

**说明**：
- `last_detection_position`：所有检测节点（OCR/图像/颜色/数字）检测成功后，会将检测到的位置统一保存到此变量
- 保存的是**绝对坐标**（屏幕坐标），而非相对于检测区域的坐标
- 点击节点勾选"点击最近检测点"时，会从此变量读取位置
- 数字条件节点检测成功后，同时将数字值保存到 `last_number_value`

### 6.3 文件格式版本历史

| 版本 | 变更说明 |
|------|----------|
| 1.0 | 初始版本，基础节点结构 |
| 2.0 | 增加元数据、画布状态、编辑器状态、连接线数据 |

### 6.4 常见问题解答

**Q: 如何实现循环执行？**

A: 设置组合节点的 `repeat_count` 为 -1 即可实现无限循环。

**Q: 如何使用黑板传递数据？**

A: 条件节点检测成功后可将位置保存到黑板，动作节点通过 `use_blackboard` 选项读取黑板位置。

**Q: 节点执行失败如何处理？**

A: 使用选择节点提供备选方案，或设置 `retry_count` 进行重试。

**Q: 如何调试行为树？**

A: 运行时观察节点状态颜色变化，查看日志输出了解执行细节。

**Q: 动作节点可以直接连接动作节点吗？**

A: **可以**。动作节点和条件节点现在支持子节点串联执行。当动作节点连接子节点时，执行逻辑如下：

```
执行流程：
动作节点A执行 → 成功 → 执行子节点B → 成功 → 执行子节点C → ...
                ↓ 失败              ↓ 失败
              返回失败            返回失败

示例：
延时节点(1秒) → 点击节点 → 按键节点
执行顺序：延时1秒 → 点击 → 按键，全部成功才返回成功
```

**条件节点同理**：条件检测成功后，会依次执行连接的子节点。

**Q: 如何确定多个子节点的执行顺序？**

A: 执行顺序按照连接线的**添加顺序**确定。当组合节点有多个子节点时，连接线上会显示序号（1、2、3...）表示执行顺序。如需调整顺序，可以删除连接线后按期望顺序重新连接。

**Q: 修改属性后运行不生效怎么办？**

A: 确保修改属性后已保存（`Ctrl+S`），或切换选中节点时会自动保存属性。属性值会同步到节点实例，运行时使用最新配置。

---

## 文档版本

- **版本**: 2.4
- **创建日期**: 2026-03-30
- **更新日期**: 2026-04-06
- **适用项目版本**: AutoDoor v3.0.5

### 更新历史

| 版本 | 日期 | 更新内容 |
|------|------|----------|
| 2.4 | 2026-04-06 | 新增：条件节点检测间隔参数(check_interval_ms)；完善：retry_count支持-1无限重试，移除上限限制；优化：ScriptNode线程池管理，添加竞态条件保护；完善：节点abort中止机制；更新：并行节点中止RUNNING子节点逻辑 |
| 2.3 | 2026-04-06 | 新增：节点中止接口（abort方法）；完善：并行节点完成时中止RUNNING子节点的行为；新增：CodeNode/ScriptNode/MouseClickNode 中止逻辑实现；更新：并行节点算法伪代码 |
| 2.2 | 2026-04-06 | 根据代码分析报告更新：统一黑板变量为 last_detection_position；补充空子节点行为说明；完善 retry_count/repeat_count 执行次数说明；补充并行节点缓存机制；补充无限循环子节点执行时机；新增 MouseScrollNode 滚轮节点；补充 MouseClickNode 多次点击参数；补充 MouseMoveNode 拖拽参数；补充 NumberConditionNode 预处理参数；补充 DelayNode 非阻塞特性说明 |
| 2.1 | 2026-04-04 | 新增：顺序节点 `continue_on_failure` 参数，支持失败后继续执行后续节点 |
| 2.0 | 2026-04-01 | 新增：子节点执行间隔、数字提取模式、鼠标点击动作类型和按住时长；优化：统一黑板变量、OCR/数字节点图像预处理、图像匹配阈值百分比格式 |
| 1.2 | 2026-03-30 | 新增：节点串联执行说明、常见问题解答 |
| 1.0 | 2026-03-28 | 初始版本 |
