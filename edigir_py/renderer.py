"""
LED Display Renderer for Edigir.
Renders text on simulated LED matrix displays with animations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Tuple
from .models import Font, FontCharacter, DisplayConfig, Palette, AnimationType


# Built-in 5x7 pixel font (column-major, each byte is one column, LSB = top)
# Standard ASCII characters from space (32) to tilde (126)
BUILTIN_FONT_5X7 = {
    ' ': [0x00, 0x00, 0x00, 0x00, 0x00],
    '!': [0x00, 0x00, 0x5f, 0x00, 0x00],
    '"': [0x00, 0x07, 0x00, 0x07, 0x00],
    '#': [0x14, 0x7f, 0x14, 0x7f, 0x14],
    '$': [0x24, 0x2a, 0x7f, 0x2a, 0x12],
    '%': [0x23, 0x13, 0x08, 0x64, 0x62],
    '&': [0x36, 0x49, 0x55, 0x22, 0x50],
    "'": [0x00, 0x05, 0x03, 0x00, 0x00],
    '(': [0x00, 0x1c, 0x22, 0x41, 0x00],
    ')': [0x00, 0x41, 0x22, 0x1c, 0x00],
    '*': [0x14, 0x08, 0x3e, 0x08, 0x14],
    '+': [0x08, 0x08, 0x3e, 0x08, 0x08],
    ',': [0x00, 0x50, 0x30, 0x00, 0x00],
    '-': [0x08, 0x08, 0x08, 0x08, 0x08],
    '.': [0x00, 0x60, 0x60, 0x00, 0x00],
    '/': [0x20, 0x10, 0x08, 0x04, 0x02],
    '0': [0x3e, 0x51, 0x49, 0x45, 0x3e],
    '1': [0x00, 0x42, 0x7f, 0x40, 0x00],
    '2': [0x42, 0x61, 0x51, 0x49, 0x46],
    '3': [0x21, 0x41, 0x45, 0x4b, 0x31],
    '4': [0x18, 0x14, 0x12, 0x7f, 0x10],
    '5': [0x27, 0x45, 0x45, 0x45, 0x39],
    '6': [0x3c, 0x4a, 0x49, 0x49, 0x30],
    '7': [0x01, 0x71, 0x09, 0x05, 0x03],
    '8': [0x36, 0x49, 0x49, 0x49, 0x36],
    '9': [0x06, 0x49, 0x49, 0x29, 0x1e],
    ':': [0x00, 0x36, 0x36, 0x00, 0x00],
    ';': [0x00, 0x56, 0x36, 0x00, 0x00],
    '<': [0x08, 0x14, 0x22, 0x41, 0x00],
    '=': [0x14, 0x14, 0x14, 0x14, 0x14],
    '>': [0x00, 0x41, 0x22, 0x14, 0x08],
    '?': [0x02, 0x01, 0x51, 0x09, 0x06],
    '@': [0x32, 0x49, 0x79, 0x41, 0x3e],
    'A': [0x7e, 0x11, 0x11, 0x11, 0x7e],
    'B': [0x7f, 0x49, 0x49, 0x49, 0x36],
    'C': [0x3e, 0x41, 0x41, 0x41, 0x22],
    'D': [0x7f, 0x41, 0x41, 0x22, 0x1c],
    'E': [0x7f, 0x49, 0x49, 0x49, 0x41],
    'F': [0x7f, 0x09, 0x09, 0x09, 0x01],
    'G': [0x3e, 0x41, 0x49, 0x49, 0x7a],
    'H': [0x7f, 0x08, 0x08, 0x08, 0x7f],
    'I': [0x00, 0x41, 0x7f, 0x41, 0x00],
    'J': [0x20, 0x40, 0x41, 0x3f, 0x01],
    'K': [0x7f, 0x08, 0x14, 0x22, 0x41],
    'L': [0x7f, 0x40, 0x40, 0x40, 0x40],
    'M': [0x7f, 0x02, 0x0c, 0x02, 0x7f],
    'N': [0x7f, 0x04, 0x08, 0x10, 0x7f],
    'O': [0x3e, 0x41, 0x41, 0x41, 0x3e],
    'P': [0x7f, 0x09, 0x09, 0x09, 0x06],
    'Q': [0x3e, 0x41, 0x51, 0x21, 0x5e],
    'R': [0x7f, 0x09, 0x19, 0x29, 0x46],
    'S': [0x46, 0x49, 0x49, 0x49, 0x31],
    'T': [0x01, 0x01, 0x7f, 0x01, 0x01],
    'U': [0x3f, 0x40, 0x40, 0x40, 0x3f],
    'V': [0x1f, 0x20, 0x40, 0x20, 0x1f],
    'W': [0x3f, 0x40, 0x38, 0x40, 0x3f],
    'X': [0x63, 0x14, 0x08, 0x14, 0x63],
    'Y': [0x07, 0x08, 0x70, 0x08, 0x07],
    'Z': [0x61, 0x51, 0x49, 0x45, 0x43],
    '[': [0x00, 0x7f, 0x41, 0x41, 0x00],
    '\\': [0x02, 0x04, 0x08, 0x10, 0x20],
    ']': [0x00, 0x41, 0x41, 0x7f, 0x00],
    '^': [0x04, 0x02, 0x01, 0x02, 0x04],
    '_': [0x40, 0x40, 0x40, 0x40, 0x40],
    '`': [0x00, 0x01, 0x02, 0x04, 0x00],
    'a': [0x20, 0x54, 0x54, 0x54, 0x78],
    'b': [0x7f, 0x48, 0x44, 0x44, 0x38],
    'c': [0x38, 0x44, 0x44, 0x44, 0x20],
    'd': [0x38, 0x44, 0x44, 0x48, 0x7f],
    'e': [0x38, 0x54, 0x54, 0x54, 0x18],
    'f': [0x08, 0x7e, 0x09, 0x01, 0x02],
    'g': [0x0c, 0x52, 0x52, 0x52, 0x3e],
    'h': [0x7f, 0x08, 0x04, 0x04, 0x78],
    'i': [0x00, 0x44, 0x7d, 0x40, 0x00],
    'j': [0x20, 0x40, 0x44, 0x3d, 0x00],
    'k': [0x7f, 0x10, 0x28, 0x44, 0x00],
    'l': [0x00, 0x41, 0x7f, 0x40, 0x00],
    'm': [0x7c, 0x04, 0x18, 0x04, 0x78],
    'n': [0x7c, 0x08, 0x04, 0x04, 0x78],
    'o': [0x38, 0x44, 0x44, 0x44, 0x38],
    'p': [0x7c, 0x14, 0x14, 0x14, 0x08],
    'q': [0x08, 0x14, 0x14, 0x18, 0x7c],
    'r': [0x7c, 0x08, 0x04, 0x04, 0x08],
    's': [0x48, 0x54, 0x54, 0x54, 0x20],
    't': [0x04, 0x3f, 0x44, 0x40, 0x20],
    'u': [0x3c, 0x40, 0x40, 0x20, 0x7c],
    'v': [0x1c, 0x20, 0x40, 0x20, 0x1c],
    'w': [0x3c, 0x40, 0x30, 0x40, 0x3c],
    'x': [0x44, 0x28, 0x10, 0x28, 0x44],
    'y': [0x0c, 0x50, 0x50, 0x50, 0x3c],
    'z': [0x44, 0x64, 0x54, 0x4c, 0x44],
    '{': [0x00, 0x08, 0x36, 0x41, 0x00],
    '|': [0x00, 0x00, 0x7f, 0x00, 0x00],
    '}': [0x00, 0x41, 0x36, 0x08, 0x00],
    '~': [0x10, 0x08, 0x08, 0x10, 0x08],
    # Extended French characters
    'é': [0x38, 0x54, 0x56, 0x55, 0x18],
    'è': [0x38, 0x55, 0x56, 0x54, 0x18],
    'ê': [0x38, 0x56, 0x55, 0x56, 0x18],
    'ë': [0x38, 0x55, 0x54, 0x55, 0x18],
    'à': [0x20, 0x55, 0x56, 0x54, 0x78],
    'â': [0x20, 0x56, 0x55, 0x56, 0x78],
    'ù': [0x3c, 0x41, 0x42, 0x20, 0x7c],
    'û': [0x3c, 0x42, 0x41, 0x42, 0x7c],
    'ô': [0x38, 0x46, 0x45, 0x46, 0x38],
    'î': [0x00, 0x46, 0x7d, 0x42, 0x00],
    'ï': [0x00, 0x45, 0x7c, 0x45, 0x00],
    'ç': [0x38, 0x44, 0xc4, 0x44, 0x20],
    'œ': [0x38, 0x54, 0x5c, 0x54, 0x58],
    'æ': [0x20, 0x54, 0x7c, 0x54, 0x18],
    '°': [0x00, 0x06, 0x09, 0x06, 0x00],
    '€': [0x14, 0x3e, 0x55, 0x41, 0x22],
    '→': [0x08, 0x08, 0x2a, 0x1c, 0x08],
    '←': [0x08, 0x1c, 0x2a, 0x08, 0x08],
    '↑': [0x04, 0x02, 0x7f, 0x02, 0x04],
    '↓': [0x10, 0x20, 0x7f, 0x20, 0x10],
}


def get_builtin_char_bitmap(char: str) -> List[List[bool]]:
    """Get bitmap for a character from the built-in font."""
    columns = BUILTIN_FONT_5X7.get(char)
    if columns is None:
        columns = BUILTIN_FONT_5X7.get(' ')  # Default to space
    
    # Convert column bytes to 7-row bitmap
    bitmap = []
    for row in range(7):
        row_pixels = []
        for col in range(5):
            if columns[col] & (1 << row):
                row_pixels.append(True)
            else:
                row_pixels.append(False)
        bitmap.append(row_pixels)
    
    return bitmap


class LEDRenderer:
    """Renders text on LED matrix displays with realistic LED effects."""
    
    # Standard LED colors
    LED_OFF = "#1a1a1a"
    LED_AMBER = "#ff6600"
    LED_GREEN = "#00ff00"
    LED_RED = "#ff0000"
    LED_YELLOW = "#ffff00"
    LED_WHITE = "#ffffff"
    LED_CYAN = "#00ffff"
    
    # Dim versions for glow effect
    LED_DIM_AMBER = "#4d2200"
    LED_DIM_GREEN = "#004d00"
    LED_DIM_RED = "#4d0000"
    LED_DIM_YELLOW = "#4d4d00"
    
    def __init__(self, canvas: tk.Canvas, display_config: DisplayConfig):
        """Initialize renderer with canvas and display configuration."""
        self.canvas = canvas
        self.display_config = display_config
        self.pixel_size = 4
        self.pixel_gap = 1
        self.fonts: Dict[str, Font] = {}
        self.palette: Optional[Palette] = None
        self.led_on_color = self.LED_AMBER
        self.use_glow = True
        
        # Pixel buffer for efficient rendering
        self._pixel_buffer: List[List[bool]] = []
        
        # Calculate canvas size
        self._setup_canvas()
    
    def _setup_canvas(self):
        """Set up canvas dimensions based on display config."""
        width = self.display_config.width1 * (self.pixel_size + self.pixel_gap)
        height = self.display_config.height1 * (self.pixel_size + self.pixel_gap)
        
        if self.display_config.is_bimode:
            width = max(width, self.display_config.width2 * (self.pixel_size + self.pixel_gap))
            height += self.display_config.height2 * (self.pixel_size + self.pixel_gap) + 10
        
        self.canvas.configure(width=width + 20, height=height + 20)
        self.canvas.configure(bg="#0a0a0a")
        
        # Initialize pixel buffer
        self._pixel_buffer = [[False] * self.display_config.width1 
                              for _ in range(self.display_config.height1)]
    
    def set_fonts(self, fonts: Dict[str, Font]):
        """Set fonts for rendering."""
        self.fonts = fonts
    
    def set_palette(self, palette: Palette):
        """Set color palette."""
        self.palette = palette
    
    def set_led_color(self, color: str):
        """Set the LED on color."""
        self.led_on_color = color
    
    def clear(self):
        """Clear the display and draw empty matrix."""
        self.canvas.delete("all")
        self._pixel_buffer = [[False] * self.display_config.width1 
                              for _ in range(self.display_config.height1)]
        self._draw_empty_matrix()
    
    def _get_glow_color(self, color: str) -> str:
        """Get dim glow color for LED effect."""
        if color == self.LED_AMBER:
            return self.LED_DIM_AMBER
        elif color == self.LED_GREEN:
            return self.LED_DIM_GREEN
        elif color == self.LED_RED:
            return self.LED_DIM_RED
        elif color == self.LED_YELLOW:
            return self.LED_DIM_YELLOW
        else:
            # Calculate dim version
            hex_color = color.lstrip('#')
            r = int(hex_color[0:2], 16) // 3
            g = int(hex_color[2:4], 16) // 3
            b = int(hex_color[4:6], 16) // 3
            return f"#{r:02x}{g:02x}{b:02x}"
    
    def _draw_empty_matrix(self):
        """Draw empty LED matrix background."""
        offset_x = 10
        offset_y = 10
        
        # Draw first matrix section
        for y in range(self.display_config.height1):
            for x in range(self.display_config.width1):
                self._draw_pixel(x, y, self.LED_OFF, offset_x, offset_y)
        
        # Draw second matrix section if bimode
        if self.display_config.is_bimode:
            offset_y += self.display_config.height1 * (self.pixel_size + self.pixel_gap) + 10
            for y in range(self.display_config.height2):
                for x in range(self.display_config.width2):
                    self._draw_pixel(x, y, self.LED_OFF, offset_x, offset_y)
    
    def _draw_pixel(self, x: int, y: int, color: str, offset_x: int = 0, offset_y: int = 0):
        """Draw a single LED pixel with optional glow effect."""
        px = offset_x + x * (self.pixel_size + self.pixel_gap)
        py = offset_y + y * (self.pixel_size + self.pixel_gap)
        
        # Draw glow effect for lit pixels
        if self.use_glow and color != self.LED_OFF and self.pixel_size >= 4:
            glow_color = self._get_glow_color(color)
            glow_size = self.pixel_size + 2
            self.canvas.create_oval(
                px - 1, py - 1,
                px + glow_size - 1, py + glow_size - 1,
                fill=glow_color,
                outline="",
                tags="glow"
            )
        
        # Draw the main LED
        self.canvas.create_oval(
            px, py,
            px + self.pixel_size, py + self.pixel_size,
            fill=color,
            outline="",
            tags="led"
        )
    
    def _get_char_bitmap(self, char: str, font_code: str = '2') -> Tuple[List[List[bool]], int]:
        """Get bitmap for a character. Returns (bitmap, width)."""
        # First try to use loaded font
        font = self.fonts.get(font_code) or self.fonts.get('2')
        
        if font:
            font_char = font.get_char(char)
            if font_char and font_char.pixels:
                return font_char.pixels, font_char.width
        
        # Fall back to built-in font
        bitmap = get_builtin_char_bitmap(char)
        return bitmap, 5  # Built-in font is 5 pixels wide
    
    def render_text(self, text: str, fonts: str = "", 
                    text_color: str = None, section: int = 0,
                    scroll_offset: int = 0) -> int:
        """
        Render text on the LED display.
        
        Args:
            text: Text to render
            fonts: Font codes for each character (e.g., "222222" for font 2)
            text_color: LED color (default amber)
            section: 0 for first section, 1 for second (bimode only)
            scroll_offset: Horizontal scroll offset for animations
            
        Returns:
            Total width of rendered text in pixels
        """
        self.clear()
        
        if not text_color:
            text_color = self.led_on_color
        
        # Determine display section
        if section == 0:
            display_width = self.display_config.width1
            display_height = self.display_config.height1
            offset_y = 10
        else:
            display_width = self.display_config.width2
            display_height = self.display_config.height2
            offset_y = 10 + self.display_config.height1 * (self.pixel_size + self.pixel_gap) + 10
        
        offset_x = 10
        
        # Render each character
        current_x = -scroll_offset
        
        for i, char in enumerate(text):
            # Handle special characters
            if char == '|' or char == '¦':
                # Line break - not rendered in single-line mode
                continue
            elif char == '²':
                # Single column skip
                current_x += 1
                continue
            
            # Get font code for this character
            font_code = fonts[i] if i < len(fonts) else '2'
            
            # Get character bitmap
            bitmap, char_width = self._get_char_bitmap(char, font_code)
            char_height = len(bitmap)
            
            # Center vertically
            y_start = (display_height - char_height) // 2
            
            # Render character pixels
            for y, row in enumerate(bitmap):
                for x, pixel in enumerate(row):
                    if pixel:
                        screen_x = current_x + x
                        screen_y = y_start + y
                        
                        # Only draw if within display bounds
                        if 0 <= screen_x < display_width and 0 <= screen_y < display_height:
                            self._draw_pixel(
                                screen_x, screen_y, text_color,
                                offset_x, offset_y
                            )
            
            current_x += char_width + 1  # Add character spacing
        
        return current_x + scroll_offset  # Return total width
    
    def get_color(self, index: int) -> str:
        """Get color from palette by index."""
        if self.palette:
            color = self.palette.get_color(index)
            if color:
                return f"#{color.rgb_hex}"
        
        # Default colors if no palette
        default_colors = [
            self.LED_OFF,
            self.LED_WHITE,
            self.LED_RED,
            self.LED_GREEN,
            "#0000ff",
            self.LED_YELLOW,
            "#ff00ff",
            self.LED_CYAN,
            self.LED_AMBER,
        ]
        
        return default_colors[index % len(default_colors)]


class DisplayPreview(ttk.Frame):
    """Widget for displaying LED preview with animation support."""
    
    def __init__(self, parent, display_config: DisplayConfig = None):
        super().__init__(parent)
        
        # Default config if none provided
        if display_config is None:
            display_config = DisplayConfig(
                name="16x084",
                height1=16,
                width1=84
            )
        
        self.display_config = display_config
        
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
        self._animation_running = False
        self._scroll_offset = 0
        self._text_width = 0
        self._blink_state = True
        self._current_alternance = 0
        self._animation_timer = None
        
        # Animation parameters
        self._animation_text = ""
        self._animation_fonts = ""
        self._animation_color = None
        self._animation_speed = 50
        self._animation_type = AnimationType.STATIC
    
    def set_display_config(self, config: DisplayConfig):
        """Update display configuration."""
        self.display_config = config
        self.renderer = LEDRenderer(self.canvas, config)
    
    def set_fonts(self, fonts: Dict[str, Font]):
        """Set fonts for rendering."""
        self.renderer.set_fonts(fonts)
    
    def set_palette(self, palette):
        """Set color palette."""
        self.renderer.set_palette(palette)
    
    def set_led_color(self, color: str):
        """Set the LED color."""
        self.renderer.set_led_color(color)
    
    def render_text(self, text: str, fonts: str = "", 
                    text_color: str = None, section: int = 0):
        """Render static text on the display."""
        self.stop_animation()
        self._text_width = self.renderer.render_text(
            text, fonts, text_color, section
        )
    
    def start_scroll_animation(self, text: str, fonts: str = "",
                               text_color: str = None, speed: int = 50):
        """Start horizontal scrolling animation."""
        self.stop_animation()
        self._animation_running = True
        self._animation_type = AnimationType.SCROLL_LEFT
        self._animation_text = text
        self._animation_fonts = fonts
        self._animation_color = text_color
        self._animation_speed = speed
        self._scroll_offset = 0
        
        self._animate_scroll()
    
    def start_blink_animation(self, text: str, fonts: str = "",
                              text_color: str = None, speed: int = 500):
        """Start blinking animation."""
        self.stop_animation()
        self._animation_running = True
        self._animation_type = AnimationType.BLINK
        self._animation_text = text
        self._animation_fonts = fonts
        self._animation_color = text_color
        self._animation_speed = speed
        self._blink_state = True
        
        self._animate_blink()
    
    def start_alternance_animation(self, alternances: List[Tuple[str, int]], 
                                   fonts: str = "", text_color: str = None):
        """
        Start alternance cycling animation.
        
        Args:
            alternances: List of (text, duration_ms) tuples
            fonts: Font codes
            text_color: LED color
        """
        self.stop_animation()
        if not alternances:
            return
            
        self._animation_running = True
        self._animation_type = AnimationType.STATIC  # Used for alternances
        self._animation_fonts = fonts
        self._animation_color = text_color
        self._alternances = alternances
        self._current_alternance = 0
        
        self._animate_alternance()
    
    def stop_animation(self):
        """Stop any running animation."""
        self._animation_running = False
        if self._animation_timer:
            self.after_cancel(self._animation_timer)
            self._animation_timer = None
    
    def _animate_scroll(self):
        """Animation loop for scrolling text."""
        if not self._animation_running:
            return
        
        self._text_width = self.renderer.render_text(
            self._animation_text, 
            self._animation_fonts, 
            self._animation_color, 
            scroll_offset=self._scroll_offset
        )
        
        self._scroll_offset += 1
        
        # Reset when text scrolls off screen
        if self._scroll_offset > self._text_width + self.display_config.width1:
            self._scroll_offset = 0
        
        self._animation_timer = self.after(
            self._animation_speed, 
            self._animate_scroll
        )
    
    def _animate_blink(self):
        """Animation loop for blinking text."""
        if not self._animation_running:
            return
        
        if self._blink_state:
            self.renderer.render_text(
                self._animation_text,
                self._animation_fonts,
                self._animation_color
            )
        else:
            self.renderer.clear()
        
        self._blink_state = not self._blink_state
        
        self._animation_timer = self.after(
            self._animation_speed,
            self._animate_blink
        )
    
    def _animate_alternance(self):
        """Animation loop for cycling through alternances."""
        if not self._animation_running:
            return
        
        if not hasattr(self, '_alternances') or not self._alternances:
            return
        
        text, duration = self._alternances[self._current_alternance]
        
        self.renderer.render_text(
            text,
            self._animation_fonts,
            self._animation_color
        )
        
        # Schedule next alternance
        self._current_alternance = (self._current_alternance + 1) % len(self._alternances)
        
        self._animation_timer = self.after(
            duration,
            self._animate_alternance
        )
    
    def clear(self):
        """Clear the display and stop animations."""
        self.stop_animation()
        self.renderer.clear()
