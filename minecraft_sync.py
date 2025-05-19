"""
Aplicación principal de Minecraft World Sync.
Proporciona una interfaz gráfica para sincronizar mundos y gestionar mods de Minecraft.
"""
import os
import sys
import tkinter as tk
from tkinter import ttk, messagebox, simpledialog
from pathlib import Path

import config
from utils import ensure_dir_exists, get_computer_id
from host_manager import HostManager
from mod_manager import ModManager

class MinecraftSyncApp:
    """Aplicación principal de Minecraft World Sync."""
    
    def __init__(self, root):
        """Inicializa la aplicación con la ventana root proporcionada."""
        self.root = root
        self.root.title(f"{config.APP_NAME} v{config.APP_VERSION}")
        self.root.geometry(config.APP_WINDOW_SIZE)
        self.root.minsize(600, 400)
        
        # Identificar la ruta de OneDrive
        self.setup_onedrive_path()
        
        # Inicializar gestores
        try:
            self.host_manager = HostManager()
            self.mod_manager = ModManager()
        except Exception as e:
            messagebox.showerror("Error de inicialización", 
                                f"No se pudo inicializar la aplicación: {str(e)}")
            root.destroy()
            return
        
        # Crear widgets
        self.create_widgets()
        
        # Mostrar pantalla inicial
        self.show_screen(config.SCREEN_MAIN)
        
        # Mostrar ID de computadora
        self.computer_id = get_computer_id()
        self.status_label.config(text=f"ID de computadora: {self.computer_id}")
    
    def setup_onedrive_path(self):
        """Configura la ruta a la carpeta compartida de OneDrive."""
        # Primero verificamos si estamos ejecutando desde dentro de la carpeta app
        current_dir = Path(os.path.abspath(os.path.dirname(__file__)))
        parent_dir = current_dir.parent
        
        # Verificar si estamos en la estructura esperada
        if current_dir.name == "app" and (parent_dir / "world_sync").exists():
            # Estamos en la estructura correcta, usar parent_dir como ONEDRIVE_ROOT
            config.ONEDRIVE_ROOT = parent_dir
        else:
            # Estamos fuera de la estructura, pedir al usuario que seleccione la carpeta
            messagebox.showinfo("Seleccionar carpeta", 
                               "Por favor, selecciona la carpeta 'Minecraft' compartida en OneDrive.")
            
            # En una aplicación real, aquí usaríamos un diálogo para seleccionar carpeta
            # Por ahora, usamos una ruta de ejemplo
            example_path = Path(os.path.expanduser("~")) / "OneDrive" / "Minecraft"
            
            if not example_path.exists():
                # Crear la estructura de carpetas para pruebas
                ensure_dir_exists(example_path / "world_sync")
                ensure_dir_exists(example_path / "mods")
                ensure_dir_exists(example_path / "app")
            
            config.ONEDRIVE_ROOT = example_path
        
        # Actualizar las rutas derivadas
        config.APP_DIR = config.ONEDRIVE_ROOT / "app"
        config.WORLD_SYNC_DIR = config.ONEDRIVE_ROOT / "world_sync"
        config.MODS_DIR = config.ONEDRIVE_ROOT / "mods"
        config.MUNDOS_JSON = config.WORLD_SYNC_DIR / "mundos.json"
        config.MODS_JSON = config.MODS_DIR / "mods.json"
    
    def create_widgets(self):
        """Crea los widgets de la interfaz gráfica."""
        # Estilo
        style = ttk.Style()
        style.configure("TFrame", background=config.BACKGROUND_COLOR)
        style.configure("TButton", background=config.PRIMARY_COLOR, foreground=config.TEXT_COLOR)
        style.configure("TLabel", background=config.BACKGROUND_COLOR, foreground=config.TEXT_COLOR)
        
        # Contenedor principal
        self.main_frame = ttk.Frame(self.root, padding="10")
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Crear contenedores para cada pantalla
        self.screens = {
            config.SCREEN_MAIN: self.create_main_screen(),
            config.SCREEN_HOST: self.create_host_screen(),
            config.SCREEN_MODS: self.create_mods_screen()
        }
        
        # Barra de estado
        self.status_bar = ttk.Frame(self.root, relief=tk.SUNKEN, padding="2")
        self.status_bar.pack(side=tk.BOTTOM, fill=tk.X)
        
        self.status_label = ttk.Label(self.status_bar, text="Listo")
        self.status_label.pack(side=tk.LEFT)
        
        # Versión
        version_label = ttk.Label(self.status_bar, text=f"v{config.APP_VERSION}")
        version_label.pack(side=tk.RIGHT)
    
    def create_main_screen(self):
        """Crea la pantalla principal con el menú de navegación."""
        frame = ttk.Frame(self.main_frame, padding="20")
        
        # Título
        title_label = ttk.Label(frame, text=config.APP_NAME, font=("Arial", 18, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Botones de navegación
        host_button = ttk.Button(frame, text="Gestionar Mundos", 
                                command=lambda: self.show_screen(config.SCREEN_HOST),
                                width=30)
        host_button.pack(pady=10)
        
        mods_button = ttk.Button(frame, text="Gestionar Mods", 
                                command=lambda: self.show_screen(config.SCREEN_MODS),
                                width=30)
        mods_button.pack(pady=10)
        
        # Información adicional
        info_label = ttk.Label(frame, text="Sincroniza tus mundos y mods de Minecraft entre dispositivos.", 
                              wraplength=400, justify=tk.CENTER)
        info_label.pack(pady=(20, 0))
        
        return frame
    
    def create_host_screen(self):
        """Crea la pantalla de gestión de mundos."""
        frame = ttk.Frame(self.main_frame, padding="20")
        
        # Título
        title_label = ttk.Label(frame, text="Gestión de Mundos", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Listbox para mundos disponibles
        worlds_frame = ttk.Frame(frame)
        worlds_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        worlds_label = ttk.Label(worlds_frame, text="Mundos disponibles:")
        worlds_label.pack(anchor=tk.W)
        
        worlds_container = ttk.Frame(worlds_frame)
        worlds_container.pack(fill=tk.BOTH, expand=True)
        
        self.worlds_listbox = tk.Listbox(worlds_container, height=10)
        self.worlds_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        worlds_scrollbar = ttk.Scrollbar(worlds_container, orient=tk.VERTICAL, 
                                        command=self.worlds_listbox.yview)
        worlds_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        
        self.worlds_listbox.config(yscrollcommand=worlds_scrollbar.set)
        self.worlds_listbox.bind('<<ListboxSelect>>', self.on_world_select)
        
        # Panel de información
        info_frame = ttk.Frame(frame)
        info_frame.pack(fill=tk.BOTH, expand=True, pady=10)
        
        self.world_info_var = tk.StringVar()
        self.world_info_var.set("Selecciona un mundo para ver su información")
        
        world_info_label = ttk.Label(info_frame, textvariable=self.world_info_var, 
                                    wraplength=500, justify=tk.LEFT)
        world_info_label.pack(fill=tk.BOTH, expand=True)
        
        # Botones de acción
        buttons_frame = ttk.Frame(frame)
        buttons_frame.pack(fill=tk.X, pady=(10, 0))
        
        self.refresh_button = ttk.Button(buttons_frame, text="Actualizar lista", 
                                        command=self.refresh_worlds_list)
        self.refresh_button.pack(side=tk.LEFT, padx=5)
        
        self.download_button = ttk.Button(buttons_frame, text="Descargar mundo", 
                                         command=self.download_selected_world,
                                         state=tk.DISABLED)
        self.download_button.pack(side=tk.LEFT, padx=5)
        
        self.upload_button = ttk.Button(buttons_frame, text="Subir mundo", 
                                       command=self.upload_selected_world,
                                       state=tk.DISABLED)
        self.upload_button.pack(side=tk.LEFT, padx=5)
        
        # Botón para regresar a la pantalla principal
        back_button = ttk.Button(frame, text="Volver al menú principal", 
                                command=lambda: self.show_screen(config.SCREEN_MAIN))
        back_button.pack(pady=(20, 0))
        
        return frame
    
    def create_mods_screen(self):
        """Crea la pantalla de gestión de mods."""
        frame = ttk.Frame(self.main_frame, padding="20")
        
        # Título
        title_label = ttk.Label(frame, text="Gestión de Mods", font=("Arial", 16, "bold"))
        title_label.pack(pady=(0, 20))
        
        # Mensaje de desarrollo
        dev_frame = ttk.Frame(frame, padding=20)
        dev_frame.pack(fill=tk.BOTH, expand=True)
        
        dev_label = ttk.Label(dev_frame, 
                             text="La funcionalidad de gestión de mods está en desarrollo.\n\nEsta característica permitirá:\n- Subir archivos .jar de mods\n- Clasificarlos por tipo\n- Añadir descripciones\n- Marcarlos como opcionales u obligatorios\n- Instalar mods faltantes", 
                             font=("Arial", 12),
                             justify=tk.CENTER,
                             wraplength=500)
        dev_label.pack(fill=tk.BOTH, expand=True)
        
        # Botón para regresar a la pantalla principal
        back_button = ttk.Button(frame, text="Volver al menú principal", 
                                command=lambda: self.show_screen(config.SCREEN_MAIN))
        back_button.pack(pady=(20, 0))
        
        return frame
    
    def show_screen(self, screen_name):
        """Muestra la pantalla especificada y oculta las demás."""
        for name, screen in self.screens.items():
            if name == screen_name:
                screen.pack(fill=tk.BOTH, expand=True)
            else:
                screen.pack_forget()
        
        # Acciones específicas para cada pantalla
        if screen_name == config.SCREEN_HOST:
            self.refresh_worlds_list()
    
    def refresh_worlds_list(self):
        """Actualiza la lista de mundos disponibles."""
        self.worlds_listbox.delete(0, tk.END)
        
        # Obtener mundos sincronizados
        sync_worlds = self.host_manager.get_available_worlds()
        for world in sync_worlds:
            self.worlds_listbox.insert(tk.END, world)
        
        # Obtener mundos locales que no estén en la lista
        local_worlds = self.host_manager.get_local_worlds()
        for world in local_worlds:
            if world not in sync_worlds:
                self.worlds_listbox.insert(tk.END, f"{world} (local)")
        
        # Desactivar botones
        self.download_button.config(state=tk.DISABLED)
        self.upload_button.config(state=tk.DISABLED)
        
        # Actualizar información
        self.world_info_var.set("Selecciona un mundo para ver su información")
    
    def on_world_select(self, event):
        """Maneja el evento de selección de un mundo en la lista."""
        if not self.worlds_listbox.curselection():
            return
        
        # Obtener el nombre del mundo seleccionado
        selected_index = self.worlds_listbox.curselection()[0]
        selected_item = self.worlds_listbox.get(selected_index)
        
        # Si es local, quitar el sufijo
        if " (local)" in selected_item:
            world_name = selected_item.replace(" (local)", "")
            is_local_only = True
        else:
            world_name = selected_item
            is_local_only = False
        
        # Verificar estado del mundo
        if is_local_only:
            # Es un mundo local que no está en el sistema de sincronización
            self.world_info_var.set(
                f"Mundo: {world_name}\n"
                f"Estado: Solo existe localmente\n"
                f"Acciones disponibles: Subir al sistema de sincronización"
            )
            self.download_button.config(state=tk.DISABLED)
            self.upload_button.config(state=tk.NORMAL)
        else:
            # Obtener información detallada
            status = self.host_manager.check_world_status(world_name)
            
            info_text = f"Mundo: {world_name}\n"
            
            if status["exists_in_sync"]:
                latest_info = status["latest_version_info"]
                info_text += f"Última actualización: {latest_info.get('timestamp', 'Desconocido')}\n"
                info_text += f"Actualizado por: {latest_info.get('pc_id', 'Desconocido')}\n"
                info_text += f"Comentario: {latest_info.get('comment', 'Sin comentario')}\n\n"
            
            if status["exists_locally"]:
                info_text += "Estado: Existe localmente\n"
            else:
                info_text += "Estado: No existe localmente\n"
            
            if status["has_latest_version"]:
                info_text += "Versión: Tienes la última versión\n"
                self.download_button.config(state=tk.DISABLED)
            else:
                if status["exists_in_sync"]:
                    info_text += "Versión: No tienes la última versión\n"
                    self.download_button.config(state=tk.NORMAL)
                else:
                    info_text += "Versión: No existe en el sistema de sincronización\n"
                    self.download_button.config(state=tk.DISABLED)
            
            # Mostrar conflictos si los hay
            if status["conflicts"]:
                info_text += "\nConflictos detectados:\n"
                for conflict in status["conflicts"]:
                    info_text += f"- {conflict['message']}\n"
            
            self.world_info_var.set(info_text)
            
            # Configurar botón de subida
            if status["exists_locally"]:
                self.upload_button.config(state=tk.NORMAL)
            else:
                self.upload_button.config(state=tk.DISABLED)
    
    def download_selected_world(self):
        """Descarga el mundo seleccionado desde el sistema de sincronización."""
        if not self.worlds_listbox.curselection():
            return
        
        # Obtener el nombre del mundo seleccionado
        selected_index = self.worlds_listbox.curselection()[0]
        selected_item = self.worlds_listbox.get(selected_index)
        
        # Si es local, quitar el sufijo
        if " (local)" in selected_item:
            return  # No se puede descargar un mundo local
        
        world_name = selected_item
        
        # Confirmar descarga
        if not messagebox.askyesno("Confirmar descarga", 
                                  f"¿Estás seguro de que quieres descargar el mundo '{world_name}'?\n\n"
                                  "Esto sobrescribirá cualquier versión local existente."):
            return
        
        # Verificar estado y posibles conflictos
        status = self.host_manager.check_world_status(world_name)
        
        if status["conflicts"]:
            # Hay conflictos, preguntar qué versión descargar
            conflict_message = "Se detectaron conflictos:\n\n"
            for conflict in status["conflicts"]:
                conflict_message += f"- {conflict['message']}\n"
            
            conflict_message += "\n¿Deseas continuar con la descarga de la última versión?"
            
            if not messagebox.askyesno("Conflictos detectados", conflict_message):
                return
        
        # Realizar descarga
        try:
            success, message = self.host_manager.download_world(world_name)
            
            if success:
                messagebox.showinfo("Descarga completada", message)
                self.refresh_worlds_list()
            else:
                messagebox.showerror("Error en la descarga", message)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error durante la descarga: {str(e)}")
    
    def upload_selected_world(self):
        """Sube el mundo seleccionado al sistema de sincronización."""
        if not self.worlds_listbox.curselection():
            return
        
        # Obtener el nombre del mundo seleccionado
        selected_index = self.worlds_listbox.curselection()[0]
        selected_item = self.worlds_listbox.get(selected_index)
        
        # Si es local, quitar el sufijo
        if " (local)" in selected_item:
            world_name = selected_item.replace(" (local)", "")
        else:
            world_name = selected_item
        
        # Pedir comentario para la subida
        comment = simpledialog.askstring("Comentario", 
                                        "Añade un comentario para esta actualización (opcional):",
                                        parent=self.root)
        
        # Verificar estado y posibles conflictos
        status = self.host_manager.check_world_status(world_name)
        
        if status["exists_in_sync"] and not status["has_latest_version"]:
            # No tenemos la última versión, advertir
            if not messagebox.askyesno("Advertencia", 
                                      "No tienes la última versión de este mundo. "
                                      "Si subes tu versión, podrías sobrescribir cambios más recientes.\n\n"
                                      "¿Estás seguro de que quieres continuar?"):
                return
        
        if status["conflicts"]:
            # Hay conflictos, advertir
            conflict_message = "Se detectaron conflictos:\n\n"
            for conflict in status["conflicts"]:
                conflict_message += f"- {conflict['message']}\n"
            
            conflict_message += "\n¿Deseas continuar con la subida? Esto podría crear más conflictos."
            
            if not messagebox.askyesno("Conflictos detectados", conflict_message):
                return
        
        # Realizar subida
        try:
            success, message = self.host_manager.upload_world(world_name, comment)
            
            if success:
                messagebox.showinfo("Subida completada", message)
                self.refresh_worlds_list()
            else:
                messagebox.showerror("Error en la subida", message)
        except Exception as e:
            messagebox.showerror("Error", f"Ocurrió un error durante la subida: {str(e)}")
            print(f"Ocurrió un error durante la subida: {str(e)}")

def main():
    """Función principal para iniciar la aplicación."""
    root = tk.Tk()
    app = MinecraftSyncApp(root)
    root.mainloop()


if __name__ == "__main__":
    main()