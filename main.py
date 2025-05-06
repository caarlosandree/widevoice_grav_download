import tkinter as tk
# from gui_app import WidevoiceDownloaderGUI # Remova esta linha
import logging
import os

# Importe ttkbootstrap e o GUI_APP modificado
import ttkbootstrap as ttk # Importe ttkbootstrap
from gui_app import WidevoiceDownloaderGUI # Mantenha a importação da classe GUI

# Configurar o diretório para logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True)
LOG_FILE = os.path.join(LOG_DIR, "widevoice_downloader.log")

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        handlers=[
            logging.FileHandler(LOG_FILE),
            logging.StreamHandler()
        ]
    )
    # Opcional: Desativar logs de bibliotecas externas se forem muito verbosos
    # logging.getLogger("requests").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Configura o logging, cria a janela principal da GUI com ttkbootstrap e inicia o loop."""
    setup_logging()
    logging.info("Iniciando o aplicativo Widevoice Downloader GUI.")

    # Altere de tk.Tk() para ttk.Window()
    # Você pode escolher um tema aqui. Alguns exemplos:
    # 'cosmo', 'flatly', 'journal', 'lumen', 'paper', 'sandstone', 'simplex', 'united'
    # ' darkly', 'cyborg', 'solar', 'superhero', 'united' (temas escuros)
    root = ttk.Window(themename="cosmo") # Exemplo com o tema 'cosmo'

    app = WidevoiceDownloaderGUI(root)
    root.mainloop()

    logging.info("Aplicativo Widevoice Downloader GUI finalizado.")


if __name__ == "__main__":
    main()