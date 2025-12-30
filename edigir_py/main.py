"""
Main GUI Application for Edigir.
A modern Python recreation of the Edigir11 destination sign editor.
"""

import tkinter as tk
from tkinter import ttk, messagebox, filedialog
import os
from typing import Optional

from .models import (
    Project, Message, Alternance, DisplayConfig, 
    Font, Palette, AnimationType
)
from .parsers import DSWParser, POLParser, PALParser, GIRParser, LEDParser
from .renderer import LEDRenderer, DisplayPreview
from .font_editor import FontEditorWidget
from .fullscreen_display import FullscreenGirouette, ScreenDetectionDialog
from .image_export import ImageExporter, check_pil_available, get_supported_formats


class EditorApplication(tk.Tk):
    """Main application window."""
    
    def __init__(self):
        super().__init__()
        
        self.title("Edigir - Éditeur de girouettes")
        self.geometry("1200x800")
        
        # Set theme
        self.style = ttk.Style()
        self._setup_theme()
        
        # Data
        self.project = Project()
        self.current_message_num: int = 1
        self.current_display_type: str = "front"
        self.modified: bool = False
        self.current_file: Optional[str] = None
        
        # Load default display configs
        self._load_default_configs()
        
        # Create UI
        self._create_menu()
        self._create_toolbar()
        self._create_main_content()
        self._create_status_bar()
        
        # Initialize with empty project
        self._new_project()
        
        # Bind keyboard shortcuts
        self._bind_shortcuts()
        
        # Protocol for window close
        self.protocol("WM_DELETE_WINDOW", self._on_close)
    
    def _setup_theme(self):
        """Set up the application theme."""
        # Try to use a modern theme
        available_themes = self.style.theme_names()
        if 'clam' in available_themes:
            self.style.theme_use('clam')
        
        # Custom styles
        self.style.configure('Title.TLabel', font=('Helvetica', 12, 'bold'))
        self.style.configure('Status.TLabel', font=('Helvetica', 9))
        self.style.configure('Toolbar.TButton', padding=5)
    
    def _load_default_configs(self):
        """Load default display configurations."""
        # Default display configs based on Edigir11 files
        self.available_displays = {
            "07x80": DisplayConfig("07x80", "Girouette à LEDs", 7, 80),
            "08x84": DisplayConfig("08x84", "Girouette à LEDs", 8, 84),
            "16x084": DisplayConfig("16x084", "Girouette à LEDs", 16, 84),
            "16x112": DisplayConfig("16x112", "Girouette à LEDs", 16, 112),
            "16x140": DisplayConfig("16x140", "Girouette à LEDs", 16, 140),
            "16x028": DisplayConfig("16x028", "Girouette à LEDs", 16, 28, has_icon=1),
            "24x40": DisplayConfig("24x40", "Girouette LED couleur", 24, 40, is_color=1),
            "16x28+16x84": DisplayConfig("16x28+16x84", "Girouette bimode", 16, 28, 16, 84),
            "24x40+16x84": DisplayConfig("24x40+16x84", "Girouette bimode LED couleur", 24, 40, 16, 84, is_color=1),
        }
        
        # Set default
        self.project.front_display = self.available_displays.get("16x084")
    
    def _create_menu(self):
        """Create the menu bar."""
        menubar = tk.Menu(self)
        self.config(menu=menubar)
        
        # Destinations menu
        dest_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Destinations", menu=dest_menu)
        dest_menu.add_command(label="Nouveau", command=self._new_project, accelerator="Ctrl+N")
        dest_menu.add_command(label="Charger...", command=self._open_file, accelerator="Ctrl+O")
        dest_menu.add_command(label="Enregistrer", command=self._save_file, accelerator="Ctrl+S")
        dest_menu.add_command(label="Enregistrer sous...", command=self._save_file_as)
        dest_menu.add_separator()
        dest_menu.add_command(label="Importer ancienne version...", command=self._import_old)
        dest_menu.add_command(label="Exporter liste...", command=self._export_list)
        dest_menu.add_separator()
        
        # Export submenu for images
        export_menu = tk.Menu(dest_menu, tearoff=0)
        dest_menu.add_cascade(label="Exporter image...", menu=export_menu)
        export_menu.add_command(label="Exporter en PNG...", command=self._export_png, accelerator="Ctrl+E")
        export_menu.add_command(label="Exporter en JPG...", command=self._export_jpg)
        export_menu.add_command(label="Exporter en GIF animé...", command=self._export_gif)
        
        dest_menu.add_separator()
        dest_menu.add_command(label="Quitter", command=self._on_close, accelerator="Alt+F4")
        
        # Edition menu
        edit_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Édition", menu=edit_menu)
        edit_menu.add_command(label="Nouveau message", command=self._new_message, accelerator="Ctrl+Ins")
        edit_menu.add_command(label="Supprimer message", command=self._delete_message, accelerator="Ctrl+Del")
        edit_menu.add_separator()
        edit_menu.add_command(label="Visualisation rapide", command=self._show_quick_view, accelerator="Ctrl+R")
        edit_menu.add_command(label="Simulation", command=self._show_simulation, accelerator="Ctrl+U")
        edit_menu.add_separator()
        edit_menu.add_command(label="Mode Girouette (plein écran)", command=self._show_fullscreen_girouette, accelerator="F11")
        
        # Polices menu
        font_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Polices", menu=font_menu)
        font_menu.add_command(label="Éditeur de polices", command=self._show_font_editor, accelerator="Ctrl+P")
        font_menu.add_command(label="Charger police...", command=self._load_font)
        font_menu.add_command(label="Enregistrer police...", command=self._save_font)
        
        # Configuration menu
        config_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Configuration", menu=config_menu)
        config_menu.add_command(label="Girouettes...", command=self._configure_displays, accelerator="Ctrl+G")
        config_menu.add_command(label="Palette de couleurs...", command=self._configure_palette)
        
        # Help menu
        help_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="?", menu=help_menu)
        help_menu.add_command(label="Aide", command=self._show_help, accelerator="F1")
        help_menu.add_separator()
        help_menu.add_command(label="À propos...", command=self._show_about)
    
    def _create_toolbar(self):
        """Create the toolbar."""
        toolbar = ttk.Frame(self)
        toolbar.pack(fill=tk.X, padx=5, pady=2)
        
        # File buttons
        ttk.Button(toolbar, text="📄", width=3, command=self._new_project,
                   style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="📂", width=3, command=self._open_file,
                   style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="💾", width=3, command=self._save_file,
                   style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Edit buttons
        ttk.Button(toolbar, text="➕", width=3, command=self._new_message,
                   style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        ttk.Button(toolbar, text="➖", width=3, command=self._delete_message,
                   style='Toolbar.TButton').pack(side=tk.LEFT, padx=1)
        
        ttk.Separator(toolbar, orient=tk.VERTICAL).pack(side=tk.LEFT, fill=tk.Y, padx=5)
        
        # Font selector
        ttk.Label(toolbar, text="Police:").pack(side=tk.LEFT, padx=5)
        self.font_var = tk.StringVar(value="2")
        font_combo = ttk.Combobox(
            toolbar,
            textvariable=self.font_var,
            values=["0", "1", "2", "3", "4", "5", "A", "B", "C", "D", "E", "F"],
            state="readonly",
            width=5
        )
        font_combo.pack(side=tk.LEFT, padx=2)
        font_combo.bind('<<ComboboxSelected>>', self._on_font_selected)
        
        # Inverse checkbox
        self.inverse_var = tk.BooleanVar()
        ttk.Checkbutton(toolbar, text="Inversé", variable=self.inverse_var).pack(side=tk.LEFT, padx=5)
        
        # Display file info on right
        self.file_label = ttk.Label(toolbar, text="Nouveau fichier", style='Status.TLabel')
        self.file_label.pack(side=tk.RIGHT, padx=10)
    
    def _create_main_content(self):
        """Create the main content area."""
        # Main paned window
        main_paned = ttk.PanedWindow(self, orient=tk.HORIZONTAL)
        main_paned.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left panel - Message editor
        left_frame = ttk.Frame(main_paned)
        main_paned.add(left_frame, weight=2)
        
        # Message navigation
        nav_frame = ttk.LabelFrame(left_frame, text="Numéro de message")
        nav_frame.pack(fill=tk.X, padx=5, pady=5)
        
        nav_inner = ttk.Frame(nav_frame)
        nav_inner.pack(padx=10, pady=10)
        
        ttk.Button(nav_inner, text="◀◀", width=4, 
                   command=lambda: self._navigate_message(-10)).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_inner, text="◀", width=3,
                   command=lambda: self._navigate_message(-1)).pack(side=tk.LEFT, padx=2)
        
        self.msg_num_var = tk.StringVar(value="1")
        self.msg_combo = ttk.Combobox(
            nav_inner,
            textvariable=self.msg_num_var,
            width=10
        )
        self.msg_combo.pack(side=tk.LEFT, padx=10)
        self.msg_combo.bind('<<ComboboxSelected>>', self._on_message_selected)
        self.msg_combo.bind('<Return>', self._on_message_entered)
        
        ttk.Button(nav_inner, text="▶", width=3,
                   command=lambda: self._navigate_message(1)).pack(side=tk.LEFT, padx=2)
        ttk.Button(nav_inner, text="▶▶", width=4,
                   command=lambda: self._navigate_message(10)).pack(side=tk.LEFT, padx=2)
        
        ttk.Button(nav_inner, text="Modifier n°", 
                   command=self._change_message_number).pack(side=tk.LEFT, padx=10)
        
        # Display tabs (Front, Side, Rear)
        self.display_notebook = ttk.Notebook(left_frame)
        self.display_notebook.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create tabs for each display type
        self.front_tab = self._create_message_editor_tab("Avant")
        self.display_notebook.add(self.front_tab, text="Girouette Avant")
        
        self.side_tab = self._create_message_editor_tab("Latérale")
        self.display_notebook.add(self.side_tab, text="Girouette Latérale")
        
        self.rear_tab = self._create_message_editor_tab("Arrière")
        self.display_notebook.add(self.rear_tab, text="Girouette Arrière")
        
        self.display_notebook.bind('<<NotebookTabChanged>>', self._on_tab_changed)
        
        # Right panel - Preview
        right_frame = ttk.Frame(main_paned)
        main_paned.add(right_frame, weight=1)
        
        # Display preview
        preview_frame = ttk.LabelFrame(right_frame, text="Aperçu girouette")
        preview_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Display type label
        self.display_type_label = ttk.Label(preview_frame, text="16x084", style='Title.TLabel')
        self.display_type_label.pack(pady=5)
        
        # LED Preview
        self.display_preview = DisplayPreview(preview_frame)
        self.display_preview.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Animation controls
        anim_frame = ttk.Frame(preview_frame)
        anim_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(anim_frame, text="▶ Jouer", 
                   command=self._play_animation).pack(side=tk.LEFT, padx=5)
        ttk.Button(anim_frame, text="↔ Défiler",
                   command=self._play_scroll_animation).pack(side=tk.LEFT, padx=5)
        ttk.Button(anim_frame, text="⏹ Stop",
                   command=self._stop_animation).pack(side=tk.LEFT, padx=5)
        
        # Options frame
        options_frame = ttk.LabelFrame(right_frame, text="Options")
        options_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Film number
        opt_row1 = ttk.Frame(options_frame)
        opt_row1.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(opt_row1, text="N° Film:").pack(side=tk.LEFT)
        self.film_var = tk.StringVar()
        ttk.Entry(opt_row1, textvariable=self.film_var, width=10).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(opt_row1, text="SAE:").pack(side=tk.LEFT, padx=(20, 0))
        self.sae_var = tk.StringVar()
        ttk.Entry(opt_row1, textvariable=self.sae_var, width=10).pack(side=tk.LEFT, padx=5)
    
    def _create_message_editor_tab(self, display_name: str) -> ttk.Frame:
        """Create a message editor tab for a display type."""
        frame = ttk.Frame(self.display_notebook)
        
        # Header entry
        header_frame = ttk.LabelFrame(frame, text="En-tête (partie fixe)")
        header_frame.pack(fill=tk.X, padx=5, pady=5)
        
        header_inner = ttk.Frame(header_frame)
        header_inner.pack(fill=tk.X, padx=10, pady=10)
        
        header_entry = ttk.Entry(header_inner, width=50)
        header_entry.pack(fill=tk.X)
        header_entry.bind('<KeyRelease>', lambda e: self._on_text_changed())
        
        # Store reference
        frame.header_entry = header_entry
        
        # Alternances
        alt_frame = ttk.LabelFrame(frame, text="Alternances")
        alt_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        frame.alternances = []
        
        for i in range(3):
            alt_panel = ttk.Frame(alt_frame)
            alt_panel.pack(fill=tk.X, padx=10, pady=5)
            
            # Alternance number
            ttk.Label(alt_panel, text=f"Alt. {i+1}:", width=6).pack(side=tk.LEFT)
            
            # Text entry
            text_entry = ttk.Entry(alt_panel, width=40)
            text_entry.pack(side=tk.LEFT, padx=5, fill=tk.X, expand=True)
            text_entry.bind('<KeyRelease>', lambda e: self._on_text_changed())
            
            # Duration
            ttk.Label(alt_panel, text="Durée:").pack(side=tk.LEFT, padx=(10, 2))
            duration_var = tk.StringVar(value="30")
            duration_entry = ttk.Spinbox(
                alt_panel,
                textvariable=duration_var,
                from_=1,
                to=999,
                width=5
            )
            duration_entry.pack(side=tk.LEFT)
            ttk.Label(alt_panel, text="1/10s").pack(side=tk.LEFT, padx=2)
            
            # Animation type
            ttk.Label(alt_panel, text="Anim:").pack(side=tk.LEFT, padx=(10, 2))
            anim_var = tk.StringVar(value="Fixe")
            anim_combo = ttk.Combobox(
                alt_panel,
                textvariable=anim_var,
                values=["Fixe", "Défilant gauche", "Défilant droite", "Clignotant"],
                state="readonly",
                width=15
            )
            anim_combo.pack(side=tk.LEFT)
            
            frame.alternances.append({
                'text_entry': text_entry,
                'duration_var': duration_var,
                'anim_var': anim_var
            })
        
        # Color selection for color displays
        color_frame = ttk.LabelFrame(frame, text="Couleurs (LED couleur)")
        color_frame.pack(fill=tk.X, padx=5, pady=5)
        
        color_inner = ttk.Frame(color_frame)
        color_inner.pack(padx=10, pady=10)
        
        ttk.Label(color_inner, text="Texte:").pack(side=tk.LEFT)
        text_color_btn = tk.Button(
            color_inner,
            bg="#ff6600",
            width=3,
            relief=tk.RAISED
        )
        text_color_btn.pack(side=tk.LEFT, padx=5)
        frame.text_color_btn = text_color_btn
        
        ttk.Label(color_inner, text="Fond:").pack(side=tk.LEFT, padx=(20, 0))
        bg_color_btn = tk.Button(
            color_inner,
            bg="#000000",
            width=3,
            relief=tk.RAISED
        )
        bg_color_btn.pack(side=tk.LEFT, padx=5)
        frame.bg_color_btn = bg_color_btn
        
        return frame
    
    def _create_status_bar(self):
        """Create the status bar."""
        status_frame = ttk.Frame(self)
        status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = ttk.Label(status_frame, text="Prêt", style='Status.TLabel')
        self.status_label.pack(side=tk.LEFT, padx=10, pady=5)
        
        # Character count
        self.char_count_label = ttk.Label(status_frame, text="0/240 caractères", style='Status.TLabel')
        self.char_count_label.pack(side=tk.RIGHT, padx=10, pady=5)
        
        # Column count
        self.col_count_label = ttk.Label(status_frame, text="0/1600 colonnes", style='Status.TLabel')
        self.col_count_label.pack(side=tk.RIGHT, padx=10, pady=5)
    
    def _bind_shortcuts(self):
        """Bind keyboard shortcuts."""
        self.bind('<Control-n>', lambda e: self._new_project())
        self.bind('<Control-o>', lambda e: self._open_file())
        self.bind('<Control-s>', lambda e: self._save_file())
        self.bind('<Control-e>', lambda e: self._export_png())
        self.bind('<Control-p>', lambda e: self._show_font_editor())
        self.bind('<Control-g>', lambda e: self._configure_displays())
        self.bind('<Control-r>', lambda e: self._show_quick_view())
        self.bind('<Control-u>', lambda e: self._show_simulation())
        self.bind('<Control-Insert>', lambda e: self._new_message())
        self.bind('<Control-Delete>', lambda e: self._delete_message())
        self.bind('<Prior>', lambda e: self._navigate_message(-1))  # PageUp
        self.bind('<Next>', lambda e: self._navigate_message(1))   # PageDown
        self.bind('<F1>', lambda e: self._show_help())
        self.bind('<F11>', lambda e: self._show_fullscreen_girouette())
    
    # --- File operations ---
    
    def _new_project(self):
        """Create a new project."""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Nouveau fichier",
                "Voulez-vous enregistrer les modifications?"
            )
            if result is True:
                self._save_file()
            elif result is None:
                return
        
        self.project = Project()
        self.project.front_display = self.available_displays.get("16x084")
        self.project.add_message(1)
        
        self.current_file = None
        self.modified = False
        self.current_message_num = 1
        
        self._update_ui()
        self._set_status("Nouveau fichier créé")
    
    def _open_file(self):
        """Open a DSW file."""
        filename = filedialog.askopenfilename(
            title="Charger un fichier destination",
            filetypes=[
                ("Fichiers destination", "*.dsw"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if not filename:
            return
        
        try:
            self.project, font_file = DSWParser.parse(filename)
            self.current_file = filename
            self.modified = False
            
            # Try to load font file
            if font_file:
                font_path = font_file
                if not os.path.isabs(font_path):
                    font_path = os.path.join(os.path.dirname(filename), font_file)
                
                if os.path.exists(font_path):
                    try:
                        self.project.fonts = POLParser.parse(font_path)
                    except Exception:
                        pass
            
            # Set current message to first
            msg_nums = self.project.get_sorted_message_numbers()
            self.current_message_num = msg_nums[0] if msg_nums else 1
            
            self._update_ui()
            self._set_status(f"Fichier chargé: {os.path.basename(filename)}")
            
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible de charger le fichier:\n{e}")
    
    def _save_file(self):
        """Save the current file."""
        if not self.current_file:
            self._save_file_as()
            return
        
        try:
            DSWParser.write(self.current_file, self.project)
            self.modified = False
            self._set_status(f"Fichier enregistré: {os.path.basename(self.current_file)}")
        except Exception as e:
            messagebox.showerror("Erreur", f"Impossible d'enregistrer:\n{e}")
    
    def _save_file_as(self):
        """Save file with new name."""
        filename = filedialog.asksaveasfilename(
            title="Enregistrer sous",
            defaultextension=".dsw",
            filetypes=[
                ("Fichiers destination", "*.dsw"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if filename:
            self.current_file = filename
            self._save_file()
    
    def _import_old(self):
        """Import old format file."""
        messagebox.showinfo("Import", "Fonction d'import non implémentée")
    
    def _export_list(self):
        """Export message list."""
        filename = filedialog.asksaveasfilename(
            title="Exporter la liste",
            defaultextension=".txt",
            filetypes=[("Fichiers texte", "*.txt")]
        )
        
        if filename:
            try:
                with open(filename, 'w', encoding='utf-8') as f:
                    f.write("N°\tEn-tête\tAlternance 1\tAlternance 2\tAlternance 3\n")
                    for num in self.project.get_sorted_message_numbers():
                        msg = self.project.get_message(num)
                        f.write(f"{num}\t{msg.header}\t")
                        f.write(f"{msg.alternances[0].text}\t")
                        f.write(f"{msg.alternances[1].text}\t")
                        f.write(f"{msg.alternances[2].text}\n")
                
                self._set_status(f"Liste exportée: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'export:\n{e}")
    
    def _get_current_message_text(self) -> str:
        """Get the text of current message for export."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return ""
        
        text = msg.header
        if msg.alternances[0].text:
            text += msg.alternances[0].text
        elif msg.alternances[1].text:
            text += msg.alternances[1].text
        elif msg.alternances[2].text:
            text += msg.alternances[2].text
        
        return text
    
    def _export_png(self):
        """Export current message to PNG image."""
        if not check_pil_available():
            messagebox.showerror(
                "Erreur",
                "PIL/Pillow est requis pour l'export d'images.\n"
                "Installez-le avec: pip install Pillow"
            )
            return
        
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            messagebox.showwarning("Attention", "Aucun message à exporter")
            return
        
        text = self._get_current_message_text()
        if not text:
            messagebox.showwarning("Attention", "Le message est vide")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exporter en PNG",
            defaultextension=".png",
            initialfile=f"message_{self.current_message_num}.png",
            filetypes=[("Images PNG", "*.png")]
        )
        
        if filename:
            try:
                exporter = ImageExporter(
                    self.project.front_display or self.available_displays["16x084"],
                    self.project.fonts
                )
                exporter.export_png(text, filename)
                self._set_status(f"Image exportée: {os.path.basename(filename)}")
                messagebox.showinfo("Export réussi", f"Image exportée:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'export:\n{e}")
    
    def _export_jpg(self):
        """Export current message to JPG image."""
        if not check_pil_available():
            messagebox.showerror(
                "Erreur",
                "PIL/Pillow est requis pour l'export d'images.\n"
                "Installez-le avec: pip install Pillow"
            )
            return
        
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            messagebox.showwarning("Attention", "Aucun message à exporter")
            return
        
        text = self._get_current_message_text()
        if not text:
            messagebox.showwarning("Attention", "Le message est vide")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exporter en JPG",
            defaultextension=".jpg",
            initialfile=f"message_{self.current_message_num}.jpg",
            filetypes=[("Images JPEG", "*.jpg;*.jpeg")]
        )
        
        if filename:
            try:
                exporter = ImageExporter(
                    self.project.front_display or self.available_displays["16x084"],
                    self.project.fonts
                )
                exporter.export_jpg(text, filename)
                self._set_status(f"Image exportée: {os.path.basename(filename)}")
                messagebox.showinfo("Export réussi", f"Image exportée:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'export:\n{e}")
    
    def _export_gif(self):
        """Export current message alternances as animated GIF."""
        if not check_pil_available():
            messagebox.showerror(
                "Erreur",
                "PIL/Pillow est requis pour l'export d'images.\n"
                "Installez-le avec: pip install Pillow"
            )
            return
        
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            messagebox.showwarning("Attention", "Aucun message à exporter")
            return
        
        # Check if there's content
        has_content = msg.header or any(alt.text for alt in msg.alternances)
        if not has_content:
            messagebox.showwarning("Attention", "Le message est vide")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Exporter en GIF animé",
            defaultextension=".gif",
            initialfile=f"message_{self.current_message_num}.gif",
            filetypes=[("Images GIF", "*.gif")]
        )
        
        if filename:
            try:
                exporter = ImageExporter(
                    self.project.front_display or self.available_displays["16x084"],
                    self.project.fonts
                )
                exporter.export_message_gif(msg, filename)
                self._set_status(f"GIF exporté: {os.path.basename(filename)}")
                messagebox.showinfo("Export réussi", f"GIF animé exporté:\n{filename}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'export:\n{e}")
    
    # --- Message operations ---
    
    def _new_message(self):
        """Create a new message."""
        # Find next available number
        existing = set(self.project.messages.keys())
        new_num = 1
        while new_num in existing:
            new_num += 1
        
        # Ask for number
        dialog = tk.Toplevel(self)
        dialog.title("Nouveau message")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text="Numéro du nouveau message:").pack(pady=10)
        
        num_var = tk.StringVar(value=str(new_num))
        entry = ttk.Entry(dialog, textvariable=num_var, width=10)
        entry.pack()
        entry.select_range(0, tk.END)
        entry.focus()
        
        def create():
            try:
                num = int(num_var.get())
                if num < 1 or num > 9999:
                    raise ValueError("Numéro invalide")
                if num in self.project.messages:
                    raise ValueError("Ce numéro existe déjà")
                
                self.project.add_message(num)
                self.current_message_num = num
                self.modified = True
                self._update_ui()
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=create).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        entry.bind('<Return>', lambda e: create())
    
    def _delete_message(self):
        """Delete current message."""
        if len(self.project.messages) <= 1:
            messagebox.showwarning("Attention", "Impossible de supprimer le dernier message")
            return
        
        if messagebox.askyesno("Confirmer", f"Supprimer le message n°{self.current_message_num}?"):
            self.project.delete_message(self.current_message_num)
            
            # Go to first remaining message
            nums = self.project.get_sorted_message_numbers()
            self.current_message_num = nums[0] if nums else 1
            
            self.modified = True
            self._update_ui()
    
    def _navigate_message(self, delta: int):
        """Navigate to next/previous message."""
        nums = self.project.get_sorted_message_numbers()
        if not nums:
            return
        
        try:
            idx = nums.index(self.current_message_num)
            new_idx = max(0, min(len(nums) - 1, idx + delta))
            self.current_message_num = nums[new_idx]
            self._update_ui()
        except ValueError:
            self.current_message_num = nums[0]
            self._update_ui()
    
    def _change_message_number(self):
        """Change current message number."""
        current = self.current_message_num
        
        dialog = tk.Toplevel(self)
        dialog.title("Modifier le numéro")
        dialog.geometry("300x100")
        dialog.transient(self)
        dialog.grab_set()
        
        ttk.Label(dialog, text=f"Nouveau numéro pour le message {current}:").pack(pady=10)
        
        num_var = tk.StringVar(value=str(current))
        entry = ttk.Entry(dialog, textvariable=num_var, width=10)
        entry.pack()
        entry.select_range(0, tk.END)
        entry.focus()
        
        def change():
            try:
                new_num = int(num_var.get())
                if new_num < 1 or new_num > 9999:
                    raise ValueError("Numéro invalide (1-9999)")
                if new_num != current and new_num in self.project.messages:
                    raise ValueError("Ce numéro existe déjà")
                
                if new_num != current:
                    msg = self.project.messages.pop(current)
                    msg.number = new_num
                    self.project.messages[new_num] = msg
                    self.current_message_num = new_num
                    self.modified = True
                    self._update_ui()
                
                dialog.destroy()
            except ValueError as e:
                messagebox.showerror("Erreur", str(e))
        
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        ttk.Button(btn_frame, text="OK", command=change).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
        
        entry.bind('<Return>', lambda e: change())
    
    def _on_message_selected(self, event):
        """Handle message selection from combo."""
        try:
            num = int(self.msg_num_var.get().split()[0])
            if num in self.project.messages:
                self.current_message_num = num
                self._load_current_message()
        except (ValueError, IndexError):
            pass
    
    def _on_message_entered(self, event):
        """Handle message number entry."""
        try:
            num = int(self.msg_num_var.get())
            if num in self.project.messages:
                self.current_message_num = num
                self._load_current_message()
        except ValueError:
            pass
    
    # --- UI updates ---
    
    def _update_ui(self):
        """Update all UI elements."""
        # Update message combo
        nums = self.project.get_sorted_message_numbers()
        values = []
        for num in nums:
            msg = self.project.get_message(num)
            preview = msg.alternances[0].text[:20] if msg.alternances[0].text else ""
            values.append(f"{num} - {preview}")
        
        self.msg_combo['values'] = values
        self.msg_num_var.set(str(self.current_message_num))
        
        # Update file label
        if self.current_file:
            name = os.path.basename(self.current_file)
            self.file_label.config(text=f"{name}{'*' if self.modified else ''}")
        else:
            self.file_label.config(text="Nouveau fichier*" if self.modified else "Nouveau fichier")
        
        # Update display label
        if self.project.front_display:
            self.display_type_label.config(text=self.project.front_display.name)
            self.display_preview.set_display_config(self.project.front_display)
        
        # Load current message
        self._load_current_message()
    
    def _load_current_message(self):
        """Load current message into editor."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Get current tab
        current_tab_idx = self.display_notebook.index(self.display_notebook.select())
        tabs = [self.front_tab, self.side_tab, self.rear_tab]
        current_tab = tabs[current_tab_idx]
        
        # Load header
        current_tab.header_entry.delete(0, tk.END)
        current_tab.header_entry.insert(0, msg.header)
        
        # Load alternances
        for i, alt in enumerate(msg.alternances):
            if i < len(current_tab.alternances):
                entry = current_tab.alternances[i]['text_entry']
                entry.delete(0, tk.END)
                entry.insert(0, alt.text)
                
                current_tab.alternances[i]['duration_var'].set(str(alt.duration))
        
        # Update options
        self.film_var.set(msg.film_number)
        self.sae_var.set(msg.sae_code)
        
        # Update preview
        self._update_preview()
        
        # Update character count
        total_chars = len(msg.header) + sum(len(alt.text) for alt in msg.alternances)
        self.char_count_label.config(text=f"{total_chars}/240 caractères")
    
    def _save_current_message(self):
        """Save current editor content to message."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Get current tab
        current_tab_idx = self.display_notebook.index(self.display_notebook.select())
        tabs = [self.front_tab, self.side_tab, self.rear_tab]
        current_tab = tabs[current_tab_idx]
        
        # Save header
        msg.header = current_tab.header_entry.get()
        
        # Save alternances
        for i, alt_widgets in enumerate(current_tab.alternances):
            if i < len(msg.alternances):
                msg.alternances[i].text = alt_widgets['text_entry'].get()
                try:
                    msg.alternances[i].duration = int(alt_widgets['duration_var'].get())
                except ValueError:
                    msg.alternances[i].duration = 30
        
        # Save options
        msg.film_number = self.film_var.get()
        msg.sae_code = self.sae_var.get()
        
        self.modified = True
    
    def _on_text_changed(self):
        """Handle text change in editor."""
        self._save_current_message()
        self._update_preview()
        
        # Update character count
        msg = self.project.get_message(self.current_message_num)
        if msg:
            total_chars = len(msg.header) + sum(len(alt.text) for alt in msg.alternances)
            self.char_count_label.config(text=f"{total_chars}/240 caractères")
    
    def _on_tab_changed(self, event):
        """Handle tab change."""
        self._load_current_message()
    
    def _on_font_selected(self, event):
        """Handle font selection."""
        # Apply font to selected text (future enhancement)
        pass
    
    def _update_preview(self):
        """Update the LED preview."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Get first non-empty alternance
        text = msg.header
        if msg.alternances[0].text:
            text += msg.alternances[0].text
        elif msg.alternances[1].text:
            text += msg.alternances[1].text
        elif msg.alternances[2].text:
            text += msg.alternances[2].text
        
        # Set fonts for preview
        if self.project.fonts:
            self.display_preview.set_fonts(self.project.fonts)
        
        # Render
        fonts = "2" * len(text)  # Default to font 2
        self.display_preview.render_text(text, fonts)
    
    def _play_animation(self):
        """Start animation playback with alternance cycling."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Build list of alternances with their durations
        alternances = []
        for alt in msg.alternances:
            if alt.text:
                text = msg.header + alt.text
                duration = alt.duration * 100  # Convert to milliseconds
                alternances.append((text, duration))
        
        if not alternances:
            # No alternances, use header only
            if msg.header:
                alternances = [(msg.header, 3000)]
        
        if alternances:
            fonts = "2" * max(len(text) for text, _ in alternances)
            self.display_preview.start_alternance_animation(alternances, fonts)
    
    def _play_scroll_animation(self):
        """Start scrolling animation."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        text = msg.header
        for alt in msg.alternances:
            if alt.text:
                text += alt.text
                break
        
        if text:
            fonts = "2" * len(text)
            self.display_preview.start_scroll_animation(text, fonts)
    
    def _stop_animation(self):
        """Stop animation playback."""
        self.display_preview.stop_animation()
    
    # --- Configuration ---
    
    def _configure_displays(self):
        """Show display configuration dialog."""
        dialog = tk.Toplevel(self)
        dialog.title("Configuration des girouettes")
        dialog.geometry("500x400")
        dialog.transient(self)
        dialog.grab_set()
        
        notebook = ttk.Notebook(dialog)
        notebook.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Front display tab
        front_frame = ttk.Frame(notebook)
        notebook.add(front_frame, text="Avant")
        
        ttk.Label(front_frame, text="Type de girouette:").pack(pady=10)
        
        front_var = tk.StringVar()
        if self.project.front_display:
            front_var.set(self.project.front_display.name)
        
        front_combo = ttk.Combobox(
            front_frame,
            textvariable=front_var,
            values=list(self.available_displays.keys()),
            state="readonly",
            width=30
        )
        front_combo.pack()
        
        # Dimensions display
        dims_label = ttk.Label(front_frame, text="")
        dims_label.pack(pady=10)
        
        def update_dims(event=None):
            name = front_var.get()
            if name in self.available_displays:
                d = self.available_displays[name]
                text = f"Dimensions: {d.height1} x {d.width1}"
                if d.is_bimode:
                    text += f" + {d.height2} x {d.width2}"
                dims_label.config(text=text)
        
        front_combo.bind('<<ComboboxSelected>>', update_dims)
        update_dims()
        
        # Buttons
        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=10)
        
        def apply_config():
            name = front_var.get()
            if name in self.available_displays:
                self.project.front_display = self.available_displays[name]
                self._update_ui()
            dialog.destroy()
        
        ttk.Button(btn_frame, text="OK", command=apply_config).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Annuler", command=dialog.destroy).pack(side=tk.LEFT, padx=5)
    
    def _configure_palette(self):
        """Show palette configuration dialog."""
        messagebox.showinfo("Palette", "Éditeur de palette à implémenter")
    
    def _load_font(self):
        """Load a font file."""
        filename = filedialog.askopenfilename(
            title="Charger une police",
            filetypes=[
                ("Fichiers police", "*.pol"),
                ("Tous les fichiers", "*.*")
            ]
        )
        
        if filename:
            try:
                self.project.fonts = POLParser.parse(filename)
                self.project.font_file = filename
                self._update_preview()
                self._set_status(f"Police chargée: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur de chargement:\n{e}")
    
    def _save_font(self):
        """Save font file."""
        if not self.project.fonts:
            messagebox.showwarning("Attention", "Aucune police à enregistrer")
            return
        
        filename = filedialog.asksaveasfilename(
            title="Enregistrer la police",
            defaultextension=".pol",
            filetypes=[("Fichiers police", "*.pol")]
        )
        
        if filename:
            try:
                POLParser.write(filename, self.project.fonts)
                self._set_status(f"Police enregistrée: {os.path.basename(filename)}")
            except Exception as e:
                messagebox.showerror("Erreur", f"Erreur d'enregistrement:\n{e}")
    
    # --- Other dialogs ---
    
    def _show_font_editor(self):
        """Show the font editor window."""
        editor_window = tk.Toplevel(self)
        editor_window.title("Éditeur de polices")
        editor_window.geometry("900x700")
        editor_window.transient(self)
        
        # Create font editor widget
        editor = FontEditorWidget(editor_window)
        editor.pack(fill=tk.BOTH, expand=True)
        
        # Set fonts
        if self.project.fonts:
            editor.set_fonts(self.project.fonts)
        else:
            # Create default fonts
            from .parsers import POLParser
            default_fonts = {}
            for code in ['0', '1', '2', '3', '4', '5', 'A', 'B', 'C', 'D', 'E', 'F']:
                from .models import Font, FontCharacter
                font = Font(name=f"Police {code}", height=16 if code in ['E', 'F'] else 7 if code in ['0', '1'] else 14)
                for c in range(32, 127):
                    char = chr(c)
                    fc = FontCharacter(char=char, width=5, height=font.height)
                    font.characters[char] = fc
                default_fonts[code] = font
            
            editor.set_fonts(default_fonts)
            self.project.fonts = default_fonts
        
        # Menu bar
        menubar = tk.Menu(editor_window)
        editor_window.config(menu=menubar)
        
        file_menu = tk.Menu(menubar, tearoff=0)
        menubar.add_cascade(label="Police", menu=file_menu)
        file_menu.add_command(label="Charger...", command=self._load_font)
        file_menu.add_command(label="Enregistrer", command=self._save_font)
        file_menu.add_separator()
        file_menu.add_command(label="Fermer", command=editor_window.destroy)
    
    def _show_quick_view(self):
        """Show quick view of all messages."""
        view_window = tk.Toplevel(self)
        view_window.title("Visualisation rapide")
        view_window.geometry("800x600")
        view_window.transient(self)
        
        # Create treeview
        columns = ("num", "header", "alt1", "alt2", "alt3")
        tree = ttk.Treeview(view_window, columns=columns, show='headings')
        
        tree.heading("num", text="N°")
        tree.heading("header", text="En-tête")
        tree.heading("alt1", text="Alternance 1")
        tree.heading("alt2", text="Alternance 2")
        tree.heading("alt3", text="Alternance 3")
        
        tree.column("num", width=60)
        tree.column("header", width=150)
        tree.column("alt1", width=180)
        tree.column("alt2", width=180)
        tree.column("alt3", width=180)
        
        # Scrollbars
        vsb = ttk.Scrollbar(view_window, orient=tk.VERTICAL, command=tree.yview)
        hsb = ttk.Scrollbar(view_window, orient=tk.HORIZONTAL, command=tree.xview)
        tree.configure(yscrollcommand=vsb.set, xscrollcommand=hsb.set)
        
        tree.grid(row=0, column=0, sticky='nsew')
        vsb.grid(row=0, column=1, sticky='ns')
        hsb.grid(row=1, column=0, sticky='ew')
        
        view_window.grid_rowconfigure(0, weight=1)
        view_window.grid_columnconfigure(0, weight=1)
        
        # Populate
        for num in self.project.get_sorted_message_numbers():
            msg = self.project.get_message(num)
            tree.insert('', 'end', values=(
                num,
                msg.header,
                msg.alternances[0].text,
                msg.alternances[1].text,
                msg.alternances[2].text
            ))
        
        # Double-click to go to message
        def on_select(event):
            selection = tree.selection()
            if selection:
                item = tree.item(selection[0])
                num = item['values'][0]
                self.current_message_num = num
                self._update_ui()
                view_window.destroy()
        
        tree.bind('<Double-1>', on_select)
    
    def _show_simulation(self):
        """Show simulation window."""
        sim_window = tk.Toplevel(self)
        sim_window.title("Simulation")
        sim_window.geometry("900x700")
        sim_window.transient(self)
        sim_window.configure(bg="#1a1a1a")
        
        # Message navigation
        nav_frame = ttk.Frame(sim_window)
        nav_frame.pack(fill=tk.X, padx=10, pady=10)
        
        msg_num_var = tk.IntVar(value=self.current_message_num)
        
        ttk.Button(nav_frame, text="◀", 
                   command=lambda: navigate(-1)).pack(side=tk.LEFT, padx=5)
        
        ttk.Label(nav_frame, text="Message:").pack(side=tk.LEFT, padx=5)
        num_label = ttk.Label(nav_frame, textvariable=msg_num_var)
        num_label.pack(side=tk.LEFT)
        
        ttk.Button(nav_frame, text="▶",
                   command=lambda: navigate(1)).pack(side=tk.LEFT, padx=5)
        
        # Display area
        display_frame = ttk.Frame(sim_window)
        display_frame.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        # Create preview for each alternance
        previews = []
        for i in range(3):
            frame = ttk.LabelFrame(display_frame, text=f"Alternance {i+1}")
            frame.pack(fill=tk.X, padx=5, pady=5)
            
            if self.project.front_display:
                preview = DisplayPreview(frame, self.project.front_display)
            else:
                preview = DisplayPreview(frame)
            preview.pack(fill=tk.X, padx=10, pady=10)
            previews.append(preview)
        
        def update_display():
            num = msg_num_var.get()
            msg = self.project.get_message(num)
            if msg:
                for i, preview in enumerate(previews):
                    if i < len(msg.alternances):
                        text = msg.header + msg.alternances[i].text
                        fonts = "2" * len(text)
                        preview.render_text(text, fonts)
        
        def navigate(delta):
            nums = self.project.get_sorted_message_numbers()
            current = msg_num_var.get()
            try:
                idx = nums.index(current)
                new_idx = max(0, min(len(nums) - 1, idx + delta))
                msg_num_var.set(nums[new_idx])
                update_display()
            except ValueError:
                pass
        
        update_display()
        
        # Close button
        ttk.Button(sim_window, text="Fermer", 
                   command=sim_window.destroy).pack(pady=10)
    
    def _show_fullscreen_girouette(self):
        """Show the fullscreen girouette display (screen as bus display)."""
        def launch_fullscreen(config):
            # Update project display config
            self.project.front_display = config
            
            # Launch fullscreen display
            fullscreen = FullscreenGirouette(
                self,
                self.project,
                config
            )
            fullscreen.set_message(self.current_message_num)
        
        # Show configuration dialog
        ScreenDetectionDialog(self, launch_fullscreen)
    
    def _show_help(self):
        """Show help window."""
        help_window = tk.Toplevel(self)
        help_window.title("Aide - Edigir")
        help_window.geometry("700x500")
        help_window.transient(self)
        
        text = tk.Text(help_window, wrap=tk.WORD, padx=10, pady=10)
        text.pack(fill=tk.BOTH, expand=True)
        
        scrollbar = ttk.Scrollbar(help_window, command=text.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        text.configure(yscrollcommand=scrollbar.set)
        
        help_text = """
MANUEL D'UTILISATION - EDIGIR

Edigir est un éditeur de messages pour girouettes LED de transports en commun.

FONCTIONNALITÉS PRINCIPALES:

1. ÉDITEUR DE DESTINATIONS
   - Créer et modifier des messages de destination
   - Jusqu'à 3 alternances par message
   - Support des girouettes avant, latérale et arrière

2. ÉDITEUR DE POLICES
   - Personnaliser les caractères LED
   - Support de plusieurs polices (0-5, A-F)
   - Édition pixel par pixel

3. SIMULATION
   - Aperçu en temps réel des messages
   - Animation défilante
   - Prévisualisation des couleurs

4. MODE GIROUETTE (PLEIN ÉCRAN)
   - Transforme l'écran de votre ordinateur en afficheur de bus
   - Affichage LED réaliste en plein écran
   - Navigation par clavier entre messages et alternances
   - Cycle automatique des alternances avec durées configurées
   - Plusieurs couleurs LED disponibles (ambre, vert, rouge, jaune, blanc)

RACCOURCIS CLAVIER:
   Ctrl+N     Nouveau fichier
   Ctrl+O     Ouvrir fichier
   Ctrl+S     Enregistrer
   Ctrl+P     Éditeur de polices
   Ctrl+G     Configuration girouettes
   Ctrl+R     Visualisation rapide
   Ctrl+U     Simulation
   F11        Mode Girouette (plein écran)
   Page Up    Message précédent
   Page Down  Message suivant
   F1         Aide

MODE GIROUETTE - COMMANDES:
   ESC        Quitter le mode plein écran
   ←/→        Message précédent/suivant
   ↑/↓        Alternance précédente/suivante
   ESPACE     Démarrer/Arrêter le cycle automatique
   C          Changer la couleur LED
   H          Afficher/Masquer les informations
   F          Basculer plein écran/fenêtré

CARACTÈRES SPÉCIAUX:
   | (pipe)   Saut de ligne
   ²          Saut de colonne (1 pixel)

FORMAT DES MESSAGES:
   - Numéros de 1 à 9999
   - Maximum 240 caractères par message
   - Maximum 1600 colonnes pour texte défilant
        """
        
        text.insert('1.0', help_text)
        text.configure(state='disabled')
    
    def _show_about(self):
        """Show about dialog."""
        messagebox.showinfo(
            "À propos d'Edigir",
            "Edigir - Éditeur de girouettes\n"
            "Version 2.0\n\n"
            "Recreation Python de Edigir11\n"
            "Pour l'édition de messages de destination\n"
            "sur girouettes LED de transports en commun.\n\n"
            "© 2024"
        )
    
    def _set_status(self, message: str):
        """Set status bar message."""
        self.status_label.config(text=message)
    
    def _on_close(self):
        """Handle window close."""
        if self.modified:
            result = messagebox.askyesnocancel(
                "Quitter",
                "Voulez-vous enregistrer les modifications avant de quitter?"
            )
            if result is True:
                self._save_file()
            elif result is None:
                return
        
        self.destroy()


def main():
    """Main entry point."""
    app = EditorApplication()
    app.mainloop()


if __name__ == "__main__":
    main()
