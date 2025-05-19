"""
Funciones de utilidad para la aplicación Minecraft World Sync.
"""
import json
import os
import platform
import uuid
import shutil
from pathlib import Path
from datetime import datetime

def get_computer_id():
    """
    Genera un identificador único para la computadora basado en hardware.
    Si no existe, crea uno nuevo y lo guarda.
    """
    id_file = Path(os.path.expanduser("~")) / ".minecraft_sync_id"
    
    if id_file.exists():
        with open(id_file, 'r') as f:
            return f.read().strip()
    else:
        # Generar ID basado en información de hardware + un UUID
        system_info = platform.node() + platform.processor()
        new_id = f"{system_info.replace(' ', '-')}_{uuid.uuid4().hex[:8]}"
        
        # Guardar el ID para uso futuro
        with open(id_file, 'w') as f:
            f.write(new_id)
        
        return new_id

def ensure_dir_exists(directory):
    """Asegura que el directorio exista, creándolo si es necesario."""
    Path(directory).mkdir(parents=True, exist_ok=True)

def load_json(file_path, default=None):
    """
    Carga un archivo JSON. Si no existe o hay error, devuelve el valor predeterminado.
    """
    if default is None:
        default = {}
    
    try:
        if not Path(file_path).exists():
            return default
        
        with open(file_path, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Error al cargar {file_path}: {e}")
        return default

def save_json(file_path, data):
    """Guarda datos en un archivo JSON."""
    ensure_dir_exists(Path(file_path).parent)
    
    with open(file_path, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def copy_directory(src, dst):
    """Copia el contenido de un directorio a otro."""
    # Asegurar que el directorio destino exista
    ensure_dir_exists(dst)
    
    # Copiar archivos y subdirectorios
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        
        if os.path.isdir(s):
            shutil.copytree(s, d, dirs_exist_ok=True)
        else:
            shutil.copy2(s, d)

def get_timestamp():
    """Obtiene una marca de tiempo en formato legible."""
    return datetime.now().strftime("%Y-%m-%d %H:%M:%S")

def compare_timestamps(timestamp1, timestamp2):
    """Compara dos marcas de tiempo y devuelve la más reciente."""
    dt1 = datetime.strptime(timestamp1, "%Y-%m-%d %H:%M:%S")
    dt2 = datetime.strptime(timestamp2, "%Y-%m-%d %H:%M:%S")
    
    if dt1 > dt2:
        return 1
    elif dt1 < dt2:
        return -1
    else:
        return 0