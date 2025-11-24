# VisionMaster 格式 - 快速参考

## 🎯 一句话总结

X-AnyLabeling 现已完整支持 VisionMaster 格式，可通过 **GUI 按钮** 或 **Python API** 导入导出。

---

## 🚀 最快上手方式

### GUI 操作（3步完成）

```
1. File → Open Dir → 选择图像文件夹
2. File → Upload → Upload VisionMaster Annotations → 选择XML文件夹
3. 完成！标注已导入，可以直接编辑
```

---

## 📋 功能速查

| 功能 | GUI | API | 命令行 |
|------|-----|-----|--------|
| **导入 VM** | ✅ | ✅ | ✅ |
| **导出 VM** | ⚠️ | ✅ | ✅ |
| **批量处理** | ✅ | ✅ | ✅ |

⚠️ GUI 导出功能暂未添加，使用 API 或命令行工具

---

## 💡 三种使用方式

### 1️⃣ GUI 上传（最简单）

```
菜单: File → Upload → Upload VisionMaster Annotations
操作: 选择XML文件夹 → OK → 完成
```

### 2️⃣ Python API（最灵活）

```python
from anylabeling.views.labeling.label_converter import LabelConverter
converter = LabelConverter()

# 导入
converter.visionmaster_to_custom("input.xml", "output.json", "image.bmp")

# 导出
converter.custom_to_visionmaster("input.json", "output.xml")
```

### 3️⃣ 命令行（最快速）

```bash
# 批量导入
python batch_convert_visionmaster.py import \
    --xml-dir ./xml_folder \
    --image-dir ./images \
    --output-dir ./output

# 批量导出
python batch_convert_visionmaster.py export \
    --json-dir ./json_folder \
    --output-dir ./output
```

---

## 📝 文件对应关系

```
VisionMaster:  annotation.xml  (多边形XML格式)
               ↕️
X-AnyLabeling: annotation.json (标准JSON格式)
```

**重要**: 文件名必须与图像文件名一致（不含扩展名）

---

## 🔧 快速测试

```bash
cd D:\github\X-AnyLabeling
python test_visionmaster_simple.py
```

看到 ✅ 表示功能正常！

---

## 📚 详细文档

| 文档 | 用途 |
|------|------|
| `VISIONMASTER_GUI_GUIDE.md` | GUI 使用指南 ⭐ |
| `QUICKSTART_VISIONMASTER.md` | 5分钟快速入门 |
| `VISIONMASTER_USAGE.md` | API 详细说明 |
| `VISIONMASTER_EXAMPLES.md` | 代码示例集合 |
| `VISIONMASTER_README.md` | 功能总结 |
| `VISIONMASTER_IMPLEMENTATION_SUMMARY.md` | 实现总结 |

---

## ⚡ 常用命令

```bash
# 启动GUI
python anylabeling_app.py

# 测试转换
python test_visionmaster_simple.py

# 批量导入
python batch_convert_visionmaster.py import \
    --xml-dir ./xml --image-dir ./img --output-dir ./out

# 批量导出
python batch_convert_visionmaster.py export \
    --json-dir ./json --output-dir ./out
```

---

## 🎯 典型工作流

### 从 VisionMaster 迁移到 X-AnyLabeling

```
VisionMaster XML
    ↓
GUI Upload (或 batch_convert import)
    ↓
X-AnyLabeling 编辑
    ↓
使用 AI 功能增强标注
    ↓
Python API 导出 (可选)
    ↓
继续使用 X-AnyLabeling 或导出其他格式
```

### 临时使用 X-AnyLabeling

```
VisionMaster XML
    ↓
GUI Upload
    ↓
使用 X-AnyLabeling 的高级功能
    ↓
Python API 导出回 VisionMaster
    ↓
在 VisionMaster 中继续使用
```

---

## ✅ 支持的标注类型

| 类型 | 支持 | 说明 |
|------|------|------|
| 多边形 | ✅ | 完全支持 |
| 中文标签 | ✅ | 完全支持 |
| 可见性标记 | ✅ | 转换为 flags.hidden |
| 坐标精度 | ✅ | 零损失转换 |

---

## ⚠️ 注意事项

1. **文件命名**: XML 和图像文件名必须一致
2. **图像路径**: 导入时需要提供对应的图像文件
3. **数据备份**: GUI 上传会覆盖现有标注，建议先备份
4. **格式限制**: 仅支持多边形，少于3个点的会被跳过

---

## 🐛 故障排除

### 上传后没有显示标注？
- 检查文件名是否匹配
- 检查 XML 格式是否正确
- 查看控制台错误信息

### 坐标不准确？
- 确保图像文件正确
- 检查图像尺寸信息

### GUI 找不到按钮？
- 确保使用修改后的代码
- 重启应用程序

---

## 🎊 快速参考卡片

```
╔═══════════════════════════════════════════════════════╗
║        VisionMaster 格式 - 快速参考卡                 ║
╠═══════════════════════════════════════════════════════╣
║                                                       ║
║  📥 GUI 导入:                                         ║
║     File → Upload → Upload VisionMaster Annotations  ║
║                                                       ║
║  🐍 Python 导入:                                      ║
║     converter.visionmaster_to_custom(                ║
║         "input.xml", "output.json", "image.bmp")     ║
║                                                       ║
║  🐍 Python 导出:                                      ║
║     converter.custom_to_visionmaster(                ║
║         "input.json", "output.xml")                  ║
║                                                       ║
║  💻 批量导入:                                         ║
║     python batch_convert_visionmaster.py import \    ║
║         --xml-dir DIR --image-dir DIR --output-dir DIR║
║                                                       ║
║  🧪 测试:                                             ║
║     python test_visionmaster_simple.py               ║
║                                                       ║
╚═══════════════════════════════════════════════════════╝
```

---

**版本**: X-AnyLabeling v3.3.0+
**状态**: ✅ 生产就绪
**文档**: 查看 `VISIONMASTER_*.md` 系列文档
