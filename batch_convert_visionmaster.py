"""Batch converter for VisionMaster format."""
import os
import os.path as osp
import sys
import argparse

sys.path.insert(0, osp.dirname(__file__))

from anylabeling.views.labeling.label_converter import LabelConverter


def batch_visionmaster_to_custom(xml_dir, image_dir, output_dir):
    """Batch convert VisionMaster XML to Custom JSON."""
    converter = LabelConverter()
    os.makedirs(output_dir, exist_ok=True)

    # Get all XML files
    xml_files = [f for f in os.listdir(xml_dir) if f.endswith('.xml')]

    if not xml_files:
        print(f"No XML files found in {xml_dir}")
        return

    print(f"Found {len(xml_files)} XML files")
    print("-" * 60)

    success_count = 0
    failed_count = 0

    for xml_file in xml_files:
        base_name = osp.splitext(xml_file)[0]
        xml_path = osp.join(xml_dir, xml_file)

        # Find corresponding image
        image_path = None
        for ext in ['.bmp', '.jpg', '.png', '.jpeg', '.BMP', '.JPG', '.PNG']:
            img_file = osp.join(image_dir, base_name + ext)
            if osp.exists(img_file):
                image_path = img_file
                break

        if not image_path:
            print(f"[SKIP] {xml_file} - Image not found")
            failed_count += 1
            continue

        # Convert
        output_path = osp.join(output_dir, base_name + '.json')
        try:
            converter.visionmaster_to_custom(xml_path, output_path, image_path)
            print(f"[OK] {xml_file} -> {base_name}.json")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {xml_file} - {e}")
            failed_count += 1

    print("-" * 60)
    print(f"Completed: {success_count} success, {failed_count} failed")


def batch_custom_to_visionmaster(json_dir, output_dir):
    """Batch convert Custom JSON to VisionMaster XML."""
    converter = LabelConverter()
    os.makedirs(output_dir, exist_ok=True)

    # Get all JSON files
    json_files = [f for f in os.listdir(json_dir) if f.endswith('.json')]

    if not json_files:
        print(f"No JSON files found in {json_dir}")
        return

    print(f"Found {len(json_files)} JSON files")
    print("-" * 60)

    success_count = 0
    failed_count = 0

    for json_file in json_files:
        base_name = osp.splitext(json_file)[0]
        json_path = osp.join(json_dir, json_file)
        output_path = osp.join(output_dir, base_name + '.xml')

        try:
            converter.custom_to_visionmaster(json_path, output_path)
            print(f"[OK] {json_file} -> {base_name}.xml")
            success_count += 1
        except Exception as e:
            print(f"[FAIL] {json_file} - {e}")
            failed_count += 1

    print("-" * 60)
    print(f"Completed: {success_count} success, {failed_count} failed")


def main():
    parser = argparse.ArgumentParser(
        description="Batch converter for VisionMaster format"
    )
    parser.add_argument(
        'mode',
        choices=['import', 'export'],
        help='Conversion mode: import (VM->Custom) or export (Custom->VM)'
    )
    parser.add_argument(
        '--xml-dir',
        help='Directory containing VisionMaster XML files (for import)'
    )
    parser.add_argument(
        '--image-dir',
        help='Directory containing image files (for import)'
    )
    parser.add_argument(
        '--json-dir',
        help='Directory containing Custom JSON files (for export)'
    )
    parser.add_argument(
        '--output-dir',
        required=True,
        help='Output directory for converted files'
    )

    args = parser.parse_args()

    print("=" * 60)
    print("VisionMaster Batch Converter")
    print("=" * 60)

    if args.mode == 'import':
        if not args.xml_dir or not args.image_dir:
            print("Error: --xml-dir and --image-dir are required for import mode")
            return

        print(f"Mode: VisionMaster -> Custom JSON")
        print(f"XML Directory: {args.xml_dir}")
        print(f"Image Directory: {args.image_dir}")
        print(f"Output Directory: {args.output_dir}")
        print()

        batch_visionmaster_to_custom(
            args.xml_dir,
            args.image_dir,
            args.output_dir
        )

    elif args.mode == 'export':
        if not args.json_dir:
            print("Error: --json-dir is required for export mode")
            return

        print(f"Mode: Custom JSON -> VisionMaster")
        print(f"JSON Directory: {args.json_dir}")
        print(f"Output Directory: {args.output_dir}")
        print()

        batch_custom_to_visionmaster(
            args.json_dir,
            args.output_dir
        )

    print("=" * 60)


if __name__ == "__main__":
    main()
