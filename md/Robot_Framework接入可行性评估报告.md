# Robot Framework 接入可行性评估报告（完整版）

## 文档信息

| 项目 | 内容 |
|------|------|
| 文档版本 | v3.0 |
| 评估日期 | 2026-03-08 |
| 评估项目 | AutoDoor OCR 识别系统 |
| 评估目标 | Robot Framework 第三方库能力分析与完整重构可行性 |

---

## 一、Robot Framework 第三方库生态分析

### 1.1 桌面自动化相关库

| 库名 | 类型 | 功能 | 平台 | 成熟度 |
|------|------|------|------|--------|
| **RPA.Desktop** | 跨平台桌面自动化 | 鼠标点击、键盘输入、屏幕操作 | Win/Mac/Linux | ⭐⭐⭐⭐ |
| **RPA.Windows** | Windows桌面自动化 | UI Automation、窗口控制 | Windows | ⭐⭐⭐⭐ |
| **AutoItLibrary** | Windows GUI自动化 | 鼠标键盘操作、窗口控制 | Windows | ⭐⭐⭐ |
| **WhiteLibrary** | Windows GUI测试 | 基于TestStack.White | Windows | ⭐⭐⭐ |
| **RPALite** | 新兴RPA库 | OCR、图像识别、鼠标键盘 | Win/Mac/Linux | ⭐⭐⭐ |

### 1.2 OCR/图像识别相关库

| 库名 | 底层技术 | 中文支持 | 特点 |
|------|----------|----------|------|
| **rpaframework-recognition** | Tesseract + OpenCV | ⚠️ 需配置 | 官方库，集成度高 |
| **RPALite** | EasyOCR/PaddleOCR | ✅ 原生支持 | 新兴库，中文友好 |

### 1.3 详细功能分析

#### RPA Framework (rpaframework)

```
安装: pip install rpaframework
OCR扩展: pip install rpaframework-recognition

包含的库:
├── RPA.Browser.Selenium - 浏览器自动化
├── RPA.Desktop - 跨平台桌面自动化
├── RPA.Windows - Windows桌面自动化
├── RPA.Excel.Files - Excel操作
├── RPA.Email - 邮件处理
├── RPA.HTTP - HTTP请求
└── RPA.Recognition - OCR/图像识别 (需单独安装)
```

**RPA.Desktop 关键字示例：**
```robot
*** Settings ***
Library    RPA.Desktop

*** Tasks ***
Desktop Automation Example
    Click    point=100,200
    Type Text    Hello World
    Press Keys    ctrl+c
    Take Screenshot    screenshot.png
```

**RPA.Recognition OCR示例：**
```robot
*** Settings ***
Library    RPA.Recognition

*** Tasks ***
OCR Example
    ${text}=    Read Text    image.png
    Log    ${text}
    
    Click Text    Submit    # 点击包含"Submit"文本的位置
```

#### RPALite

```
安装: pip install RPALite

特点:
├── 多OCR引擎支持 (EasyOCR, PaddleOCR)
├── 原生中文识别支持
├── 智能元素定位 (文本/图像/坐标)
├── 跨平台支持 (Windows最完善)
└── 支持Robot Framework集成
```

**RPALite Python示例：**
```python
from rpalite import RPALite

rpa = RPALite()
rpa.run_command("notepad.exe")
rpa.input_text("Hello World")
rpa.close_app()
```

**RPALite Robot Framework示例：**
```robot
*** Settings ***
Library    RPALite

*** Tasks ***
RPALite Example
    Run Command    notepad.exe
    Input Text    Hello World
    Click By Text    文件
    Close App
```

---

## 二、功能替代性详细分析

### 2.1 功能对比矩阵

| 功能模块 | AutoDoor实现 | RF第三方库 | 替代程度 | 说明 |
|----------|--------------|------------|----------|------|
| **OCR文字识别** | Tesseract + pytesseract | rpaframework-recognition / RPALite | ✅ 90% | 可替代，RPALite中文支持更好 |
| **图像模板匹配** | OpenCV cv2.matchTemplate | rpaframework-recognition | ✅ 85% | 可替代，功能相似 |
| **鼠标点击** | PyAutoGUI | RPA.Desktop / AutoItLibrary | ✅ 95% | 可替代，功能更丰富 |
| **键盘输入** | pynput | RPA.Desktop / AutoItLibrary | ✅ 95% | 可替代，功能更丰富 |
| **后台窗口监控** | PrintWindow API | ❌ 无 | ❌ 0% | **不可替代**，无库支持 |
| **窗口捕获** | Win32 API | RPA.Windows (有限) | ⚠️ 40% | 部分替代，需窗口可见 |
| **脚本录制** | 内置录制功能 | ❌ 无 | ❌ 0% | **不可替代**，无库支持 |
| **颜色识别** | RGB颜色匹配 | ❌ 无直接支持 | ⚠️ 30% | 需自定义关键字 |
| **数字识别** | OCR + 正则提取 | ❌ 无直接支持 | ⚠️ 30% | 需自定义关键字 |
| **定时任务** | 多线程调度 | RF内置支持 | ✅ 100% | 可替代 |
| **优先级事件队列** | PriorityQueue | ❌ 无 | ⚠️ 20% | 需自定义实现 |
| **分辨率自适应** | 比例坐标系统 | ❌ 无 | ⚠️ 10% | 需自定义实现 |
| **GUI界面** | CustomTkinter | ❌ RF无GUI | ❌ N/A | 不适用 |

### 2.2 核心功能详细对比

#### 2.2.1 OCR识别对比

| 维度 | AutoDoor | rpaframework-recognition | RPALite |
|------|----------|--------------------------|---------|
| 引擎 | Tesseract | Tesseract | EasyOCR/PaddleOCR |
| 中文支持 | ✅ chi_sim | ⚠️ 需修改源码 | ✅ 原生支持 |
| 多语言 | ✅ 可配置 | ⚠️ 默认英文 | ✅ 80+语言 |
| 区域识别 | ✅ 支持 | ✅ 支持 | ✅ 支持 |
| 置信度 | ❌ 无 | ✅ 支持 | ✅ 支持 |
| 点击文本 | ❌ 无 | ✅ Click Text | ✅ Click By Text |

**结论：RF库在OCR方面功能相当甚至更强（RPALite中文支持更好）**

#### 2.2.2 图像检测对比

| 维度 | AutoDoor | rpaframework-recognition |
|------|----------|--------------------------|
| 技术 | OpenCV模板匹配 | OpenCV模板匹配 |
| 阈值设置 | ✅ 支持 | ✅ 支持 |
| 多模板 | ✅ 支持 | ⚠️ 需循环处理 |
| 点击匹配位置 | ✅ 支持 | ✅ 支持 |

**结论：RF库在图像检测方面功能相当**

#### 2.2.3 后台监控对比（关键差异）

| 维度 | AutoDoor | RF第三方库 |
|------|----------|------------|
| 后台截图 | ✅ PrintWindow API | ❌ 不支持 |
| 最小化窗口监控 | ✅ 支持 | ❌ 不支持 |
| 窗口句柄操作 | ✅ Win32 API | ⚠️ 有限支持 |
| 相对坐标系统 | ✅ 支持 | ❌ 不支持 |
| 分辨率自适应 | ✅ 比例坐标 | ❌ 不支持 |

**结论：后台监控是AutoDoor的核心竞争优势，RF生态无替代方案**

#### 2.2.4 脚本录制对比

| 维度 | AutoDoor | RF第三方库 |
|------|----------|------------|
| 录制功能 | ✅ 内置 | ❌ 无 |
| 脚本格式 | 自定义DSL | RF关键字语法 |
| 回放功能 | ✅ 支持 | ✅ 支持 |
| 编辑功能 | ✅ GUI编辑 | ❌ 需外部编辑器 |

**结论：脚本录制是AutoDoor的独特功能，RF生态无替代方案**

### 2.3 替代性总结

```
功能替代性统计:
┌─────────────────────────────────────────────────────────────┐
│  可完全替代 (80%+):     5项 / 13项  (38%)                   │
│  部分可替代 (20-80%):   5项 / 13项  (38%)                   │
│  不可替代 (0-20%):      3项 / 13项  (24%)                   │
│                                                             │
│  整体替代率: 约 60%                                          │
│                                                             │
│  不可替代的核心功能:                                         │
│  ├── 后台窗口监控 (PrintWindow API)                         │
│  ├── 脚本录制功能                                           │
│  └── 分辨率自适应坐标系统                                    │
└─────────────────────────────────────────────────────────────┘
```

---

## 三、完整重构必要性分析

### 3.1 重构必要性评估

| 评估维度 | 评分 | 说明 |
|----------|------|------|
| 技术债务 | 低 | 现有代码架构清晰，模块化程度高 |
| 维护困难度 | 低 | 代码可读性好，有完善文档 |
| 功能缺失 | 低 | 核心功能完整，无重大缺陷 |
| 扩展需求 | 中 | 可能需要更多高级功能 |
| 性能问题 | 低 | 性能满足需求 |
| 团队能力 | 低 | 团队熟悉现有技术栈 |

**必要性评分：2.0/5.0（低）**

### 3.2 重构收益分析

| 收益维度 | 现有方案 | RF重构后 | 收益评估 |
|----------|----------|----------|----------|
| 代码可读性 | 良好 | 更好（关键字驱动） | 小幅提升 |
| 测试报告 | 日志窗口 | HTML报告 | 明显提升 |
| 非技术人员参与 | 困难 | 容易 | 明显提升 |
| 社区支持 | 有限 | 丰富 | 明显提升 |
| 扩展性 | 良好 | 更好 | 小幅提升 |
| 后台监控能力 | ✅ 强大 | ❌ 丢失 | **重大损失** |
| 脚本录制 | ✅ 有 | ❌ 丢失 | **重大损失** |
| 打包体积 | ~100MB | ~200MB+ | 增加 |
| 启动速度 | 快 | 较慢 | 下降 |

### 3.3 重构风险分析

| 风险项 | 风险等级 | 说明 |
|--------|----------|------|
| 功能丢失 | **极高** | 后台监控、脚本录制无法实现 |
| 工作量超支 | 高 | 预计16-24周，可能更长 |
| 学习曲线 | 中 | 团队需学习RF生态 |
| 性能下降 | 中 | RF框架开销 |
| 用户接受度 | 高 | 现有用户需重新学习 |
| 维护成本 | 中 | 需维护RF版本兼容性 |

---

## 四、完整重构可行性分析

### 4.1 技术可行性

```
┌─────────────────────────────────────────────────────────────┐
│  技术可行性评估                                              │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│  可行的部分 (约60%):                                         │
│  ├── ✅ OCR识别 → rpaframework-recognition / RPALite        │
│  ├── ✅ 图像检测 → rpaframework-recognition                 │
│  ├── ✅ 鼠标点击 → RPA.Desktop / AutoItLibrary              │
│  ├── ✅ 键盘输入 → RPA.Desktop / AutoItLibrary              │
│  ├── ✅ 定时任务 → RF内置                                    │
│  └── ✅ 报告生成 → RF内置                                    │
│                                                             │
│  需自定义的部分 (约25%):                                     │
│  ├── ⚠️ 颜色识别 → 自定义关键字库                           │
│  ├── ⚠️ 数字识别 → 自定义关键字库                           │
│  ├── ⚠️ 优先级队列 → 自定义实现                             │
│  └── ⚠️ 分辨率自适应 → 自定义实现                           │
│                                                             │
│  不可行的部分 (约15%):                                       │
│  ├── ❌ 后台窗口监控 → 无RF库支持PrintWindow API            │
│  └── ❌ 脚本录制 → 无RF库支持                               │
│                                                             │
│  整体技术可行性: 60%                                         │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

### 4.2 工作量估算

| 阶段 | 工作内容 | 工作量 | 风险 |
|------|----------|--------|------|
| Phase 1 | RF环境搭建、基础库集成 | 1-2周 | 低 |
| Phase 2 | OCR/图像检测模块迁移 | 2-3周 | 中 |
| Phase 3 | 鼠标键盘模块迁移 | 1-2周 | 低 |
| Phase 4 | 自定义关键字库开发 | 3-4周 | 中 |
| Phase 5 | 后台监控替代方案研发 | 4-6周 | **极高** |
| Phase 6 | 脚本录制替代方案研发 | 3-4周 | **极高** |
| Phase 7 | GUI界面重构 | 2-3周 | 中 |
| Phase 8 | 测试与调试 | 2-3周 | 中 |
| **总计** | | **18-27周** | **高** |

### 4.3 关键技术挑战

#### 挑战1: 后台窗口监控

```
问题描述:
├── RF生态无支持PrintWindow API的库
├── RPA.Windows需要窗口可见
└── AutoItLibrary同样需要窗口可见

可能的解决方案:
├── 方案A: 自定义RF库封装PrintWindow API
│   ├── 可行性: 技术可行
│   ├── 工作量: 2-3周
│   └── 风险: 中等
│
├── 方案B: 使用Windows Hook
│   ├── 可行性: 技术可行，但复杂
│   ├── 工作量: 4-6周
│   └── 风险: 高
│
└── 方案C: 放弃后台监控功能
    ├── 可行性: 可行
    ├── 影响: 丢失核心竞争优势
    └── 风险: 极高（用户流失）
```

#### 挑战2: 脚本录制

```
问题描述:
├── RF生态无脚本录制工具
├── RF脚本需要手动编写
└── 非技术人员无法使用

可能的解决方案:
├── 方案A: 开发RF脚本录制器
│   ├── 可行性: 技术可行
│   ├── 工作量: 4-6周
│   └── 风险: 高
│
├── 方案B: 使用RIDE编辑器
│   ├── 可行性: 可行
│   ├── 用户体验: 较差
│   └── 风险: 中等
│
└── 方案C: 放弃录制功能
    ├── 可行性: 可行
    ├── 影响: 用户体验大幅下降
    └── 风险: 高（用户流失）
```

---

## 五、综合评估

### 5.1 决策矩阵

| 决策因素 | 权重 | 保持现状 | RF重构 | 加分项 |
|----------|------|----------|--------|--------|
| 功能完整性 | 25% | 5 | 2 | 保持现状 |
| 核心竞争力 | 20% | 5 | 1 | 保持现状 |
| 开发成本 | 15% | 5 | 2 | 保持现状 |
| 维护成本 | 15% | 4 | 3 | 保持现状 |
| 扩展性 | 10% | 3 | 4 | RF重构 |
| 社区支持 | 10% | 2 | 5 | RF重构 |
| 学习曲线 | 5% | 5 | 3 | 保持现状 |
| **加权得分** | 100% | **4.35** | **2.55** | **保持现状** |

### 5.2 SWOT分析

#### 保持现状

| 优势 (S) | 劣势 (W) |
|----------|----------|
| 后台监控能力独特 | 社区支持有限 |
| 脚本录制功能 | 扩展性一般 |
| 代码架构清晰 | 非技术人员难参与 |
| 团队熟悉 | 报告功能简单 |

| 机会 (O) | 威胁 (T) |
|----------|----------|
| 持续优化核心功能 | 竞品出现 |
| 增加RF作为可选功能 | 技术债务积累 |
| 开源社区建设 | 用户需求变化 |

#### RF完整重构

| 优势 (S) | 劣势 (W) |
|----------|----------|
| 社区支持丰富 | 丢失核心功能 |
| 关键字驱动易读 | 工作量大 |
| 扩展性强 | 学习曲线陡 |
| 报告功能强大 | 打包体积大 |

| 机会 (O) | 威胁 (T) |
|----------|----------|
| 吸引新用户 | 现有用户流失 |
| 企业级应用 | 功能不完整被诟病 |
| 开源贡献 | 维护成本增加 |

### 5.3 最终建议

```
┌─────────────────────────────────────────────────────────────┐
│                      最终建议                                │
├─────────────────────────────────────────────────────────────┤
│                                                             │
│   ❌ 不建议使用RF完整重构项目                                │
│                                                             │
│   核心原因:                                                  │
│   ├── 功能替代率仅60%，丢失40%核心功能                       │
│   ├── 后台监控能力无法替代（核心竞争优势）                    │
│   ├── 脚本录制功能无法替代（用户体验关键）                    │
│   ├── 工作量巨大（18-27周）                                  │
│   ├── 风险极高（功能丢失、用户流失）                         │
│   └── 投入产出比极低                                         │
│                                                             │
│   替代建议:                                                  │
│   ├── ✅ 保持现有核心架构                                    │
│   ├── ✅ 引入RF作为可选的高级脚本功能（功能扩展方案）          │
│   ├── ✅ 借鉴RF生态的优秀实践（报告、关键字驱动思想）          │
│   └── ✅ 持续优化现有功能                                    │
│                                                             │
└─────────────────────────────────────────────────────────────┘
```

---

## 六、RF第三方库能力总结

### 6.1 可用的RF第三方库清单

| 库名 | 安装命令 | 用途 | 推荐度 |
|------|----------|------|--------|
| rpaframework | `pip install rpaframework` | RPA核心库集合 | ⭐⭐⭐⭐⭐ |
| rpaframework-recognition | `pip install rpaframework-recognition` | OCR/图像识别 | ⭐⭐⭐⭐ |
| RPALite | `pip install RPALite` | 新兴RPA库，中文友好 | ⭐⭐⭐⭐ |
| robotframework-autoitlibrary | `pip install robotframework-autoitlibrary` | Windows GUI自动化 | ⭐⭐⭐ |
| robotframework-whitelibrary | `pip install robotframework-whitelibrary` | Windows GUI测试 | ⭐⭐⭐ |

### 6.2 功能覆盖情况

```
AutoDoor功能 → RF第三方库覆盖情况:

✅ 完全覆盖:
├── OCR识别 → rpaframework-recognition, RPALite
├── 图像检测 → rpaframework-recognition
├── 鼠标点击 → RPA.Desktop, AutoItLibrary, RPALite
├── 键盘输入 → RPA.Desktop, AutoItLibrary, RPALite
└── 定时任务 → RF内置

⚠️ 部分覆盖:
├── 窗口操作 → RPA.Windows (需窗口可见)
├── 颜色识别 → 需自定义
├── 数字识别 → 需自定义
└── 优先级调度 → 需自定义

❌ 无法覆盖:
├── 后台窗口监控 → 无库支持PrintWindow API
├── 脚本录制 → 无库支持
└── 分辨率自适应 → 无库支持
```

---

## 七、附录

### 7.1 RF库使用示例

#### RPA.Desktop 示例

```robot
*** Settings ***
Library    RPA.Desktop

*** Variables ***
${REGION}    100,100,500,300

*** Tasks ***
Desktop Automation
    # 鼠标操作
    Click    point=100,200
    Right Click    point=100,200
    Double Click    point=100,200
    
    # 键盘操作
    Type Text    Hello World
    Press Keys    ctrl+a
    Press Keys    ctrl+c
    
    # 截图
    Take Screenshot    screenshot.png
```

#### RPA.Recognition 示例

```robot
*** Settings ***
Library    RPA.Recognition

*** Tasks ***
OCR And Image Recognition
    # OCR识别
    ${text}=    Read Text    image.png
    Log    Recognized text: ${text}
    
    # 点击文本
    Click Text    Submit    confidence=0.8
    
    # 查找图像
    ${matches}=    Find Template    template.png    confidence=0.9
    FOR    ${match}    IN    @{matches}
        Log    Found at: ${match}
    END
```

#### RPALite 示例

```robot
*** Settings ***
Library    RPALite

*** Tasks ***
RPALite Automation
    # 启动应用
    Run Command    notepad.exe
    
    # 等待窗口
    Wait For Window    记事本    timeout=10
    
    # 输入文本
    Input Text    Hello World
    
    # 点击文本（支持中文）
    Click By Text    文件
    
    # OCR识别
    ${text}=    Get Text From Screen    region=100,100,500,300
    
    # 关闭应用
    Close App
```

### 7.2 自定义关键字库示例

```python
# CustomAutoDoorKeywords.py
"""
自定义RF关键字库，补充RF生态缺失的功能
"""
from robot.api.deco import keyword, library
import win32gui
import win32ui
import win32con
from PIL import Image
import ctypes

@library
class CustomAutoDoorKeywords:
    """补充RF生态缺失的AutoDoor功能"""
    
    @keyword
    def capture_window_background(self, window_title: str) -> str:
        """
        后台截图 - 使用PrintWindow API
        这是RF生态缺失的核心功能
        """
        hwnd = win32gui.FindWindow(None, window_title)
        if not hwnd:
            raise Exception(f"Window not found: {window_title}")
        
        # PrintWindow API实现
        # ... 实现代码 ...
        return "screenshot.png"
    
    @keyword
    def click_at_relative_position(self, window_title: str, rel_x: int, rel_y: int):
        """
        相对坐标点击 - 支持分辨率自适应
        """
        hwnd = win32gui.FindWindow(None, window_title)
        rect = win32gui.GetWindowRect(hwnd)
        
        abs_x = rect[0] + rel_x
        abs_y = rect[1] + rel_y
        
        # 执行点击
        # ... 实现代码 ...
    
    @keyword
    def recognize_color(self, x: int, y: int, expected_color: str, tolerance: int = 10) -> bool:
        """
        颜色识别
        """
        # 获取屏幕颜色
        # 比较颜色
        # ... 实现代码 ...
        return True
```

### 7.3 参考资料

| 资料 | 链接 |
|------|------|
| RPA Framework 官方文档 | https://rpaframework.org/ |
| RPA.Desktop 文档 | https://rpaframework.org/libraries/desktop/ |
| RPA.Windows 文档 | https://rpaframework.org/libraries/windows/ |
| RPALite GitHub | https://gitcode.com/jieliu2000/rpalite |
| Robot Framework 官网 | https://robotframework.org/ |
| AutoItLibrary 文档 | https://github.com/markbergsma/robotframework-autoitlibrary |

---

## 八、结论

### 8.1 核心发现

1. **RF第三方库可以替代约60%的AutoDoor功能**
2. **后台窗口监控（PrintWindow API）无RF库支持，是核心差异**
3. **脚本录制功能无RF库支持，是用户体验关键**
4. **完整重构工作量巨大（18-27周），风险极高**
5. **投入产出比极低，不建议完整重构**

### 8.2 最终建议

| 建议 | 说明 |
|------|------|
| **完整重构** | ❌ 不建议 |
| **功能扩展** | ✅ 建议作为可选高级功能 |
| **借鉴实践** | ✅ 学习RF的报告、关键字驱动思想 |

---

*本报告由 AutoDoor 开发团队编制，如有问题请提交 Issue。*
