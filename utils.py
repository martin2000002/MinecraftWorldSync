"""
Funciones de utilidad para la aplicación Minecraft World Sync.
"""
import json
import os
import platform
import uuid
import shutil
import hashlib
import filecmp
import time
from datetime import datetime
from pathlib import Path

def get_computer_id():
    """
    Genera un identificador único para la computadora.
    Si no existe, crea uno nuevo y lo guarda.
    Ahora genera un identificador corto (máximo 5 caracteres) para evitar
    problemas con rutas demasiado largas.
    """
    id_file = Path(os.path.expanduser("~")) / ".minecraft_sync_id"
    
    if id_file.exists():
        with open(id_file, 'r') as f:
            return f.read().strip()
    else:
        # Generar un hash corto basado en información de hardware
        system_info = platform.node() + platform.processor()
        
        # Usar hashlib para generar un identificador corto pero único
        hash_obj = hashlib.md5(system_info.encode())
        new_id = hash_obj.hexdigest()[:5]  # Solo usar los primeros 5 caracteres del hash
        
        # Guardar el ID para uso futuro
        with open(id_file, 'w') as f:
            f.write(new_id)
        
        return new_id

def get_computer_name():
    """
    Recupera el nombre amigable de la computadora.
    Si no existe, retorna None (para que la aplicación solicite uno).
    """
    name_file = Path(os.path.expanduser("~")) / ".minecraft_sync_name"
    
    if name_file.exists():
        with open(name_file, 'r', encoding='utf-8') as f:
            return f.read().strip()
    return None

def save_computer_name(name):
    """
    Guarda el nombre amigable de la computadora.
    """
    name_file = Path(os.path.expanduser("~")) / ".minecraft_sync_name"
    
    with open(name_file, 'w', encoding='utf-8') as f:
        f.write(name)

def get_computer_display_name():
    """
    Retorna el nombre para mostrar de la computadora.
    Si hay un nombre guardado, lo usa; si no, usa el ID.
    """
    name = get_computer_name()
    if name:
        return name
    return get_computer_id()

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
    """
    Copia el contenido de un directorio a otro.
    Maneja mejor los errores para proveer más información.
    """
    # Asegurar que el directorio destino exista
    ensure_dir_exists(dst)
    
    errors = []
    
    # Copiar archivos y subdirectorios
    for item in os.listdir(src):
        s = os.path.join(src, item)
        d = os.path.join(dst, item)
        
        try:
            if os.path.isdir(s):
                ensure_dir_exists(d)  # Asegurar que el directorio destino existe primero
                shutil.copytree(s, d, dirs_exist_ok=True)
            else:
                # Asegurar que el directorio padre del archivo destino exista
                ensure_dir_exists(os.path.dirname(d))
                shutil.copy2(s, d)
        except Exception as e:
            print(f"No se pudo copiar {s} a {d}: {e}")
            errors.append((s, d, str(e)))
    
    if errors:
        print(f"Error copiando directorio: {len(errors)} errores")
        raise Exception(errors)

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

def compare_directories(dir1, dir2):
    """
    Compara dos directorios para determinar si tienen diferencias.
    Retorna un diccionario con información sobre las diferencias.
    
    La comparación tiene en cuenta:
    - Archivos que existen en dir1 pero no en dir2
    - Archivos que existen en dir2 pero no en dir1
    - Archivos con el mismo nombre pero contenido diferente
    - Carpetas adicionales en cada directorio
    
    Ignora ciertos archivos que Minecraft actualiza constantemente pero no son relevantes
    para la sincronización (como archivos de sesión o temporales).
    """
    result = {
        "identical": True,
        "differences": {
            "files_only_in_dir1": [],
            "files_only_in_dir2": [],
            "modified_files": [],
            "dirs_only_in_dir1": [],
            "dirs_only_in_dir2": []
        },
        "has_important_changes": False
    }
    
    # Archivos y carpetas a ignorar (patrones)
    ignore_patterns = [
        'session.lock',
        '.DS_Store',
        'Thumbs.db',
        '*.tmp'
    ]
    
    # Convertir a objetos Path
    dir1_path = Path(dir1)
    dir2_path = Path(dir2)
    
    # Verificar si los directorios existen
    if not dir1_path.exists() or not dir2_path.exists():
        result["identical"] = False
        result["has_important_changes"] = True
        return result
    
    # Función para determinar si un archivo debe ser ignorado
    def should_ignore(path):
        name = os.path.basename(path)
        return any(name == pattern or (pattern.startswith('*') and name.endswith(pattern[1:])) for pattern in ignore_patterns)
    
    # Función para comparar un directorio y sus subdirectorios
    def compare_dirs(subdir1, subdir2, rel_path=""):
        nonlocal result
        
        # Obtener listas de archivos y carpetas en ambos directorios
        dir1_items = os.listdir(subdir1)
        dir2_items = os.listdir(subdir2)
        
        # Crear conjuntos para facilitar comparaciones
        dir1_set = set(dir1_items)
        dir2_set = set(dir2_items)
        
        # Elementos únicos en cada directorio
        only_in_dir1 = dir1_set - dir2_set
        only_in_dir2 = dir2_set - dir1_set
        
        # Comprobar elementos únicos en dir1
        for item in only_in_dir1:
            item_path = os.path.join(subdir1, item)
            rel_item_path = os.path.join(rel_path, item)
            
            if os.path.isdir(item_path):
                result["differences"]["dirs_only_in_dir1"].append(rel_item_path)
                result["identical"] = False
                # Considerar carpetas adicionales como cambios importantes
                result["has_important_changes"] = True
            elif not should_ignore(item):
                result["differences"]["files_only_in_dir1"].append(rel_item_path)
                result["identical"] = False
                # Archivos adicionales siempre son cambios importantes
                result["has_important_changes"] = True
        
        # Comprobar elementos únicos en dir2
        for item in only_in_dir2:
            item_path = os.path.join(subdir2, item)
            rel_item_path = os.path.join(rel_path, item)
            
            if os.path.isdir(item_path):
                result["differences"]["dirs_only_in_dir2"].append(rel_item_path)
                result["identical"] = False
                # Considerar carpetas adicionales como cambios importantes
                result["has_important_changes"] = True
            elif not should_ignore(item):
                result["differences"]["files_only_in_dir2"].append(rel_item_path)
                result["identical"] = False
                # Archivos adicionales siempre son cambios importantes
                result["has_important_changes"] = True
        
        # Comprobar elementos comunes
        common_items = dir1_set.intersection(dir2_set)
        for item in common_items:
            item1_path = os.path.join(subdir1, item)
            item2_path = os.path.join(subdir2, item)
            rel_item_path = os.path.join(rel_path, item)
            
            if os.path.isdir(item1_path) and os.path.isdir(item2_path):
                # Recursivamente comparar subdirectorios
                compare_dirs(item1_path, item2_path, rel_item_path)
            elif os.path.isfile(item1_path) and os.path.isfile(item2_path):
                # Ignorar archivos en la lista de ignorados
                if should_ignore(item):
                    continue
                
                # Comparar archivos
                if not filecmp.cmp(item1_path, item2_path, shallow=False):
                    result["differences"]["modified_files"].append(rel_item_path)
                    result["identical"] = False
                    
                    # Comprobar modificación reciente (últimas 24 horas)
                    mod_time1 = os.path.getmtime(item1_path)
                    mod_time2 = os.path.getmtime(item2_path)
                    current_time = time.time()
                    
                    # Si alguno de los archivos fue modificado recientemente o
                    # sus tamaños son significativamente diferentes, considerar como cambio importante
                    if (current_time - mod_time1 < 86400 or current_time - mod_time2 < 86400 or
                        abs(os.path.getsize(item1_path) - os.path.getsize(item2_path)) > 100):
                        result["has_important_changes"] = True
    
    # Iniciar la comparación recursiva
    compare_dirs(dir1_path, dir2_path)
    
    return result