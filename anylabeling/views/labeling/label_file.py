import base64
import json
import os.path as osp
import xml.etree.ElementTree as ET

import PIL.Image
from PIL import ImageFile

ImageFile.LOAD_TRUNCATED_IMAGES = True

from . import utils
from .label_converter import LabelConverter
from .logger import logger
from .schema import XLABEL_BASIC_FIELDS, create_xlabel_template
from .shape import Shape

PIL.Image.MAX_IMAGE_PIXELS = None


class LabelFileError(Exception):
    pass


class LabelFile:
    suffix = ".xml"  # Default to VisionMaster format

    def __init__(self, filename=None, image_dir=None):
        self.shapes = []
        self.image_path = None
        self.image_data = None
        self.image_dir = image_dir
        if filename is not None:
            self.load(filename)
        self.filename = filename

    @staticmethod
    def _check_image_height_and_width(image_data, image_height, image_width):
        img_arr = utils.img_b64_to_arr(image_data)
        if image_height is not None and img_arr.shape[0] != image_height:
            logger.error(
                "image_height does not match with image_data or image_path, "
                "so getting image_height from actual image."
            )
            image_height = img_arr.shape[0]
        if image_width is not None and img_arr.shape[1] != image_width:
            logger.error(
                "image_width does not match with image_data or image_path, "
                "so getting image_width from actual image."
            )
            image_width = img_arr.shape[1]
        return image_height, image_width

    @staticmethod
    def is_label_file(filename):
        ext = osp.splitext(filename)[1].lower()
        return ext in [".xml", ".json"]  # Support both VisionMaster and JSON formats

    @staticmethod
    def load_image_file(filename, default=None):
        try:
            with open(filename, "rb") as f:
                return f.read()
        except Exception:
            logger.error(f"Failed opening image file: {filename}")
            return default

    def load(self, filename):
        ext = osp.splitext(filename)[1].lower()
        if ext == ".xml":
            self._load_xml(filename)
        else:
            self._load_json(filename)

    def _load_json(self, filename):
        try:
            with utils.io_open(filename, "r") as f:
                data = json.load(f)

            if data.get("version") is None:
                logger.warning(
                    f"Loading JSON file ({filename}) of unknown version"
                )

            if data["shapes"]:
                for i in range(len(data["shapes"])):
                    shape_points = data["shapes"][i]["points"]
                    if (
                        data["shapes"][i]["shape_type"] == "rectangle"
                        and len(shape_points) == 2
                    ):
                        logger.warning(
                            "UserWarning: Diagonal vertex mode is deprecated in X-AnyLabeling release v2.2.0 or later.\n"
                            "Please update your code to accommodate the new four-point mode."
                        )
                        data["shapes"][i]["points"] = (
                            utils.rectangle_from_diagonal(shape_points)
                        )

            data["imagePath"] = osp.basename(data["imagePath"])
            if data["imageData"] is not None:
                image_data = base64.b64decode(data["imageData"])
            else:
                # relative path from label file to relative path from cwd
                if self.image_dir:
                    image_path = osp.join(self.image_dir, data["imagePath"])
                else:
                    image_path = osp.join(
                        osp.dirname(filename), data["imagePath"]
                    )
                image_data = self.load_image_file(image_path)

            flags = data.get("flags", {})
            image_path = data["imagePath"]

            self._check_image_height_and_width(
                base64.b64encode(image_data).decode("utf-8"),
                data.get("imageHeight"),
                data.get("imageWidth"),
            )

            shapes = [Shape().load_from_dict(s) for s in data["shapes"]]

        except Exception as e:  # noqa
            raise LabelFileError(e) from e

        other_data = {}
        for key, value in data.items():
            if key not in XLABEL_BASIC_FIELDS:
                other_data[key] = value

        # Add new fields if not available
        other_data["description"] = other_data.get("description", "")

        # Only replace data after everything is loaded.
        self.flags = flags
        self.shapes = shapes
        self.image_path = image_path
        self.image_data = image_data
        self.filename = filename
        self.other_data = other_data

    def _load_xml(self, filename):
        """Load VisionMaster XML format"""
        try:
            if osp.getsize(filename) == 0:
                # Empty XML means OK image
                image_path = osp.splitext(osp.basename(filename))[0]
                # Try to find image with common extensions
                for ext in ['.jpg', '.png', '.bmp', '.jpeg']:
                    test_path = osp.join(osp.dirname(filename),
                                        osp.splitext(osp.basename(filename))[0] + ext)
                    if osp.exists(test_path):
                        image_path = osp.basename(test_path)
                        image_data = self.load_image_file(test_path)
                        break
                else:
                    raise LabelFileError("Image file not found for empty XML")

                self.flags = {"OK": True}
                self.shapes = []
                self.image_path = image_path
                self.image_data = image_data
                self.filename = filename
                self.other_data = {"description": ""}
                return

            tree = ET.parse(filename)
            root = tree.getroot()

            # Get image path from XML
            image_path_elem = root.find("_ImagePath")
            if image_path_elem is not None and image_path_elem.text:
                image_path = osp.basename(image_path_elem.text)
            else:
                image_path = osp.splitext(osp.basename(filename))[0]

            # Load image data
            if self.image_dir:
                full_image_path = osp.join(self.image_dir, image_path)
            else:
                full_image_path = osp.join(osp.dirname(filename), image_path)
            image_data = self.load_image_file(full_image_path)

            # Parse shapes
            shapes = []
            items_data = root.find("_ItemsData")
            if items_data is not None:
                import math

                # Load FlawCoverRoiParameter (rectangle/rotation)
                for param in items_data.findall(
                    "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawCoverRoiParameter"
                ):
                    flags_elem = param.find("flags")
                    label = flags_elem.text if flags_elem is not None and flags_elem.text else "ignore"

                    visible_elem = param.find("_TIsVisible")
                    is_visible = visible_elem is not None and visible_elem.text == "True"

                    # Parse origin, width, height, angle
                    origin_elem = param.find("_OriginPoint")
                    width_elem = param.find("_width")
                    height_elem = param.find("_height")
                    angle_elem = param.find("_Angle")

                    if origin_elem is not None and width_elem is not None and height_elem is not None:
                        cx, cy = map(float, origin_elem.text.split(','))
                        width = float(width_elem.text)
                        height = float(height_elem.text)
                        angle = float(angle_elem.text) if angle_elem is not None else 0

                        # Convert to 4 corner points
                        angle_rad = math.radians(angle)
                        cos_a = math.cos(angle_rad)
                        sin_a = math.sin(angle_rad)
                        w_half = width / 2
                        h_half = height / 2

                        # Four corners (top-left, top-right, bottom-right, bottom-left)
                        points = [
                            [cx + (-w_half * cos_a - (-h_half) * sin_a), cy + (-w_half * sin_a + (-h_half) * cos_a)],
                            [cx + (w_half * cos_a - (-h_half) * sin_a), cy + (w_half * sin_a + (-h_half) * cos_a)],
                            [cx + (w_half * cos_a - h_half * sin_a), cy + (w_half * sin_a + h_half * cos_a)],
                            [cx + (-w_half * cos_a - h_half * sin_a), cy + (-w_half * sin_a + h_half * cos_a)]
                        ]

                        # Determine shape_type based on angle
                        shape_type = "rectangle" if abs(angle) < 0.01 else "rotation"

                        shape_dict = {
                            "label": label,
                            "shape_type": shape_type,
                            "flags": {} if is_visible else {"hidden": True},
                            "points": points,
                            "group_id": None,
                            "description": "",
                            "difficult": False,
                            "attributes": {},
                        }
                        shape = Shape().load_from_dict(shape_dict)
                        shapes.append(shape)

                # Load FlawPolygonRoiParameter (polygon)
                for param in items_data.findall(
                    "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter"
                ):
                    flags_elem = param.find("flags")
                    label = flags_elem.text if flags_elem is not None and flags_elem.text else "ignore"

                    visible_elem = param.find("_TIsVisible")
                    is_visible = visible_elem is not None and visible_elem.text == "True"

                    points = []
                    polygon_points = param.find("_PolygonPoints")
                    if polygon_points is not None:
                        for point_elem in polygon_points.findall("HikPcUI.ImageView.PolygonPoint"):
                            x_elem = point_elem.find("x")
                            y_elem = point_elem.find("y")
                            if x_elem is not None and y_elem is not None:
                                points.append([float(x_elem.text), float(y_elem.text)])

                    if len(points) >= 3:
                        shape_dict = {
                            "label": label,
                            "shape_type": "polygon",
                            "flags": {} if is_visible else {"hidden": True},
                            "points": points,
                            "group_id": None,
                            "description": "",
                            "difficult": False,
                            "attributes": {},
                        }
                        shape = Shape().load_from_dict(shape_dict)
                        shapes.append(shape)

            self.flags = {}
            self.shapes = shapes
            self.image_path = image_path
            self.image_data = image_data
            self.filename = filename
            self.other_data = {"description": ""}

        except Exception as e:
            raise LabelFileError(e) from e

    def save(
        self,
        filename=None,
        shapes=None,
        image_path=None,
        image_height=None,
        image_width=None,
        image_data=None,
        other_data=None,
        flags=None,
    ):
        ext = osp.splitext(filename)[1].lower()
        if ext == ".xml":
            self._save_xml(filename, shapes, image_path, flags)
        else:
            self._save_json(filename, shapes, image_path, image_height,
                          image_width, image_data, other_data, flags)

    def _save_json(self, filename, shapes, image_path, image_height,
                   image_width, image_data, other_data, flags):
        if image_data is not None:
            image_data = base64.b64encode(image_data).decode("utf-8")
            image_height, image_width = self._check_image_height_and_width(
                image_data, image_height, image_width
            )

        if other_data is None:
            other_data = {}
        if flags is None:
            flags = {}
        for i, shape in enumerate(shapes):
            if shape["shape_type"] == "rectangle":
                sorted_box = LabelConverter.calculate_bounding_box(
                    shape["points"]
                )
                xmin, ymin, xmax, ymax = sorted_box
                shape["points"] = [
                    [xmin, ymin],
                    [xmax, ymin],
                    [xmax, ymax],
                    [xmin, ymax],
                ]
                shapes[i] = shape

        data = create_xlabel_template(
            flags=flags,
            shapes=shapes,
            image_path=image_path,
            image_data=image_data,
            image_height=image_height,
            image_width=image_width,
        )

        for key, value in other_data.items():
            assert key not in data
            data[key] = value
        try:
            with utils.io_open(filename, "w") as f:
                json.dump(data, f, ensure_ascii=False, indent=2)
            self.filename = filename
        except Exception as e:  # noqa
            raise LabelFileError(e) from e

    def _save_xml(self, filename, shapes, image_path, flags):
        """Save as VisionMaster XML format"""
        try:
            import math

            root = ET.Element(
                "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawTrainData"
            )

            # Check if OK flag is set
            is_ok = flags and (flags.get("OK") or flags.get("ok"))

            if is_ok:
                # Create empty XML file for OK images
                with open(filename, 'w', encoding='utf-8') as f:
                    pass  # Create empty file
                self.filename = filename
                return
            else:
                # Add shapes
                items_data = ET.SubElement(root, "_ItemsData")

                for shape in shapes:
                    shape_type = shape["shape_type"]
                    label = shape.get("label", "")
                    is_ignore = label.lower() == "ignore"

                    # Rectangle and Rotation -> FlawCoverRoiParameter
                    if shape_type in ["rectangle", "rotation"]:
                        param = ET.SubElement(
                            items_data,
                            "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawCoverRoiParameter"
                        )

                        points = shape["points"]
                        # Calculate center point, width, height, angle
                        cx = sum(p[0] for p in points) / len(points)
                        cy = sum(p[1] for p in points) / len(points)

                        # Calculate width and height from first two edges
                        width = math.sqrt((points[1][0] - points[0][0])**2 + (points[1][1] - points[0][1])**2)
                        height = math.sqrt((points[2][0] - points[1][0])**2 + (points[2][1] - points[1][1])**2)

                        # Calculate angle (from horizontal to first edge)
                        angle = math.degrees(math.atan2(points[1][1] - points[0][1], points[1][0] - points[0][0]))
                        if shape_type == "rectangle":
                            angle = 0  # Force 0 for rectangle

                        level_num = ET.SubElement(param, "_LevelNum")
                        level_num.text = "1" if is_ignore else "2"

                        flags_elem = ET.SubElement(param, "flags")
                        flags_elem.text = "" if is_ignore else label

                        color_value = ET.SubElement(param, "_ColorValue")
                        color_value.text = "128" if is_ignore else "0"

                        bg_color = ET.SubElement(param, "_BackgroundColor")
                        bg_color.text = "#fe8b04" if is_ignore else "#ff1a1a"

                        origin = ET.SubElement(param, "_OriginPoint")
                        origin.text = f"{cx},{cy}"

                        width_elem = ET.SubElement(param, "_width")
                        width_elem.text = str(width)

                        height_elem = ET.SubElement(param, "_height")
                        height_elem.text = str(height)

                        sign = ET.SubElement(param, "_Sign")
                        sign.text = "True"

                        sign_visible = ET.SubElement(param, "_TIsSignVisible")
                        sign_visible.text = "True"

                        angle_elem = ET.SubElement(param, "_Angle")
                        angle_elem.text = str(angle)

                        visible = ET.SubElement(param, "_TIsVisible")
                        is_visible = "hidden" not in shape.get("flags", {})
                        visible.text = "True" if is_visible else "False"

                    # Polygon -> FlawPolygonRoiParameter
                    elif shape_type == "polygon":
                        param = ET.SubElement(
                            items_data,
                            "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter"
                        )

                        level_num = ET.SubElement(param, "_LevelNum")
                        level_num.text = "1" if is_ignore else "2"

                        flags_elem = ET.SubElement(param, "flags")
                        flags_elem.text = "" if is_ignore else label

                        color_value = ET.SubElement(param, "_ColorValue")
                        color_value.text = "128" if is_ignore else "0"

                        bg_color = ET.SubElement(param, "_BackgroundColor")
                        bg_color.text = "#fe8b04" if is_ignore else "#ff1a1a"

                        polygon_points = ET.SubElement(param, "_PolygonPoints")
                        for point in shape["points"]:
                            point_elem = ET.SubElement(
                                polygon_points, "HikPcUI.ImageView.PolygonPoint"
                            )
                            x_elem = ET.SubElement(point_elem, "x")
                            x_elem.text = str(point[0])
                            y_elem = ET.SubElement(point_elem, "y")
                            y_elem.text = str(point[1])

                        sign = ET.SubElement(param, "_Sign")
                        sign.text = "True"

                        visible = ET.SubElement(param, "_TIsVisible")
                        is_visible = "hidden" not in shape.get("flags", {})
                        visible.text = "True" if is_visible else "False"

                calibrated = ET.SubElement(root, "_IsOKCalibrated")
                calibrated.text = "False"
                image_path_elem = ET.SubElement(root, "_ImagePath")
                image_path_elem.text = image_path

            tree = ET.ElementTree(root)
            ET.indent(tree, space="  ")
            tree.write(filename, encoding="utf-8", xml_declaration=True)

            # Fix format to match VisionMaster
            with open(filename, "r", encoding="utf-8") as f:
                content = f.read()
            content = content.replace('encoding="utf-8"', 'encoding="utf-8" ')
            with open(filename, "w", encoding="utf-8") as f:
                f.write(content)

            self.filename = filename
        except Exception as e:
            raise LabelFileError(e) from e
