import tkinter as tk
from gui_app import WidevoiceDownloaderGUI
import logging # Importamos o módulo logging
import os # Precisamos de os para criar o diretório de logs

# Configurar o diretório para logs
LOG_DIR = "logs"
os.makedirs(LOG_DIR, exist_ok=True) # Garante que o diretório de logs exista
LOG_FILE = os.path.join(LOG_DIR, "widevoice_downloader.log")

def setup_logging():
    """Configura o sistema de logging."""
    logging.basicConfig(
        level=logging.INFO, # Define o nível mínimo de logging (INFO, DEBUG, WARNING, ERROR, CRITICAL)
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', # Define o formato das mensagens
        handlers=[
            logging.FileHandler(LOG_FILE), # Envia logs para um arquivo
            logging.StreamHandler()        # Envia logs para o console
        ]
    )
    # Opcional: Desativar logs de bibliotecas externas se forem muito verbosos
    # logging.getLogger("requests").setLevel(logging.WARNING)
    # logging.getLogger("urllib3").setLevel(logging.WARNING)


def main():
    """Configura o logging, cria a janela principal da GUI e inicia o loop."""
    setup_logging() # Configura o logging antes de iniciar a GUI

    # Adiciona uma mensagem inicial ao log
    logging.info("Iniciando o aplicativo Widevoice Downloader GUI.")

    root = tk.Tk()
    app = WidevoiceDownloaderGUI(root)
    root.mainloop()

    logging.info("Aplicativo Widevoice Downloader GUI finalizado.")


# Executar a função principal se o script for rodado diretamente
if __name__ == "__main__":
    main()