"""Simple test for VisionMaster conversion - auto-detects image path."""
import os
import os.path as osp
import sys
from PIL import Image

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, osp.dirname(__file__))

from anylabeling.views.labeling.label_converter import LabelConverter


def find_or_create_image(xml_file):
    """Find the image file or create a dummy one for testing."""
    # Parse XML to get image path
    import xml.etree.ElementTree as ET
    tree = ET.parse(xml_file)
    root = tree.getroot()

    image_path_elem = root.find("_ImagePath")
    if image_path_elem is not None:
        original_path = image_path_elem.text
        print(f"Original image path in XML: {original_path}")

        if osp.exists(original_path):
            return original_path

    # Try to find image in same directory as XML
    xml_dir = osp.dirname(xml_file)
    xml_name = osp.splitext(osp.basename(xml_file))[0]

    for ext in ['.bmp', '.jpg', '.png', '.jpeg']:
        image_file = osp.join(xml_dir, xml_name + ext)
        if osp.exists(image_file):
            print(f"Found image: {image_file}")
            return image_file

    # Create a dummy image for testing
    print("Creating dummy image for testing...")
    image_file = osp.join(xml_dir, xml_name + '.bmp')
    dummy_img = Image.new('RGB', (2574, 1942), color='white')
    dummy_img.save(image_file)
    print(f"Created dummy image: {image_file}")
    return image_file


def main():
    print("\n" + "=" * 60)
    print("VisionMaster Format Converter Test")
    print("=" * 60 + "\n")

    converter = LabelConverter()

    # Test 1: VisionMaster → Custom JSON
    vm_file = r"D:\github\X-AnyLabeling\file\020250326103150729.xml"
    json_file = r"D:\github\X-AnyLabeling\file\020250326103150729.json"

    print(f"Input VisionMaster XML: {vm_file}")

    if not osp.exists(vm_file):
        print(f"❌ VisionMaster file not found: {vm_file}")
        return

    # Find or create image
    image_file = find_or_create_image(vm_file)

    print(f"\n[Test 1] VisionMaster → Custom JSON")
    print("-" * 60)
    try:
        converter.visionmaster_to_custom(vm_file, json_file, image_file)
        print(f"✅ SUCCESS: Created {json_file}")

        # Show result
        import json
        with open(json_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        print(f"   - Image: {data['imagePath']}")
        print(f"   - Size: {data['imageWidth']} x {data['imageHeight']}")
        print(f"   - Shapes: {len(data['shapes'])}")
        for i, shape in enumerate(data['shapes'], 1):
            print(f"     {i}. {shape['label']} ({shape['shape_type']}) - {len(shape['points'])} points")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    # Test 2: Custom JSON → VisionMaster
    output_vm_file = r"D:\github\X-AnyLabeling\file\020250326103150729_output.xml"

    print(f"\n[Test 2] Custom JSON → VisionMaster")
    print("-" * 60)
    try:
        converter.custom_to_visionmaster(json_file, output_vm_file)
        print(f"✅ SUCCESS: Created {output_vm_file}")

        # Compare file sizes
        original_size = osp.getsize(vm_file)
        output_size = osp.getsize(output_vm_file)
        print(f"   - Original: {original_size} bytes")
        print(f"   - Output: {output_size} bytes")
    except Exception as e:
        print(f"❌ FAILED: {e}")
        import traceback
        traceback.print_exc()
        return

    print("\n" + "=" * 60)
    print("✅ All tests completed successfully!")
    print("=" * 60)


if __name__ == "__main__":
    main()
