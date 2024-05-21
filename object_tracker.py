import cv2
import os
import numpy as np
from PyQt5.QtWidgets import QMainWindow, QLabel, QApplication, QVBoxLayout, QPushButton, QFileDialog, QSlider, QWidget, QHBoxLayout
from PyQt5.QtCore import Qt, pyqtSignal, QEventLoop, QTimer
from PyQt5.QtGui import QImage, QPixmap

class ROISelector(QMainWindow):
    roi_selected = pyqtSignal(tuple)

    def __init__(self, image):
        super().__init__()
        self.image = image
        self.roi = None
        self.setWindowTitle("Select ROI")
        self.setGeometry(100, 100, image.shape[1], image.shape[0])

        self.label = QLabel(self)
        self.setCentralWidget(self.label)
        self.display_image()

    def display_image(self):
        """Visualizza l'immagine nella finestra."""
        height, width, channel = self.image.shape
        bytes_per_line = 3 * width
        q_img = QImage(self.image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

    def mousePressEvent(self, event):
        """Gestisce l'evento di pressione del mouse per iniziare la selezione della ROI."""
        if event.button() == Qt.LeftButton:
            self.start_point = (event.x(), event.y())

    def mouseMoveEvent(self, event):
        """Gestisce l'evento di movimento del mouse per aggiornare la selezione della ROI."""
        if hasattr(self, 'start_point'):
            end_point = (event.x(), event.y())
            temp_image = self.image.copy()
            cv2.rectangle(temp_image, self.start_point, end_point, (0, 255, 0), 2)
            self.display_image_with_rectangle(temp_image)

    def mouseReleaseEvent(self, event):
        """Gestisce l'evento di rilascio del mouse per completare la selezione della ROI."""
        if event.button() == Qt.LeftButton:
            self.end_point = (event.x(), event.y())
            self.roi = (self.start_point[0], self.start_point[1], self.end_point[0] - self.start_point[0], self.end_point[1] - self.start_point[1])
            self.roi_selected.emit(self.roi)
            self.close()

    def display_image_with_rectangle(self, image):
        """Visualizza l'immagine con un rettangolo (ROI) disegnato sopra."""
        height, width, channel = image.shape
        bytes_per_line = 3 * width
        q_img = QImage(image.data, width, height, bytes_per_line, QImage.Format_RGB888)
        self.label.setPixmap(QPixmap.fromImage(q_img))

    def get_roi(self):
        """Restituisce la ROI selezionata."""
        return self.roi

class TrackingWindow(QMainWindow):
    tracking_cancelled = pyqtSignal()
    
    def __init__(self, video_path, tracker):
        super().__init__()
        self.setWindowTitle("Tracking")
        self.setGeometry(100, 100, 800, 600)
        
        self.video_path = video_path
        self.tracker = tracker
        self.cap = cv2.VideoCapture(video_path)
        if not self.cap.isOpened():
            print("Error: Could not open video file.")
            return

        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame)

        self.video_label = QLabel(self)
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)
        self.play_button = QPushButton("Play")
        self.play_button.clicked.connect(self.play_video)
        self.pause_button = QPushButton("Pause")
        self.pause_button.clicked.connect(self.pause_video)
        self.cancel_button = QPushButton("Cancel")
        self.cancel_button.clicked.connect(self.cancel_tracking)
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.save_video)

        self.controls_layout = QHBoxLayout()
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.cancel_button)
        self.controls_layout.addWidget(self.save_button)

        self.layout = QVBoxLayout()
        self.layout.addWidget(self.video_label)
        self.layout.addWidget(self.slider)
        self.layout.addLayout(self.controls_layout)

        container = QWidget()
        container.setLayout(self.layout)
        self.setCentralWidget(container)

        self.out = None
        self.positions = []
        self.tracking = True

        self.init_tracking()

    def init_tracking(self):
        """Inizia il tracciamento dell'oggetto nel video."""
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

    def play_video(self):
        """Avvia la riproduzione del video."""
        self.timer.start(30)

    def pause_video(self):
        """Mette in pausa la riproduzione del video."""
        self.timer.stop()

    def set_position(self, position):
        """Imposta la posizione corrente del video."""
        self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)

    def next_frame(self):
        """Aggiorna il frame successivo del video."""
        ret, frame = self.cap.read()
        if not ret:
            self.timer.stop()
            return

        success, box = self.tracker.update(frame)
        if success:
            x, y, w, h = [int(v) for v in box]
            self.positions.append((x + w // 2, y + h // 2))
            cv2.rectangle(frame, (x, y), (x + w, y + h), (0, 255, 0), 2)
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

    def cancel_tracking(self):
        """Annulla il tracciamento."""
        self.tracking = False
        self.tracking_cancelled.emit()
        self.close()

    def save_video(self):
        """Salva il video tracciato."""
        filename, _ = QFileDialog.getSaveFileName(self, "Save Video", "", "MP4 files (*.mp4)")
        if filename:
            if self.out is not None:
                self.out.release()
            os.rename('tracked_output.mp4', filename)
            self.out = cv2.VideoWriter('tracked_output.mp4', cv2.VideoWriter_fourcc(*'mp4v'), 30.0, (int(self.cap.get(3)), int(self.cap.get(4))))
            if not self.out.isOpened():
                print("Error: Could not open video writer after saving.")
                return

    def closeEvent(self, event):
        """Gestisce la chiusura della finestra."""
        if self.tracking:
            self.timer.stop()
            if self.cap is not None:
                self.cap.release()
            if self.out is not None:
                self.out.release()
            cv2.destroyAllWindows()
            super().closeEvent(event)

class ObjectTracker:
    def __init__(self):
        self.tracker = cv2.legacy.TrackerCSRT_create()
        self.bbox = None

    def select_roi(self, frame):
        """Seleziona una ROI nell'immagine."""
        app = QApplication.instance()
        if app is None:
            app = QApplication([])

        selector = ROISelector(frame)
        loop = QEventLoop()
        selector.roi_selected.connect(loop.quit)
        selector.show()
        loop.exec_()
        return selector.get_roi()

    def track(self, video_path):
        """Avvia il tracciamento del video."""
        self.tracking_window = TrackingWindow(video_path, self)
        self.tracking_window.tracking_cancelled.connect(self.cancel_tracking)
        self.tracking_window.show()

    def init(self, frame, bbox):
        """Inizializza il tracker con il frame e la ROI."""
        if bbox[2] <= 0 or bbox[3] <= 0:
            raise ValueError("Invalid bounding box dimensions.")
        self.tracker.init(frame, bbox)

    def update(self, frame):
        """Aggiorna il tracker con il frame corrente."""
        return self.tracker.update(frame)

    def cancel_tracking(self):
        """Annulla il tracciamento."""
        self.tracking_window.close()
