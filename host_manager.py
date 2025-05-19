"""
Gestor de mundos para la aplicación Minecraft World Sync.
Maneja la sincronización bidireccional de mundos entre computadoras.
"""
import os
import shutil
from pathlib import Path

import config
from utils import (
    get_computer_id, ensure_dir_exists, load_json, save_json,
    copy_directory, get_timestamp, compare_timestamps
)

class HostManager:
    """Clase para gestionar la sincronización de mundos de Minecraft."""
    
    def __init__(self):
        """Inicializa el gestor de mundos."""
        self.computer_id = get_computer_id()
        
        # Asegurar que existan las carpetas necesarias
        ensure_dir_exists(config.WORLD_SYNC_DIR)
        self.computer_dir = config.WORLD_SYNC_DIR / self.computer_id
        ensure_dir_exists(self.computer_dir)
        
        # Cargar lista de mundos
        self.mundos = load_json(config.MUNDOS_JSON, {"mundos": {}})
        
        # Verificar si la carpeta de guardados de Minecraft existe
        if not os.path.exists(config.MINECRAFT_SAVES_DIR):
            raise FileNotFoundError(f"No se encontró la carpeta de guardados de Minecraft en {config.MINECRAFT_SAVES_DIR}")
    
    def get_available_worlds(self):
        """Obtiene la lista de mundos disponibles en el sistema de sincronización."""
        return list(self.mundos.get("mundos", {}).keys())
    
    def get_local_worlds(self):
        """Obtiene la lista de mundos locales en la carpeta de Minecraft."""
        return [d.name for d in os.scandir(config.MINECRAFT_SAVES_DIR) if d.is_dir()]
    
    def check_world_status(self, world_name):
        """
        Verifica el estado de un mundo.
        Retorna un diccionario con información sobre si el mundo está sincronizado,
        si hay una versión más reciente, etc.
        """
        result = {
            "exists_locally": False,
            "exists_in_sync": False,
            "has_latest_version": False,
            "latest_version_info": None,
            "local_version_info": None,
            "conflicts": []
        }
        
        # Verificar si el mundo existe localmente
        local_world_path = config.MINECRAFT_SAVES_DIR / world_name
        result["exists_locally"] = local_world_path.exists()
        
        # Verificar si el mundo existe en el sistema de sincronización
        if world_name in self.mundos.get("mundos", {}):
            result["exists_in_sync"] = True
            
            # Obtener información de la última versión
            latest_info = self.mundos["mundos"][world_name]
            result["latest_version_info"] = latest_info
            
            # Verificar si existe control.json para este mundo en la computadora actual
            local_control_path = self.computer_dir / world_name / "control.json"
            if local_control_path.exists():
                local_control = load_json(local_control_path)
                result["local_version_info"] = local_control
                
                # Comparar versiones basadas en timestamp
                if local_control.get("timestamp") == latest_info.get("timestamp"):
                    result["has_latest_version"] = True
                elif local_control.get("base_commit") != latest_info.get("commit_id"):
                    # Posible conflicto: versiones basadas en diferentes commits
                    result["conflicts"].append({
                        "type": "base_commit_mismatch",
                        "message": "La versión local está basada en un commit diferente al de la última versión"
                    })
            
            # Detectar conflictos potenciales (commits paralelos)
            for pc_id in os.listdir(config.WORLD_SYNC_DIR):
                if pc_id == self.computer_id:
                    continue  # Saltamos nuestra propia PC
                
                pc_control_path = config.WORLD_SYNC_DIR / pc_id / world_name / "control.json"
                if pc_control_path.exists():
                    pc_control = load_json(pc_control_path)
                    
                    # Si hay dos PC con el mismo base_commit pero diferente commit_id,
                    # podría haber un conflicto de versiones paralelas
                    if (pc_control.get("base_commit") == local_control.get("base_commit") and
                        pc_control.get("commit_id") != local_control.get("commit_id") and
                        pc_control.get("timestamp") != local_control.get("timestamp")):
                        result["conflicts"].append({
                            "type": "parallel_commits",
                            "message": f"La PC {pc_id} tiene una versión diferente basada en el mismo commit base",
                            "pc_id": pc_id,
                            "pc_info": pc_control
                        })
        
        return result
    
    def download_world(self, world_name):
        """
        Descarga la última versión de un mundo desde el sistema de sincronización.
        Retorna True si todo salió bien, False en caso de error.
        """
        if world_name not in self.mundos.get("mundos", {}):
            return False, "El mundo no existe en el sistema de sincronización"
        
        # Obtener información de la última versión
        latest_info = self.mundos["mundos"][world_name]
        latest_pc_id = latest_info.get("pc_id")
        
        # Ruta a los datos del mundo en el sistema de sincronización
        source_path = config.WORLD_SYNC_DIR / latest_pc_id / world_name / "minecraft_saves_data"
        if not source_path.exists():
            return False, f"No se encontraron los datos del mundo en {source_path}"
        
        # Ruta local donde se guardarán los datos
        local_world_path = config.MINECRAFT_SAVES_DIR / world_name
        
        # Crear copia de seguridad si el mundo ya existe localmente
        if local_world_path.exists():
            backup_path = config.MINECRAFT_SAVES_DIR / f"{world_name}_backup_{get_timestamp().replace(':', '-').replace(' ', '_')}"
            shutil.copytree(local_world_path, backup_path)
        
        # Copiar datos del mundo a la carpeta local
        if local_world_path.exists():
            shutil.rmtree(local_world_path)
        shutil.copytree(source_path, local_world_path)
        
        # Copiar datos a nuestra carpeta de sincronización
        local_sync_path = self.computer_dir / world_name / "minecraft_saves_data"
        if local_sync_path.exists():
            shutil.rmtree(local_sync_path)
        ensure_dir_exists(local_sync_path.parent)
        shutil.copytree(source_path, local_sync_path)
        
        # Actualizar control.json local con la información más reciente
        local_control = {
            "commit_id": latest_info.get("commit_id"),
            "base_commit": latest_info.get("commit_id"),
            "comment": "Descargado de la última versión",
            "timestamp": get_timestamp(),
            "original_timestamp": latest_info.get("timestamp")
        }
        save_json(self.computer_dir / world_name / "control.json", local_control)
        
        return True, "Mundo descargado correctamente"
    
    def upload_world(self, world_name, comment=""):
        """
        Sube un mundo local al sistema de sincronización.
        Retorna True si todo salió bien, False en caso de error.
        """
        # Verificar si el mundo existe localmente
        local_world_path = config.MINECRAFT_SAVES_DIR / world_name
        if not local_world_path.exists():
            return False, "El mundo no existe localmente"
        
        # Generar un nuevo ID de commit
        import uuid
        new_commit_id = uuid.uuid4().hex[:12]
        
        # Determinar el commit base
        base_commit = None
        if world_name in self.mundos.get("mundos", {}):
            base_commit = self.mundos["mundos"][world_name].get("commit_id")
        
        # Si no hay control.json para este mundo, crearlo
        local_control_path = self.computer_dir / world_name / "control.json"
        if local_control_path.exists():
            local_control = load_json(local_control_path)
            base_commit = local_control.get("commit_id") or base_commit
        
        # Preparar nueva información de control
        timestamp = get_timestamp()
        control_info = {
            "commit_id": new_commit_id,
            "base_commit": base_commit,
            "comment": comment or "Actualización",
            "timestamp": timestamp
        }
        
        # Copiar mundo local a carpeta de sincronización
        local_sync_path = self.computer_dir / world_name / "minecraft_saves_data"
        if local_sync_path.exists():
            shutil.rmtree(local_sync_path)
        ensure_dir_exists(local_sync_path.parent)
        shutil.copytree(local_world_path, local_sync_path)
        
        # Guardar control.json
        save_json(local_control_path, control_info)
        
        # Actualizar mundos.json con la nueva información
        if "mundos" not in self.mundos:
            self.mundos["mundos"] = {}
        
        self.mundos["mundos"][world_name] = {
            "commit_id": new_commit_id,
            "pc_id": self.computer_id,
            "timestamp": timestamp,
            "comment": comment or "Actualización"
        }
        save_json(config.MUNDOS_JSON, self.mundos)
        
        return True, "Mundo subido correctamente"
    
    def resolve_conflict(self, world_name, chosen_pc_id):
        """
        Resuelve un conflicto eligiendo cuál versión mantener.
        """
        if world_name not in self.mundos.get("mundos", {}):
            return False, "El mundo no existe en el sistema de sincronización"
        
        if chosen_pc_id not in os.listdir(config.WORLD_SYNC_DIR):
            return False, f"No se encontró la computadora {chosen_pc_id}"
        
        # Obtener información de la versión elegida
        chosen_control_path = config.WORLD_SYNC_DIR / chosen_pc_id / world_name / "control.json"
        if not chosen_control_path.exists():
            return False, f"No se encontró control.json para el mundo en la computadora {chosen_pc_id}"
        
        chosen_control = load_json(chosen_control_path)
        
        # Actualizar mundos.json con la información de la versión elegida
        self.mundos["mundos"][world_name] = {
            "commit_id": chosen_control.get("commit_id"),
            "pc_id": chosen_pc_id,
            "timestamp": chosen_control.get("timestamp"),
            "comment": f"Conflicto resuelto: se eligió la versión de {chosen_pc_id}"
        }
        save_json(config.MUNDOS_JSON, self.mundos)
        
        # Si la versión elegida no es la nuestra, la descargamos
        if chosen_pc_id != self.computer_id:
            return self.download_world(world_name)
        
        return True, f"Conflicto resuelto: se eligió la versión de {chosen_pc_id}"