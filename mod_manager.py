"""
Gestor de mods para la aplicación Minecraft World Sync.
Actualmente en fase de desarrollo.
"""
import os
from pathlib import Path

import config
from utils import ensure_dir_exists, load_json, save_json

class ModManager:
    """Clase para gestionar la sincronización de mods de Minecraft."""
    
    def __init__(self):
        """Inicializa el gestor de mods."""
        # Asegurar que existan las carpetas necesarias
        ensure_dir_exists(config.MODS_DIR)
        
        # Cargar lista de mods
        self.mods = load_json(config.MODS_JSON, {"mods": {}})
    
    def get_mod_status(self):
        """
        Retorna el estado de la funcionalidad de mods.
        En este momento, retorna un mensaje de que está en desarrollo.
        """
        return {
            "status": "in_development",
            "message": "La funcionalidad de gestión de mods está en desarrollo."
        }
    
    def get_available_mods(self):
        """
        Retorna una lista de los mods disponibles en el sistema.
        """
        return list(self.mods.get("mods", {}).keys())