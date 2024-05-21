import sys
from PyQt5.QtWidgets import QApplication
from video_player import VideoPlayer

# Definizione della funzione principale
def main():
    # Creazione dell'oggetto QApplication, necessario per qualsiasi applicazione PyQt
    app = QApplication(sys.argv)
    
    # Creazione di un'istanza della classe VideoPlayer
    player = VideoPlayer()
    
    # Visualizzazione della finestra del player
    player.show()
    
    # Avvio del ciclo di eventi dell'applicazione. L'app rimarrà in esecuzione finché non verrà chiusa.
    sys.exit(app.exec_())

# Controllo se lo script è eseguito direttamente (non importato come modulo)
if __name__ == '__main__':
    main()  # Chiamata alla funzione principale per avviare l'applicazione
