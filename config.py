"""
Configuraciones y constantes para la aplicación Minecraft World Sync.
"""
import os
import platform
from pathlib import Path

# Rutas principales
ONEDRIVE_ROOT = Path(".")  # Esto se configurará dinámicamente
APP_DIR = ONEDRIVE_ROOT / "app"
WORLD_SYNC_DIR = ONEDRIVE_ROOT / "world_sync"
MODS_DIR = ONEDRIVE_ROOT / "mods"

# Archivos de metadatos
MUNDOS_JSON = WORLD_SYNC_DIR / "mundos.json"
MODS_JSON = MODS_DIR / "mods.json"

# Ruta a la carpeta .minecraft (varía según sistema operativo)
def get_minecraft_dir():
    """Obtiene la ruta a la carpeta .minecraft según el sistema operativo."""
    if platform.system() == "Windows":
        return Path(os.path.expanduser("~")) / "AppData" / "Roaming" / ".minecraft"
    elif platform.system() == "Darwin":  # macOS
        return Path(os.path.expanduser("~")) / "Library" / "Application Support" / "minecraft"
    else:
        return Path(os.path.expanduser("~")) / ".minecraft"

MINECRAFT_DIR = get_minecraft_dir()
MINECRAFT_SAVES_DIR = MINECRAFT_DIR / "saves"
MINECRAFT_MODS_DIR = MINECRAFT_DIR / "mods"

# Configuración de la aplicación
APP_NAME = "Minecraft World Sync"
APP_VERSION = "1.0.0"
APP_WINDOW_SIZE = "800x600"

# Colores y estilos
PRIMARY_COLOR = "#4CAF50"  # Verde
SECONDARY_COLOR = "#2196F3"  # Azul
TEXT_COLOR = "#212121"  # Casi negro
BACKGROUND_COLOR = "#F5F5F5"  # Gris muy claro
WARNING_COLOR = "#FFC107"  # Amarillo
ERROR_COLOR = "#F44336"  # Rojo

# Nombres de pantallas
SCREEN_MAIN = "main"
SCREEN_HOST = "host"
SCREEN_MODS = "mods"