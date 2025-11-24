"""Test script for VisionMaster format conversion."""
import os
import os.path as osp
import sys

sys.path.insert(0, osp.dirname(__file__))

from anylabeling.views.labeling.label_converter import LabelConverter


def test_visionmaster_to_custom():
    """Test VisionMaster to Custom JSON conversion."""
    print("=" * 60)
    print("Testing VisionMaster → Custom JSON conversion...")
    print("=" * 60)

    converter = LabelConverter()

    # Input files
    vm_file = r"D:\github\X-AnyLabeling\file\020250326103150729.xml"
    image_file = r"D:\mhy\image_1200\020250326103150729.bmp"
    output_file = r"D:\github\X-AnyLabeling\file\020250326103150729.json"

    # Check if image exists
    if not osp.exists(image_file):
        print(f"⚠️  Image file not found: {image_file}")
        print("Please update the image path in the test script.")
        return False

    try:
        converter.visionmaster_to_custom(vm_file, output_file, image_file)
        print(f"✅ Conversion successful!")
        print(f"   Output: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_custom_to_visionmaster():
    """Test Custom JSON to VisionMaster conversion."""
    print("\n" + "=" * 60)
    print("Testing Custom JSON → VisionMaster conversion...")
    print("=" * 60)

    converter = LabelConverter()

    # Use the VOC format file for testing (convert it first)
    json_file = r"D:\github\X-AnyLabeling\file\020250326103150729.json"
    output_file = r"D:\github\X-AnyLabeling\file\020250326103150729_output.xml"

    if not osp.exists(json_file):
        print(f"⚠️  JSON file not found: {json_file}")
        print("Run visionmaster_to_custom test first.")
        return False

    try:
        converter.custom_to_visionmaster(json_file, output_file)
        print(f"✅ Conversion successful!")
        print(f"   Output: {output_file}")
        return True
    except Exception as e:
        print(f"❌ Conversion failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    print("\n🔧 VisionMaster Format Converter Test Suite\n")

    result1 = test_visionmaster_to_custom()
    result2 = test_custom_to_visionmaster()

    print("\n" + "=" * 60)
    print("Test Summary:")
    print("=" * 60)
    print(f"VisionMaster → Custom: {'✅ PASS' if result1 else '❌ FAIL'}")
    print(f"Custom → VisionMaster: {'✅ PASS' if result2 else '❌ FAIL'}")
    print("=" * 60)
