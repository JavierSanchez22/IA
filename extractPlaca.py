import sys
import cv2
import numpy as np
import pytesseract
from PyQt5.QtWidgets import (
    QApplication, QMainWindow, QWidget, QLabel, QPushButton,
    QVBoxLayout, QHBoxLayout, QFileDialog, QSizePolicy
)
from PyQt5.QtCore import Qt
from PyQt5.QtGui import QImage, QPixmap

def cv2_to_qpixmap(cv_img):
    if cv_img is None:
        return QPixmap()
    if len(cv_img.shape) == 2:
        h, w = cv_img.shape
        qimg = QImage(cv_img.data, w, h, w, QImage.Format_Grayscale8)
    else:
        img_rgb = cv2.cvtColor(cv_img, cv2.COLOR_BGR2RGB)
        h, w, ch = img_rgb.shape
        qimg = QImage(img_rgb.data, w, h, ch * w, QImage.Format_RGB888)
    return QPixmap.fromImage(qimg.copy())

def identificar_placa(image):
    img_result = image.copy()
    
    gray = cv2.cvtColor(img_result, cv2.COLOR_BGR2GRAY)
    gray_blur = cv2.blur(gray, (3, 3))
    
    canny = cv2.Canny(gray_blur, 150, 200)
    canny = cv2.dilate(canny, None, iterations=1)
    
    contornos, _ = cv2.findContours(canny, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)
    contornos = sorted(contornos, key=cv2.contourArea, reverse=True)[:80]
    
    placa_texto = "No detectada"
    
    for c in contornos:
        x, y, w, h = cv2.boundingRect(c)
        area = w * h
        relAspec = float(w) / h
        
        if 800 < area < 45000 and 1.2 < relAspec < 6.5:
            placa = gray[y:y+h, x:x+w]
            placa_zoom = cv2.resize(placa, (0, 0), fx=2, fy=2, interpolation=cv2.INTER_CUBIC)
            _, placa_bin = cv2.threshold(placa_zoom, 0, 255, cv2.THRESH_BINARY | cv2.THRESH_OTSU)
            
            for img_tess in [placa_zoom, placa_bin]:
                tess_config = '--psm 11 -c tessedit_char_whitelist=ABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
                texto = pytesseract.image_to_string(img_tess, config=tess_config).strip()
                texto_limpio = "".join(filter(str.isalnum, texto)).upper()
                
                for i in range(len(texto_limpio)):
                    if texto_limpio[i] == 'P':
                        candidato = texto_limpio[i:i+7]
                        if len(candidato) >= 6 and "PNC" not in candidato:
                            if sum(char.isdigit() for char in candidato) >= 1:
                                placa_texto = candidato
                                cv2.rectangle(img_result, (x, y), (x+w, y+h), (0, 255, 0), 3)
                                cv2.putText(img_result, candidato, (x, y - 10), cv2.FONT_HERSHEY_SIMPLEX, 1.2, (0, 255, 0), 3)
                                return placa_texto, img_result
                        
    return placa_texto, img_result

class ImageLabel(QLabel):
    def __init__(self):
        super().__init__()
        self.setAlignment(Qt.AlignCenter)
        self.setMinimumSize(800, 600)
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

class ALPRWindow(QMainWindow):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Detector de Placas Automotrices")
        self.resize(1200, 900)
        self._build_ui()

    def _build_ui(self):
        central = QWidget()
        self.setCentralWidget(central)
        layout = QVBoxLayout(central)

        top_layout = QHBoxLayout()
        btn_load = QPushButton("Cargar Imagen del Vehículo")
        btn_load.setMinimumHeight(45)
        btn_load.clicked.connect(self._process_image)
        self.lbl_result = QLabel("Placa Detectada: N/A")
        self.lbl_result.setStyleSheet("font-size: 24px; font-weight: bold; color: #0078D7;")
        
        top_layout.addWidget(btn_load)
        top_layout.addStretch()
        top_layout.addWidget(self.lbl_result)
        
        layout.addLayout(top_layout)

        self.img_view = ImageLabel()
        layout.addWidget(self.img_view, stretch=1)

    def _process_image(self):
        path, _ = QFileDialog.getOpenFileName(self, "Seleccionar imagen", "", "Imágenes (*.png *.jpg *.jpeg)")
        if not path:
            return

        image = cv2.imread(path)
        if image is None:
            return

        h, w = image.shape[:2]
        new_w = 800
        new_h = int((new_w / w) * h)
        image_resized = cv2.resize(image, (new_w, new_h))

        texto_placa, imagen_procesada = identificar_placa(image_resized)

        self.lbl_result.setText(f"Placa Detectada: {texto_placa}")
        self.img_view.set_cv_image(imagen_procesada)

def main():
    app = QApplication(sys.argv)
    app.setStyle("Fusion")
    w = ALPRWindow()
    w.show()
    sys.exit(app.exec_())

if __name__ == "__main__":
    main()