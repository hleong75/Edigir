"""
Font Editor for Edigir.
Provides a pixel-based font character editor.
"""

import tkinter as tk
from tkinter import ttk, messagebox
from typing import Dict, Optional, Callable
from .models import Font, FontCharacter


class FontEditorWidget(ttk.Frame):
    """Widget for editing font characters pixel by pixel."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.fonts: Dict[str, Font] = {}
        self.current_font: Optional[Font] = None
        self.current_char: Optional[FontCharacter] = None
        self.on_change_callback: Optional[Callable] = None
        
        self.pixel_size = 20
        self.grid_color = "#333333"
        self.pixel_on = "#ff6600"
        self.pixel_off = "#1a1a1a"
        
        self._create_widgets()
    
    def _create_widgets(self):
        """Create editor widgets."""
        # Top controls
        controls_frame = ttk.Frame(self)
        controls_frame.pack(fill=tk.X, padx=5, pady=5)
        
        # Font selector
        ttk.Label(controls_frame, text="Police:").pack(side=tk.LEFT, padx=2)
        self.font_var = tk.StringVar()
        self.font_combo = ttk.Combobox(
            controls_frame, 
            textvariable=self.font_var,
            state="readonly",
            width=20
        )
        self.font_combo.pack(side=tk.LEFT, padx=5)
        self.font_combo.bind('<<ComboboxSelected>>', self._on_font_selected)
        
        # Character entry
        ttk.Label(controls_frame, text="Caractère:").pack(side=tk.LEFT, padx=(20, 2))
        self.char_var = tk.StringVar()
        self.char_entry = ttk.Entry(
            controls_frame,
            textvariable=self.char_var,
            width=5
        )
        self.char_entry.pack(side=tk.LEFT, padx=5)
        self.char_entry.bind('<Return>', self._on_char_entered)
        self.char_entry.bind('<KeyRelease>', self._on_char_key)
        
        # Character navigation
        nav_frame = ttk.Frame(controls_frame)
        nav_frame.pack(side=tk.LEFT, padx=20)
        
        ttk.Button(nav_frame, text="◀", width=3, 
                   command=self._prev_char).pack(side=tk.LEFT)
        ttk.Button(nav_frame, text="▶", width=3,
                   command=self._next_char).pack(side=tk.LEFT, padx=2)
        
        # Middle area - editor and character grid
        middle_frame = ttk.Frame(self)
        middle_frame.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Left - Pixel editor canvas
        editor_frame = ttk.LabelFrame(middle_frame, text="Éditeur de caractère")
        editor_frame.pack(side=tk.LEFT, fill=tk.BOTH, padx=5)
        
        self.canvas = tk.Canvas(
            editor_frame,
            width=200,
            height=300,
            bg="#0a0a0a",
            highlightthickness=1,
            highlightbackground="#555555"
        )
        self.canvas.pack(padx=10, pady=10)
        self.canvas.bind('<Button-1>', self._on_canvas_click)
        self.canvas.bind('<B1-Motion>', self._on_canvas_drag)
        self.canvas.bind('<Button-3>', self._on_canvas_right_click)
        self.canvas.bind('<B3-Motion>', self._on_canvas_right_drag)
        
        # Editor buttons
        btn_frame = ttk.Frame(editor_frame)
        btn_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Button(btn_frame, text="Remplir", 
                   command=self._fill_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Vider",
                   command=self._clear_all).pack(side=tk.LEFT, padx=2)
        ttk.Button(btn_frame, text="Inverser",
                   command=self._invert_all).pack(side=tk.LEFT, padx=2)
        
        # Width adjustment
        width_frame = ttk.Frame(editor_frame)
        width_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(width_frame, text="Largeur:").pack(side=tk.LEFT)
        self.width_var = tk.IntVar(value=5)
        width_spin = ttk.Spinbox(
            width_frame,
            from_=1,
            to=16,
            textvariable=self.width_var,
            width=5,
            command=self._on_width_changed
        )
        width_spin.pack(side=tk.LEFT, padx=5)
        
        # Right - Character grid
        grid_frame = ttk.LabelFrame(middle_frame, text="Alphabet")
        grid_frame.pack(side=tk.LEFT, fill=tk.BOTH, expand=True, padx=5)
        
        # Scrollable character grid
        grid_canvas = tk.Canvas(grid_frame, highlightthickness=0)
        scrollbar = ttk.Scrollbar(grid_frame, orient=tk.VERTICAL, 
                                   command=grid_canvas.yview)
        self.char_grid_frame = ttk.Frame(grid_canvas)
        
        grid_canvas.create_window((0, 0), window=self.char_grid_frame, anchor=tk.NW)
        grid_canvas.configure(yscrollcommand=scrollbar.set)
        
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)
        grid_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
        
        self.char_grid_frame.bind('<Configure>',
            lambda e: grid_canvas.configure(scrollregion=grid_canvas.bbox("all")))
        
        # Preview
        preview_frame = ttk.LabelFrame(self, text="Aperçu")
        preview_frame.pack(fill=tk.X, padx=5, pady=5)
        
        self.preview_canvas = tk.Canvas(
            preview_frame,
            width=400,
            height=50,
            bg="#0a0a0a",
            highlightthickness=1,
            highlightbackground="#333333"
        )
        self.preview_canvas.pack(padx=10, pady=10)
        
        self.preview_var = tk.StringVar(value="ABCDEFGHIJKLMNOPQRSTUVWXYZ")
        preview_entry = ttk.Entry(
            preview_frame,
            textvariable=self.preview_var,
            width=50
        )
        preview_entry.pack(padx=10, pady=5)
        preview_entry.bind('<KeyRelease>', lambda e: self._update_preview())
    
    def set_fonts(self, fonts: Dict[str, Font]):
        """Set the fonts to edit."""
        self.fonts = fonts
        
        # Update font combo
        font_names = []
        for code, font in fonts.items():
            font_names.append(f"{code}: {font.name}")
        
        self.font_combo['values'] = font_names
        
        if font_names:
            self.font_combo.current(0)
            self._on_font_selected(None)
        
        self._update_char_grid()
    
    def set_on_change_callback(self, callback: Callable):
        """Set callback for when font is modified."""
        self.on_change_callback = callback
    
    def _on_font_selected(self, event):
        """Handle font selection."""
        selection = self.font_var.get()
        if not selection:
            return
        
        code = selection.split(':')[0].strip()
        self.current_font = self.fonts.get(code)
        
        # Load first character
        if self.current_font and self.current_font.characters:
            first_char = list(self.current_font.characters.keys())[0]
            self.char_var.set(first_char)
            self._load_character(first_char)
        
        self._update_char_grid()
        self._update_preview()
    
    def _on_char_entered(self, event):
        """Handle character entry."""
        char = self.char_var.get()
        if char:
            self._load_character(char[0])
    
    def _on_char_key(self, event):
        """Handle character key release."""
        char = self.char_var.get()
        if len(char) > 1:
            self.char_var.set(char[-1])
            self._load_character(char[-1])
        elif char:
            self._load_character(char)
    
    def _load_character(self, char: str):
        """Load a character for editing."""
        if not self.current_font:
            return
        
        self.current_char = self.current_font.get_char(char)
        
        if self.current_char is None:
            # Create new character
            self.current_char = FontCharacter(
                char=char,
                width=5,
                height=self.current_font.height
            )
            self.current_font.characters[char] = self.current_char
        
        self.width_var.set(self.current_char.width)
        self._draw_editor()
    
    def _draw_editor(self):
        """Draw the pixel editor grid."""
        self.canvas.delete("all")
        
        if not self.current_char:
            return
        
        width = self.current_char.width
        height = self.current_char.height
        
        # Calculate pixel size to fit canvas
        canvas_width = 180
        canvas_height = 280
        self.pixel_size = min(canvas_width // (width + 1), canvas_height // (height + 1))
        self.pixel_size = max(self.pixel_size, 8)  # Minimum size
        
        # Draw grid and pixels
        offset_x = (canvas_width - width * self.pixel_size) // 2 + 10
        offset_y = (canvas_height - height * self.pixel_size) // 2 + 10
        
        for y in range(height):
            for x in range(width):
                px = offset_x + x * self.pixel_size
                py = offset_y + y * self.pixel_size
                
                # Check if pixel is on
                is_on = False
                if y < len(self.current_char.pixels) and x < len(self.current_char.pixels[y]):
                    is_on = self.current_char.pixels[y][x]
                
                color = self.pixel_on if is_on else self.pixel_off
                
                self.canvas.create_rectangle(
                    px, py,
                    px + self.pixel_size - 1, py + self.pixel_size - 1,
                    fill=color,
                    outline=self.grid_color,
                    tags=f"pixel_{x}_{y}"
                )
        
        # Draw height scale
        for i in range(height):
            self.canvas.create_text(
                offset_x - 15,
                offset_y + i * self.pixel_size + self.pixel_size // 2,
                text=str(i + 1),
                fill="#666666",
                font=("Arial", 8)
            )
    
    def _on_canvas_click(self, event):
        """Handle canvas click to toggle pixel."""
        self._set_pixel_at(event.x, event.y, True)
    
    def _on_canvas_drag(self, event):
        """Handle canvas drag to paint pixels on."""
        self._set_pixel_at(event.x, event.y, True)
    
    def _on_canvas_right_click(self, event):
        """Handle right click to turn pixel off."""
        self._set_pixel_at(event.x, event.y, False)
    
    def _on_canvas_right_drag(self, event):
        """Handle right drag to erase pixels."""
        self._set_pixel_at(event.x, event.y, False)
    
    def _set_pixel_at(self, canvas_x: int, canvas_y: int, value: bool):
        """Set pixel at canvas coordinates."""
        if not self.current_char:
            return
        
        width = self.current_char.width
        height = self.current_char.height
        
        canvas_width = 180
        canvas_height = 280
        offset_x = (canvas_width - width * self.pixel_size) // 2 + 10
        offset_y = (canvas_height - height * self.pixel_size) // 2 + 10
        
        # Calculate grid position
        x = (canvas_x - offset_x) // self.pixel_size
        y = (canvas_y - offset_y) // self.pixel_size
        
        if 0 <= x < width and 0 <= y < height:
            # Ensure pixels array is properly sized
            while len(self.current_char.pixels) <= y:
                self.current_char.pixels.append([False] * width)
            while len(self.current_char.pixels[y]) <= x:
                self.current_char.pixels[y].append(False)
            
            self.current_char.pixels[y][x] = value
            self._draw_editor()
            self._update_preview()
            
            if self.on_change_callback:
                self.on_change_callback()
    
    def _fill_all(self):
        """Fill all pixels."""
        if not self.current_char:
            return
        
        for y in range(len(self.current_char.pixels)):
            for x in range(len(self.current_char.pixels[y])):
                self.current_char.pixels[y][x] = True
        
        self._draw_editor()
        self._update_preview()
    
    def _clear_all(self):
        """Clear all pixels."""
        if not self.current_char:
            return
        
        for y in range(len(self.current_char.pixels)):
            for x in range(len(self.current_char.pixels[y])):
                self.current_char.pixels[y][x] = False
        
        self._draw_editor()
        self._update_preview()
    
    def _invert_all(self):
        """Invert all pixels."""
        if not self.current_char:
            return
        
        for y in range(len(self.current_char.pixels)):
            for x in range(len(self.current_char.pixels[y])):
                self.current_char.pixels[y][x] = not self.current_char.pixels[y][x]
        
        self._draw_editor()
        self._update_preview()
    
    def _on_width_changed(self):
        """Handle character width change."""
        if not self.current_char:
            return
        
        new_width = self.width_var.get()
        old_width = self.current_char.width
        
        if new_width == old_width:
            return
        
        self.current_char.width = new_width
        
        # Resize pixel rows
        for row in self.current_char.pixels:
            while len(row) < new_width:
                row.append(False)
            while len(row) > new_width:
                row.pop()
        
        self._draw_editor()
        self._update_preview()
    
    def _prev_char(self):
        """Go to previous character."""
        if not self.current_font or not self.current_char:
            return
        
        chars = list(self.current_font.characters.keys())
        try:
            idx = chars.index(self.current_char.char)
            if idx > 0:
                self.char_var.set(chars[idx - 1])
                self._load_character(chars[idx - 1])
        except ValueError:
            pass
    
    def _next_char(self):
        """Go to next character."""
        if not self.current_font or not self.current_char:
            return
        
        chars = list(self.current_font.characters.keys())
        try:
            idx = chars.index(self.current_char.char)
            if idx < len(chars) - 1:
                self.char_var.set(chars[idx + 1])
                self._load_character(chars[idx + 1])
        except ValueError:
            pass
    
    def _update_char_grid(self):
        """Update the character grid display."""
        # Clear existing grid
        for widget in self.char_grid_frame.winfo_children():
            widget.destroy()
        
        if not self.current_font:
            return
        
        # Create buttons for each character
        chars = sorted(self.current_font.characters.keys())
        col = 0
        row = 0
        max_cols = 10
        
        for char in chars:
            btn = ttk.Button(
                self.char_grid_frame,
                text=char,
                width=3,
                command=lambda c=char: self._select_char_from_grid(c)
            )
            btn.grid(row=row, column=col, padx=1, pady=1)
            
            col += 1
            if col >= max_cols:
                col = 0
                row += 1
    
    def _select_char_from_grid(self, char: str):
        """Select a character from the grid."""
        self.char_var.set(char)
        self._load_character(char)
    
    def _update_preview(self):
        """Update the preview display."""
        self.preview_canvas.delete("all")
        
        if not self.current_font:
            return
        
        text = self.preview_var.get()
        pixel_size = 3
        offset_x = 10
        offset_y = 10
        
        for char in text:
            font_char = self.current_font.get_char(char)
            
            if font_char:
                # Draw character
                for y, row in enumerate(font_char.pixels):
                    for x, pixel in enumerate(row):
                        if pixel:
                            px = offset_x + x * pixel_size
                            py = offset_y + y * pixel_size
                            
                            self.preview_canvas.create_rectangle(
                                px, py,
                                px + pixel_size - 1, py + pixel_size - 1,
                                fill=self.pixel_on,
                                outline=""
                            )
                
                offset_x += (font_char.width + 1) * pixel_size
            else:
                offset_x += 4 * pixel_size
