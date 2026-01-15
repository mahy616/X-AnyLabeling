# X-AnyLabeling 项目架构分析报告

**文档生成日期**: 2026年1月15日
**用途**: 本文档旨在梳理项目架构、核心组件交互及数据流向，为后续功能开发（Feature Implementation）提供上下文参考。

---

## 1. 项目概览 (Project Overview)

**X-AnyLabeling** 是一个基于 PyQt5/PySide6 的图像标注工具，主要用于计算机视觉任务（检测、分割、姿态估计等）。它集成了 AI 自动标注功能，并支持多种导出格式。

- **核心框架**: Python + PyQt5 / PySide6 (GUI)
- **主要特点**: 交互式标注 (Canvas), 自动标注 (Auto-Labeling Service), 多格式支持 (JSON, XML, TXT)。
- **最近更新**: 增加了 VisionMaster (VM) 格式支持（分割/检测模式）、批量删除功能、多边形右键撤回。

---

## 2. 目录结构与核心模块 (Directory Structure)

```text
D:\github\X-AnyLabeling\
├── anylabeling\
│   ├── app.py                  # [Entry] 程序入口，负责初始化 Application 和 MainWindow
│   ├── configs\                # [Config] 配置文件 (models.yaml, xanylabeling_config.yaml)
│   ├── services\               # [Service] 后台服务
│   │   └── auto_labeling\      # AI 自动标注模型推理服务
│   ├── views\                  # [View/Controller] UI 视图与逻辑
│   │   ├── mainwindow.py       # 主窗口框架
│   │   └── labeling\           # 核心标注业务逻辑
│   │       ├── label_widget.py # [Core] "God Class"，核心控制器，管理所有标注逻辑
│   │       ├── label_file.py   # [Model] 数据持久化 (IO)，处理各种格式的读写
│   │       ├── shape.py        # [Model] 图形对象 (点、线、多边形)
│   │       └── widgets\
│   │           └── canvas.py   # [View] 画布组件，处理绘制交互
├── tools\                      # 独立工具脚本 (转换器, 导出器)
└── assets\                     # 静态资源 (图标, 预设标签等)
```

---

## 3. 核心架构组件 (Core Architectural Components)

项目采用典型的 **View-Controller** 混合模式，其中 `LabelingWidget` 承担了大部分 Controller 的职责。

### 3.1 程序入口与主窗口
- **`anylabeling/app.py`**:
    - 负责解析命令行参数。
    - 初始化 `QApplication`。
    - 启动 `MainWindow`。
- **`anylabeling/views/mainwindow.py`**:
    - 应用的顶层容器。
    - 包含菜单栏、工具栏。
    - **关键**: 它加载并持有一个 `LabelingWidget` 实例，将大部分业务逻辑委托给它。

### 3.2 核心控制器: `LabelingWidget` (最重要的类)
- **位置**: `anylabeling/views/labeling/label_widget.py`
- **职责**:
    - **状态管理**: 当前图片、当前工具、标签列表、脏状态 (Dirty State)。
    - **UI 协调**: 协调右侧标签列表、文件列表、工具栏按钮与 Canvas 的交互。
    - **文件操作**: 调用 `LabelFile` 加载/保存数据。
    - **AI 集成**: 触发 `AutoLabeling` 服务并接收结果。
- **注意**: 这是一个 "God Class" (6000+ 行)，后续大部分功能修改都会涉及此文件。

### 3.3 绘图引擎: `Canvas`
- **位置**: `anylabeling/views/labeling/widgets/canvas.py`
- **职责**:
    - 渲染图片 (QPixmap)。
    - 渲染形状 (`Shape` 对象列表)。
    - **交互处理**: 捕获鼠标点击、移动事件，实现绘制逻辑（如多边形打点、矩形拖拽）。
    - 提供坐标转换 (Image Coordinates <-> Screen Coordinates)。

### 3.4 数据模型: `Shape`
- **位置**: `anylabeling/views/labeling/shape.py`
- **职责**:
    - 存储单个标注对象的几何信息 (Points)。
    - 存储属性 (Label, Group ID, Direction, Flags)。
    - 提供绘图路径 (`QPainterPath`)。

---

## 4. 数据流与逻辑流程 (Data Flow & Logic)

### 4.1 图像加载流程
1. 用户点击文件列表 -> `LabelingWidget.file_selection_changed()`
2. `LabelingWidget.load_file(filename)` 被调用。
3. 读取图像数据 -> `Canvas.loadPixmap()`。
4. **关键**: 调用 `LabelingWidget.load_labels(shape_file)` 尝试加载对应的标注文件。

### 4.2 标注保存流程
1. 用户点击保存 (Ctrl+S) -> `LabelingWidget.save_file()`。
2. 收集 `Canvas.shapes` 中的所有 `Shape` 对象。
3. 创建 `LabelFile` 实例。
4. 根据配置 (`configs/xanylabeling_config.yaml` 或当前模式) 决定保存格式：
    - **JSON**: 标准 AnyLabeling 格式。
    - **VM XML**: VisionMaster 分割格式 (调用 `LabelFile.save_vm_xml`)。
    - **VM TXT**: VisionMaster 检测格式 (调用 `LabelFile.save_detect_data`)。

### 4.3 自动标注流程 (Auto-Labeling)
1. 用户点击 "Run AI" -> `LabelingWidget.run_auto_labeling()`。
2. 图像数据发送给 `AutoLabeling` 服务。
3. 模型推理 (YOLO, SAM, etc.)。
4. 返回 `shapes` 列表。
5. `LabelingWidget` 将这些 `shapes` 加载到 `Canvas` 中。

---

## 5. 最近新增功能上下文 (Recent Features Context)

### 5.1 VisionMaster (VM) 格式支持
- **模式切换**: 在 `LabelingWidget` 中维护了 `annotation_mode` 状态。
- **分割模式 (XML)**:
    - 逻辑位于 `LabelFile.save_vm_xml` 和 `load_vm_xml`。
    - 特殊处理: `[OK]` (空XML), `[Ignore]` (Flags)。
- **检测模式 (TXT)**:
    - 逻辑位于 `LabelFile.save_detect_data`。
    - **特点**: 单个 `DetectTrainData.txt` 文件存储文件夹下所有图片的标注。需要在加载文件夹时预读取。

### 5.2 批量删除 (Batch Delete)
- **位置**: `LabelingWidget.delete_selected_images()`。
- **逻辑**:
    - 获取文件列表中的选中项。
    - 物理删除图片文件。
    - 物理删除对应的标注文件 (JSON/XML)。
    - 从内存列表和 UI 中移除。
    - 自动更新 `DetectTrainData.txt` (如果处于检测模式)。

---

## 6. 开发指南与扩展点 (Extension Guidelines)

### 6.1 添加新工具 (New Tool)
1. **Canvas**: 在 `canvas.py` 中处理新的鼠标交互逻辑（如画圆、画样条曲线）。
2. **Action**: 在 `label_widget.py` 中添加对应的 `QAction` 和图标。
3. **Mode**: 在 `canvas.py` 的 `createMode` / `editMode` 中处理新工具的状态。

### 6.2 添加新导出格式 (New Export Format)
1. **LabelFile**: 在 `anylabeling/views/labeling/label_file.py` 中添加 `save_xxx_format` 方法。
2. **LabelConverter**: 如果需要独立转换，修改 `tools/label_converter.py`。
3. **UI 入口**: 在 `label_widget.py` 的导出菜单中注册新格式。

### 6.3 性能注意事项
- **LabelWidget**: 避免在 `paintEvent` 或高频循环中执行耗时操作。
- **大图处理**: Canvas 已经做了缩放优化，但加载极大分辨率图片时仍需注意内存。

---

## 7. 常用开发命令

- **运行应用**: `python anylabeling/app.py`
- **生成翻译**: `python scripts/generate_languages.py`
- **构建可执行文件**: `bash scripts/build_executable.sh` (或 Windows 对应脚本)

---
**备注**: 此文档应随着架构变更定期更新。
