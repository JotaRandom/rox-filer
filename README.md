# ROX-Filer (Modern Python 3 + GTK4 Port)

A modernized port of the classic RISC OS-like file manager for X11 and Wayland, built using Python 3, PyGObject, and GTK 4.

## Quick Start & Local Execution

To run ROX-Filer locally using a virtual environment:

1. **Clone and enter the directory**:
   ```bash
   cd rox-filer
   ```

2. **Set up the virtual environment**:
   ```bash
   python3 -m venv .venv
   source .venv/bin/activate
   pip install pygobject Pillow
   ```

3. **Run the file manager**:
   ```bash
   ./AppRun [options] [directory]
   ```

   *Use `./AppRun --help` to show all supported command-line parameters.*

## Installation

### Local Installation
To make ROX-Filer accessible only to your user, you can create a symlink in your local bin directory:
```bash
ln -s /path/to/rox-filer/AppRun ~/.local/bin/rox-filer
```

### Global Installation
For system-wide usage, you can symlink the launcher to `/usr/local/bin`:
```bash
sudo ln -s /absolute/path/to/rox-filer/AppRun /usr/local/bin/rox
```

You can also copy the desktop configuration file and application icon to standard locations to integrate it with your desktop environment launcher:
```bash
cp /path/to/rox-filer/ROX-Filer.xml ~/.local/share/mime/packages/
cp /path/to/rox-filer/ROX-Filer/app_icon/org.rox.filer.png ~/.local/share/icons/hicolor/512x512/apps/
```

## Running under X11 vs Wayland

ROX-Filer is built using native **GTK4** APIs via **PyGObject**, which makes it fully independent of X11-only libraries (such as Xlib or Xt).

* **Under X11**: Simply launch `./AppRun`. GTK4 automatically hooks into your X server.
* **Under Wayland**: Simply launch `./AppRun`. The application runs natively on Wayland without relying on XWayland. The window will be mapped correctly to the registered Application ID `org.rox.filer`.

## Internationalization (i18n)

ROX-Filer automatically detects and adapts to your system locale using the standard environment variables (`LANG`, `LC_ALL`, `LC_MESSAGES`).

To force a specific language, run the application prefixing the environment variable:
```bash
LANG=es_ES.UTF-8 ./AppRun
```

## License

This program is free software; you can redistribute it and/or modify it under the terms of the GNU General Public License as published by the Free Software Foundation; either version 2 of the License, or (at your option) any later version.
