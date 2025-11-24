"""Test complete VisionMaster export with images and config files."""
import os
import os.path as osp
import sys
import shutil

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, osp.dirname(__file__))

from anylabeling.views.labeling.label_converter import LabelConverter


def test_full_export():
    """Test complete VisionMaster export."""
    print("=" * 60)
    print("VisionMaster Complete Export Test")
    print("=" * 60)

    # Setup paths
    test_dir = r"D:\github\X-AnyLabeling\file"
    output_dir = r"D:\github\X-AnyLabeling\file\visionmaster_test_output"

    # Clean output directory
    if osp.exists(output_dir):
        shutil.rmtree(output_dir)
    os.makedirs(output_dir)

    print(f"Input directory: {test_dir}")
    print(f"Output directory: {output_dir}")
    print()

    # Find test files
    json_file = osp.join(test_dir, "020250326103150729.json")
    image_file = osp.join(test_dir, "020250326103150729.bmp")

    if not osp.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        return False

    if not osp.exists(image_file):
        print(f"❌ Image file not found: {image_file}")
        return False

    try:
        converter = LabelConverter()

        # 1. Export XML
        xml_file = osp.join(output_dir, "020250326103150729.xml")
        converter.custom_to_visionmaster(json_file, xml_file)
        print("✅ Exported XML annotation")

        # 2. Copy image
        dst_image = osp.join(output_dir, "020250326103150729.bmp")
        shutil.copy2(image_file, dst_image)
        print("✅ Copied original image")

        # 3. Create label_color.txt
        import json
        all_labels = set()
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
            for shape in data.get('shapes', []):
                label = shape.get('label')
                if label:
                    all_labels.add(label)

        label_color_file = osp.join(output_dir, "label_color.txt")
        with open(label_color_file, 'w', encoding='utf-8') as f:
            for idx, label in enumerate(sorted(all_labels), start=1):
                f.write(f"{idx} {label}\n")
        print(f"✅ Created label_color.txt with {len(all_labels)} labels")

        # 4. Create mark.txt
        mark_file = osp.join(output_dir, "mark.txt")
        with open(mark_file, 'w', encoding='utf-8') as f:
            f.write("020250326103150729.bmp 020250326103150729.bmp\n")
        print("✅ Created mark.txt")

        # Verify output
        print("\n" + "-" * 60)
        print("Output directory contents:")
        print("-" * 60)
        for item in sorted(os.listdir(output_dir)):
            item_path = osp.join(output_dir, item)
            size = osp.getsize(item_path)
            print(f"  {item:30s} {size:>10,} bytes")

        # Show label_color.txt
        print("\n" + "-" * 60)
        print("label_color.txt:")
        print("-" * 60)
        with open(label_color_file, 'r', encoding='utf-8') as f:
            print(f.read())

        # Show mark.txt
        print("-" * 60)
        print("mark.txt:")
        print("-" * 60)
        with open(mark_file, 'r', encoding='utf-8') as f:
            print(f.read())

        return True

    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_full_export()
    print("=" * 60)
    if success:
        print("✅ Complete export test PASSED")
    else:
        print("❌ Complete export test FAILED")
    print("=" * 60)
