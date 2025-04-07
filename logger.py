# logger.py
import logging
import sys

# Crear el logger
logger = logging.getLogger("chatbot")
logger.setLevel(logging.INFO)

# Evitar duplicar handlers
if not logger.hasHandlers():
    # Handler para consola, compatible con UTF-8 en Windows
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(logging.INFO)
    console_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    console_handler.setFormatter(console_formatter)

    # Handler para archivo con codificación UTF-8
    file_handler = logging.FileHandler("app.log", encoding="utf-8")
    file_handler.setLevel(logging.INFO)
    file_formatter = logging.Formatter(
        "%(asctime)s - %(levelname)s - %(message)s"
    )
    file_handler.setFormatter(file_formatter)

    # Agregar handlers al logger
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
