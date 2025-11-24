"""Test VisionMaster export functionality."""
import os
import os.path as osp
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')

sys.path.insert(0, osp.dirname(__file__))

from anylabeling.views.labeling.label_converter import LabelConverter


def test_export():
    """Test exporting Custom JSON to VisionMaster XML."""
    converter = LabelConverter()

    # Test file paths
    json_file = r"D:\github\X-AnyLabeling\file\020250326103150729.json"
    output_file = r"D:\github\X-AnyLabeling\file\test_export.xml"

    print("=" * 60)
    print("VisionMaster Export Test")
    print("=" * 60)

    if not osp.exists(json_file):
        print(f"❌ JSON file not found: {json_file}")
        print("Please ensure you have run the import test first.")
        return False

    print(f"Input JSON: {json_file}")
    print(f"Output XML: {output_file}")
    print()

    try:
        converter.custom_to_visionmaster(json_file, output_file)
        print("✅ Export successful!")

        # Check output file
        if osp.exists(output_file):
            size = osp.getsize(output_file)
            print(f"   Output file size: {size} bytes")

            # Show first few lines
            print("\nFirst 10 lines of output XML:")
            print("-" * 60)
            with open(output_file, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= 10:
                        break
                    print(f"   {line.rstrip()}")

            return True
        else:
            print("❌ Output file was not created!")
            return False

    except Exception as e:
        print(f"❌ Export failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = test_export()
    print()
    print("=" * 60)
    if success:
        print("✅ Test PASSED")
    else:
        print("❌ Test FAILED")
    print("=" * 60)
