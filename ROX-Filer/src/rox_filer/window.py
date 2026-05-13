from gi.repository import Gtk, Gio, GLib
from pathlib import Path

class RoxFilerWindow(Gtk.ApplicationWindow):
    def __init__(self, app):
        super().__init__(application=app)
        self.set_title("ROX-Filer")
        self.set_default_size(900, 600)
        
        # Main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Toolbar
        self.create_toolbar()
        
        # Address bar
        self.create_address_bar()
        
        # Main file view area
        self.fileview = Gtk.ScrolledWindow()
        self.fileview.set_hexpand(True)
        self.fileview.set_vexpand(True)
        self.main_box.append(self.fileview)
        
        # Initial directory
        self.current_path = Path.home()
        self.load_directory(self.current_path)
    
    def create_toolbar(self):
        toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        toolbar.set_margin_start(8)
        toolbar.set_margin_end(8)
        toolbar.set_margin_top(4)
        toolbar.set_margin_bottom(4)
        
        self.btn_back = Gtk.Button(icon_name="go-previous-symbolic")
        self.btn_back.connect("clicked", lambda b: self.go_back())
        toolbar.append(self.btn_back)
        
        self.btn_up = Gtk.Button(icon_name="go-up-symbolic")
        self.btn_up.connect("clicked", lambda b: self.go_up())
        toolbar.append(self.btn_up)
        
        self.btn_home = Gtk.Button(icon_name="go-home-symbolic")
        self.btn_home.connect("clicked", lambda b: self.go_home())
        toolbar.append(self.btn_home)
        
        self.main_box.append(toolbar)
    
    def create_address_bar(self):
        box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        box.set_margin_start(8)
        box.set_margin_end(8)
        box.set_margin_bottom(4)
        
        self.address_entry = Gtk.Entry()
        self.address_entry.set_text(str(self.current_path))
        self.address_entry.connect("activate", self.on_address_activated)
        box.append(self.address_entry)
        
        self.main_box.append(box)
    
    def load_directory(self, path: Path):
        self.current_path = path
        if hasattr(self, 'address_entry'):
            self.address_entry.set_text(str(path))
        
        # Placeholder view
        label = Gtk.Label(label=f"Contenido de: {path}\n\nImplementando vista de archivos...")
        self.fileview.set_child(label)
        
        print(f"[ROX-Filer] Cargando: {path}")
    
    def on_address_activated(self, entry):
        try:
            path = Path(entry.get_text()).expanduser()
            if path.exists() and path.is_dir():
                self.load_directory(path)
            else:
                print("Ruta no válida o no es directorio")
        except Exception as e:
            print(f"Error: {e}")
    
    def go_up(self):
        parent = self.current_path.parent
        if parent != self.current_path:
            self.load_directory(parent)
    
    def go_home(self):
        self.load_directory(Path.home())
    
    def go_back(self):
        print("Función Ir Atrás pendiente de implementación")