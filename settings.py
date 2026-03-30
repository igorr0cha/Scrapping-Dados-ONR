import os
import sys
from dotenv import load_dotenv


class Settings:
    def __init__(self):
        # Lógica para encontrar o .env dentro do .exe ou na pasta normal
        if getattr(sys, "frozen", False):
            # Se estiver rodando como EXE (PyInstaller)
            base_path = sys._MEIPASS # type: ignore
        else:
            # Se estiver rodando no VS Code
            base_path = os.getcwd()

        env_path = os.path.join(base_path, ".env")
        load_dotenv(dotenv_path=env_path)

        # Banco de Dados
        self.DB_SERVER = os.getenv("DB_SERVER", "192.168.32.3")
        self.DB_NAME = os.getenv("DB_NAME", "DBSGI")
        self.DB_USER = os.getenv("DB_USER")
        self.DB_PASS = os.getenv("DB_PASS")




settings = Settings()
