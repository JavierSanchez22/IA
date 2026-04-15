import sys
import math
import numpy as np
import cv2
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QSlider, QFileDialog, QHBoxLayout, QVBoxLayout, QGridLayout,
    QGroupBox, QRadioButton, QButtonGroup, QSizePolicy, QFrame,
    QScrollArea
)
from PyQt5.QtCore import Qt, QPoint, QRect, pyqtSignal
from PyQt5.QtGui import (
    QImage, QPixmap, QPainter, QPen, QColor, QFont, QPalette, QBrush
)

def cv2_to_qpixmap(cv_img):
    if cv_img is None:
        return QPixmap()
    if len(cv_img.shape) == 2:
        h, w = cv_img.shape
        if cv_img.dtype != np.uint8:
            mn, mx = cv_img.min(), cv_img.max()
            if mx > mn:
                cv_img = ((cv_img - mn) / (mx - mn) * 255).astype(np.uint8)
            else:
                cv_img = cv_img.astype(np.uint8)
        qimg = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        qimg = QImage(img_rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())

class AngleWheel(QWidget):
    angleChanged = pyqtSignal(int)

    def __init__(self, parent=None):
        super().__init__(parent)
        self._angle = 0
        self.setFixedSize(120, 120)
        self.setMouseTracking(True)
        self._dragging = False

    @property
    def angle(self):
        return self._angle

    @angle.setter
    def angle(self, value):
        self._angle = int(max(-180, min(180, value)))
        self.update()

    def paintEvent(self, event):
        p = QPainter(self)
        p.setRenderHint(QPainter.Antialiasing)
        cx, cy, r = 60, 60, 46
        center = QPoint(cx, cy)

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(240, 240, 240)))
        p.drawEllipse(center, r, r)

        p.setPen(QPen(QColor(180, 180, 180), 2))
        p.setBrush(Qt.NoBrush)
        p.drawEllipse(center, r, r)

        marker_font = QFont("Arial", 7)
        p.setFont(marker_font)
        for deg, label in [(0, "0°"), (90, "90°"), (180, "180°"), (270, "270°")]:
            rad = math.radians(deg - 90)
            mx = cx + (r - 8) * math.cos(rad)
            my = cy + (r - 8) * math.sin(rad)
            p.setPen(QPen(QColor(100, 100, 100), 1))
            p.drawEllipse(QPoint(int(mx), int(my)), 3, 3)
            lx = cx + (r + 10) * math.cos(rad)
            ly = cy + (r + 10) * math.sin(rad)
            p.setPen(QColor(50, 50, 50))
            p.drawText(QRect(int(lx) - 14, int(ly) - 7, 28, 14), Qt.AlignCenter, label)

        rad = math.radians(self._angle - 90)
        hx = cx + r * 0.65 * math.cos(rad)
        hy = cy + r * 0.65 * math.sin(rad)
        p.setPen(QPen(QColor(0, 120, 215), 2, Qt.SolidLine, Qt.RoundCap))
        p.drawLine(center, QPoint(int(hx), int(hy)))

        p.setPen(Qt.NoPen)
        p.setBrush(QBrush(QColor(0, 120, 215)))
        p.drawEllipse(center, 5, 5)
        p.drawEllipse(QPoint(int(hx), int(hy)), 5, 5)
        p.end()

    def _angle_from_pos(self, pos):
        dx = pos.x() - 60
        dy = pos.y() - 60
        deg = math.degrees(math.atan2(dy, dx)) + 90
        if deg > 180:
            deg -= 360
        return int(round(deg))

    def mousePressEvent(self, e):
        if e.button() == Qt.LeftButton:
            self._dragging = True
            self._set_from_pos(e.pos())

    def mouseMoveEvent(self, e):
        if self._dragging:
            self._set_from_pos(e.pos())

    def mouseReleaseEvent(self, e):
        self._dragging = False

    def _set_from_pos(self, pos):
        a = self._angle_from_pos(pos)
        self._angle = a
        self.update()
        self.angleChanged.emit(a)

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(400, 320)
        self.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        self.setStyleSheet("border: 1px solid #ccc; background-color: #fff;")
        self.setText("Sin imagen\nSeleccionar archivo para comenzar")

    def set_cv_image(self, cv_img):
        if cv_img is None:
            self.setText("Sin imagen")
            return
        pixmap = cv2_to_qpixmap(cv_img)
        scaled = pixmap.scaled(self.size(), Qt.KeepAspectRatio, Qt.SmoothTransformation)
        self.setPixmap(scaled)

    def resizeEvent(self, e):
        super().resizeEvent(e)

def make_slider_row(label_text, min_val, max_val, init_val, parent=None):
    row = QHBoxLayout()
    row.setSpacing(8)

    lbl = QLabel(label_text)
    lbl.setFixedWidth(60)

    slider = QSlider(Qt.Horizontal)
    slider.setMinimum(min_val)
    slider.setMaximum(max_val)
    slider.setValue(init_val)

    val_lbl = QLabel(str(init_val))
    val_lbl.setFixedWidth(36)
    val_lbl.setAlignment(Qt.AlignRight | Qt.AlignVCenter)

    slider.valueChanged.connect(lambda v: val_lbl.setText(str(v)))

    row.addWidget(lbl)
    row.addWidget(slider)
    row.addWidget(val_lbl)
    return row, slider, val_lbl

class OpenCVEditor(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("OpenCV Editor")
        self.resize(1100, 780)

        self._original_image = None
        self._working_image = None
        self._shape = "rect"

        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        main_layout = QVBoxLayout(central)

        header = QWidget()
        header.setFixedHeight(40)
        hl = QHBoxLayout(header)
        title = QLabel("Imagen Editor")
        title.setStyleSheet("font-size: 14px; font-weight: bold;")
        hl.addWidget(title)
        hl.addStretch()
        main_layout.addWidget(header)

        body = QWidget()
        body_layout = QHBoxLayout(body)

        left = self._build_left_panel()
        body_layout.addWidget(left, stretch=3)

        right_scroll = QScrollArea()
        right_scroll.setWidgetResizable(True)
        right_scroll.setFixedWidth(320)
        right_widget = self._build_right_panel()
        right_scroll.setWidget(right_widget)
        body_layout.addWidget(right_scroll)

        main_layout.addWidget(body, stretch=1)

    def _build_left_panel(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        load_row = QHBoxLayout()
        btn_load = QPushButton("Cargar Imagen")
        btn_load.clicked.connect(self._load_image)
        self._file_path_lbl = QLabel("Sin archivo seleccionado")
        load_row.addWidget(btn_load)
        load_row.addWidget(self._file_path_lbl)
        layout.addLayout(load_row)

        self._img_label = ImageLabel()
        layout.addWidget(self._img_label, stretch=1)

        sel_group = QGroupBox("Selección de Área")
        sg_layout = QVBoxLayout(sel_group)

        shape_row = QHBoxLayout()
        self._radio_rect = QRadioButton("Rectángulo")
        self._radio_rect.setChecked(True)
        self._radio_circle = QRadioButton("Círculo")
        self._radio_rect.toggled.connect(lambda c: self._on_shape_change("rect") if c else None)
        self._radio_circle.toggled.connect(lambda c: self._on_shape_change("circle") if c else None)
        shape_row.addWidget(self._radio_rect)
        shape_row.addWidget(self._radio_circle)
        sg_layout.addLayout(shape_row)

        r, self._s_shape_x, _ = make_slider_row("Pos X", 0, 100, 25)
        sg_layout.addLayout(r)
        self._s_shape_x.valueChanged.connect(self._render)

        r, self._s_shape_y, _ = make_slider_row("Pos Y", 0, 100, 25)
        sg_layout.addLayout(r)
        self._s_shape_y.valueChanged.connect(self._render)

        r, self._s_shape_size, _ = make_slider_row("Tamaño", 5, 80, 30)
        sg_layout.addLayout(r)
        self._s_shape_size.valueChanged.connect(self._render)

        r, self._s_sr, _ = make_slider_row("R", 0, 255, 0)
        sg_layout.addLayout(r)
        self._s_sr.valueChanged.connect(self._update_swatch)
        self._s_sr.valueChanged.connect(self._render)

        r, self._s_sg, _ = make_slider_row("G", 0, 255, 200)
        sg_layout.addLayout(r)
        self._s_sg.valueChanged.connect(self._update_swatch)
        self._s_sg.valueChanged.connect(self._render)

        r, self._s_sb, _ = make_slider_row("B", 0, 255, 0)
        sg_layout.addLayout(r)
        self._s_sb.valueChanged.connect(self._update_swatch)
        self._s_sb.valueChanged.connect(self._render)

        swatch_row = QHBoxLayout()
        swatch_lbl = QLabel("Color:")
        self._swatch = QLabel()
        self._swatch.setFixedSize(24, 16)
        self._swatch.setStyleSheet("background: rgb(0,200,0); border: 1px solid #ccc;")
        swatch_row.addWidget(swatch_lbl)
        swatch_row.addWidget(self._swatch)
        swatch_row.addStretch()
        sg_layout.addLayout(swatch_row)

        layout.addWidget(sel_group)
        return w

    def _build_right_panel(self):
        w = QWidget()
        layout = QVBoxLayout(w)

        cc_group = QGroupBox("Canales de Color")
        cc_l = QVBoxLayout(cc_group)
        r, self._s_img_r, _ = make_slider_row("R", -128, 128, 0)
        cc_l.addLayout(r)
        self._s_img_r.valueChanged.connect(self._render)
        r, self._s_img_g, _ = make_slider_row("G", -128, 128, 0)
        cc_l.addLayout(r)
        self._s_img_g.valueChanged.connect(self._render)
        r, self._s_img_b, _ = make_slider_row("B", -128, 128, 0)
        cc_l.addLayout(r)
        self._s_img_b.valueChanged.connect(self._render)
        layout.addWidget(cc_group)

        blur_group = QGroupBox("Desenfoque Gaussiano")
        bl = QVBoxLayout(blur_group)
        r, self._s_blur, _ = make_slider_row("Blur", 0, 20, 0)
        bl.addLayout(r)
        self._s_blur.valueChanged.connect(self._render)
        layout.addWidget(blur_group)

        sb_group = QGroupBox("Bordes - Sobel")
        sbl = QVBoxLayout(sb_group)
        r, self._s_sobel_x, _ = make_slider_row("Bordes X", 0, 10, 0)
        sbl.addLayout(r)
        self._s_sobel_x.valueChanged.connect(self._render)
        r, self._s_sobel_y, _ = make_slider_row("Bordes Y", 0, 10, 0)
        sbl.addLayout(r)
        self._s_sobel_y.valueChanged.connect(self._render)
        layout.addWidget(sb_group)

        ang_group = QGroupBox("Ángulo de Rotación")
        ang_l = QVBoxLayout(ang_group)
        
        wheel_row = QHBoxLayout()
        self._wheel = AngleWheel()
        self._wheel.angleChanged.connect(self._on_wheel_angle)
        self._wheel_lbl = QLabel("0°")
        self._wheel_lbl.setAlignment(Qt.AlignCenter)
        wheel_row.addStretch()
        wheel_row.addWidget(self._wheel)
        wheel_row.addWidget(self._wheel_lbl)
        wheel_row.addStretch()
        ang_l.addLayout(wheel_row)

        r, self._s_angle, _ = make_slider_row("Ángulo", -180, 180, 0)
        ang_l.addLayout(r)
        self._s_angle.valueChanged.connect(self._on_slider_angle)
        layout.addWidget(ang_group)

        sep = QFrame()
        sep.setFrameShape(QFrame.HLine)
        layout.addWidget(sep)

        btn_apply = QPushButton("Aplicar Todo")
        btn_apply.clicked.connect(self._render)
        layout.addWidget(btn_apply)

        btn_reset = QPushButton("Restablecer")
        btn_reset.clicked.connect(self._reset_all)
        layout.addWidget(btn_reset)

        layout.addStretch()
        return w

    def _load_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg *.bmp *.tif *.tiff *.webp)")
        if not path:
            return
        img = cv2.imread(path)
        if img is None:
            return
        self._original_image = img.copy()
        self._file_path_lbl.setText(path.split("/")[-1])
        self._render()

    def _on_shape_change(self, shape):
        self._shape = shape
        self._render()

    def _on_wheel_angle(self, angle):
        self._s_angle.blockSignals(True)
        self._s_angle.setValue(angle)
        self._wheel_lbl.setText(f"{angle}°")
        self._s_angle.blockSignals(False)
        self._render()

    def _on_slider_angle(self, angle):
        self._wheel.angle = angle
        self._wheel_lbl.setText(f"{angle}°")
        self._render()

    def _update_swatch(self):
        r = self._s_sr.value()
        g = self._s_sg.value()
        b = self._s_sb.value()
        self._swatch.setStyleSheet(f"background: rgb({r},{g},{b}); border: 1px solid #ccc;")

    def _reset_all(self):
        for slider in [self._s_img_r, self._s_img_g, self._s_img_b,
                       self._s_blur, self._s_sobel_x, self._s_sobel_y,
                       self._s_angle]:
            slider.blockSignals(True)
            slider.setValue(0)
            slider.blockSignals(False)
        self._wheel.angle = 0
        self._wheel_lbl.setText("0°")
        self._render()

    def _render(self, _=None):
        if self._original_image is None:
            return

        img = self._original_image.copy()
        h, w = img.shape[:2]

        angle = self._s_angle.value()
        if angle != 0:
            cx, cy = w / 2, h / 2
            M = cv2.getRotationMatrix2D((cx, cy), angle, 1.0)
            img = cv2.warpAffine(img, M, (w, h), flags=cv2.INTER_LINEAR, borderMode=cv2.BORDER_REPLICATE)

        r_adj = self._s_img_r.value()
        g_adj = self._s_img_g.value()
        b_adj = self._s_img_b.value()
        if r_adj != 0 or g_adj != 0 or b_adj != 0:
            img = img.astype(np.int16)
            img[:, :, 2] = np.clip(img[:, :, 2] + r_adj, 0, 255)
            img[:, :, 1] = np.clip(img[:, :, 1] + g_adj, 0, 255)
            img[:, :, 0] = np.clip(img[:, :, 0] + b_adj, 0, 255)
            img = img.astype(np.uint8)

        d = self._s_blur.value()
        if d > 0:
            ksize = 2 * d + 1
            img = cv2.GaussianBlur(img, (ksize, ksize), -1)

        sx_pct = self._s_shape_x.value()
        sy_pct = self._s_shape_y.value()
        ss_pct = self._s_shape_size.value()
        sr = self._s_sr.value()
        sg = self._s_sg.value()
        sb = self._s_sb.value()

        px = int(sx_pct / 100 * w)
        py = int(sy_pct / 100 * h)
        pw = int(ss_pct / 100 * w)
        ph = int(ss_pct / 100 * h)

        blank_image = np.zeros((h, w, 3), np.uint8)

        if self._shape == "rect":
            blank_image[max(0, py):min(h, py + ph), max(0, px):min(w, px + pw)] = [sb, sg, sr]
        else:
            cx_s = px + pw // 2
            cy_s = py + ph // 2
            cv2.ellipse(blank_image, (cx_s, cy_s), (pw // 2, ph // 2), 0, 0, 360, (sb, sg, sr), -1)

        img = cv2.add(blank_image, img)

        sx_ksize = self._s_sobel_x.value()
        sy_ksize = self._s_sobel_y.value()
        if sx_ksize > 0 or sy_ksize > 0:
            img_gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            ksize_x = max(1, sx_ksize * 2 - 1) if sx_ksize > 0 else 1
            ksize_y = max(1, sy_ksize * 2 - 1) if sy_ksize > 0 else 1
            ksize = max(ksize_x, ksize_y)
            if ksize % 2 == 0:
                ksize += 1

            if sx_ksize > 0 and sy_ksize > 0:
                sobel = cv2.Sobel(img_gray, cv2.CV_64F, 1, 1, ksize=ksize)
            elif sx_ksize > 0:
                sobel = cv2.Sobel(img_gray, cv2.CV_64F, 1, 0, ksize=ksize)
            else:
                sobel = cv2.Sobel(img_gray, cv2.CV_64F, 0, 1, ksize=ksize)

            img = sobel

        self._img_label.set_cv_image(img)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    window = OpenCVEditor()
    window.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()