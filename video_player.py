import cv2
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSlider, QApplication, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QIcon
from object_tracker import ObjectTracker
from utils import resource_path

class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.init_ui()
        self.cap = None
        self.original_cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame_slot)
        self.tracker = ObjectTracker()
        self.screen_rect = QApplication.desktop().screenGeometry()

    def init_ui(self):
        """Inizializza l'interfaccia utente."""
        self.setWindowTitle('Gym Tracker')
        self.setMinimumSize(800, 600)
        
        self.video_label = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)

        self.open_button = QPushButton('Open Video')
        self.open_button.clicked.connect(self.open_file)

        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon(resource_path('icons/play.png')))
        self.play_button.clicked.connect(self.play_video)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(QIcon(resource_path('icons/pause.png')))
        self.pause_button.clicked.connect(self.pause_video)

        self.track_button = QPushButton('Track Object')
        self.track_button.clicked.connect(self.track_object)

        self.back_button = QPushButton('Back to Original Video')
        self.back_button.clicked.connect(self.back_to_original)
        self.back_button.setEnabled(False)

        self.layout = QVBoxLayout()
        self.controls_layout = QHBoxLayout()
        self.video_layout = QVBoxLayout()
        self.grid_layout = QGridLayout()

        self.video_layout.addWidget(self.video_label)
        self.video_layout.addWidget(self.slider)

        self.controls_layout.addWidget(self.open_button)
        self.controls_layout.addWidget(self.play_button)
        self.controls_layout.addWidget(self.pause_button)
        self.controls_layout.addWidget(self.track_button)
        self.controls_layout.addWidget(self.back_button)

        self.grid_layout.addLayout(self.video_layout, 0, 0)
        self.grid_layout.addLayout(self.controls_layout, 1, 0)

        self.layout.addLayout(self.grid_layout)
        self.setLayout(self.layout)

    def open_file(self):
        """Apre un file video selezionato dall'utente."""
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename:
            self.cap = cv2.VideoCapture(filename)
            if not self.cap.isOpened():
                print("Error: Could not open video file.")
                return
            self.original_cap = filename
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.adjust_window_size()
            self.back_button.setEnabled(False)

    def adjust_window_size(self):
        """Adatta la dimensione della finestra alle dimensioni del video."""
        if self.cap and self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            window_height = height + 100
            if window_height > self.screen_rect.height():
                window_height = self.screen_rect.height() - 100
            self.setFixedSize(width, window_height)

    def play_video(self):
        """Avvia la riproduzione del video."""
        if self.cap and self.cap.isOpened():
            self.timer.start(30)
    
    def pause_video(self):
        """Mette in pausa la riproduzione del video."""
        if self.cap and self.cap.isOpened():
            self.timer.stop()

    def next_frame_slot(self):
        """Aggiorna il frame successivo del video."""
        if self.cap:
            ret, frame = self.cap.read()
            if ret:
                self.slider.setValue(int(self.cap.get(cv2.CAP_PROP_POS_FRAMES)))
                frame = cv2.cvtColor(frame, cv2.COLOR_BGR2RGB)
                height, width, channel = frame.shape
                step = channel * width
                q_img = QImage(frame.data, width, height, step, QImage.Format_RGB888)
                self.video_label.setPixmap(QPixmap.fromImage(q_img))
            else:
                self.timer.stop()
    
    def set_position(self, position):
        """Imposta la posizione corrente del video."""
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)

    def track_object(self):
        """Avvia il tracciamento di un oggetto nel video."""
        if self.original_cap:
            self.pause_video()
            self.tracker.track(self.original_cap)
            if not os.path.exists('tracked_output.mp4'):
                print("Error: Could not open tracked video file.")
                return
            self.cap = cv2.VideoCapture('tracked_output.mp4')
            if not self.cap.isOpened():
                print("Error: Could not open tracked video file.")
                return
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.back_button.setEnabled(True)

    def back_to_original(self):
        """Ritorna al video originale."""
        if self.original_cap:
            self.pause_video()
            self.cap.release()
            self.cap = cv2.VideoCapture(self.original_cap)
            if not self.cap.isOpened():
                print("Error: Could not open original video file.")
                return
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.back_button.setEnabled(False)
