# VisionMaster 功能 - Bug 修复记录

## ❌ 问题描述

**错误信息**:
```
AttributeError: module 'anylabeling.views.labeling.utils' has no attribute 'upload_visionmaster_annotation'
```

**症状**: 点击 GUI 的 "Upload VisionMaster Annotations" 按钮时应用闪退

---

## ✅ 原因分析

在 `upload.py` 中添加了 `upload_visionmaster_annotation()` 函数，但忘记在 `utils/__init__.py` 中导出该函数。

Python 模块需要在 `__init__.py` 中显式导出函数才能被外部访问。

---

## 🔧 修复方法

### 修改文件: `anylabeling/views/labeling/utils/__init__.py`

在第 72 行添加导入：

```python
from .upload import (
    upload_image_flags_file,
    upload_label_flags_file,
    upload_shape_attrs_file,
    upload_label_classes_file,
    upload_yolo_annotation,
    upload_voc_annotation,
    upload_coco_annotation,
    upload_dota_annotation,
    upload_mask_annotation,
    upload_mot_annotation,
    upload_odvg_annotation,
    upload_mmgd_annotation,
    upload_ppocr_annotation,
    upload_vlm_r1_ovd_annotation,
    upload_visionmaster_annotation,  # ← 添加这一行
)
```

---

## ✅ 验证修复

### 1. 重启应用

```bash
cd D:\github\X-AnyLabeling
python anylabeling_app.py
```

### 2. 测试上传功能

1. File → Open Dir → 选择图像文件夹
2. File → Upload → Upload VisionMaster Annotations
3. 选择 VisionMaster XML 文件夹
4. 确认上传

**预期结果**:
- ✅ 不再闪退
- ✅ 显示上传进度对话框
- ✅ 成功导入标注并显示在画布上

---

## 📝 修改文件清单

| 文件 | 修改 | 状态 |
|------|------|------|
| `anylabeling/views/labeling/utils/__init__.py` | 添加 1 行导入 | ✅ 已修复 |

---

## 🎉 修复完成

问题已解决！现在可以正常使用 GUI 上传 VisionMaster 标注了。

---

**修复日期**: 2025-01-21
**状态**: ✅ 已解决
