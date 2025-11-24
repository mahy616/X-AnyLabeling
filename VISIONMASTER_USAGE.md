# VisionMaster 格式转换使用说明

## 功能概述

X-AnyLabeling 现已支持 VisionMaster 标注格式的双向转换：
- ✅ **导入**：VisionMaster XML → X-AnyLabeling JSON
- ✅ **导出**：X-AnyLabeling JSON → VisionMaster XML

## 快速开始

### 方法一：使用 Python API

```python
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# 1. 导入 VisionMaster 格式
converter.visionmaster_to_custom(
    input_file="annotation.xml",      # VisionMaster XML 文件
    output_file="annotation.json",    # 输出的 JSON 文件
    image_file="image.bmp"            # 对应的图像文件
)

# 2. 导出为 VisionMaster 格式
converter.custom_to_visionmaster(
    input_file="annotation.json",     # X-AnyLabeling JSON 文件
    output_file="annotation.xml"      # 输出的 VisionMaster XML 文件
)
```

### 方法二：批量转换脚本

```python
import os
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# 批量导入 VisionMaster 标注
xml_dir = "visionmaster_annotations"
json_dir = "xanylabeling_annotations"
image_dir = "images"

os.makedirs(json_dir, exist_ok=True)

for xml_file in os.listdir(xml_dir):
    if not xml_file.endswith('.xml'):
        continue

    base_name = os.path.splitext(xml_file)[0]

    # 查找对应的图像文件
    for ext in ['.bmp', '.jpg', '.png']:
        image_file = os.path.join(image_dir, base_name + ext)
        if os.path.exists(image_file):
            break
    else:
        print(f"图像文件未找到: {base_name}")
        continue

    # 执行转换
    converter.visionmaster_to_custom(
        input_file=os.path.join(xml_dir, xml_file),
        output_file=os.path.join(json_dir, base_name + '.json'),
        image_file=image_file
    )
    print(f"已转换: {xml_file}")
```

## VisionMaster 格式说明

### XML 结构
```xml
<?xml version="1.0" encoding="utf-8"?>
<VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawTrainData>
    <_ItemsData>
        <VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter>
            <_LevelNum>2</_LevelNum>
            <flags>标签名称</flags>
            <_ColorValue>1</_ColorValue>
            <_BackgroundColor>#FFFF00</_BackgroundColor>
            <_PolygonPoints>
                <HikPcUI.ImageView.PolygonPoint>
                    <x>100.5</x>
                    <y>200.3</y>
                </HikPcUI.ImageView.PolygonPoint>
                <!-- 更多点... -->
            </_PolygonPoints>
            <_Sign>True</_Sign>
            <_TIsVisible>True</_TIsVisible>
        </VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter>
    </_ItemsData>
    <_IsOKCalibrated>False</_IsOKCalibrated>
    <_ImagePath>D:\images\image.bmp</_ImagePath>
</VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawTrainData>
```

### 字段映射

| VisionMaster | X-AnyLabeling | 说明 |
|-------------|---------------|------|
| `<flags>` | `label` | 标签名称 |
| `<_PolygonPoints>` | `points` | 多边形坐标点 |
| `<_TIsVisible>` | `flags.hidden` | 可见性（反向映射） |
| `<_ImagePath>` | `imagePath` | 图像路径 |

## 支持的标注类型

- ✅ **多边形（Polygon）**：完全支持
- ⚠️ **矩形/旋转框**：将自动转换为多边形
- ❌ **关键点**：不支持（VisionMaster 不使用此类型）

## 注意事项

1. **图像尺寸**
   - VisionMaster XML 不包含图像尺寸信息
   - 导入时必须提供对应的图像文件
   - 图像尺寸将从图像文件自动读取

2. **坐标系统**
   - 使用像素绝对坐标（非归一化）
   - 原点位于图像左上角

3. **默认值**
   - `_LevelNum`: 固定为 `2`
   - `_ColorValue`: 固定为 `1`
   - `_BackgroundColor`: 固定为 `#FFFF00`
   - `_Sign`: 固定为 `True`
   - `_IsOKCalibrated`: 固定为 `False`

4. **特殊处理**
   - 坐标点会自动限制在图像边界内
   - 少于3个点的多边形会被跳过
   - 非多边形标注类型会被忽略

## 测试

运行测试脚本验证功能：

```bash
cd D:\github\X-AnyLabeling
python test_visionmaster_simple.py
```

## 常见问题

### Q: 导入时提示找不到图像文件？
A: 确保图像文件与 XML 文件在同一目录，或者提供正确的图像路径。

### Q: 转换后的标注位置不对？
A: 检查图像尺寸是否正确，VisionMaster 使用绝对坐标。

### Q: 可以批量转换吗？
A: 可以，参考上面的批量转换脚本。

### Q: 支持其他标注类型吗？
A: 目前只支持多边形，矩形会被转换为4点多边形。

## 版本信息

- 添加日期: 2025-01-21
- 最低版本: X-AnyLabeling v3.3.0+
- 测试状态: ✅ 通过
