import sys
from pathlib import Path

import gi
gi.require_version('Gtk', '4.0')
from gi.repository import Gtk, Gio

from .window import RoxFilerWindow

def main():
    # Parse arguments manually to handle compatibility flags and directory paths
    args = sys.argv[1:]
    
    # Handle help flag
    if "--help" in args or "-h" in args:
        print("Uso: AppRun [OPCIÓN] [DIRECTORIO]")
        print("")
        print("Opciones:")
        print("  -h, --help      Mostrar esta ayuda")
        print("  --rox-filer     Bandera de compatibilidad de ROX-Filer")
        sys.exit(0)
        
    # Filter out --rox-filer compatibility flag
    if "--rox-filer" in args:
        args.remove("--rox-filer")
        
    # Get the target directory if passed
    target_path = None
    for arg in args:
        if not arg.startswith("-"):
            try:
                p = Path(arg).expanduser().resolve()
                if p.is_dir():
                    target_path = p
                    break
            except Exception:
                pass

    app = Gtk.Application(
        application_id="org.rox.filer",
        flags=Gio.ApplicationFlags.FLAGS_NONE
    )
    
    def on_activate(app):
        window = RoxFilerWindow(app, initial_path=target_path)
        window.present()
    
    app.connect("activate", on_activate)
    # Pass only the script name to app.run to bypass GApplication's strict command-line validation
    sys.exit(app.run([sys.argv[0]]))

if __name__ == "__main__":
    main()