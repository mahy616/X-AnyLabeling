import os
import tempfile
import unittest
import xml.etree.ElementTree as ET

import cv2
import numpy as np

from anylabeling.services.evaluation import segmentation_eval as eval_mod


def _write_vm_polygon_xml(path, label, points):
    root = ET.Element(
        "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawTrainData"
    )
    items = ET.SubElement(root, "_ItemsData")
    param = ET.SubElement(
        items,
        "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter",
    )
    flags = ET.SubElement(param, "flags")
    flags.text = label
    polygon_points = ET.SubElement(param, "_PolygonPoints")
    for x, y in points:
        point_elem = ET.SubElement(
            polygon_points, "HikPcUI.ImageView.PolygonPoint"
        )
        x_elem = ET.SubElement(point_elem, "x")
        x_elem.text = str(x)
        y_elem = ET.SubElement(point_elem, "y")
        y_elem.text = str(y)

    tree = ET.ElementTree(root)
    tree.write(path, encoding="utf-8", xml_declaration=True)


class TestEvalDemo(unittest.TestCase):
    def test_load_class_names_file(self):
        with tempfile.TemporaryDirectory() as tmp:
            path = os.path.join(tmp, "class_names.txt")
            with open(path, "w", encoding="utf-8") as f:
                f.write("# comment\n")
                f.write("0 background\n")
                f.write("1 defect\n")
                f.write("ignore\n")
                f.write("scratch\n")

            mapping = eval_mod.load_class_names_file(path)
            self.assertEqual(mapping[0], "background")
            self.assertEqual(mapping[1], "defect")
            self.assertEqual(mapping[2], "scratch")

    def test_evaluate_dataset_simple_match(self):
        orig_mp = eval_mod.USE_MULTIPROCESS
        orig_ds = eval_mod.DS_FACTOR
        try:
            eval_mod.USE_MULTIPROCESS = False
            eval_mod.DS_FACTOR = 1
            with tempfile.TemporaryDirectory() as tmp:
                xml_dir = os.path.join(tmp, "xml")
                pred_dir = os.path.join(tmp, "pred")
                os.makedirs(xml_dir, exist_ok=True)
                os.makedirs(pred_dir, exist_ok=True)

                image_path = os.path.join(xml_dir, "img.png")
                xml_path = os.path.join(xml_dir, "img.xml")
                mask_path = os.path.join(pred_dir, "img.png")
                class_path = os.path.join(pred_dir, "class_names.txt")

                image = np.zeros((20, 20, 3), dtype=np.uint8)
                cv2.imwrite(image_path, image)

                points = [(5, 5), (14, 5), (14, 14), (5, 14)]
                _write_vm_polygon_xml(xml_path, "defect", points)

                mask = np.zeros((20, 20), dtype=np.uint8)
                mask[5:15, 5:15] = 1
                cv2.imwrite(mask_path, mask)

                with open(class_path, "w", encoding="utf-8") as f:
                    f.write("1 defect\n")

                results, stats, class_source, error_rows = eval_mod.evaluate_dataset(
                    xml_dir=xml_dir,
                    pred_dir=pred_dir,
                    dataset_dir="",
                    iou_thr=0.5,
                    include_background=False,
                    limit=0,
                    scope="train_test",
                )

                self.assertTrue(class_source.endswith("class_names.txt"))
                self.assertIn(1, results)
                info = results[1]
                self.assertEqual(info["gt"], 1)
                self.assertEqual(info["tp"], 1)
                self.assertEqual(info["fp"], 0)
                self.assertEqual(info["fn"], 0)
                self.assertEqual(stats["images"], 1)
                self.assertEqual(stats["missing_pred"], 0)
                self.assertEqual(len(error_rows), 0)
        finally:
            eval_mod.USE_MULTIPROCESS = orig_mp
            eval_mod.DS_FACTOR = orig_ds
