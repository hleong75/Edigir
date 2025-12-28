# Edigir - LED Destination Sign Editor

A Python recreation of Edigir11, a destination sign editor for public transport LED displays (girouettes).

## Features

- **Destination Editor**: Create and edit destination messages with up to 3 alternances
- **Font Editor**: Pixel-by-pixel editing of LED display fonts
- **Display Preview**: Real-time LED matrix simulation
- **Animation Support**: Scrolling text and alternance timing
- **Color LED Support**: Color palette management for color LED displays
- **File Compatibility**: Import/export DSW (destination) and POL (font) files

## Requirements

- Python 3.8+
- Tkinter (usually included with Python)

### Installing Tkinter

**Ubuntu/Debian:**
```bash
sudo apt-get install python3-tk
```

**Fedora:**
```bash
sudo dnf install python3-tkinter
```

**macOS:**
Tkinter is included with Python from python.org

**Windows:**
Tkinter is included with Python from python.org

## Usage

### Running the Application

```bash
python run_edigir.py
```

Or:
```bash
python -m edigir_py.main
```

### Quick Start

1. **New Project**: File → New (Ctrl+N)
2. **Add Messages**: Edit → New Message (Ctrl+Insert)
3. **Edit Text**: Type in the alternance text fields
4. **Preview**: View the LED display preview on the right
5. **Save**: File → Save (Ctrl+S)

### Keyboard Shortcuts

| Shortcut | Action |
|----------|--------|
| Ctrl+N | New file |
| Ctrl+O | Open file |
| Ctrl+S | Save file |
| Ctrl+P | Font editor |
| Ctrl+G | Configure displays |
| Ctrl+R | Quick view |
| Ctrl+U | Simulation |
| Page Up | Previous message |
| Page Down | Next message |
| F1 | Help |

### Special Characters

- `|` (pipe) - Line break
- `²` - Single column skip (1 pixel)

## File Formats

### DSW Files (Destinations)
Contains destination messages with:
- Message numbers (1-9999)
- Header text
- Up to 3 alternances
- Animation settings
- Color information (for color displays)

### POL Files (Fonts)
Contains LED font definitions:
- Multiple font sizes (7px, 14px, 16px height)
- Font codes: 0-5, A-F
- Custom character bitmaps

### PAL Files (Palette)
Contains color palette for color LED displays:
- RGB values for display
- LED-specific color values
- Color names

## Project Structure

```
edigir_py/
├── __init__.py      # Package initialization
├── main.py          # Main application GUI
├── models.py        # Data models
├── parsers.py       # File format parsers
├── renderer.py      # LED display renderer
└── font_editor.py   # Font editing widget
```

## Screenshots

The application provides:
- Modern themed interface using ttk
- LED matrix preview with authentic amber/color LEDs
- Pixel-based font editor
- Message list quick view
- Full simulation mode

## Improvements over Edigir11

- **Cross-platform**: Runs on Windows, macOS, and Linux
- **Modern UI**: Clean, themed interface
- **Better error handling**: Graceful handling of file errors
- **Unicode support**: Full UTF-8 text handling
- **Undo support**: (Planned) Full undo/redo functionality
- **Export options**: Export to various formats

## License

This is a recreation of the Edigir11 software for educational and preservation purposes.

## Contributing

Contributions are welcome! Please feel free to submit pull requests.
