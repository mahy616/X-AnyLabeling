# VisionMaster 转换示例

## 示例 1：单文件转换

### 导入单个 VisionMaster 文件

```python
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# VisionMaster -> X-AnyLabeling
converter.visionmaster_to_custom(
    input_file="D:/annotations/defect_001.xml",
    output_file="D:/converted/defect_001.json",
    image_file="D:/images/defect_001.bmp"
)
```

### 导出为 VisionMaster 格式

```python
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# X-AnyLabeling -> VisionMaster
converter.custom_to_visionmaster(
    input_file="D:/converted/defect_001.json",
    output_file="D:/exported/defect_001.xml"
)
```

## 示例 2：批量转换

### 使用命令行工具

```bash
# 批量导入 VisionMaster 格式
python batch_convert_visionmaster.py import \
    --xml-dir "D:/visionmaster_annotations" \
    --image-dir "D:/images" \
    --output-dir "D:/xanylabeling_annotations"

# 批量导出为 VisionMaster 格式
python batch_convert_visionmaster.py export \
    --json-dir "D:/xanylabeling_annotations" \
    --output-dir "D:/visionmaster_output"
```

### 使用 Python 脚本

```python
import os
from anylabeling.views.labeling.label_converter import LabelConverter

def convert_all_visionmaster(xml_dir, image_dir, output_dir):
    """批量转换所有 VisionMaster 标注"""
    converter = LabelConverter()
    os.makedirs(output_dir, exist_ok=True)

    for xml_file in os.listdir(xml_dir):
        if not xml_file.endswith('.xml'):
            continue

        base_name = os.path.splitext(xml_file)[0]

        # 查找图像文件
        image_file = None
        for ext in ['.bmp', '.jpg', '.png']:
            img_path = os.path.join(image_dir, base_name + ext)
            if os.path.exists(img_path):
                image_file = img_path
                break

        if not image_file:
            print(f"图像未找到: {base_name}")
            continue

        # 转换
        try:
            converter.visionmaster_to_custom(
                input_file=os.path.join(xml_dir, xml_file),
                output_file=os.path.join(output_dir, base_name + '.json'),
                image_file=image_file
            )
            print(f"✓ {xml_file}")
        except Exception as e:
            print(f"✗ {xml_file}: {e}")

# 执行批量转换
convert_all_visionmaster(
    xml_dir="D:/visionmaster_data/annotations",
    image_dir="D:/visionmaster_data/images",
    output_dir="D:/xanylabeling_data/annotations"
)
```

## 示例 3：集成到工作流

### 从 VisionMaster 迁移到 X-AnyLabeling

```python
import os
import shutil
from anylabeling.views.labeling.label_converter import LabelConverter

def migrate_visionmaster_project(src_dir, dst_dir):
    """
    完整迁移 VisionMaster 项目到 X-AnyLabeling

    目录结构：
    src_dir/
      ├── annotations/  (XML files)
      └── images/       (BMP/JPG/PNG files)

    dst_dir/
      ├── annotations/  (JSON files)
      └── images/       (copied images)
    """
    converter = LabelConverter()

    src_xml_dir = os.path.join(src_dir, 'annotations')
    src_img_dir = os.path.join(src_dir, 'images')
    dst_json_dir = os.path.join(dst_dir, 'annotations')
    dst_img_dir = os.path.join(dst_dir, 'images')

    os.makedirs(dst_json_dir, exist_ok=True)
    os.makedirs(dst_img_dir, exist_ok=True)

    # 转换标注
    for xml_file in os.listdir(src_xml_dir):
        if not xml_file.endswith('.xml'):
            continue

        base_name = os.path.splitext(xml_file)[0]

        # 查找并复制图像
        for ext in ['.bmp', '.jpg', '.png', '.BMP', '.JPG', '.PNG']:
            src_img = os.path.join(src_img_dir, base_name + ext)
            if os.path.exists(src_img):
                dst_img = os.path.join(dst_img_dir, base_name + ext)
                shutil.copy2(src_img, dst_img)

                # 转换标注
                converter.visionmaster_to_custom(
                    input_file=os.path.join(src_xml_dir, xml_file),
                    output_file=os.path.join(dst_json_dir, base_name + '.json'),
                    image_file=dst_img
                )
                print(f"迁移完成: {base_name}")
                break

# 使用示例
migrate_visionmaster_project(
    src_dir="D:/VisionMaster_Projects/defect_detection",
    dst_dir="D:/XAnyLabeling_Projects/defect_detection"
)
```

### 从 X-AnyLabeling 导出供 VisionMaster 使用

```python
import os
from anylabeling.views.labeling.label_converter import LabelConverter

def export_for_visionmaster(json_dir, output_dir):
    """将 X-AnyLabeling 标注导出为 VisionMaster 格式"""
    converter = LabelConverter()
    os.makedirs(output_dir, exist_ok=True)

    success = 0
    failed = 0

    for json_file in os.listdir(json_dir):
        if not json_file.endswith('.json'):
            continue

        base_name = os.path.splitext(json_file)[0]

        try:
            converter.custom_to_visionmaster(
                input_file=os.path.join(json_dir, json_file),
                output_file=os.path.join(output_dir, base_name + '.xml')
            )
            success += 1
        except Exception as e:
            print(f"失败: {json_file} - {e}")
            failed += 1

    print(f"\n导出完成: {success} 成功, {failed} 失败")

# 使用示例
export_for_visionmaster(
    json_dir="D:/project/annotations",
    output_dir="D:/project/visionmaster_export"
)
```

## 示例 4：过滤和处理

### 只转换特定标签

```python
import os
import json
from anylabeling.views.labeling.label_converter import LabelConverter

def convert_specific_labels(xml_dir, image_dir, output_dir, target_labels):
    """只转换包含特定标签的标注"""
    converter = LabelConverter()
    os.makedirs(output_dir, exist_ok=True)

    for xml_file in os.listdir(xml_dir):
        if not xml_file.endswith('.xml'):
            continue

        base_name = os.path.splitext(xml_file)[0]

        # 查找图像
        image_file = None
        for ext in ['.bmp', '.jpg', '.png']:
            img_path = os.path.join(image_dir, base_name + ext)
            if os.path.exists(img_path):
                image_file = img_path
                break

        if not image_file:
            continue

        # 转换
        temp_output = os.path.join(output_dir, base_name + '_temp.json')
        converter.visionmaster_to_custom(
            input_file=os.path.join(xml_dir, xml_file),
            output_file=temp_output,
            image_file=image_file
        )

        # 过滤标签
        with open(temp_output, 'r', encoding='utf-8') as f:
            data = json.load(f)

        filtered_shapes = [
            shape for shape in data['shapes']
            if shape['label'] in target_labels
        ]

        if filtered_shapes:
            data['shapes'] = filtered_shapes
            final_output = os.path.join(output_dir, base_name + '.json')
            with open(final_output, 'w', encoding='utf-8') as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
            print(f"✓ {xml_file} ({len(filtered_shapes)} shapes)")

        os.remove(temp_output)

# 只转换"划痕"和"裂纹"标签
convert_specific_labels(
    xml_dir="D:/annotations",
    image_dir="D:/images",
    output_dir="D:/filtered_annotations",
    target_labels=['划痕', '裂纹']
)
```

## 常用命令速查

```bash
# 快速测试
python test_visionmaster_simple.py

# 批量导入
python batch_convert_visionmaster.py import \
    --xml-dir ./vm_annotations \
    --image-dir ./images \
    --output-dir ./xa_annotations

# 批量导出
python batch_convert_visionmaster.py export \
    --json-dir ./xa_annotations \
    --output-dir ./vm_export
```
