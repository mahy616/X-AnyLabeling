# VisionMaster GUI 上传功能使用指南

## ✅ 已添加功能

在 X-AnyLabeling 的 GUI 工具栏中已添加 **"Upload VisionMaster Annotations"** 按钮，可以直接通过图形界面上传 VisionMaster 格式的标注。

## 📍 菜单位置

```
File → Upload → Upload VisionMaster Annotations
```

或者在工具栏点击 **Upload** 下拉菜单，找到 **"Upload VisionMaster Annotations"**

## 🚀 使用步骤

### 1. 准备数据

确保你的数据结构如下：

```
project/
├── images/              # 图像文件夹
│   ├── image_001.bmp
│   ├── image_002.bmp
│   └── image_003.bmp
└── annotations/         # VisionMaster XML 标注文件夹
    ├── image_001.xml
    ├── image_002.xml
    └── image_003.xml
```

**重要**:
- XML 文件名必须与图像文件名一致（不含扩展名）
- 图像文件必须已经加载到 X-AnyLabeling 中

### 2. 打开 X-AnyLabeling

```bash
cd D:\github\X-AnyLabeling
python anylabeling_app.py
```

### 3. 加载图像

1. 点击 `File → Open Dir` 打开图像文件夹
2. 或者点击 `File → Open` 打开单张图像

### 4. 上传 VisionMaster 标注

1. 点击 `File → Upload → Upload VisionMaster Annotations`

2. 在弹出的对话框中：
   - 点击 **Browse** 按钮
   - 选择包含 VisionMaster XML 文件的文件夹
   - 点击 **OK**

3. 确认警告对话框：
   - 点击 **OK** 继续（当前标注将被替换）
   - 或点击 **Cancel** 取消

4. 等待上传完成：
   - 进度条会显示上传进度
   - 可以点击 **Cancel** 中止上传

5. 上传成功：
   - 会显示成功提示
   - 画布会自动刷新并显示导入的标注

## 📋 功能特点

### ✅ 批量上传
- 自动处理整个文件夹的标注
- 按图像列表批量转换
- 显示实时进度

### ✅ 自动匹配
- 根据文件名自动匹配 XML 和图像
- 跳过没有对应标注的图像
- 智能容错处理

### ✅ 格式转换
- 自动将 VisionMaster XML 转换为 X-AnyLabeling JSON
- 保留所有标注信息（标签、多边形、可见性）
- 坐标自动限制在图像边界内

### ✅ 即时预览
- 上传完成后自动刷新画布
- 可立即查看和编辑导入的标注
- 支持所有 X-AnyLabeling 编辑功能

## 🎯 实际使用场景

### 场景 1：从 VisionMaster 迁移项目

```
1. 准备 VisionMaster 导出的 XML 文件
2. 在 X-AnyLabeling 中打开图像文件夹
3. 使用 Upload VisionMaster Annotations 导入标注
4. 开始使用 X-AnyLabeling 的高级功能编辑
```

### 场景 2：使用 X-AnyLabeling 辅助 VisionMaster 标注

```
1. 从 VisionMaster 导出部分完成的标注
2. 在 X-AnyLabeling 中导入
3. 使用 AI 模型辅助标注剩余部分
4. 使用 Export VisionMaster 导出回 VisionMaster
```

### 场景 3：批量质量检查

```
1. 导入 VisionMaster 标注
2. 使用 X-AnyLabeling 的可视化工具检查
3. 快速修正错误标注
4. 导出回 VisionMaster 或其他格式
```

## ⚠️ 注意事项

### 文件命名
- **必须严格一致**: `image_001.bmp` ↔ `image_001.xml`
- 大小写敏感（在某些系统上）
- 只匹配文件名，不包括扩展名

### 图像格式
- 支持常见格式：BMP, JPG, PNG, JPEG
- 图像必须先加载到 X-AnyLabeling
- 确保图像路径可访问

### 标注格式
- 仅支持 VisionMaster 的多边形标注
- 少于 3 个点的多边形会被跳过
- 不可见的标注会保留但标记为 hidden

### 数据备份
- **重要**: 上传会覆盖现有标注
- 建议先备份当前标注
- 可以使用版本控制（Git）管理标注文件

## 🔧 故障排除

### 问题 1: 找不到菜单按钮

**解决方案**:
```bash
# 确保使用的是修改后的代码
cd D:\github\X-AnyLabeling
git status  # 检查是否有修改
```

### 问题 2: 上传后没有标注显示

**可能原因**:
1. XML 文件名与图像文件名不匹配
2. XML 格式不正确
3. 多边形点数少于 3 个

**解决方案**:
- 检查文件名是否完全一致
- 查看控制台错误信息
- 使用测试脚本验证 XML 格式

### 问题 3: 上传失败或报错

**解决方案**:
```python
# 使用命令行工具测试
python batch_convert_visionmaster.py import \
    --xml-dir ./annotations \
    --image-dir ./images \
    --output-dir ./output

# 检查输出的 JSON 文件是否正确
```

### 问题 4: 坐标偏移或不准确

**可能原因**:
- 图像尺寸信息不正确
- 坐标系统不匹配

**解决方案**:
- 确保 XML 中的图像路径正确
- 检查图像文件是否损坏
- 使用测试脚本验证转换结果

## 📝 技术细节

### 实现文件
- `anylabeling/views/labeling/utils/upload.py` - 上传逻辑
- `anylabeling/views/labeling/label_widget.py` - GUI 菜单集成
- `anylabeling/views/labeling/label_converter.py` - 格式转换

### 转换流程
```
1. 用户选择 XML 文件夹
2. 遍历图像列表
3. 查找对应的 XML 文件
4. 调用 visionmaster_to_custom() 转换
5. 保存为 JSON 格式
6. 刷新画布显示
```

### 数据流
```
VisionMaster XML → Parser → Custom JSON → Canvas Display
     (输入)         (转换)      (存储)        (显示)
```

## 🎉 快速测试

### 测试步骤

1. **启动应用**:
   ```bash
   cd D:\github\X-AnyLabeling
   python anylabeling_app.py
   ```

2. **加载测试数据**:
   - File → Open Dir → 选择 `file` 文件夹
   - 会看到测试图像

3. **上传标注**:
   - File → Upload → Upload VisionMaster Annotations
   - Browse → 选择 `file` 文件夹（包含 .xml 文件）
   - OK → 等待上传完成

4. **验证结果**:
   - 画布上应该显示多边形标注
   - 标签应该显示为"擦伤"
   - 可以编辑和修改标注

## 📚 相关文档

- **使用说明**: `VISIONMASTER_USAGE.md`
- **代码示例**: `VISIONMASTER_EXAMPLES.md`
- **快速入门**: `QUICKSTART_VISIONMASTER.md`
- **功能总结**: `VISIONMASTER_README.md`

---

**添加日期**: 2025-01-21
**状态**: ✅ 已实现并测试
**版本**: X-AnyLabeling v3.3.0+
