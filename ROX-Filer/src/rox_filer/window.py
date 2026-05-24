import os
import gi
gi.require_version('Gtk', '4.0')
gi.require_version('GdkPixbuf', '2.0')
from gi.repository import Gtk, Gio, GLib, Gdk, Pango, GdkPixbuf
from pathlib import Path
from .options import options_manager

def get_classic_icon_path(path: Path) -> str:
    project_dir = Path(__file__).resolve().parents[2]
    rox_dir = project_dir / "ROX"
    mime_dir = rox_dir / "MIME"
    
    try:
        if path.is_dir():
            app_icon = path / ".DirIcon"
            if app_icon.exists():
                return str(app_icon)
            if (path / "AppRun").exists():
                return str(mime_dir / "application-x-executable.png")
            return str(mime_dir / "inode-directory.png")
    except Exception:
        pass
        
    try:
        gfile = Gio.File.new_for_path(str(path))
        info = gfile.query_info("standard::content-type", Gio.FileQueryInfoFlags.NONE, None)
        content_type = info.get_content_type()
        
        mime_filename = content_type.replace("/", "-") + ".png"
        icon_path = mime_dir / mime_filename
        if icon_path.exists():
            return str(icon_path)
            
        if content_type.startswith("text/"):
            return str(mime_dir / "text-x-generic.png")
        elif content_type.startswith("image/"):
            return str(mime_dir / "image-x-generic.png")
        elif content_type.startswith("audio/"):
            return str(mime_dir / "audio-x-generic.png")
        elif content_type.startswith("video/"):
            return str(mime_dir / "video-x-generic.png")
        elif content_type.startswith("application/"):
            if os.access(path, os.X_OK):
                return str(mime_dir / "application-x-executable.png")
            return str(mime_dir / "application-x-generic.png")
    except Exception:
        pass
        
    try:
        if os.access(path, os.X_OK):
            return str(mime_dir / "application-x-executable.png")
    except Exception:
        pass
    return str(mime_dir / "text-x-generic.png")

CSS_DATA = """
.rox-toolbar {
    border-bottom: 1px solid alpha(currentColor, 0.15);
    padding: 2px 4px;
}
.rox-toolbar button {
    background: transparent;
    border: none;
    box-shadow: none;
    padding: 4px;
}
.rox-toolbar button:hover {
    background-color: alpha(currentColor, 0.08);
    border-radius: 4px;
}
.rox-toolbar button:active {
    background-color: alpha(currentColor, 0.15);
    border-radius: 4px;
}
.rox-address-box {
    border-top: 1px solid alpha(currentColor, 0.15);
    padding: 0px 2px;
}
.rox-address-box entry,
.rox-address-box entry > text,
.rox-address-box entry * {
    min-height: 0px;
    padding-top: 0px;
    padding-bottom: 0px;
    margin-top: 0px;
    margin-bottom: 0px;
    font-size: 8.5pt;
}
.rox-file-view, scrolledwindow, scrolledwindow > viewport, viewport {
    background-color: #ffffff;
}
.rox-item-count {
    font-family: sans-serif;
    font-size: 10pt;
    color: alpha(currentColor, 0.6);
    margin-right: 8px;
}
flowbox {
    background-color: #ffffff;
    padding: 4px;
}
flowboxchild {
    padding: 0px;
    margin: 2px 4px;
    border-radius: 4px;
    min-width: 140px;
}
flowboxchild:selected {
    background-color: #b0d0ff;
    outline: 1px solid #70a0ff;
}
flowboxchild:hover {
    background-color: #e0ecff;
}
.rox-file-box {
    padding: 2px 4px;
}
.rox-file-label {
    font-family: sans-serif;
    font-size: 10pt;
}
.rox-file-label.directory {
    color: #0000ff;
    font-weight: bold;
}
.rox-file-label.executable {
    color: #008000;
}
.rox-file-label.regular {
    color: #000000;
}
"""

class RoxFilerWindow(Gtk.ApplicationWindow):
    def __init__(self, app, initial_path=None):
        super().__init__(application=app)
        self.set_title("ROX-Filer")
        self.set_default_size(480, 320)
        
        # Set window icon
        project_dir = Path(__file__).resolve().parents[2]
        icon_dir = project_dir / "app_icon"
        display = Gdk.Display.get_default()
        if display:
            icon_theme = Gtk.IconTheme.get_for_display(display)
            icon_theme.add_search_path(str(icon_dir))
        try:
            self.set_icon_name("org.rox.filer")
        except RuntimeError:
            pass
        
        # Load CSS Styles
        css_provider = Gtk.CssProvider()
        css_provider.load_from_data(CSS_DATA.encode('utf-8'))
        display = Gdk.Display.get_default()
        if display:
            Gtk.StyleContext.add_provider_for_display(
                display,
                css_provider,
                Gtk.STYLE_PROVIDER_PRIORITY_APPLICATION
            )
            
        # Navigation state
        self.current_path = initial_path or Path.home()
        self.history = []
        self.btn_back = None
        self.manual_zoom = False
        self.icon_size = self.get_default_icon_size()
        self.view_mode = "list" if options_manager.get_int("filer_view_type") == 1 else "grid"
        
        # Main vertical box
        self.main_box = Gtk.Box(orientation=Gtk.Orientation.VERTICAL)
        self.set_child(self.main_box)
        
        # Toolbar
        self.create_toolbar()
        
        # Main file view area
        self.fileview = Gtk.ScrolledWindow()
        self.fileview.set_hexpand(True)
        self.fileview.set_vexpand(True)
        self.fileview.set_policy(Gtk.PolicyType.AUTOMATIC, Gtk.PolicyType.AUTOMATIC)
        self.main_box.append(self.fileview)
        
        # Address bar (bottom-anchored, hidden by default)
        self.create_address_bar()
        self.address_bar_visible = False
        
        # Keyboard shortcut controller
        key_controller = Gtk.EventControllerKey()
        key_controller.connect("key-pressed", self.on_key_pressed)
        self.add_controller(key_controller)
        
        self.load_directory(self.current_path, push_history=False)
        
    def create_icon_button(self, icon_name, callback) -> Gtk.Button:
        btn = Gtk.Button()
        image = Gtk.Image.new_from_icon_name(icon_name)
        image.set_pixel_size(32)
        btn.set_child(image)
        btn.add_css_class("flat")
        if callback:
            btn.connect("clicked", lambda b: callback())
        return btn

    def create_local_icon_button(self, icon_filename, callback) -> Gtk.Button:
        btn = Gtk.Button()
        project_dir = Path(__file__).resolve().parents[2]
        image_path = project_dir / "images" / icon_filename
        
        icon_loaded = False
        if image_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(image_path),
                    32, 32,
                    True
                )
                image = Gtk.Image.new_from_pixbuf(pixbuf)
                icon_loaded = True
            except Exception as e:
                print(f"Error loading local icon {image_path}: {e}")
                
        if not icon_loaded:
            image = Gtk.Image.new_from_icon_name("image-missing")
            image.set_pixel_size(32)
            
        btn.set_child(image)
        btn.add_css_class("flat")
        if callback:
            btn.connect("clicked", lambda b: callback())
        return btn

    def create_toolbar(self):
        self.toolbar = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=4)
        self.toolbar.add_css_class("rox-toolbar")
        
        # Original ROX-Filer toolbar buttons in order:
        self.btn_up = self.create_icon_button("go-up", self.go_up)
        self.toolbar.append(self.btn_up)
        
        self.btn_home = self.create_icon_button("go-home", self.go_home)
        self.toolbar.append(self.btn_home)
        
        self.btn_bookmarks = self.create_icon_button("go-jump", lambda: self.show_bookmarks(self.btn_bookmarks))
        self.toolbar.append(self.btn_bookmarks)
        
        self.btn_rescan = self.create_icon_button("view-refresh", self.rescan)
        self.toolbar.append(self.btn_rescan)
        
        self.btn_zoom_in = self.create_icon_button("zoom-in", self.zoom_in)
        self.toolbar.append(self.btn_zoom_in)
        
        self.btn_zoom_out = self.create_icon_button("zoom-out", self.zoom_out)
        self.toolbar.append(self.btn_zoom_out)
        
        # Single Options button replacing View Details and Show Hidden buttons
        self.btn_options = self.create_icon_button("preferences-system", lambda: self.show_options_menu(self.btn_options))
        self.toolbar.append(self.btn_options)
        
        self.btn_help = self.create_icon_button("help-about", self.show_help)
        self.toolbar.append(self.btn_help)
        
        # Spacer
        spacer = Gtk.Box()
        spacer.set_hexpand(True)
        self.toolbar.append(spacer)
        
        # Item count
        self.item_count_label = Gtk.Label(label="0 items")
        self.item_count_label.add_css_class("rox-item-count")
        self.toolbar.append(self.item_count_label)
        
        self.main_box.append(self.toolbar)
        
    def create_address_bar(self):
        self.address_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=2)
        self.address_box.add_css_class("rox-address-box")
        self.address_box.set_valign(Gtk.Align.END)
        self.address_box.set_size_request(-1, 20)
        
        self.address_entry = Gtk.Entry()
        self.address_entry.set_hexpand(True)
        self.address_entry.set_valign(Gtk.Align.CENTER)
        self.address_entry.set_size_request(-1, 18)
        self.address_entry.set_text(str(self.current_path))
        self.address_entry.connect("activate", self.on_address_activated)
        self.address_box.append(self.address_entry)
        
    def load_directory(self, path: Path, push_history=True):
        try:
            path = Path(path).expanduser().resolve()
        except Exception as e:
            print(f"Error resolviendo ruta: {e}")
            return
            
        if not path.exists() or not path.is_dir():
            print("Ruta no válida o no es directorio")
            return
            
        if push_history and hasattr(self, 'current_path') and self.current_path != path:
            self.history.append(self.current_path)
            if getattr(self, 'btn_back', None) is not None:
                self.btn_back.set_sensitive(True)
                
        self.current_path = path
        
        # Update address entry
        if hasattr(self, 'address_entry'):
            self.address_entry.set_text(str(path))
            
        # Update window title (match ~ prefix for home relative)
        title_path = str(path)
        home_str = str(Path.home())
        if title_path.startswith(home_str):
            title_path = title_path.replace(home_str, "~", 1)
        self.set_title(title_path)
        
        # Build FlowBox
        self.flowbox = Gtk.FlowBox()
        self.flowbox.add_css_class("rox-file-view")
        self.flowbox.set_column_spacing(12)
        self.flowbox.set_row_spacing(6)
        self.flowbox.set_selection_mode(Gtk.SelectionMode.SINGLE)
        
        single_click = options_manager.get_bool('bind_single_click')
        self.flowbox.set_activate_on_single_click(single_click)
        
        # Right click gesture for flowbox context menus
        flowbox_click = Gtk.GestureClick()
        flowbox_click.set_button(3)
        flowbox_click.connect("pressed", self.on_flowbox_right_clicked)
        self.flowbox.add_controller(flowbox_click)
        
        if self.view_mode == "grid":
            self.flowbox.set_max_children_per_line(100)
            self.flowbox.set_orientation(Gtk.Orientation.HORIZONTAL)
        else:
            self.flowbox.set_max_children_per_line(1)
            self.flowbox.set_orientation(Gtk.Orientation.HORIZONTAL)
            
        display_dirs_first = options_manager.get_bool('display_dirs_first')
        try:
            def sort_key(p):
                is_directory = False
                if display_dirs_first:
                    try:
                        is_directory = p.is_dir()
                    except Exception:
                        pass
                return (not is_directory if display_dirs_first else False, p.name.lower())
                
            items = sorted(path.iterdir(), key=sort_key)
        except Exception as e:
            label = Gtk.Label(label=f"Error al leer directorio:\n{e}")
            self.fileview.set_child(label)
            return
            
        show_hidden = options_manager.get_bool('display_show_hidden')
        visible_items = []
        for p in items:
            if p.name.startswith(".") and not p.name == "..":
                if not show_hidden:
                    continue
            visible_items.append(p)
            
        # Dynamically adjust icon size in Auto mode
        if not getattr(self, 'manual_zoom', False):
            if options_manager.get_int('display_icon_size') == 3:
                self.icon_size = 24 if len(visible_items) >= 50 else 48
            
        for p in visible_items:
            # Determine icon and CSS class
            css_class = "regular"
            is_appdir = False
            try:
                if p.is_dir():
                    is_appdir = (p / "AppRun").exists()
                    if is_appdir:
                        css_class = "executable"
                    else:
                        css_class = "directory"
                elif os.access(p, os.X_OK):
                    css_class = "executable"
            except Exception:
                try:
                    if p.is_dir():
                        css_class = "directory"
                except Exception:
                    pass
                
            # Icon selection
            icon_loaded = False
            actual_icon_size = max(16, self.icon_size // 2) if self.view_mode == "list" else self.icon_size
            
            # 1. Custom folder icon (.DirIcon) has highest priority as it is a specific folder mascot
            try:
                if p.is_dir() and (p / ".DirIcon").exists():
                    icon_path = str(p / ".DirIcon")
                    pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                        icon_path,
                        actual_icon_size,
                        actual_icon_size,
                        True
                    )
                    image = Gtk.Image.new_from_pixbuf(pixbuf)
                    image.set_pixel_size(actual_icon_size)
                    image.set_size_request(actual_icon_size, actual_icon_size)
                    icon_loaded = True
            except Exception:
                pass
                
            # 2. Try loading standard desktop theme icon (standard::icon)
            if not icon_loaded:
                try:
                    gfile = Gio.File.new_for_path(str(p))
                    info = gfile.query_info("standard::icon", Gio.FileQueryInfoFlags.NONE, None)
                    gicon = info.get_icon()
                    if gicon:
                        image = Gtk.Image.new_from_gicon(gicon)
                        image.set_pixel_size(actual_icon_size)
                        image.set_size_request(actual_icon_size, actual_icon_size)
                        icon_loaded = True
                except Exception:
                    pass
                    
            # 3. Fallback to classic MIME icons from project resources
            if not icon_loaded:
                try:
                    icon_path = get_classic_icon_path(p)
                    if icon_path and os.path.exists(icon_path):
                        pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                            icon_path,
                            actual_icon_size,
                            actual_icon_size,
                            True
                        )
                        image = Gtk.Image.new_from_pixbuf(pixbuf)
                        image.set_pixel_size(actual_icon_size)
                        image.set_size_request(actual_icon_size, actual_icon_size)
                        icon_loaded = True
                except Exception as e:
                    print(f"Error loading classic icon for {p}: {e}")
                    
            # 4. Final Fallback to basic generic icons
            if not icon_loaded:
                if is_appdir:
                    image = Gtk.Image.new_from_icon_name("application-x-executable")
                elif p.is_dir():
                    image = Gtk.Image.new_from_icon_name("folder")
                else:
                    image = Gtk.Image.new_from_icon_name("text-x-generic")
                image.set_pixel_size(actual_icon_size)
                image.set_size_request(actual_icon_size, actual_icon_size)
            
            # Item layout
            item_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
            item_box.add_css_class("rox-file-box")
            item_box.set_vexpand(False)
            item_box.set_valign(Gtk.Align.CENTER)
            item_box.append(image)
            
            label = Gtk.Label(label=p.name)
            label.add_css_class("rox-file-label")
            label.add_css_class(css_class)
            label.set_ellipsize(Pango.EllipsizeMode.END)
            label.set_halign(Gtk.Align.START)
            
            if self.view_mode == "grid":
                item_box.set_hexpand(False)
                item_box.set_halign(Gtk.Align.START)
                label.set_max_width_chars(15)
                item_box.append(label)
            else:
                # List view: name expands, details placed to the right
                item_box.set_hexpand(True)
                item_box.set_halign(Gtk.Align.FILL)
                label.set_hexpand(True)
                item_box.append(label)
                
                # Fetch details
                file_size_str = ""
                file_mtime_str = ""
                file_perms_str = ""
                try:
                    stat_info = p.stat()
                    # Size
                    try:
                        if p.is_dir():
                            file_size_str = "dir"
                        else:
                            size_bytes = stat_info.st_size
                            if size_bytes < 1024:
                                file_size_str = f"{size_bytes} B"
                            elif size_bytes < 1024 * 1024:
                                file_size_str = f"{size_bytes/1024:.1f} KB"
                            else:
                                file_size_str = f"{size_bytes/(1024*1024):.1f} MB"
                    except Exception:
                        file_size_str = "-"
                    
                    # Perms
                    import stat
                    try:
                        file_perms_str = stat.filemode(stat_info.st_mode)
                    except Exception:
                        file_perms_str = "-"
                        
                    # Modification date
                    import datetime
                    try:
                        mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime)
                        file_mtime_str = mtime.strftime("%d/%m/%Y %H:%M")
                    except Exception:
                        file_mtime_str = "-"
                except Exception:
                    file_size_str = "-"
                    file_perms_str = "-"
                    file_mtime_str = "-"
                    
                # Append labels with fixed width requests for column alignment
                size_label = Gtk.Label(label=file_size_str)
                size_label.add_css_class("rox-file-label")
                size_label.add_css_class("regular")
                size_label.set_size_request(80, -1)
                size_label.set_halign(Gtk.Align.END)
                item_box.append(size_label)
                
                perms_label = Gtk.Label(label=file_perms_str)
                perms_label.add_css_class("rox-file-label")
                perms_label.add_css_class("regular")
                perms_label.set_size_request(100, -1)
                perms_label.set_halign(Gtk.Align.CENTER)
                item_box.append(perms_label)
                
                mtime_label = Gtk.Label(label=file_mtime_str)
                mtime_label.add_css_class("rox-file-label")
                mtime_label.add_css_class("regular")
                mtime_label.set_size_request(140, -1)
                mtime_label.set_halign(Gtk.Align.START)
                item_box.append(mtime_label)
            
            child = Gtk.FlowBoxChild()
            child.set_child(item_box)
            child.set_vexpand(False)
            child.set_valign(Gtk.Align.CENTER)
            if self.view_mode == "grid":
                child.set_hexpand(False)
                child.set_halign(Gtk.Align.START)
            else:
                child.set_hexpand(True)
                child.set_halign(Gtk.Align.FILL)
                item_box.set_hexpand(True)
            child.file_path = p
            
            # Gesture click to capture explicit double-clicks securely
            gesture = Gtk.GestureClick()
            gesture.set_button(1)
            gesture.connect("pressed", self.on_item_pressed, p)
            child.add_controller(gesture)
            
            self.flowbox.append(child)
            
        self.flowbox.connect("child-activated", self.on_item_activated)
        self.fileview.set_child(self.flowbox)
        
        # Update item count
        if hasattr(self, 'item_count_label'):
            self.item_count_label.set_text(f"{len(visible_items)} items")
            
        # Update button states
        if hasattr(self, 'btn_up'):
            self.btn_up.set_sensitive(path.parent != path)
            
        print(f"[ROX-Filer] Cargando: {path}")

    def on_key_pressed(self, controller, keyval, keycode, state):
        if keyval == Gdk.KEY_slash:
            if not getattr(self, 'address_bar_visible', False):
                self.main_box.append(self.address_box)
                self.address_bar_visible = True
            self.address_entry.grab_focus()
            return True
        elif keyval == Gdk.KEY_Escape:
            if getattr(self, 'address_bar_visible', False):
                self.main_box.remove(self.address_box)
                self.address_bar_visible = False
            self.fileview.grab_focus()
            return True
        return False

    def activate_path(self, path):
        if path.is_dir():
            self.load_directory(path)
        else:
            print(f"[ROX-Filer] Abrir archivo: {path}")
            try:
                Gio.AppInfo.launch_default_for_uri(path.as_uri(), None)
            except Exception as e:
                print(f"Error al abrir: {e}")

    def on_item_activated(self, flowbox, child):
        self.activate_path(child.file_path)

    def on_item_pressed(self, gesture, n_press, x, y, path):
        if n_press == 2:
            self.activate_path(path)

    def on_address_activated(self, entry):
        try:
            path = Path(entry.get_text()).expanduser()
            if path.exists() and path.is_dir():
                self.load_directory(path)
                if getattr(self, 'address_bar_visible', False):
                    self.main_box.remove(self.address_box)
                    self.address_bar_visible = False
                self.fileview.grab_focus()
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
        if self.history:
            prev_path = self.history.pop()
            if not self.history and getattr(self, 'btn_back', None) is not None:
                self.btn_back.set_sensitive(False)
            self.load_directory(prev_path, push_history=False)

    def rescan(self):
        self.load_directory(self.current_path, push_history=False)

    def get_default_icon_size(self, items_count=0) -> int:
        size_opt = options_manager.get_int('display_icon_size')
        if size_opt == 1:
            return 24
        elif size_opt == 2:
            return 64
        elif size_opt == 3: # Auto
            if items_count >= 50:
                return 24
            else:
                return 48
        else: # 0 = Large (default)
            return 48

    def zoom_in(self):
        self.manual_zoom = True
        steps = [16, 24, 36, 48, 64]
        try:
            idx = steps.index(self.icon_size)
            if idx < len(steps) - 1:
                self.icon_size = steps[idx + 1]
        except ValueError:
            larger_steps = [s for s in steps if s > self.icon_size]
            if larger_steps:
                self.icon_size = larger_steps[0]
            else:
                self.icon_size = steps[-1]
        self.load_directory(self.current_path, push_history=False)

    def zoom_out(self):
        self.manual_zoom = True
        steps = [16, 24, 36, 48, 64]
        try:
            idx = steps.index(self.icon_size)
            if idx > 0:
                self.icon_size = steps[idx - 1]
        except ValueError:
            smaller_steps = [s for s in steps if s < self.icon_size]
            if smaller_steps:
                self.icon_size = smaller_steps[-1]
            else:
                self.icon_size = steps[0]
        self.load_directory(self.current_path, push_history=False)

    def toggle_view_mode(self):
        if self.view_mode == "grid":
            self.view_mode = "list"
        else:
            self.view_mode = "grid"
        self.load_directory(self.current_path, push_history=False)

    def show_options_menu(self, button):
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=8)
        vbox.set_margin_start(12)
        vbox.set_margin_end(12)
        vbox.set_margin_top(12)
        vbox.set_margin_bottom(12)
        
        chk_view = Gtk.CheckButton(label="Vista de Lista")
        chk_view.set_active(self.view_mode == "list")
        
        def on_view_toggled(widget):
            self.view_mode = "list" if chk_view.get_active() else "grid"
            self.load_directory(self.current_path, push_history=False)
            
        chk_view.connect("toggled", on_view_toggled)
        vbox.append(chk_view)
        
        chk_hidden = Gtk.CheckButton(label="Mostrar Ocultos")
        chk_hidden.set_active(options_manager.get_bool("display_show_hidden"))
        
        def on_hidden_toggled(widget):
            options_manager.set_bool("display_show_hidden", chk_hidden.get_active())
            self.load_directory(self.current_path, push_history=False)
            
        chk_hidden.connect("toggled", on_hidden_toggled)
        vbox.append(chk_hidden)
        
        popover.set_child(vbox)
        popover.popup()

    def show_help(self):
        # Custom Dialog for Help with the ROX eagle logo
        help_window = Gtk.Window(transient_for=self, modal=True, title="Ayuda de ROX-Filer")
        help_window.set_default_size(350, 300)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        help_window.set_child(vbox)
        
        title_label = Gtk.Label(label="ROX-Filer")
        title_label.add_css_class("title-4")
        title_label.set_halign(Gtk.Align.CENTER)
        vbox.append(title_label)
        
        # Load eagle logo (.DirIcon is PNG) below the name
        project_dir = Path(__file__).resolve().parents[2]
        logo_path = project_dir / ".DirIcon"
        if logo_path.exists():
            try:
                pixbuf = GdkPixbuf.Pixbuf.new_from_file_at_scale(
                    str(logo_path),
                    200, 200,
                    True
                )
                logo_img = Gtk.Image.new_from_pixbuf(pixbuf)
                logo_img.set_halign(Gtk.Align.CENTER)
                logo_img.set_pixel_size(200)
                logo_img.set_size_request(200, 102)
                vbox.append(logo_img)
            except Exception as e:
                print(f"Error loading logo: {e}")
        
        desc_label = Gtk.Label(label="Port moderno de ROX-Filer a GTK4 + Python 3.")
        desc_label.set_halign(Gtk.Align.CENTER)
        desc_label.set_wrap(True)
        vbox.append(desc_label)
        
        shortcuts_label = Gtk.Label()
        shortcuts_label.set_markup(
            "<b>Atajos de teclado:</b>\n"
            "• <b>/</b> : Mostrar barra de direcciones\n"
            "• <b>Escape</b> : Ocultar barra de direcciones\n"
            "• <b>Doble clic</b> : Abrir archivo o carpeta"
        )
        shortcuts_label.set_halign(Gtk.Align.START)
        shortcuts_label.set_wrap(True)
        vbox.append(shortcuts_label)
        
        btn_ok = Gtk.Button(label="Aceptar")
        btn_ok.set_halign(Gtk.Align.CENTER)
        btn_ok.connect("clicked", lambda b: help_window.destroy())
        vbox.append(btn_ok)
        
        help_window.present()

    def toggle_show_hidden(self):
        current = options_manager.get_bool('display_show_hidden')
        options_manager.set_bool('display_show_hidden', not current)
        options_manager.save()
        self.load_directory(self.current_path, push_history=False)

    def show_bookmarks(self, button):
        popover = Gtk.Popover()
        popover.set_parent(button)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=4)
        vbox.set_margin_start(8)
        vbox.set_margin_end(8)
        vbox.set_margin_top(8)
        vbox.set_margin_bottom(8)
        
        btn_home = Gtk.Button(label="Carpeta Personal")
        btn_home.add_css_class("flat")
        btn_home.connect("clicked", lambda b: [self.go_home(), popover.popdown()])
        vbox.append(btn_home)
        
        btn_root = Gtk.Button(label="Raíz (/)")
        btn_root.add_css_class("flat")
        btn_root.connect("clicked", lambda b: [self.load_directory(Path("/")), popover.popdown()])
        vbox.append(btn_root)
        
        popover.set_child(vbox)
        popover.popup()

    def on_flowbox_right_clicked(self, gesture, n_press, x, y):
        child = self.flowbox.get_child_at_pos(x, y)
        if child is not None:
            self.flowbox.select_child(child)
            self.show_item_context_menu(child, x, y)
        else:
            self.show_directory_context_menu(x, y)

    def show_item_context_menu(self, child, x, y):
        path = child.file_path
        popover = Gtk.Popover()
        popover.set_parent(self.flowbox)
        
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_margin_start(4)
        vbox.set_margin_end(4)
        vbox.set_margin_top(4)
        vbox.set_margin_bottom(4)
        
        def create_menu_btn(label, callback, sensitive=True):
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.set_halign(Gtk.Align.START)
            btn.set_sensitive(sensitive)
            if callback and sensitive:
                btn.connect("clicked", lambda b: [callback(), popover.popdown()])
            return btn
            
        vbox.append(create_menu_btn("Copiar", lambda: self.action_copy(path)))
        
        has_copied = getattr(self, 'copied_path', None) is not None
        vbox.append(create_menu_btn("Pegar", lambda: self.action_paste(path), sensitive=(path.is_dir() and has_copied)))
        vbox.append(create_menu_btn("Detalles", lambda: self.action_details(path)))
        vbox.append(create_menu_btn("Comprimir", lambda: self.action_compress(path)))
        
        is_archive = path.suffix.lower() in ['.zip', '.gz', '.tgz', '.tar', '.bz2', '.xz'] or path.name.endswith('.tar.gz')
        vbox.append(create_menu_btn("Descomprimir", lambda: self.action_decompress(path), sensitive=is_archive))
        
        popover.set_child(vbox)
        popover.popup()

    def show_directory_context_menu(self, x, y):
        popover = Gtk.Popover()
        popover.set_parent(self.flowbox)
        
        rect = Gdk.Rectangle()
        rect.x = int(x)
        rect.y = int(y)
        rect.width = 1
        rect.height = 1
        popover.set_pointing_to(rect)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=2)
        vbox.set_margin_start(4)
        vbox.set_margin_end(4)
        vbox.set_margin_top(4)
        vbox.set_margin_bottom(4)
        
        def create_menu_btn(label, callback, sensitive=True):
            btn = Gtk.Button(label=label)
            btn.add_css_class("flat")
            btn.set_halign(Gtk.Align.START)
            btn.set_sensitive(sensitive)
            if callback and sensitive:
                btn.connect("clicked", lambda b: [callback(), popover.popdown()])
            return btn
            
        has_copied = getattr(self, 'copied_path', None) is not None
        vbox.append(create_menu_btn("Pegar", lambda: self.action_paste(self.current_path), sensitive=has_copied))
        vbox.append(create_menu_btn("Detalles de carpeta", lambda: self.action_details(self.current_path)))
        vbox.append(create_menu_btn("Crear carpeta", self.action_create_folder))
        vbox.append(create_menu_btn("Crear archivo", self.action_create_file))
        
        popover.set_child(vbox)
        popover.popup()

    def action_copy(self, path):
        from gi.repository import GObject
        self.copied_path = path
        display = Gdk.Display.get_default()
        if display:
            try:
                cb = display.get_clipboard()
                val = GObject.Value(GObject.TYPE_STRING, str(path))
                cb.set(val)
                print(f"[ROX-Filer] Copiado al portapapeles: {path}")
            except Exception as e:
                print(f"Error al copiar al portapapeles: {e}")

    def action_paste(self, dest_dir):
        if not hasattr(self, 'copied_path') or self.copied_path is None:
            return
        src = self.copied_path
        dst = dest_dir / src.name
        
        if dst.exists():
            base = src.stem
            suffix = src.suffix
            counter = 1
            while True:
                dst = dest_dir / f"{base}_copy{counter}{suffix}"
                if not dst.exists():
                    break
                counter += 1
                
        try:
            import shutil
            if src.is_dir():
                shutil.copytree(src, dst)
            else:
                shutil.copy2(src, dst)
            self.rescan()
        except Exception as e:
            self.show_error_dialog(f"Error al pegar:\n{e}")

    def show_error_dialog(self, message):
        dialog = Gtk.Window(transient_for=self, modal=True, title="Error")
        dialog.set_default_size(300, 150)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        dialog.set_child(vbox)
        
        lbl = Gtk.Label(label=message)
        lbl.set_wrap(True)
        lbl.set_halign(Gtk.Align.CENTER)
        vbox.append(lbl)
        
        btn = Gtk.Button(label="Aceptar")
        btn.set_halign(Gtk.Align.CENTER)
        btn.connect("clicked", lambda b: dialog.destroy())
        vbox.append(btn)
        
        dialog.present()

    def action_details(self, path):
        dialog = Gtk.Window(transient_for=self, modal=True, title=f"Detalles - {path.name}")
        dialog.set_default_size(350, 250)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        dialog.set_child(vbox)
        
        grid = Gtk.Grid()
        grid.set_column_spacing(12)
        grid.set_row_spacing(6)
        grid.set_halign(Gtk.Align.FILL)
        vbox.append(grid)
        
        import stat
        import datetime
        import pwd
        import grp
        
        file_type = "Desconocido"
        file_size_str = "-"
        file_owner = "-"
        file_group = "-"
        file_mtime = "-"
        file_atime = "-"
        file_perms = "-"
        
        try:
            stat_info = path.stat()
            if path.is_symlink():
                file_type = "Enlace simbólico"
            elif path.is_dir():
                file_type = "Directorio"
            else:
                file_type = "Archivo regular"
                
            size_bytes = stat_info.st_size
            if size_bytes < 1024:
                file_size_str = f"{size_bytes} B"
            elif size_bytes < 1024 * 1024:
                file_size_str = f"{size_bytes/1024:.2f} KB ({size_bytes} bytes)"
            else:
                file_size_str = f"{size_bytes/(1024*1024):.2f} MB ({size_bytes} bytes)"
                
            try:
                file_owner = pwd.getpwuid(stat_info.st_uid).pw_name
            except Exception:
                file_owner = str(stat_info.st_uid)
            try:
                file_group = grp.getgrgid(stat_info.st_gid).gr_name
            except Exception:
                file_group = str(stat_info.st_gid)
                
            file_mtime = datetime.datetime.fromtimestamp(stat_info.st_mtime).strftime("%d/%m/%Y %H:%M:%S")
            file_atime = datetime.datetime.fromtimestamp(stat_info.st_atime).strftime("%d/%m/%Y %H:%M:%S")
            
            mode = stat_info.st_mode
            file_perms = f"{stat.filemode(mode)} ({oct(mode & 0o777)})"
        except Exception as e:
            print(f"Error reading stats: {e}")
            
        properties = [
            ("Nombre:", path.name),
            ("Ruta completa:", str(path)),
            ("Tipo:", file_type),
            ("Tamaño:", file_size_str),
            ("Propietario:", file_owner),
            ("Grupo:", file_group),
            ("Modificado:", file_mtime),
            ("Accedido:", file_atime),
            ("Permisos:", file_perms),
        ]
        
        for idx, (label_text, value_text) in enumerate(properties):
            lbl_name = Gtk.Label()
            lbl_name.set_markup(f"<b>{label_text}</b>")
            lbl_name.set_halign(Gtk.Align.END)
            grid.attach(lbl_name, 0, idx, 1, 1)
            
            lbl_val = Gtk.Label(label=value_text)
            lbl_val.set_halign(Gtk.Align.START)
            lbl_val.set_selectable(True)
            lbl_val.set_wrap(True)
            grid.attach(lbl_val, 1, idx, 1, 1)
            
        btn_close = Gtk.Button(label="Cerrar")
        btn_close.set_halign(Gtk.Align.CENTER)
        btn_close.connect("clicked", lambda b: dialog.destroy())
        vbox.append(btn_close)
        
        dialog.present()

    def action_compress(self, path):
        dialog = Gtk.Window(transient_for=self, modal=True, title="Comprimir elemento")
        dialog.set_default_size(350, 180)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        dialog.set_child(vbox)
        
        lbl = Gtk.Label(label=f"Comprimir: {path.name}")
        lbl.set_halign(Gtk.Align.START)
        vbox.append(lbl)
        
        entry_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=6)
        vbox.append(entry_box)
        
        lbl_name = Gtk.Label(label="Nombre del archivo:")
        entry_box.append(lbl_name)
        
        entry = Gtk.Entry()
        entry.set_hexpand(True)
        entry.set_text(f"{path.name}.tar.gz")
        entry_box.append(entry)
        
        format_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        vbox.append(format_box)
        
        lbl_format = Gtk.Label(label="Formato:")
        format_box.append(lbl_format)
        
        rb_tgz = Gtk.CheckButton(label=".tar.gz")
        rb_tgz.set_active(True)
        format_box.append(rb_tgz)
        
        rb_zip = Gtk.CheckButton(label=".zip")
        rb_zip.set_group(rb_tgz)
        format_box.append(rb_zip)
        
        def on_tgz_toggled(widget):
            if rb_tgz.get_active():
                entry.set_text(f"{path.name}.tar.gz")
            else:
                entry.set_text(f"{path.name}.zip")
        rb_tgz.connect("toggled", on_tgz_toggled)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)
        vbox.append(btn_box)
        
        btn_cancel = Gtk.Button(label="Cancelar")
        btn_cancel.connect("clicked", lambda b: dialog.destroy())
        btn_box.append(btn_cancel)
        
        def do_compression():
            archive_name = entry.get_text().strip()
            if not archive_name:
                return
            
            archive_path = path.parent / archive_name
            format_type = "zip" if rb_zip.get_active() else "tar.gz"
            
            try:
                import tarfile
                import zipfile
                import os
                
                if format_type == "zip":
                    with zipfile.ZipFile(archive_path, 'w', zipfile.ZIP_DEFLATED) as zipf:
                        if path.is_dir():
                            for root, dirs, files in os.walk(path):
                                for file in files:
                                    filepath = Path(root) / file
                                    arcname = filepath.relative_to(path.parent)
                                    zipf.write(filepath, arcname)
                        else:
                            zipf.write(path, path.name)
                else:
                    with tarfile.open(archive_path, 'w:gz') as tarf:
                        if path.is_dir():
                            tarf.add(path, arcname=path.name)
                        else:
                            tarf.add(path, arcname=path.name)
                            
                dialog.destroy()
                self.rescan()
            except Exception as e:
                self.show_error_dialog(f"Error al comprimir:\n{e}")
                
        btn_confirm = Gtk.Button(label="Comprimir")
        btn_confirm.connect("clicked", lambda b: do_compression())
        btn_box.append(btn_confirm)
        
        dialog.present()

    def action_decompress(self, path):
        try:
            import tarfile
            import zipfile
            
            suffix = path.suffix.lower()
            if suffix == '.zip':
                with zipfile.ZipFile(path, 'r') as zipf:
                    zipf.extractall(self.current_path)
            elif suffix in ['.tar', '.gz', '.tgz', '.bz2', '.xz'] or path.name.endswith('.tar.gz'):
                with tarfile.open(path, 'r:*') as tarf:
                    tarf.extractall(self.current_path)
            self.rescan()
        except Exception as e:
            self.show_error_dialog(f"Error al descomprimir:\n{e}")

    def action_create_folder(self):
        dialog = Gtk.Window(transient_for=self, modal=True, title="Nueva Carpeta")
        dialog.set_default_size(300, 120)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        dialog.set_child(vbox)
        
        lbl = Gtk.Label(label="Nombre de la nueva carpeta:")
        lbl.set_halign(Gtk.Align.START)
        vbox.append(lbl)
        
        entry = Gtk.Entry()
        vbox.append(entry)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)
        vbox.append(btn_box)
        
        btn_cancel = Gtk.Button(label="Cancelar")
        btn_cancel.connect("clicked", lambda b: dialog.destroy())
        btn_box.append(btn_cancel)
        
        def do_create():
            name = entry.get_text().strip()
            if not name:
                return
            new_dir = self.current_path / name
            try:
                new_dir.mkdir(parents=False, exist_ok=False)
                dialog.destroy()
                self.rescan()
            except Exception as e:
                self.show_error_dialog(f"Error al crear carpeta:\n{e}")
                
        btn_confirm = Gtk.Button(label="Crear")
        btn_confirm.connect("clicked", lambda b: do_create())
        entry.connect("activate", lambda e: do_create())
        btn_box.append(btn_confirm)
        
        dialog.present()
        entry.grab_focus()

    def action_create_file(self):
        dialog = Gtk.Window(transient_for=self, modal=True, title="Nuevo Archivo")
        dialog.set_default_size(300, 120)
        
        vbox = Gtk.Box(orientation=Gtk.Orientation.VERTICAL, spacing=12)
        vbox.set_margin_start(16)
        vbox.set_margin_end(16)
        vbox.set_margin_top(16)
        vbox.set_margin_bottom(16)
        dialog.set_child(vbox)
        
        lbl = Gtk.Label(label="Nombre del nuevo archivo:")
        lbl.set_halign(Gtk.Align.START)
        vbox.append(lbl)
        
        entry = Gtk.Entry()
        vbox.append(entry)
        
        btn_box = Gtk.Box(orientation=Gtk.Orientation.HORIZONTAL, spacing=12)
        btn_box.set_halign(Gtk.Align.END)
        vbox.append(btn_box)
        
        btn_cancel = Gtk.Button(label="Cancelar")
        btn_cancel.connect("clicked", lambda b: dialog.destroy())
        btn_box.append(btn_cancel)
        
        def do_create():
            name = entry.get_text().strip()
            if not name:
                return
            new_file = self.current_path / name
            try:
                new_file.touch(exist_ok=False)
                dialog.destroy()
                self.rescan()
            except Exception as e:
                self.show_error_dialog(f"Error al crear archivo:\n{e}")
                
        btn_confirm = Gtk.Button(label="Crear")
        btn_confirm.connect("clicked", lambda b: do_create())
        entry.connect("activate", lambda e: do_create())
        btn_box.append(btn_confirm)
        
        dialog.present()
        entry.grab_focus()