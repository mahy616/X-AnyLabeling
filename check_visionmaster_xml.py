"""Diagnostic tool to check VisionMaster XML files."""
import os
import os.path as osp
import xml.etree.ElementTree as ET
import sys

# Fix Windows console encoding
if sys.platform == 'win32':
    import codecs
    sys.stdout = codecs.getwriter('utf-8')(sys.stdout.buffer, 'strict')
    sys.stderr = codecs.getwriter('utf-8')(sys.stderr.buffer, 'strict')


def check_xml_file(xml_file):
    """Check if XML file is valid VisionMaster format."""
    print(f"\n{'='*60}")
    print(f"Checking: {xml_file}")
    print('='*60)

    # Check file exists
    if not osp.exists(xml_file):
        print("❌ File not found!")
        return False

    # Check file size
    size = osp.getsize(xml_file)
    print(f"File size: {size} bytes")
    if size == 0:
        print("❌ File is empty!")
        return False

    # Try to parse XML
    try:
        tree = ET.parse(xml_file)
        root = tree.getroot()
        print(f"✅ Valid XML file")
        print(f"Root tag: {root.tag}")
    except ET.ParseError as e:
        print(f"❌ Invalid XML format: {e}")
        print("\nFirst 500 characters of file:")
        with open(xml_file, 'r', encoding='utf-8', errors='ignore') as f:
            print(f.read(500))
        return False

    # Check if it's VisionMaster format
    expected_root = "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawTrainData"
    if root.tag != expected_root:
        print(f"⚠️  Warning: Root tag is not VisionMaster format")
        print(f"   Expected: {expected_root}")
        print(f"   Got: {root.tag}")
        return False

    # Check structure
    items_data = root.find("_ItemsData")
    if items_data is None:
        print("⚠️  Warning: No _ItemsData found")
        annotation_count = 0
    else:
        params = items_data.findall(
            "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter"
        )
        annotation_count = len(params)
        print(f"✅ Found {annotation_count} annotations")

        # Check first annotation
        if annotation_count > 0:
            param = params[0]
            flags = param.find("flags")
            points = param.find("_PolygonPoints")

            if flags is not None:
                print(f"   Label: {flags.text}")

            if points is not None:
                point_count = len(points.findall("HikPcUI.ImageView.PolygonPoint"))
                print(f"   Points: {point_count}")

    # Check image path
    image_path = root.find("_ImagePath")
    if image_path is not None:
        print(f"Image path: {image_path.text}")

    print("✅ File is valid VisionMaster XML format")
    return True


def check_directory(directory):
    """Check all XML files in directory."""
    print(f"\n{'='*60}")
    print(f"Checking directory: {directory}")
    print('='*60)

    if not osp.exists(directory):
        print("❌ Directory not found!")
        return

    xml_files = [f for f in os.listdir(directory) if f.endswith('.xml')]

    if not xml_files:
        print("❌ No XML files found in directory!")
        return

    print(f"Found {len(xml_files)} XML files\n")

    valid_count = 0
    for xml_file in xml_files:
        full_path = osp.join(directory, xml_file)
        if check_xml_file(full_path):
            valid_count += 1

    print(f"\n{'='*60}")
    print(f"Summary: {valid_count}/{len(xml_files)} valid files")
    print('='*60)


def main():
    if len(sys.argv) < 2:
        print("Usage:")
        print("  python check_visionmaster_xml.py <xml_file_or_directory>")
        print("\nExamples:")
        print("  python check_visionmaster_xml.py file/020250326103150729.xml")
        print("  python check_visionmaster_xml.py file/")
        return

    path = sys.argv[1]

    if osp.isfile(path):
        check_xml_file(path)
    elif osp.isdir(path):
        check_directory(path)
    else:
        print(f"❌ Path not found: {path}")


if __name__ == "__main__":
    main()
