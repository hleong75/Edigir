"""
LED Display Renderer for Edigir.
Renders text on simulated LED matrix displays.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple
from .models import Font, FontCharacter, DisplayConfig, Palette


class LEDRenderer:
    """Renders text on LED matrix displays."""
    
    # Standard LED colors
    LED_OFF = "#1a1a1a"
    LED_ON = "#ff6600"  # Amber LED
    LED_GREEN = "#00ff00"
    LED_RED = "#ff0000"
    LED_YELLOW = "#ffff00"
    
    def __init__(self, canvas: tk.Canvas, display_config: DisplayConfig):
        """Initialize renderer with canvas and display configuration."""
        self.canvas = canvas
        self.config = display_config
        self.pixel_size = 4
        self.pixel_gap = 1
        self.fonts: Dict[str, Font] = {}
        self.palette: Optional[Palette] = None
        
        # Calculate canvas size
        self._setup_canvas()
    
    def _setup_canvas(self):
        """Set up canvas dimensions based on display config."""
        width = self.config.width1 * (self.pixel_size + self.pixel_gap)
        height = self.config.height1 * (self.pixel_size + self.pixel_gap)
        
        if self.config.is_bimode:
            width = max(width, self.config.width2 * (self.pixel_size + self.pixel_gap))
            height += self.config.height2 * (self.pixel_size + self.pixel_gap) + 10
        
        self.canvas.configure(width=width + 20, height=height + 20)
        self.canvas.configure(bg="#0a0a0a")
    
    def set_fonts(self, fonts: Dict[str, Font]):
        """Set fonts for rendering."""
        self.fonts = fonts
    
    def set_palette(self, palette: Palette):
        """Set color palette."""
        self.palette = palette
    
    def clear(self):
        """Clear the display."""
        self.canvas.delete("all")
        self._draw_empty_matrix()
    
    def _draw_empty_matrix(self):
        """Draw empty LED matrix."""
        offset_x = 10
        offset_y = 10
        
        # Draw first matrix section
        for y in range(self.config.height1):
            for x in range(self.config.width1):
                self._draw_pixel(x, y, self.LED_OFF, offset_x, offset_y)
        
        # Draw second matrix section if bimode
        if self.config.is_bimode:
            offset_y += self.config.height1 * (self.pixel_size + self.pixel_gap) + 10
            for y in range(self.config.height2):
                for x in range(self.config.width2):
                    self._draw_pixel(x, y, self.LED_OFF, offset_x, offset_y)
    
    def _draw_pixel(self, x: int, y: int, color: str, offset_x: int = 0, offset_y: int = 0):
        """Draw a single LED pixel."""
        px = offset_x + x * (self.pixel_size + self.pixel_gap)
        py = offset_y + y * (self.pixel_size + self.pixel_gap)
        
        self.canvas.create_oval(
            px, py,
            px + self.pixel_size, py + self.pixel_size,
            fill=color,
            outline="",
            tags="led"
        )
    
    def render_text(self, text: str, fonts: str = "", 
                    text_color: str = None, section: int = 0,
                    scroll_offset: int = 0):
        """
        Render text on the LED display.
        
        Args:
            text: Text to render
            fonts: Font codes for each character (e.g., "222222" for font 2)
            text_color: LED color (default amber)
            section: 0 for first section, 1 for second (bimode only)
            scroll_offset: Horizontal scroll offset for animations
        """
        self.clear()
        
        if not text_color:
            text_color = self.LED_ON
        
        # Determine display section
        if section == 0:
            width = self.config.width1
            height = self.config.height1
            offset_y = 10
        else:
            width = self.config.width2
            height = self.config.height2
            offset_y = 10 + self.config.height1 * (self.pixel_size + self.pixel_gap) + 10
        
        offset_x = 10 - scroll_offset
        
        # Render each character
        current_x = 0
        for i, char in enumerate(text):
            # Get font code for this character
            font_code = fonts[i] if i < len(fonts) else '2'
            font = self.fonts.get(font_code)
            
            if font is None:
                font = self.fonts.get('2')  # Default to medium font
            
            if font is None:
                continue
            
            # Handle special characters
            if char == '|' or char == '¦':
                # Line break - not rendered
                continue
            elif char == '²':
                # Single column skip
                current_x += 1
                continue
            
            # Get character from font
            font_char = font.get_char(char)
            
            if font_char:
                # Render character pixels
                self._render_character(
                    font_char, 
                    current_x + offset_x, 
                    offset_y,
                    text_color,
                    height
                )
                current_x += font_char.width + 1  # Add spacing
            else:
                # Unknown character - render as space
                current_x += 4
        
        return current_x  # Return total width for scrolling
    
    def _render_character(self, font_char: FontCharacter, 
                         x_offset: int, y_offset: int,
                         color: str, max_height: int):
        """Render a single character on the display."""
        # Center vertically if character is shorter than display
        y_start = (max_height - font_char.height) // 2
        
        for y, row in enumerate(font_char.pixels):
            for x, pixel in enumerate(row):
                if pixel:
                    screen_x = x_offset + x
                    screen_y = y_start + y
                    
                    # Only draw if within bounds
                    if screen_x >= 0 and screen_y >= 0:
                        self._draw_pixel(
                            screen_x, screen_y, color,
                            0, y_offset
                        )
    
    def get_color(self, index: int) -> str:
        """Get color from palette by index."""
        if self.palette:
            color = self.palette.get_color(index)
            if color:
                return f"#{color.rgb_hex}"
        
        # Default colors if no palette
        default_colors = [
            "#000000",  # Black
            "#ffffff",  # White
            "#ff0000",  # Red
            "#00ff00",  # Green
            "#0000ff",  # Blue
            "#ffff00",  # Yellow
            "#ff00ff",  # Magenta
            "#00ffff",  # Cyan
            "#ff6600",  # Orange/Amber
        ]
        
        return default_colors[index % len(default_colors)]


class DisplayPreview(ttk.Frame):
    """Widget for displaying LED preview."""
    
    def __init__(self, parent, display_config: DisplayConfig = None):
        super().__init__(parent)
        
        # Default config if none provided
        if display_config is None:
            display_config = DisplayConfig(
                name="16x084",
                height1=16,
                width1=84
            )
        
        self.config = display_config
        
        # Create canvas
        self.canvas = tk.Canvas(
            self,
            bg="#0a0a0a",
            highlightthickness=2,
            highlightbackground="#333333"
        )
        self.canvas.pack(fill=tk.BOTH, expand=True, padx=5, pady=5)
        
        # Create renderer
        self.renderer = LEDRenderer(self.canvas, display_config)
        
        # Animation state
        self.animation_running = False
        self.scroll_offset = 0
        self.text_width = 0
    
    def set_display_config(self, config: DisplayConfig):
        """Update display configuration."""
        self.config = config
        self.renderer = LEDRenderer(self.canvas, config)
    
    def set_fonts(self, fonts: Dict[str, Font]):
        """Set fonts for rendering."""
        self.renderer.set_fonts(fonts)
    
    def set_palette(self, palette):
        """Set color palette."""
        self.renderer.set_palette(palette)
    
    def render_text(self, text: str, fonts: str = "", 
                    text_color: str = None, section: int = 0):
        """Render text on the display."""
        self.text_width = self.renderer.render_text(
            text, fonts, text_color, section
        )
    
    def start_scroll_animation(self, text: str, fonts: str = "",
                               text_color: str = None, speed: int = 50):
        """Start scrolling animation."""
        self.animation_running = True
        self.scroll_offset = 0
        self._animate_scroll(text, fonts, text_color, speed)
    
    def stop_animation(self):
        """Stop any running animation."""
        self.animation_running = False
    
    def _animate_scroll(self, text: str, fonts: str,
                        text_color: str, speed: int):
        """Animation loop for scrolling."""
        if not self.animation_running:
            return
        
        self.renderer.render_text(
            text, fonts, text_color, 
            scroll_offset=self.scroll_offset
        )
        
        self.scroll_offset += 1
        
        # Reset when text scrolls off screen
        if self.scroll_offset > self.text_width + self.config.width1:
            self.scroll_offset = -self.config.width1
        
        self.after(speed, lambda: self._animate_scroll(text, fonts, text_color, speed))
    
    def clear(self):
        """Clear the display."""
        self.stop_animation()
        self.renderer.clear()
