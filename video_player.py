import cv2
import numpy as np
import os
from PyQt5.QtWidgets import QWidget, QVBoxLayout, QHBoxLayout, QPushButton, QFileDialog, QLabel, QSlider, QApplication, QDesktopWidget, QGridLayout
from PyQt5.QtCore import Qt, QTimer
from PyQt5.QtGui import QImage, QPixmap, QIcon
from object_tracker import ObjectTracker

# Definizione della classe VideoPlayer che eredita da QWidget
class VideoPlayer(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle('Gym Tracker')
        self.setMinimumSize(800, 600)  # Imposta una dimensione minima per la finestra

        # Creazione dei widget dell'interfaccia utente
        self.video_label = QLabel()
        self.slider = QSlider(Qt.Horizontal)
        self.slider.sliderMoved.connect(self.set_position)

        self.open_button = QPushButton('Open Video')
        self.open_button.clicked.connect(self.open_file)

        self.play_button = QPushButton()
        self.play_button.setIcon(QIcon(self.resource_path('play.png')))
        self.play_button.clicked.connect(self.play_video)

        self.pause_button = QPushButton()
        self.pause_button.setIcon(QIcon(self.resource_path('pause.png')))
        self.pause_button.clicked.connect(self.pause_video)

        self.track_button = QPushButton('Track Object')
        self.track_button.clicked.connect(self.track_object)

        self.back_button = QPushButton('Back to Original Video')
        self.back_button.clicked.connect(self.back_to_original)
        self.back_button.setEnabled(False)  # Disabilitato inizialmente

        # Disposizione dei layout
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

        # Inizializzazione delle variabili
        self.cap = None
        self.original_cap = None
        self.timer = QTimer(self)
        self.timer.timeout.connect(self.next_frame_slot)
        self.tracker = ObjectTracker()

        # Ottieni la dimensione dello schermo
        self.screen_rect = QApplication.desktop().screenGeometry()

    # Metodo per ottenere il percorso assoluto di una risorsa
    def resource_path(self, relative_path):
        """ Ottieni il percorso assoluto della risorsa, funziona per dev e per PyInstaller """
        base_path = os.path.abspath(".")
        return os.path.join(base_path, relative_path)

    # Metodo per aprire un file video
    def open_file(self):
        filename, _ = QFileDialog.getOpenFileName(self, "Open Video")
        if filename != '':
            self.cap = cv2.VideoCapture(filename)
            if not self.cap.isOpened():
                print("Error: Could not open video file.")
                return
            self.original_cap = filename  # Salva il nome del file invece dell'oggetto capture
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.adjust_window_size()
            self.back_button.setEnabled(False)  # Disabilita il pulsante back quando si apre un nuovo video

    # Metodo per regolare la dimensione della finestra in base alle dimensioni del video
    def adjust_window_size(self):
        if self.cap and self.cap.isOpened():
            width = int(self.cap.get(cv2.CAP_PROP_FRAME_WIDTH))
            height = int(self.cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
            window_height = height + 100

            # Assicurarsi che l'altezza della finestra non superi l'altezza dello schermo
            if window_height > self.screen_rect.height():
                window_height = self.screen_rect.height() - 100

            self.setFixedSize(width, window_height)

    # Metodo per riprodurre il video
    def play_video(self):
        if self.cap and self.cap.isOpened():
            self.timer.start(30)

    # Metodo per mettere in pausa il video
    def pause_video(self):
        if self.cap and self.cap.isOpened():
            self.timer.stop()

    # Metodo per aggiornare il frame successivo
    def next_frame_slot(self):
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

    # Metodo per impostare la posizione del video
    def set_position(self, position):
        if self.cap:
            self.cap.set(cv2.CAP_PROP_POS_FRAMES, position)

    # Metodo per tracciare un oggetto nel video
    def track_object(self):
        if self.original_cap:
            self.pause_video()  # Mette in pausa il video durante il tracciamento dell'oggetto
            self.tracker.track(self.original_cap)
            self.cap = cv2.VideoCapture('tracked_output.mp4')  # Carica il video tracciato
            if not self.cap.isOpened():
                print("Error: Could not open tracked video file.")
                return
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.back_button.setEnabled(True)  # Abilita il pulsante back dopo il tracciamento

    # Metodo per tornare al video originale
    def back_to_original(self):
        if self.original_cap:
            self.pause_video()
            self.cap.release()  # Rilascia la cattura del video tracciato
            self.cap = cv2.VideoCapture(self.original_cap)  # Riapre il video originale
            if not self.cap.isOpened():
                print("Error: Could not open original video file.")
                return
            self.slider.setMaximum(int(self.cap.get(cv2.CAP_PROP_FRAME_COUNT)))
            self.back_button.setEnabled(False)  # Disabilita il pulsante back quando si torna al video originale

# Esecuzione del programma principale
if __name__ == '__main__':
    import sys
    from PyQt5.QtWidgets import QApplication
    app = QApplication(sys.argv)
    player = VideoPlayer()
    player.show()
    sys.exit(app.exec_())
