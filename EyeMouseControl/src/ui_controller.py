from queue import Queue
from types import SimpleNamespace

import cv2
import numpy as np

from qt_compat import QtWidgets, QtGui, QtCore, Qt

QMainWindow = QtWidgets.QMainWindow
QLabel = QtWidgets.QLabel
QVBoxLayout = QtWidgets.QVBoxLayout
QHBoxLayout = QtWidgets.QHBoxLayout
QGridLayout = QtWidgets.QGridLayout
QWidget = QtWidgets.QWidget
QSlider = QtWidgets.QSlider
QCheckBox = QtWidgets.QCheckBox
QComboBox = QtWidgets.QComboBox
QPushButton = QtWidgets.QPushButton
QProgressBar = QtWidgets.QProgressBar
QFrame = QtWidgets.QFrame
QGroupBox = QtWidgets.QGroupBox
QTimer = QtCore.QTimer
QImage = QtGui.QImage
QPixmap = QtGui.QPixmap
QPainter = QtGui.QPainter
QPen = QtGui.QPen
QColor = QtGui.QColor
QBrush = QtGui.QBrush
QFont = QtGui.QFont


class CalibrationOverlay(QWidget):
    def __init__(self):
        super().__init__()
        self.config = {}
        self.monitor = None
        self.point = None
        self.index = 0
        self.total = 0
        self.progress = 0.0
        self.status_text = ""
        self.hint_text = ""
        self.quality = 0.0
        self.stability = None
        self.accepted_samples = 0
        self.target_samples = 0
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint
            | Qt.WindowType.WindowStaysOnTopHint
            | Qt.WindowType.Tool
        )

    def set_config(self, config):
        self.config = config

    def show_target(self, overlay_state):
        self.monitor = overlay_state["monitor"]
        self.point = overlay_state["point"]
        self.index = overlay_state["index"]
        self.total = overlay_state["total"]
        self.progress = overlay_state.get("progress", 0.0)
        self.accepted_samples = overlay_state.get("accepted_samples", 0)
        self.target_samples = overlay_state.get("target_samples", 0)
        self.quality = overlay_state.get("tracking_quality", 0.0)
        self.stability = overlay_state.get("stability")
        self.hint_text = overlay_state.get("hint", "")
        self.status_text = f"Smart calibration point {self.index}/{self.total}"
        self.setGeometry(self.monitor["x"], self.monitor["y"], self.monitor["width"], self.monitor["height"])
        self.show()
        self.raise_()
        self.update()

    def hide_overlay(self):
        self.hide()

    def paintEvent(self, _event):
        if self.monitor is None or self.point is None:
            return

        painter = QPainter(self)
        painter.fillRect(self.rect(), QColor(8, 10, 16, 235))

        target_x = int(self.point[0] - self.monitor["x"])
        target_y = int(self.point[1] - self.monitor["y"])
        panel_rect = self._panel_rect(target_x, target_y)
        target_radius = int(self.config.get("target_radius_px", 18))

        painter.setRenderHint(QPainter.RenderHint.Antialiasing)
        painter.setPen(QPen(QColor(255, 255, 255), 2))
        painter.setBrush(QBrush(QColor(255, 80, 80, 80)))
        painter.drawEllipse(target_x - target_radius * 2, target_y - target_radius * 2, target_radius * 4, target_radius * 4)
        painter.setBrush(QBrush(QColor(255, 80, 80)))
        painter.drawEllipse(target_x - target_radius, target_y - target_radius, target_radius * 2, target_radius * 2)
        painter.drawLine(target_x - (target_radius + 16), target_y, target_x + (target_radius + 16), target_y)
        painter.drawLine(target_x, target_y - (target_radius + 16), target_x, target_y + (target_radius + 16))

        painter.setPen(Qt.PenStyle.NoPen)
        painter.setBrush(QBrush(QColor(7, 12, 20, 220)))
        painter.drawRoundedRect(panel_rect, 14, 14)
        painter.setPen(QPen(QColor(255, 255, 255), 1))
        painter.setFont(QFont("Segoe UI", 16))
        title_flags = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap)
        body_flags = int(Qt.AlignmentFlag.AlignLeft | Qt.AlignmentFlag.AlignTop | Qt.TextFlag.TextWordWrap)
        painter.drawText(panel_rect.adjusted(18, 18, -18, -18), title_flags, self.status_text)
        painter.setFont(QFont("Segoe UI", 11))
        painter.drawText(panel_rect.adjusted(18, 54, -18, -18), body_flags, self.hint_text or "Keep your head steady and look directly at the target")
        progress_rect = QtCore.QRect(panel_rect.left() + 18, panel_rect.top() + 96, panel_rect.width() - 36, 18)
        painter.drawRect(progress_rect)
        inner_width = max(progress_rect.width() - 4, 1)
        painter.fillRect(progress_rect.left() + 2, progress_rect.top() + 2, int(inner_width * self.progress), progress_rect.height() - 4, QColor(255, 110, 110))
        painter.drawText(panel_rect.left() + 18, panel_rect.top() + 138, f"Accepted samples: {self.accepted_samples}/{self.target_samples}")
        painter.drawText(panel_rect.left() + 18, panel_rect.top() + 164, f"Tracking quality: {self.quality:.2f}")
        stability_text = "n/a" if self.stability is None else f"{self.stability:.4f}"
        painter.drawText(panel_rect.left() + 18, panel_rect.top() + 190, f"Gaze stability: {stability_text}")
        painter.end()

    def _panel_rect(self, target_x, target_y):
        panel_width = min(430, max(320, self.width() // 3))
        panel_height = 220
        padding = 28

        left = padding if target_x > self.width() * 0.52 else self.width() - panel_width - padding
        top = padding if target_y > self.height() * 0.52 else self.height() - panel_height - padding

        left = max(padding, min(left, self.width() - panel_width - padding))
        top = max(padding, min(top, self.height() - panel_height - padding))
        return QtCore.QRect(int(left), int(top), int(panel_width), int(panel_height))


class UIController(QMainWindow):
    def __init__(self, camera_manager, gesture_engine, config, monitors, action_queue=None):
        super().__init__()
        self.camera_manager = camera_manager
        self.gesture_engine = gesture_engine
        self.config = config
        self.monitors = monitors
        self.action_queue = action_queue or Queue()
        self.tracking_result = None
        self.runtime_state = {}
        self.calibration_overlay = CalibrationOverlay()
        self.calibration_overlay.set_config(self.config["calibration"])
        self._init_ui()
        self.preview_timer = QTimer()
        self.preview_timer.timeout.connect(self.update_preview)
        self.preview_timer.start(33)

    def _init_ui(self):
        self.setWindowTitle("Eye Mouse Control Pro")
        self.setGeometry(80, 60, 1340, 840)
        self.setStyleSheet(
            """
            QMainWindow, QWidget { background-color: #11151b; color: #f1f5f9; }
            QGroupBox { border: 1px solid #243041; border-radius: 10px; margin-top: 14px; padding-top: 14px; }
            QGroupBox::title { subcontrol-origin: margin; left: 12px; padding: 0 6px; color: #9fb3c8; }
            QPushButton { background-color: #1d4ed8; border: none; border-radius: 8px; padding: 10px 14px; font-weight: 600; }
            QPushButton:hover { background-color: #2563eb; }
            QComboBox, QSlider, QCheckBox, QLabel { font-size: 13px; }
            QProgressBar { border: 1px solid #334155; border-radius: 6px; text-align: center; background-color: #0f172a; }
            QProgressBar::chunk { background-color: #f97316; border-radius: 5px; }
            """
        )

        root = QWidget()
        self.setCentralWidget(root)
        root_layout = QHBoxLayout(root)
        root_layout.setContentsMargins(18, 18, 18, 18)
        root_layout.setSpacing(18)

        preview_panel = QVBoxLayout()
        preview_panel.setSpacing(12)
        root_layout.addLayout(preview_panel, 3)

        self.video_label = QLabel()
        self.video_label.setMinimumSize(920, 620)
        self.video_label.setStyleSheet("background-color: #020617; border-radius: 12px; border: 1px solid #243041;")
        preview_panel.addWidget(self.video_label)

        summary_box = QGroupBox("Runtime")
        summary_layout = QGridLayout(summary_box)
        self.status_label = QLabel("Tracking: waiting for face")
        self.metrics_label = QLabel("FPS: 0 | CPU: n/a")
        self.calibration_label = QLabel("Calibration: raw mapping")
        self.cursor_label = QLabel("Cursor: n/a")
        self.hotkeys_label = QLabel(
            "Hotkeys: rest mode Ctrl+Alt+E | click mode Ctrl+Alt+M | calibration Ctrl+Alt+C"
        )
        summary_layout.addWidget(self.status_label, 0, 0)
        summary_layout.addWidget(self.metrics_label, 0, 1)
        summary_layout.addWidget(self.calibration_label, 1, 0)
        summary_layout.addWidget(self.cursor_label, 1, 1)
        summary_layout.addWidget(self.hotkeys_label, 2, 0, 1, 2)
        preview_panel.addWidget(summary_box)

        side_panel = QVBoxLayout()
        side_panel.setSpacing(12)
        root_layout.addLayout(side_panel, 2)

        control_box = QGroupBox("Controls")
        control_layout = QVBoxLayout(control_box)
        control_layout.setSpacing(10)

        self.start_calibration_button = QPushButton("Start Smart Calibration")
        self.start_calibration_button.clicked.connect(lambda: self.enqueue_action("start_calibration"))
        control_layout.addWidget(self.start_calibration_button)

        self.reset_calibration_button = QPushButton("Reset Calibration")
        self.reset_calibration_button.clicked.connect(lambda: self.enqueue_action("reset_calibration"))
        control_layout.addWidget(self.reset_calibration_button)

        self.save_settings_button = QPushButton("Save Settings")
        self.save_settings_button.clicked.connect(lambda: self.enqueue_action("save_settings"))
        control_layout.addWidget(self.save_settings_button)

        control_layout.addWidget(QLabel("Click Mode"))
        self.click_mode_combo = QComboBox()
        self.click_mode_combo.addItems(["Blink", "Dwell", "Off"])
        self.click_mode_combo.setCurrentText(self.config["click"]["mode"])
        self.click_mode_combo.currentTextChanged.connect(self._click_mode_changed)
        control_layout.addWidget(self.click_mode_combo)

        control_layout.addWidget(QLabel("Target Monitor"))
        self.monitor_combo = QComboBox()
        for idx, monitor in enumerate(self.monitors):
            self.monitor_combo.addItem(f"Monitor {idx + 1} | {monitor.width}x{monitor.height}", idx)
        selected_index = min(self.config["monitors"]["selected_monitor_index"], len(self.monitors) - 1)
        self.monitor_combo.setCurrentIndex(selected_index)
        self.monitor_combo.currentIndexChanged.connect(self._monitor_changed)
        control_layout.addWidget(self.monitor_combo)

        control_layout.addWidget(QLabel("Cursor Sensitivity"))
        self.sensitivity_slider = QSlider(Qt.Orientation.Horizontal)
        self.sensitivity_slider.setRange(1, 15)
        self.sensitivity_slider.setValue(self._sensitivity_to_slider(self.config["tracking"]["sensitivity"]))
        control_layout.addWidget(self.sensitivity_slider)

        self.rest_mode_checkbox = QCheckBox("Rest Mode")
        self.rest_mode_checkbox.stateChanged.connect(self._rest_mode_changed)
        control_layout.addWidget(self.rest_mode_checkbox)

        self.mirror_checkbox = QCheckBox("Mirror Preview")
        self.mirror_checkbox.setChecked(self.config["ui"]["mirror_preview"])
        control_layout.addWidget(self.mirror_checkbox)

        self.debug_checkbox = QCheckBox("Show Debug Details")
        self.debug_checkbox.setChecked(self.config["ui"]["show_debug"])
        control_layout.addWidget(self.debug_checkbox)

        side_panel.addWidget(control_box)

        diagnostics_box = QGroupBox("Diagnostics")
        diagnostics_layout = QVBoxLayout(diagnostics_box)
        self.quality_label = QLabel("Tracking quality: 0%")
        self.blink_label = QLabel("Blink EAR: n/a")
        self.pose_label = QLabel("Head pose: yaw 0 | pitch 0 | roll 0")
        self.last_action_label = QLabel("Last action: none")
        diagnostics_layout.addWidget(self.quality_label)
        diagnostics_layout.addWidget(self.blink_label)
        diagnostics_layout.addWidget(self.pose_label)
        diagnostics_layout.addWidget(self.last_action_label)
        diagnostics_layout.addWidget(QLabel("Dwell Progress"))
        self.dwell_progress = QProgressBar()
        self.dwell_progress.setRange(0, 100)
        diagnostics_layout.addWidget(self.dwell_progress)
        side_panel.addWidget(diagnostics_box)

        help_box = QGroupBox("Workflow")
        help_layout = QVBoxLayout(help_box)
        help_layout.addWidget(QLabel("1. Start smart calibration on the target monitor"))
        help_layout.addWidget(QLabel("2. Wait for the lock to become stable before each point"))
        help_layout.addWidget(QLabel("3. Let the system reject noisy samples automatically"))
        help_layout.addWidget(QLabel("4. Save settings after tuning sensitivity"))
        side_panel.addWidget(help_box)
        side_panel.addStretch(1)

    def enqueue_action(self, action, payload=None):
        self.action_queue.put({"action": action, "payload": payload})

    def set_tracking_result(self, tracking_result):
        self.tracking_result = tracking_result

    def set_runtime_state(self, runtime_state):
        self.runtime_state = runtime_state or {}
        self._refresh_runtime_widgets()

    def get_selected_monitor_index(self):
        return self.monitor_combo.currentData()

    def get_calibration_monitor_geometry(self, index):
        app = QtWidgets.QApplication.instance()
        if app is not None:
            screens = app.screens()
            if 0 <= index < len(screens):
                rect = screens[index].availableGeometry()
                return SimpleNamespace(
                    x=rect.x(),
                    y=rect.y(),
                    width=rect.width(),
                    height=rect.height(),
                    name=screens[index].name(),
                )
        monitor = self.monitors[index]
        return SimpleNamespace(
            x=monitor.x,
            y=monitor.y,
            width=monitor.width,
            height=monitor.height,
            name=getattr(monitor, "name", f"Monitor {index + 1}"),
        )

    def get_sensitivity(self):
        slider_value = self.sensitivity_slider.value()
        return 0.55 + (slider_value - 1) * 0.11

    def get_click_mode(self):
        return self.click_mode_combo.currentText()

    def is_mirror_enabled(self):
        return self.mirror_checkbox.isChecked()

    def is_debug_enabled(self):
        return self.debug_checkbox.isChecked()

    def set_click_mode(self, click_mode):
        self.click_mode_combo.blockSignals(True)
        self.click_mode_combo.setCurrentText(click_mode)
        self.click_mode_combo.blockSignals(False)

    def set_rest_mode(self, enabled):
        self.rest_mode_checkbox.blockSignals(True)
        self.rest_mode_checkbox.setChecked(enabled)
        self.rest_mode_checkbox.blockSignals(False)

    def update_preview(self):
        frame = self.camera_manager.get_frame()
        if frame is None:
            return

        tracking_result = self.tracking_result
        mirror_preview = self.is_mirror_enabled()
        display_frame = frame.copy()
        self._draw_overlays(display_frame, tracking_result, mirror_preview)
        if mirror_preview:
            display_frame = cv2.flip(display_frame, 1)

        rgb_image = cv2.cvtColor(display_frame, cv2.COLOR_BGR2RGB)
        h, w, ch = rgb_image.shape
        bytes_per_line = ch * w
        qt_image = QImage(rgb_image.data, w, h, bytes_per_line, QImage.Format.Format_RGB888)
        scaled = QPixmap.fromImage(qt_image).scaled(
            self.video_label.width(),
            self.video_label.height(),
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )
        self.video_label.setPixmap(scaled)

    def show_calibration_overlay(self, overlay_state):
        if overlay_state is None:
            self.calibration_overlay.hide_overlay()
            return
        self.calibration_overlay.show_target(overlay_state)

    def hide_calibration_overlay(self):
        self.calibration_overlay.hide_overlay()

    def snapshot_settings(self):
        return {
            "click_mode": self.get_click_mode(),
            "sensitivity": self.get_sensitivity(),
            "mirror_preview": self.is_mirror_enabled(),
            "show_debug": self.is_debug_enabled(),
            "selected_monitor_index": self.get_selected_monitor_index(),
            "rest_mode": self.rest_mode_checkbox.isChecked(),
        }

    def _draw_overlays(self, frame, tracking_result, mirror_preview):
        if tracking_result is None:
            return

        x1, y1, x2, y2 = tracking_result["face_bbox"]
        frame_width = frame.shape[1]
        if mirror_preview:
            x1, x2 = frame_width - x2, frame_width - x1

        cv2.rectangle(frame, (x1, y1), (x2, y2), (76, 214, 152), 2)

        for key in ("left", "right"):
            for point in tracking_result["iris_points"][key]:
                px, py = self._display_point(point, frame_width, mirror_preview)
                cv2.circle(frame, (px, py), 2, (56, 189, 248), -1)

        nose_x, nose_y = self._display_point(tracking_result["nose_point"], frame_width, mirror_preview)
        cv2.circle(frame, (nose_x, nose_y), 4, (255, 200, 0), -1)

        if self.is_debug_enabled():
            cv2.putText(
                frame,
                f"Gaze {tracking_result['normalized_point'][0]:.2f}, {tracking_result['normalized_point'][1]:.2f}",
                (20, 32),
                cv2.FONT_HERSHEY_SIMPLEX,
                0.7,
                (255, 255, 255),
                2,
            )

    def _refresh_runtime_widgets(self):
        state = self.runtime_state
        tracking_text = "active" if state.get("face_detected") else "waiting for face"
        self.status_label.setText(f"Tracking: {tracking_text}")
        self.metrics_label.setText(
            f"FPS: {state.get('fps', 0):.1f} | CPU: {state.get('cpu_percent', 'n/a')}"
        )
        self.calibration_label.setText(state.get("calibration_text", "Calibration: raw mapping"))
        self.cursor_label.setText(state.get("cursor_text", "Cursor: n/a"))
        self.quality_label.setText(f"Tracking quality: {int(state.get('tracking_quality', 0.0) * 100)}%")
        self.blink_label.setText(f"Blink EAR: {state.get('blink_ear', 'n/a')}")
        self.pose_label.setText(state.get("pose_text", "Head pose: yaw 0 | pitch 0 | roll 0"))
        self.last_action_label.setText(f"Last action: {state.get('last_action', 'none')}")
        self.dwell_progress.setValue(int(state.get("dwell_progress", 0.0) * 100))

    def _click_mode_changed(self, click_mode):
        self.enqueue_action("set_click_mode", click_mode)

    def _monitor_changed(self, index):
        self.enqueue_action("set_monitor", self.monitor_combo.itemData(index))

    def _rest_mode_changed(self, state):
        self.enqueue_action("set_rest_mode", state != 0)

    def _sensitivity_to_slider(self, value):
        normalized = max(1, min(15, int(round((value - 0.55) / 0.11 + 1))))
        return normalized

    def _display_point(self, point, frame_width, mirror_preview):
        px, py = int(point[0]), int(point[1])
        if mirror_preview:
            px = frame_width - px
        return px, py
