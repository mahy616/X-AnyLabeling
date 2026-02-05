import csv
import hashlib
import json
import multiprocessing as mp
import os
import os.path as osp
import xml.etree.ElementTree as ET
from concurrent.futures import ProcessPoolExecutor
from typing import Dict, List, Optional, Tuple

import cv2
import numpy as np

from anylabeling.views.labeling.logger import logger

FAST_MODE = True
DS_FACTOR = 4
USE_MULTIPROCESS = True
CACHE_SUBDIR = "_cache"

_WORKER_CFG: Dict[str, object] = {}


def read_text_lines(path: str) -> List[str]:
    for enc in ("utf-8", "gbk"):
        try:
            with open(path, "r", encoding=enc) as f:
                return f.readlines()
        except UnicodeDecodeError:
            continue
    with open(path, "r", encoding="utf-8", errors="ignore") as f:
        return f.readlines()


def load_class_names_file(path: str) -> Dict[int, str]:
    lines = read_text_lines(path)
    class_dict: Dict[int, str] = {}
    next_id = 0
    for line in lines:
        line = line.strip()
        if not line or line.startswith("#") or "ignore" in line.lower():
            continue
        parts = line.split(maxsplit=1)
        if len(parts) >= 2 and parts[0].isdigit():
            cid = int(parts[0])
            class_dict[cid] = parts[1]
            next_id = max(next_id, cid + 1)
        else:
            while next_id in class_dict:
                next_id += 1
            class_dict[next_id] = line
            next_id += 1
    if not class_dict:
        raise ValueError(f"No valid class names found in {path}")
    return class_dict


def load_class_names(pred_dir: str, dataset_dir: str) -> Tuple[Dict[int, str], str]:
    pred_path = osp.join(pred_dir, "class_names.txt")
    if osp.exists(pred_path):
        class_dict = load_class_names_file(pred_path)
        return class_dict, pred_path
    if dataset_dir:
        dataset_path = osp.join(dataset_dir, "class_names.txt")
        if osp.exists(dataset_path):
            class_dict = load_class_names_file(dataset_path)
            return class_dict, dataset_path
    raise FileNotFoundError("class_names.txt not found in pred_dir or dataset_dir")


def iter_xml_files(xml_dir: str):
    for root, _dirs, files in os.walk(xml_dir):
        for name in files:
            if name.lower().endswith(".xml"):
                yield osp.join(root, name)


def find_image_path(xml_path: str) -> Optional[str]:
    base = osp.splitext(xml_path)[0]
    for ext in (".jpg", ".jpeg", ".png", ".bmp"):
        candidate = base + ext
        if osp.exists(candidate):
            return candidate
    return None


def _downsample_shape(img_shape: Tuple[int, int], ds_factor: int) -> Tuple[int, int]:
    h, w = img_shape[:2]
    if ds_factor <= 1:
        return (h, w)
    return (max(1, h // ds_factor), max(1, w // ds_factor))


def _downsample_mask(mask: Optional[np.ndarray], ds_factor: int, target_shape=None):
    if mask is None:
        return None
    if ds_factor <= 1 and target_shape is None:
        return mask
    if target_shape is None:
        target_shape = _downsample_shape(mask.shape, ds_factor)
    h, w = target_shape
    if mask.shape[:2] == (h, w):
        return mask
    return cv2.resize(mask, (w, h), interpolation=cv2.INTER_NEAREST)


def _scale_shapes(
    shapes, scale_x: float, scale_y: float, max_w: Optional[int], max_h: Optional[int]
):
    scaled = []
    for shape in shapes:
        label = shape.get("label") or "ignore"
        points = shape.get("points") or []
        scaled_points = []
        for x, y in points:
            nx = int(round(x * scale_x))
            ny = int(round(y * scale_y))
            if max_w is not None:
                nx = min(max(nx, 0), max_w - 1)
            if max_h is not None:
                ny = min(max(ny, 0), max_h - 1)
            scaled_points.append([nx, ny])
        scaled.append({"label": label, "points": scaled_points})
    return scaled


def _cache_key(xml_path: str, img_shape: Tuple[int, int], ds_factor: int) -> str:
    try:
        stat = os.stat(xml_path)
        mtime = getattr(stat, "st_mtime_ns", int(stat.st_mtime * 1e9))
        size = stat.st_size
    except Exception:
        mtime = 0
        size = 0
    key = f"{xml_path}|{mtime}|{size}|{img_shape[0]}x{img_shape[1]}|ds{ds_factor}"
    return hashlib.md5(key.encode("utf-8")).hexdigest()


def _cache_path(
    xml_path: str, img_shape: Tuple[int, int], ds_factor: int, cache_dir: str
) -> str:
    base_name = osp.splitext(osp.basename(xml_path))[0]
    key = _cache_key(xml_path, img_shape, ds_factor)
    name = f"{base_name}_{key[:12]}.npy"
    return osp.join(cache_dir, name)


def shape2mask(img_size: Tuple[int, int], points: List[List[float]]):
    mask = np.zeros(img_size[:2], dtype=np.uint8)
    if not points:
        return mask.astype(bool)
    pts = np.array(points, dtype=np.int32)
    if pts.ndim != 2:
        return mask.astype(bool)
    if len(pts) == 2:
        x1, y1 = pts[0]
        x2, y2 = pts[1]
        cv2.rectangle(mask, (int(x1), int(y1)), (int(x2), int(y2)), 1, -1)
    elif len(pts) > 2:
        cv2.fillPoly(mask, [pts], 1)
    return mask.astype(bool)


def shape2label(
    img_size: Tuple[int, int], shapes, class_name_mapping: Dict[str, int]
) -> np.ndarray:
    label = np.zeros(img_size[:2], dtype=np.uint8)
    for shape in shapes:
        points = shape.get("points") or []
        class_name = shape.get("label")
        if class_name not in class_name_mapping:
            continue
        class_id = class_name_mapping[class_name]
        label_mask = shape2mask(img_size[:2], points)
        label[label_mask] = class_id
    return label


def get_xml_annotation(xml_path: str):
    tree = ET.parse(xml_path)
    root = tree.getroot()
    shapes = []
    defect_list = []

    if len(root) == 0:
        return shapes, defect_list

    items_data = root[0]
    for item in items_data:
        shape = {}
        points = []
        flags = item.find("flags")
        label = flags.text if flags is not None else None
        if label is None:
            label = "ignore"
        shape_type = None

        if (
            item.tag
            == "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawPolygonRoiParameter"
        ):
            shape_type = "polygon"
            ps = item.find("_PolygonPoints")
            if ps is None:
                continue
            for p in ps:
                x = p.find("x")
                y = p.find("y")
                if x is None or y is None:
                    continue
                points.append([float(x.text), float(y.text)])
        elif (
            item.tag
            == "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawCoverRoiParameter"
        ):
            shape_type = "rectangle"
            origin = item.find("_OriginPoint")
            width = item.find("_width")
            height = item.find("_height")
            if origin is None or width is None or height is None:
                continue
            ox, oy = [float(v) for v in origin.text.split(",")]
            w = float(width.text)
            h = float(height.text)
            points.append([ox, oy])
            points.append([ox + w, oy + h])
        elif (
            item.tag
            == "VisionMaster.ModuleMainWindow.ModuleDialogNew.DeepLearning.FlawCoverCircleRoiParameter"
        ):
            shape_type = "circle"
            center = item.find("_CenterPoint")
            radius = item.find("_Radius")
            if center is None or radius is None:
                continue
            cx, cy = [float(v) for v in center.text.split(",")]
            r = float(radius.text.split(",")[0])
            points.append([cx, cy])
            points.append([cx + r, cy])
        else:
            continue

        shape["label"] = label
        shape["points"] = points
        shape["group_id"] = None
        shape["shape_type"] = shape_type
        shape["flags"] = {}
        shapes.append(shape)
        defect_list.append(label)

    return shapes, defect_list


def build_gt_mask_fast(
    xml_path: str, img_shape: Tuple[int, int], class2id: Dict[str, int], ds_factor: int
):
    shapes, _ = get_xml_annotation(xml_path)
    if ds_factor <= 1:
        return shape2label(img_shape, shapes, class2id)
    dst_h, dst_w = _downsample_shape(img_shape, ds_factor)
    scale_x = dst_w / float(img_shape[1])
    scale_y = dst_h / float(img_shape[0])
    scaled_shapes = _scale_shapes(shapes, scale_x, scale_y, dst_w, dst_h)
    return shape2label((dst_h, dst_w), scaled_shapes, class2id)


def _load_or_build_gt_fast(
    xml_path: str,
    img_shape: Tuple[int, int],
    class2id: Dict[str, int],
    ds_factor: int,
    cache_dir: str,
):
    cache_path = None
    if cache_dir:
        os.makedirs(cache_dir, exist_ok=True)
        cache_path = _cache_path(xml_path, img_shape, ds_factor, cache_dir)
        if osp.exists(cache_path):
            try:
                cached = np.load(cache_path)
                if cached.shape[:2] == _downsample_shape(img_shape, ds_factor):
                    return cached
            except Exception:
                pass
    gt_mask = build_gt_mask_fast(xml_path, img_shape, class2id, ds_factor)
    if cache_dir and cache_path:
        try:
            np.save(cache_path, gt_mask)
        except Exception:
            pass
    return gt_mask


def _pre_scan_labels(xml_files, class_dict, class2id, results, include_background):
    for xml_path in xml_files:
        if not osp.exists(xml_path) or osp.getsize(xml_path) == 0:
            continue
        try:
            shapes, _ = get_xml_annotation(xml_path)
        except Exception:
            continue
        ensure_labels_in_mapping(
            shapes, class_dict, class2id, results, include_background
        )


def _init_worker(cfg):
    global _WORKER_CFG
    _WORKER_CFG = cfg
    try:
        cv2.setNumThreads(0)
    except Exception:
        pass


def _process_one_xml(xml_path: str):
    cfg = _WORKER_CFG
    stats = {"images": 0, "skipped": 0, "missing_pred": 0}
    per_class = {}
    error_rows = []

    if not osp.exists(xml_path) or osp.getsize(xml_path) == 0:
        stats["skipped"] += 1
        return per_class, stats, error_rows

    base_name = osp.splitext(osp.basename(xml_path))[0]
    img_path = find_image_path(xml_path)
    img_shape = None
    if img_path:
        img = cv2.imread(img_path)
        if img is not None:
            img_shape = img.shape[:2]

    pred_dirs = resolve_pred_dirs(
        xml_path, cfg["xml_dir"], cfg["pred_dir"], cfg["scope"]
    )
    pred_mask, _ = load_pred_mask(pred_dirs, base_name, img_shape)

    if img_shape is None and pred_mask is not None:
        img_shape = pred_mask.shape[:2]

    if img_shape is None:
        stats["skipped"] += 1
        return per_class, stats, error_rows

    try:
        gt_mask = _load_or_build_gt_fast(
            xml_path,
            img_shape,
            cfg["class2id"],
            cfg["ds_factor"],
            cfg["cache_dir"],
        )
    except KeyError as exc:
        logger.warning(f"Label not found in class mapping: {exc} ({xml_path})")
        stats["skipped"] += 1
        return per_class, stats, error_rows
    except Exception as exc:
        logger.warning(f"Failed to parse XML {xml_path}: {exc}")
        stats["skipped"] += 1
        return per_class, stats, error_rows

    if pred_mask is None:
        pred_mask = np.zeros_like(gt_mask, dtype=np.uint8)
        stats["missing_pred"] += 1
    else:
        pred_mask = _downsample_mask(pred_mask, cfg["ds_factor"], gt_mask.shape[:2])

    stats["images"] += 1

    present_ids = set(int(x) for x in np.unique(gt_mask))
    present_ids.update(int(x) for x in np.unique(pred_mask))
    present_ids = present_ids & cfg["class_id_set"]

    for cid in present_ids:
        gt_list = extract_instances(gt_mask, cid)
        pred_list = extract_instances(pred_mask, cid)
        gt_count = len(gt_list)

        if not gt_list and not pred_list:
            continue

        tp, fp, fn = match_instances(gt_list, pred_list, cfg["iou_thr"])
        per_class[cid] = (gt_count, tp, fp, fn)

        if fp > 0:
            error_rows.append(
                {
                    "image": base_name,
                    "type": "FP",
                    "class": cfg["class_names"].get(cid, str(cid)),
                    "count": fp,
                }
            )
        if fn > 0:
            error_rows.append(
                {
                    "image": base_name,
                    "type": "FN",
                    "class": cfg["class_names"].get(cid, str(cid)),
                    "count": fn,
                }
            )

    return per_class, stats, error_rows


def _merge_results(results, per_class):
    for cid, (gt, tp, fp, fn) in per_class.items():
        info = results.get(cid)
        if info is None:
            continue
        info["gt"] += gt
        info["tp"] += tp
        info["fp"] += fp
        info["fn"] += fn


def ensure_labels_in_mapping(
    shapes, class_dict, class2id, results, include_background
):
    if "ignore" not in class2id:
        class2id["ignore"] = 255
    for shape in shapes:
        label = shape.get("label")
        if not label:
            label = "ignore"
        if label.lower() == "ignore":
            continue
        if label not in class2id:
            valid_ids = [cid for cid in class_dict.keys() if cid != 255]
            new_id = (max(valid_ids) + 1) if valid_ids else 0
            class_dict[new_id] = label
            class2id[label] = new_id
            if not should_skip_class(new_id, label, include_background):
                results[new_id] = init_class_result(label)


def should_skip_class(class_id: int, name: str, include_background: bool) -> bool:
    if class_id == 255:
        return True
    if include_background:
        return False
    if class_id == 0:
        return True
    if name and name.lower() in ("background", "bg"):
        return True
    return False


def init_class_result(name: str) -> Dict[str, object]:
    return {
        "name": name,
        "gt": 0,
        "tp": 0,
        "fp": 0,
        "fn": 0,
    }


def extract_instances(mask: np.ndarray, class_id: int):
    binary = (mask == class_id).astype(np.uint8)
    if binary.sum() == 0:
        return []
    num_labels, labels = cv2.connectedComponents(binary, connectivity=8)
    instances = []
    for i in range(1, num_labels):
        instances.append(labels == i)
    return instances


def iou(a: np.ndarray, b: np.ndarray) -> float:
    inter = np.logical_and(a, b).sum()
    union = np.logical_or(a, b).sum()
    if union == 0:
        return 0.0
    return inter / union


def match_instances(gt_list, pred_list, iou_thr: float):
    used = [False] * len(pred_list)
    tp = 0
    fn = 0
    for gt in gt_list:
        best_iou = 0.0
        best_idx = -1
        for idx, pred in enumerate(pred_list):
            if used[idx]:
                continue
            val = iou(gt, pred)
            if val > best_iou:
                best_iou = val
                best_idx = idx
        if best_iou >= iou_thr and best_idx >= 0:
            tp += 1
            used[best_idx] = True
        else:
            fn += 1
    fp = sum(1 for u in used if not u)
    return tp, fp, fn


def build_gt_mask(
    xml_path: str,
    img_shape: Tuple[int, int],
    class2id: Dict[str, int],
    class_dict,
    results,
    include_background: bool,
):
    shapes, _ = get_xml_annotation(xml_path)
    ensure_labels_in_mapping(shapes, class_dict, class2id, results, include_background)
    return shape2label(img_shape, shapes, class2id)


def load_pred_mask(
    pred_dirs, base_name: str, target_shape, exts=(".png", ".bmp", ".jpg")
):
    for pred_dir in pred_dirs:
        for ext in exts:
            pred_path = osp.join(pred_dir, base_name + ext)
            if not osp.exists(pred_path):
                continue
            pred = cv2.imread(pred_path, cv2.IMREAD_GRAYSCALE)
            if pred is None:
                continue
            if target_shape and pred.shape[:2] != target_shape[:2]:
                pred = cv2.resize(
                    pred,
                    (target_shape[1], target_shape[0]),
                    interpolation=cv2.INTER_NEAREST,
                )
            return pred, pred_path
    if pred_dirs:
        return None, osp.join(pred_dirs[-1], base_name + exts[0])
    return None, base_name + exts[0]


def collect_xml_files(xml_dir: str, scope: str):
    if scope == "train_test":
        train_dir = osp.join(xml_dir, "train")
        test_dir = osp.join(xml_dir, "test")
        if osp.isdir(train_dir) and osp.isdir(test_dir):
            return list(iter_xml_files(train_dir)) + list(iter_xml_files(test_dir))
    return list(iter_xml_files(xml_dir))


def _is_under(path: str, root: str) -> bool:
    try:
        return osp.commonpath([osp.abspath(path), osp.abspath(root)]) == osp.abspath(
            root
        )
    except ValueError:
        return False


def resolve_pred_dirs(xml_path: str, xml_dir: str, pred_dir: str, scope: str):
    pred_train = osp.join(pred_dir, "train")
    pred_test = osp.join(pred_dir, "test")
    has_pred_subdirs = osp.isdir(pred_train) or osp.isdir(pred_test)

    if not has_pred_subdirs:
        return [pred_dir]

    if scope == "test":
        return [pred_test] if osp.isdir(pred_test) else [pred_dir]

    xml_train_dir = osp.join(xml_dir, "train")
    xml_test_dir = osp.join(xml_dir, "test")

    if osp.isdir(xml_train_dir) and _is_under(xml_path, xml_train_dir):
        return [pred_train] if osp.isdir(pred_train) else [pred_dir]
    if osp.isdir(xml_test_dir) and _is_under(xml_path, xml_test_dir):
        return [pred_test] if osp.isdir(pred_test) else [pred_dir]

    pred_dirs = []
    if osp.isdir(pred_train):
        pred_dirs.append(pred_train)
    if osp.isdir(pred_test):
        pred_dirs.append(pred_test)
    return pred_dirs or [pred_dir]


def evaluate_dataset(
    xml_dir: str,
    pred_dir: str,
    dataset_dir: str,
    iou_thr: float,
    include_background: bool,
    limit: int,
    scope: str,
):
    if FAST_MODE:
        return evaluate_dataset_fast(
            xml_dir,
            pred_dir,
            dataset_dir,
            iou_thr,
            include_background,
            limit,
            scope,
        )
    return _evaluate_dataset_exact(
        xml_dir,
        pred_dir,
        dataset_dir,
        iou_thr,
        include_background,
        limit,
        scope,
    )


def evaluate_dataset_fast(
    xml_dir: str,
    pred_dir: str,
    dataset_dir: str,
    iou_thr: float,
    include_background: bool,
    limit: int,
    scope: str,
):
    class_dict, class_source = load_class_names(pred_dir, dataset_dir)
    class2id = {name: cid for cid, name in class_dict.items()}

    results = {}
    for cid, name in class_dict.items():
        if should_skip_class(cid, name, include_background):
            continue
        results[cid] = init_class_result(name)

    stats = {"images": 0, "skipped": 0, "missing_pred": 0}
    error_rows = []

    xml_files = collect_xml_files(xml_dir, scope)
    if limit and limit > 0:
        xml_files = xml_files[:limit]

    _pre_scan_labels(xml_files, class_dict, class2id, results, include_background)

    class_ids = set(results.keys())
    class_names = {cid: info["name"] for cid, info in results.items()}
    cache_dir = osp.abspath(osp.join(pred_dir, "..", "eval", CACHE_SUBDIR))

    cfg = {
        "xml_dir": xml_dir,
        "pred_dir": pred_dir,
        "scope": scope,
        "class2id": class2id,
        "class_id_set": class_ids,
        "class_names": class_names,
        "iou_thr": iou_thr,
        "ds_factor": DS_FACTOR,
        "cache_dir": cache_dir,
    }

    use_mp = USE_MULTIPROCESS and len(xml_files) > 1
    if use_mp:
        workers = max(1, os.cpu_count() or 1)
        ctx = mp.get_context("spawn")
        chunksize = max(1, len(xml_files) // (workers * 4))
        with ProcessPoolExecutor(
            max_workers=workers,
            mp_context=ctx,
            initializer=_init_worker,
            initargs=(cfg,),
        ) as ex:
            for per_class, delta, errs in ex.map(
                _process_one_xml, xml_files, chunksize=chunksize
            ):
                _merge_results(results, per_class)
                stats["images"] += delta["images"]
                stats["skipped"] += delta["skipped"]
                stats["missing_pred"] += delta["missing_pred"]
                error_rows.extend(errs)
    else:
        _init_worker(cfg)
        for xml_path in xml_files:
            per_class, delta, errs = _process_one_xml(xml_path)
            _merge_results(results, per_class)
            stats["images"] += delta["images"]
            stats["skipped"] += delta["skipped"]
            stats["missing_pred"] += delta["missing_pred"]
            error_rows.extend(errs)

    return results, stats, class_source, error_rows


def _evaluate_dataset_exact(
    xml_dir: str,
    pred_dir: str,
    dataset_dir: str,
    iou_thr: float,
    include_background: bool,
    limit: int,
    scope: str,
):
    class_dict, class_source = load_class_names(pred_dir, dataset_dir)
    class2id = {name: cid for cid, name in class_dict.items()}

    results = {}
    for cid, name in class_dict.items():
        if should_skip_class(cid, name, include_background):
            continue
        results[cid] = init_class_result(name)

    stats = {"images": 0, "skipped": 0, "missing_pred": 0}
    error_rows = []

    xml_files = collect_xml_files(xml_dir, scope)
    if limit and limit > 0:
        xml_files = xml_files[:limit]

    for xml_path in xml_files:
        if not osp.exists(xml_path) or osp.getsize(xml_path) == 0:
            stats["skipped"] += 1
            continue
        base_name = osp.splitext(osp.basename(xml_path))[0]
        img_path = find_image_path(xml_path)
        img_shape = None
        if img_path:
            img = cv2.imread(img_path)
            if img is not None:
                img_shape = img.shape[:2]

        pred_dirs = resolve_pred_dirs(xml_path, xml_dir, pred_dir, scope)
        pred_mask, _ = load_pred_mask(pred_dirs, base_name, img_shape)

        if img_shape is None:
            stats["skipped"] += 1
            continue

        try:
            gt_mask = build_gt_mask(
                xml_path, img_shape, class2id, class_dict, results, include_background
            )
        except KeyError as exc:
            logger.warning(f"Label not found in class mapping: {exc} ({xml_path})")
            stats["skipped"] += 1
            continue
        except Exception as exc:
            logger.warning(f"Failed to parse XML {xml_path}: {exc}")
            stats["skipped"] += 1
            continue

        if pred_mask is None:
            pred_mask = np.zeros_like(gt_mask, dtype=np.uint8)
            stats["missing_pred"] += 1

        stats["images"] += 1

        for cid, info in results.items():
            gt_list = extract_instances(gt_mask, cid)
            pred_list = extract_instances(pred_mask, cid)

            info["gt"] += len(gt_list)

            if not gt_list and not pred_list:
                continue

            tp, fp, fn = match_instances(gt_list, pred_list, iou_thr)
            info["tp"] += tp
            info["fp"] += fp
            info["fn"] += fn
            if fp > 0:
                error_rows.append(
                    {
                        "image": base_name,
                        "type": "FP",
                        "class": info["name"],
                        "count": fp,
                    }
                )
            if fn > 0:
                error_rows.append(
                    {
                        "image": base_name,
                        "type": "FN",
                        "class": info["name"],
                        "count": fn,
                    }
                )

    return results, stats, class_source, error_rows


def save_class_level(results, out_dir: str):
    os.makedirs(out_dir, exist_ok=True)
    rows = []
    for cid in sorted(results.keys()):
        info = results[cid]
        tp = info["tp"]
        fp = info["fp"]
        fn = info["fn"]
        gt = info["gt"]
        over_rate = fp / gt if gt > 0 else 0.0
        miss_rate = fn / gt if gt > 0 else 0.0
        rows.append(
            {
                "class_id": cid,
                "class_name": info["name"],
                "gt": gt,
                "correct": tp,
                "fp": fp,
                "fn": fn,
                "over_rate": round(over_rate * 100.0, 2),
                "miss_rate": round(miss_rate * 100.0, 2),
            }
        )

    csv_path = osp.join(out_dir, "class_level.csv")
    with open(csv_path, "w", encoding="utf-8", newline="") as f:
        writer = csv.DictWriter(
            f,
            fieldnames=[
                "class_id",
                "class_name",
                "gt",
                "correct",
                "fp",
                "fn",
                "over_rate",
                "miss_rate",
            ],
        )
        writer.writeheader()
        writer.writerows(rows)

    json_path = osp.join(out_dir, "class_level.json")
    with open(json_path, "w", encoding="utf-8") as f:
        json.dump(rows, f, ensure_ascii=False, indent=2)

    return csv_path, json_path
