# VisionMaster 转换快速入门

## 🎯 5分钟快速上手

### 步骤 1: 准备文件

确保你有：
- ✅ VisionMaster XML 标注文件
- ✅ 对应的图像文件（BMP/JPG/PNG）

### 步骤 2: 单文件转换

创建一个 Python 脚本 `convert.py`:

```python
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# 导入 VisionMaster 标注
converter.visionmaster_to_custom(
    input_file="你的标注.xml",
    output_file="输出标注.json",
    image_file="对应图像.bmp"
)

print("转换完成！")
```

运行：
```bash
python convert.py
```

### 步骤 3: 批量转换

使用提供的批量转换工具：

```bash
# 将整个文件夹的 VisionMaster 标注转换为 X-AnyLabeling 格式
python batch_convert_visionmaster.py import \
    --xml-dir "VisionMaster标注文件夹" \
    --image-dir "图像文件夹" \
    --output-dir "输出文件夹"
```

## 📁 典型的项目结构

### 转换前（VisionMaster 项目）
```
VisionMaster_Project/
├── annotations/
│   ├── image_001.xml
│   ├── image_002.xml
│   └── image_003.xml
└── images/
    ├── image_001.bmp
    ├── image_002.bmp
    └── image_003.bmp
```

### 转换命令
```bash
python batch_convert_visionmaster.py import \
    --xml-dir VisionMaster_Project/annotations \
    --image-dir VisionMaster_Project/images \
    --output-dir XAnyLabeling_Project/annotations
```

### 转换后（X-AnyLabeling 项目）
```
XAnyLabeling_Project/
└── annotations/
    ├── image_001.json
    ├── image_002.json
    └── image_003.json
```

## 🔄 双向转换示例

### 完整工作流

```python
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# 1. 从 VisionMaster 导入
print("导入 VisionMaster 标注...")
converter.visionmaster_to_custom(
    input_file="defect_001.xml",
    output_file="defect_001.json",
    image_file="defect_001.bmp"
)

# 2. 在 X-AnyLabeling 中编辑标注
print("现在可以在 X-AnyLabeling 中打开 defect_001.json 进行编辑")

# 3. 编辑完成后，导出回 VisionMaster 格式
print("导出为 VisionMaster 格式...")
converter.custom_to_visionmaster(
    input_file="defect_001.json",
    output_file="defect_001_edited.xml"
)

print("完成！")
```

## 🚀 实际应用场景

### 场景 1: 团队迁移到 X-AnyLabeling

```python
"""完整迁移 VisionMaster 项目"""
import os
import shutil
from anylabeling.views.labeling.label_converter import LabelConverter

def migrate_project(vm_dir, xa_dir):
    converter = LabelConverter()

    os.makedirs(f"{xa_dir}/annotations", exist_ok=True)
    os.makedirs(f"{xa_dir}/images", exist_ok=True)

    for xml_file in os.listdir(f"{vm_dir}/annotations"):
        if not xml_file.endswith('.xml'):
            continue

        base = os.path.splitext(xml_file)[0]

        # 查找图像
        for ext in ['.bmp', '.jpg', '.png']:
            src_img = f"{vm_dir}/images/{base}{ext}"
            if os.path.exists(src_img):
                # 复制图像
                shutil.copy(src_img, f"{xa_dir}/images/")

                # 转换标注
                converter.visionmaster_to_custom(
                    f"{vm_dir}/annotations/{xml_file}",
                    f"{xa_dir}/annotations/{base}.json",
                    src_img
                )
                print(f"✓ {base}")
                break

# 执行迁移
migrate_project("D:/VisionMaster_Data", "D:/XAnyLabeling_Data")
```

### 场景 2: 临时使用 X-AnyLabeling，最后导出回 VisionMaster

```python
"""使用 X-AnyLabeling 的高级功能，然后导出回 VisionMaster"""
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()

# 1. 导入所有 VisionMaster 标注
import os
for xml_file in os.listdir("vm_annotations"):
    base = os.path.splitext(xml_file)[0]
    converter.visionmaster_to_custom(
        f"vm_annotations/{xml_file}",
        f"temp_json/{base}.json",
        f"images/{base}.bmp"
    )

# 2. 在 X-AnyLabeling 中使用 AI 模型辅助标注
print("现在可以使用 X-AnyLabeling 的 AI 功能了...")

# 3. 完成后批量导出回 VisionMaster
for json_file in os.listdir("temp_json"):
    base = os.path.splitext(json_file)[0]
    converter.custom_to_visionmaster(
        f"temp_json/{json_file}",
        f"vm_output/{base}.xml"
    )
```

### 场景 3: 数据清洗和过滤

```python
"""只保留特定类别的标注"""
import json
from anylabeling.views.labeling.label_converter import LabelConverter

converter = LabelConverter()
target_labels = ['划痕', '裂纹']  # 只保留这些类别

for xml_file in os.listdir("vm_input"):
    base = os.path.splitext(xml_file)[0]

    # 转换
    temp_json = f"temp/{base}.json"
    converter.visionmaster_to_custom(
        f"vm_input/{xml_file}",
        temp_json,
        f"images/{base}.bmp"
    )

    # 过滤
    with open(temp_json, 'r', encoding='utf-8') as f:
        data = json.load(f)

    data['shapes'] = [
        s for s in data['shapes']
        if s['label'] in target_labels
    ]

    # 保存
    if data['shapes']:  # 只保存有标注的
        with open(temp_json, 'w', encoding='utf-8') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)

        # 导出回 VisionMaster
        converter.custom_to_visionmaster(
            temp_json,
            f"vm_filtered/{base}.xml"
        )
```

## ⚡ 常用命令速查表

| 操作 | 命令 |
|------|------|
| 测试功能 | `python test_visionmaster_simple.py` |
| 批量导入 | `python batch_convert_visionmaster.py import --xml-dir <xml目录> --image-dir <图像目录> --output-dir <输出目录>` |
| 批量导出 | `python batch_convert_visionmaster.py export --json-dir <json目录> --output-dir <输出目录>` |
| 单文件转换 | 见上面的 Python 代码示例 |

## 🐛 常见问题

### 问题 1: 找不到图像文件
```
错误: Image file not found
```

**解决**: 确保图像文件和 XML 文件的文件名（不含扩展名）完全一致

### 问题 2: 编码错误
```
错误: UnicodeDecodeError
```

**解决**: 确保 XML 文件是 UTF-8 编码

### 问题 3: 标注丢失
```
转换后没有标注
```

**检查**:
1. XML 中是否有 `<_ItemsData>` 节点
2. 多边形点数是否 ≥ 3
3. 运行测试脚本诊断

## 📚 更多资源

- 详细使用说明: `VISIONMASTER_USAGE.md`
- 代码示例: `VISIONMASTER_EXAMPLES.md`
- 完整功能说明: `VISIONMASTER_README.md`

## ✅ 验证转换结果

转换完成后，可以：
1. 用 X-AnyLabeling 打开 JSON 文件检查标注
2. 对比原始 XML 和转换后的 XML
3. 运行测试脚本验证

```bash
python test_visionmaster_simple.py
```

---

**需要帮助?** 检查文档或运行测试脚本进行诊断！
