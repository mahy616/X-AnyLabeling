import os
import time

from PyQt5 import QtCore, QtGui
from PyQt5.QtCore import Qt
from PyQt5.QtWidgets import (
    QCheckBox,
    QComboBox,
    QDialog,
    QDoubleSpinBox,
    QFileDialog,
    QGridLayout,
    QHBoxLayout,
    QLabel,
    QLineEdit,
    QMessageBox,
    QPushButton,
    QSpinBox,
    QTableWidget,
    QTableWidgetItem,
    QTextEdit,
    QVBoxLayout,
)

from anylabeling.services.evaluation import evaluate_dataset, save_class_level


class ModelEvaluationDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.parent = parent
        self.setWindowTitle(self.tr("Model Evaluation"))
        self.resize(1000, 720)
        self._build_ui()
        self._load_default_paths()

    def _build_ui(self):
        main_layout = QVBoxLayout(self)

        form_layout = QGridLayout()
        row = 0

        self.xml_dir = QLineEdit()
        self._add_path_row(
            form_layout, row, self.tr("XML目录:"), self.xml_dir, self._browse_xml_dir
        )
        row += 1

        self.pred_dir = QLineEdit()
        self._add_path_row(
            form_layout, row, self.tr("Pred目录:"), self.pred_dir, self._browse_pred_dir
        )
        row += 1

        self.dataset_dir = QLineEdit()
        self._add_path_row(
            form_layout,
            row,
            self.tr("Dataset目录(可选):"),
            self.dataset_dir,
            self._browse_dataset_dir,
        )
        row += 1

        self.out_dir = QLineEdit()
        self._add_path_row(
            form_layout,
            row,
            self.tr("输出目录(可选):"),
            self.out_dir,
            self._browse_out_dir,
        )
        row += 1

        self.iou_spin = QDoubleSpinBox()
        self.iou_spin.setRange(0.05, 0.95)
        self.iou_spin.setSingleStep(0.05)
        self.iou_spin.setValue(0.5)
        form_layout.addWidget(QLabel(self.tr("IoU阈值:")), row, 0)
        form_layout.addWidget(self.iou_spin, row, 1)

        self.scope_combo = QComboBox()
        self.scope_combo.addItems([self.tr("训练+测试集"), self.tr("仅测试集")])
        self.scope_combo.setCurrentIndex(0)
        form_layout.addWidget(QLabel(self.tr("评估范围:")), row, 2)
        form_layout.addWidget(self.scope_combo, row, 3)
        row += 1

        self.limit_spin = QSpinBox()
        self.limit_spin.setRange(0, 1000000)
        self.limit_spin.setValue(0)
        form_layout.addWidget(QLabel(self.tr("限制数量(0=全量):")), row, 0)
        form_layout.addWidget(self.limit_spin, row, 1)
        row += 1

        self.include_bg = QCheckBox(self.tr("包含背景类"))
        form_layout.addWidget(self.include_bg, row, 0)
        row += 1

        main_layout.addLayout(form_layout)

        btn_layout = QHBoxLayout()
        self.run_btn = QPushButton(self.tr("运行评估"))
        self.run_btn.clicked.connect(self._run_eval)
        btn_layout.addWidget(self.run_btn)

        self.open_out_btn = QPushButton(self.tr("打开输出目录"))
        self.open_out_btn.clicked.connect(self._open_out_dir)
        btn_layout.addWidget(self.open_out_btn)
        btn_layout.addStretch(1)
        main_layout.addLayout(btn_layout)

        self.log_box = QTextEdit()
        self.log_box.setReadOnly(True)
        self.log_box.setFixedHeight(140)
        main_layout.addWidget(self.log_box)

        self.table = QTableWidget(0, 8)
        self.table.setHorizontalHeaderLabels(
            [
                self.tr("类别ID"),
                self.tr("类别名称"),
                self.tr("标注数量"),
                self.tr("正确检测数"),
                self.tr("过检"),
                self.tr("漏检"),
                self.tr("过检率(%)"),
                self.tr("漏检率(%)"),
            ]
        )
        self.table.horizontalHeader().setStretchLastSection(True)
        self.table.setSortingEnabled(True)
        main_layout.addWidget(self.table)

        self.error_label = QLabel(self.tr("Errors (FP/FN)"))
        main_layout.addWidget(self.error_label)

        self.error_table = QTableWidget(0, 4)
        self.error_table.setHorizontalHeaderLabels(
            [
                self.tr("Image"),
                self.tr("Type"),
                self.tr("Class"),
                self.tr("Count"),
            ]
        )
        self.error_table.horizontalHeader().setStretchLastSection(True)
        self.error_table.setSortingEnabled(True)
        main_layout.addWidget(self.error_table)

    def _add_path_row(self, layout, row, label, line_edit, browse_cb):
        layout.addWidget(QLabel(label), row, 0)
        layout.addWidget(line_edit, row, 1, 1, 2)
        btn = QPushButton(self.tr("浏览"))
        btn.clicked.connect(browse_cb)
        layout.addWidget(btn, row, 3)

    def _load_default_paths(self):
        base_dir = getattr(self.parent, "last_open_dir", None)
        if base_dir and os.path.isdir(base_dir):
            self.xml_dir.setText(base_dir)

    def _browse_xml_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("选择XML目录"), "")
        if path:
            self.xml_dir.setText(path)

    def _browse_pred_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("选择Pred目录"), "")
        if path:
            self.pred_dir.setText(path)

    def _browse_dataset_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("选择Dataset目录"), "")
        if path:
            self.dataset_dir.setText(path)

    def _browse_out_dir(self):
        path = QFileDialog.getExistingDirectory(self, self.tr("选择输出目录"), "")
        if path:
            self.out_dir.setText(path)

    def _open_out_dir(self):
        out_dir = self._resolve_out_dir()
        if not out_dir:
            return
        if not os.path.isdir(out_dir):
            QMessageBox.warning(self, self.tr("提示"), self.tr("输出目录不存在"))
            return
        if hasattr(os, "startfile"):
            os.startfile(out_dir)
        else:
            QtGui.QDesktopServices.openUrl(QtCore.QUrl.fromLocalFile(out_dir))

    def _resolve_out_dir(self):
        out_dir = self.out_dir.text().strip()
        if out_dir:
            return out_dir
        pred_dir = self.pred_dir.text().strip()
        if pred_dir:
            return os.path.abspath(os.path.join(pred_dir, "..", "eval"))
        return ""

    def _log(self, msg):
        self.log_box.append(msg)

    def _run_eval(self):
        xml_dir = self.xml_dir.text().strip()
        pred_dir = self.pred_dir.text().strip()
        dataset_dir = self.dataset_dir.text().strip()
        out_dir = self._resolve_out_dir()
        iou = float(self.iou_spin.value())
        limit = int(self.limit_spin.value())
        include_bg = bool(self.include_bg.isChecked())
        scope = "train_test" if self.scope_combo.currentIndex() == 0 else "test"

        if not xml_dir or not os.path.isdir(xml_dir):
            QMessageBox.warning(self, self.tr("提示"), self.tr("XML目录无效"))
            return
        if not pred_dir or not os.path.isdir(pred_dir):
            QMessageBox.warning(self, self.tr("提示"), self.tr("Pred目录无效"))
            return

        self.log_box.clear()
        self._log(self.tr("开始评估 ..."))
        start_time = time.perf_counter()

        try:
            results, stats, class_source, error_rows = evaluate_dataset(
                xml_dir,
                pred_dir,
                dataset_dir,
                iou,
                include_bg,
                limit,
                scope,
            )
            csv_path, json_path = save_class_level(results, out_dir)

            self._log(self.tr("class_names source: {0}").format(class_source))
            self._log(
                self.tr("processed images: {0}").format(stats["images"])
            )
            self._log(
                self.tr("skipped images: {0}").format(stats["skipped"])
            )
            self._log(
                self.tr("missing pred: {0}").format(stats["missing_pred"])
            )
            self._log(self.tr("saved: {0}").format(csv_path))
            self._log(self.tr("saved: {0}").format(json_path))
            elapsed = time.perf_counter() - start_time
            self._log(self.tr("total_time_sec: {0:.3f}").format(elapsed))

            self._populate_table(results)
            self._populate_error_table(error_rows)
        except Exception as exc:
            QMessageBox.critical(self, self.tr("错误"), str(exc))

    def _populate_table(self, results):
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
                [
                    cid,
                    info["name"],
                    gt,
                    tp,
                    fp,
                    fn,
                    round(over_rate * 100.0, 2),
                    round(miss_rate * 100.0, 2),
                ]
            )

        self.table.setSortingEnabled(False)
        self.table.setRowCount(len(rows))
        for r_idx, row in enumerate(rows):
            for c_idx, val in enumerate(row):
                item = QTableWidgetItem(str(val))
                if c_idx == 0:
                    item.setTextAlignment(Qt.AlignCenter)
                self.table.setItem(r_idx, c_idx, item)
        self.table.setSortingEnabled(True)

    def _populate_error_table(self, error_rows):
        self.error_table.setSortingEnabled(False)
        self.error_table.setRowCount(len(error_rows))
        for r_idx, row in enumerate(error_rows):
            values = [
                row.get("image", ""),
                row.get("type", ""),
                row.get("class", ""),
                row.get("count", 0),
            ]
            for c_idx, val in enumerate(values):
                item = QTableWidgetItem(str(val))
                if c_idx == 3:
                    item.setTextAlignment(Qt.AlignCenter)
                self.error_table.setItem(r_idx, c_idx, item)
        self.error_table.setSortingEnabled(True)
