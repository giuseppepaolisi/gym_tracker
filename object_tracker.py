import cv2
import os
import numpy as np
import matplotlib.pyplot as plt
from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QVBoxLayout, QPushButton, QFileDialog, QSlider, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QEventLoop, QTimer
from PyQt5.QtGui import QImage, QPixmap

# Classe ROISelector per la selezione di una regione di interesse (ROI) in un'immagine
class ROISelector(QMainWindow):
    # Segnale personalizzato che emette una tupla (il bounding box selezionato)
    roi_selected = pyqtSignal(tuple)

    def __init__(self, image):
        super().__init__()
        self.image = image  # Salva l'immagine da cui selezionare la ROI
        self.roi = None  # Inizializza la variabile per memorizzare il bounding box selezionato
        self.setWindowTitle("Select ROI")
        self.setGeometry(100, 100, image.shape[1], image.shape[0])

        self.label = QLabel(self)  # Etichetta per visualizzare l'immagine
        self.setCentralWidget(self.label)
        self.display_image()

    # Metodo per visualizzare l'immagine
    def display_image(self):
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

    # Metodo chiamato quando si preme il mouse
    def mousePressEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.start_point = (event.x(), event.y())  # Salva il punto iniziale del bounding box

    # Metodo chiamato quando si muove il mouse
    def mouseMoveEvent(self, event):
        if hasattr(self, 'start_point'):
            end_point = (event.x(), event.y())
            temp_image = self.image.copy()
            cv2.rectangle(temp_image, self.start_point, end_point, (0, 255, 0), 2)
            self.display_image_with_rectangle(temp_image)

    # Metodo chiamato quando si rilascia il mouse
    def mouseReleaseEvent(self, event):
        if event.button() == Qt.LeftButton:
            self.end_point = (event.x(), event.y())
            self.roi = (self.start_point[0], self.start_point[1], self.end_point[0] - self.start_point[0], self.end_point[1] - self.start_point[1])
            self.roi_selected.emit(self.roi)  # Emissione del segnale con la ROI selezionata
            self.close()  # Chiude la finestra

    # Metodo per visualizzare l'immagine con un rettangolo (bounding box) disegnato sopra
    def display_image_with_rectangle(self, image):
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

    # Metodo per ottenere la ROI selezionata
    def get_roi(self):
        return self.roi

# Classe TrackingWindow per la finestra di tracciamento degli oggetti nel video
class TrackingWindow(QMainWindow):
    # Segnale personalizzato per indicare che il tracciamento è stato annullato
    tracking_cancelled = pyqtSignal()

    def __init__(self, video_path, tracker):
        super().__init__()
        self.setWindowTitle("Tracking")
        self.setGeometry(100, 100, 800, 600)
        
        self.video_path = video_path
        self.tracker = tracker
        self.cap = cv2.VideoCapture(video_path)  # Cattura del video
        if not self.cap.isOpened():
            print("Error: Could not open video file.")
            return

        self.timer = QTimer(self)  # Timer per aggiornare i frame del video
        self.timer.timeout.connect(self.next_frame)

        self.video_label = QLabel(self)  # Etichetta per visualizzare il video
        self.slider = QSlider(Qt.Horizontal)  # Slider per controllare la posizione del video
        self.slider.sliderMoved.connect(self.set_position)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_tracking)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_video)

        # Layout per i controlli
        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.cancel_button)
        self.controls_layout.addWidget(self.save_button)

        # Layout principale
        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.slider)
        self.layout.addLayout(self.controls_layout)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.out = None  # Variabile per il video writer
        self.positions = []  # Lista per memorizzare le posizioni dell'oggetto tracciato
        self.tracking = True

        self.init_tracking()

    # Metodo per iniziare il tracciamento
    def init_tracking(self):
        ret, frame = self.cap.read()
        if not ret:
            return
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        bbox = self.tracker.select_roi(frame_rgb)

        if bbox is None or bbox[2] <= 0 or bbox[3] <= 0:
            return

        self.tracker.init(frame, bbox)
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        self.out = cv2.VideoWriter('tracked_output.mp4', fourcc, 30.0, (frame.shape[1], frame.shape[0]))
        if not self.out.isOpened():
            print("Error: Could not open video writer.")
            return
        self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
        self.play_video()

    # Metodo per avviare la riproduzione del video
    def play_video(self):
        self.timer.start(30)

    # Metodo per mettere in pausa la riproduzione del video
    def pause_video(self):
        self.timer.stop()

    # Metodo per impostare la posizione del video
    def set_position(self, position):
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)

    # Metodo per aggiornare il frame successivo del video
    def next_frame(self):
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            return

        success, box = self.tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in box]
            self.positions.append((x + w // 2, y + h // 2))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
            # Disegna i punti di tracciamento
            for pos in self.positions:
                cv2.circle(frame, pos, 3, (0, 0, 255), -1)

        if self.out is not None:
            self.out.write(frame)

        self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
        frame_rgb = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
        height, width, channel = frame_rgb.shape
        bytes_per_line = channel * width
        q_img = QImage(frame_rgb.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.video_label.setPixmap(QPixmap.fromImage(q_img))

    # Metodo per annullare il tracciamento
    def cancel_tracking(self):
        self.tracking = False
        self.tracking_cancelled.emit()
        self.close()

    # Metodo per salvare il video tracciato
    def save_video(self):
        filename, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 files (*.mp4)")
        if filename:
            if self.out is not None:
                self.out.release()
            os.rename('tracked_output.mp4', filename)
            self.out = cv2.VideoWriter('tracked_output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (int(self.cap.get(3)), int(self.cap.get(4))))
            if not self.out.isOpened():
                print("Error: Could not open video writer after saving.")
                return

    # Metodo per gestire la chiusura della finestra
    def closeEvent(self, event):
        if self.tracking:
            self.timer.stop()
            if self.cap is not None:
                self.cap.release()
            if self.out is not None:
                self.out.release()
            cv2.destroyAllWindows()
            super().closeEvent(event)

# Classe ObjectTracker per il tracciamento degli oggetti
class ObjectTracker:
    def __init__(self):
        self.tracker = cv2.legacy.TrackerCSRT_create()
        self.bbox = None

    # Metodo per selezionare la ROI
    def select_roi(self, frame):
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        selector = ROISelector(frame)
        loop = QEventLoop()
        selector.roi_selected.connect(loop.quit)
        selector.show()
        loop.exec_()  # Avvia un ciclo di eventi locale
        return selector.get_roi()

    # Metodo per avviare il tracciamento
    def track(self, video_path):
        self.tracking_window = TrackingWindow(video_path, self)
        self.tracking_window.tracking_cancelled.connect(self.cancel_tracking)
        self.tracking_window.show()

    # Metodo per inizializzare il tracker
    def init(self, frame, bbox):
        if bbox[2] <= 0 or bbox[3] <= 0:
            raise ValueError("Invalid bounding box dimensions.")
        self.tracker.init(frame, bbox)

    # Metodo per aggiornare il tracker
    def update(self, frame):
        return self.tracker.update(frame)

    # Metodo per annullare il tracciamento
    def cancel_tracking(self):
        self.tracking_window.close()
