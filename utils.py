import os

def resource_path(relative_path):
    """Ottiene il percorso assoluto della risorsa, funziona per dev e per PyInstaller."""
    base_path = os.path.abspath(".")
    return os.path.join(base_path, relative_path)
