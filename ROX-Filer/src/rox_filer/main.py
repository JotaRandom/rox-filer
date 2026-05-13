import sys
from pathlib import Path

from gi.repository import Gtk, Gio

from .window import RoxFilerWindow

def main():
    app = Gtk.Application(
        application_id="org.rox.filer",
        flags=Gio.ApplicationFlags.FLAGS_NONE
    )
    
    def on_activate(app):
        window = RoxFilerWindow(app)
        window.present()
    
    app.connect("activate", on_activate)
    sys.exit(app.run(sys.argv))

if __name__ == "__main__":
    main()