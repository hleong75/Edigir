"""
Image Export Module for Edigir.
Exports LED display renderings to image formats (PNG, JPG, GIF).
"""

import os
from typing import Dict, List, Optional, Tuple
from .models import DisplayConfig, Font, FontCharacter, Message, Project

# Try to import PIL for image export
try:
    from PIL import Image, ImageDraw
    PIL_AVAILABLE = True
except ImportError:
    PIL_AVAILABLE = False


class ImageExporter:
    """
    Exports LED display renderings to image files.
    Supports PNG, JPG, and animated GIF formats.
    """
    
    # LED colors
    LED_OFF = (26, 26, 26)  # RGB
    LED_AMBER = (255, 102, 0)
    LED_GREEN = (0, 255, 0)
    LED_RED = (255, 0, 0)
    LED_YELLOW = (255, 255, 0)
    LED_WHITE = (255, 255, 255)
    
    BG_COLOR = (10, 10, 10)
    
    def __init__(self, display_config: DisplayConfig, fonts: Dict[str, Font] = None):
        """Initialize exporter with display configuration."""
        self.config = display_config
        self.fonts = fonts or {}
        self.pixel_size = 8
        self.pixel_gap = 2
        self.led_color = self.LED_AMBER
        
    def set_pixel_size(self, size: int, gap: int = 2):
        """Set the pixel size and gap for rendering."""
        self.pixel_size = max(2, size)
        self.pixel_gap = max(0, gap)
    
    def set_led_color(self, color: Tuple[int, int, int]):
        """Set the LED color for rendering."""
        self.led_color = color
    
    def set_led_color_by_name(self, name: str):
        """Set LED color by name."""
        colors = {
            'amber': self.LED_AMBER,
            'green': self.LED_GREEN,
            'red': self.LED_RED,
            'yellow': self.LED_YELLOW,
            'white': self.LED_WHITE,
        }
        self.led_color = colors.get(name.lower(), self.LED_AMBER)
    
    def _calculate_image_size(self) -> Tuple[int, int]:
        """Calculate the image size based on display config."""
        margin = 20
        width = self.config.width1 * (self.pixel_size + self.pixel_gap) + margin * 2
        height = self.config.height1 * (self.pixel_size + self.pixel_gap) + margin * 2
        
        if self.config.is_bimode:
            width = max(width, self.config.width2 * (self.pixel_size + self.pixel_gap) + margin * 2)
            height += self.config.height2 * (self.pixel_size + self.pixel_gap) + margin
        
        return (width, height)
    
    def _draw_pixel(self, draw: ImageDraw.Draw, x: int, y: int, 
                    color: Tuple[int, int, int], offset_x: int, offset_y: int):
        """Draw a single LED pixel."""
        px = offset_x + x * (self.pixel_size + self.pixel_gap)
        py = offset_y + y * (self.pixel_size + self.pixel_gap)
        
        # Draw LED as circle (ellipse)
        draw.ellipse(
            [px, py, px + self.pixel_size, py + self.pixel_size],
            fill=color
        )
    
    def _draw_simple_char(self, draw: ImageDraw.Draw, char: str, 
                          start_x: int, offset_x: int, offset_y: int) -> int:
        """
        Draw a simple character using a basic 5x7 font pattern.
        Returns the width of the character.
        """
        # Simple 5x7 pixel font patterns for common characters
        SIMPLE_FONT = {
            '0': ['01110', '10001', '10011', '10101', '11001', '10001', '01110'],
            '1': ['00100', '01100', '00100', '00100', '00100', '00100', '01110'],
            '2': ['01110', '10001', '00001', '00110', '01000', '10000', '11111'],
            '3': ['01110', '10001', '00001', '00110', '00001', '10001', '01110'],
            '4': ['00010', '00110', '01010', '10010', '11111', '00010', '00010'],
            '5': ['11111', '10000', '11110', '00001', '00001', '10001', '01110'],
            '6': ['00110', '01000', '10000', '11110', '10001', '10001', '01110'],
            '7': ['11111', '00001', '00010', '00100', '01000', '01000', '01000'],
            '8': ['01110', '10001', '10001', '01110', '10001', '10001', '01110'],
            '9': ['01110', '10001', '10001', '01111', '00001', '00010', '01100'],
            'A': ['01110', '10001', '10001', '11111', '10001', '10001', '10001'],
            'B': ['11110', '10001', '10001', '11110', '10001', '10001', '11110'],
            'C': ['01110', '10001', '10000', '10000', '10000', '10001', '01110'],
            'D': ['11110', '10001', '10001', '10001', '10001', '10001', '11110'],
            'E': ['11111', '10000', '10000', '11110', '10000', '10000', '11111'],
            'F': ['11111', '10000', '10000', '11110', '10000', '10000', '10000'],
            'G': ['01110', '10001', '10000', '10111', '10001', '10001', '01110'],
            'H': ['10001', '10001', '10001', '11111', '10001', '10001', '10001'],
            'I': ['01110', '00100', '00100', '00100', '00100', '00100', '01110'],
            'J': ['00111', '00010', '00010', '00010', '00010', '10010', '01100'],
            'K': ['10001', '10010', '10100', '11000', '10100', '10010', '10001'],
            'L': ['10000', '10000', '10000', '10000', '10000', '10000', '11111'],
            'M': ['10001', '11011', '10101', '10101', '10001', '10001', '10001'],
            'N': ['10001', '11001', '10101', '10011', '10001', '10001', '10001'],
            'O': ['01110', '10001', '10001', '10001', '10001', '10001', '01110'],
            'P': ['11110', '10001', '10001', '11110', '10000', '10000', '10000'],
            'Q': ['01110', '10001', '10001', '10001', '10101', '10010', '01101'],
            'R': ['11110', '10001', '10001', '11110', '10100', '10010', '10001'],
            'S': ['01110', '10001', '10000', '01110', '00001', '10001', '01110'],
            'T': ['11111', '00100', '00100', '00100', '00100', '00100', '00100'],
            'U': ['10001', '10001', '10001', '10001', '10001', '10001', '01110'],
            'V': ['10001', '10001', '10001', '10001', '10001', '01010', '00100'],
            'W': ['10001', '10001', '10001', '10101', '10101', '11011', '10001'],
            'X': ['10001', '10001', '01010', '00100', '01010', '10001', '10001'],
            'Y': ['10001', '10001', '01010', '00100', '00100', '00100', '00100'],
            'Z': ['11111', '00001', '00010', '00100', '01000', '10000', '11111'],
            ' ': ['00000', '00000', '00000', '00000', '00000', '00000', '00000'],
            '-': ['00000', '00000', '00000', '11111', '00000', '00000', '00000'],
            '.': ['00000', '00000', '00000', '00000', '00000', '00000', '00100'],
            ':': ['00000', '00100', '00100', '00000', '00100', '00100', '00000'],
        }
        
        # Convert to uppercase for lookup
        char_upper = char.upper()
        pattern = SIMPLE_FONT.get(char_upper, SIMPLE_FONT.get(' '))
        
        if pattern is None:
            return 4  # Return default width for unknown chars
        
        # Calculate vertical offset to center
        char_height = len(pattern)
        y_start = (self.config.height1 - char_height) // 2
        
        # Draw the character
        for y, row in enumerate(pattern):
            for x, pixel in enumerate(row):
                if pixel == '1':
                    screen_x = start_x + x
                    screen_y = y_start + y
                    
                    if 0 <= screen_x < self.config.width1:
                        if 0 <= screen_y < self.config.height1:
                            self._draw_pixel(
                                draw, screen_x, screen_y,
                                self.led_color, offset_x, offset_y
                            )
        
        return 5  # Width of simple font
    
    def _draw_empty_matrix(self, draw: ImageDraw.Draw):
        """Draw the empty LED matrix background."""
        offset_x = 10
        offset_y = 10
        
        # Draw first section
        for y in range(self.config.height1):
            for x in range(self.config.width1):
                self._draw_pixel(draw, x, y, self.LED_OFF, offset_x, offset_y)
        
        # Draw second section if bimode
        if self.config.is_bimode:
            offset_y += self.config.height1 * (self.pixel_size + self.pixel_gap) + 20
            for y in range(self.config.height2):
                for x in range(self.config.width2):
                    self._draw_pixel(draw, x, y, self.LED_OFF, offset_x, offset_y)
    
    def _render_text_to_image(self, text: str, font_codes: str = "") -> Image.Image:
        """Render text to a PIL Image."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow is required for image export")
        
        # Create image
        size = self._calculate_image_size()
        image = Image.new('RGB', size, self.BG_COLOR)
        draw = ImageDraw.Draw(image)
        
        # Draw empty matrix first
        self._draw_empty_matrix(draw)
        
        # Render text
        offset_x = 10
        offset_y = 10
        current_x = 0
        
        for i, char in enumerate(text):
            # Handle special characters
            if char == '|' or char == '¦':
                continue
            elif char == '²':
                current_x += 1
                continue
            
            # Get font
            font_code = font_codes[i] if i < len(font_codes) else '2'
            font = self.fonts.get(font_code) or self.fonts.get('2')
            
            if font is None:
                # No font available - use simple fallback rendering
                char_width = self._draw_simple_char(draw, char, current_x, offset_x, offset_y)
                current_x += char_width + 1
                continue
            
            # Get character
            font_char = font.get_char(char)
            
            if font_char:
                # Center vertically
                y_start = (self.config.height1 - font_char.height) // 2
                
                # Draw character pixels
                for y, row in enumerate(font_char.pixels):
                    for x, pixel in enumerate(row):
                        if pixel:
                            screen_x = current_x + x
                            screen_y = y_start + y
                            
                            if 0 <= screen_x < self.config.width1:
                                if 0 <= screen_y < self.config.height1:
                                    self._draw_pixel(
                                        draw, screen_x, screen_y,
                                        self.led_color, offset_x, offset_y
                                    )
                
                current_x += font_char.width + 1
            else:
                current_x += 4
        
        return image
    
    def export_png(self, text: str, filepath: str, font_codes: str = ""):
        """Export display to PNG file."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow est requis pour l'export d'images. Installez-le avec: pip install Pillow")
        
        image = self._render_text_to_image(text, font_codes)
        image.save(filepath, 'PNG')
        return filepath
    
    def export_jpg(self, text: str, filepath: str, font_codes: str = "", quality: int = 95):
        """Export display to JPG file."""
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow est requis pour l'export d'images. Installez-le avec: pip install Pillow")
        
        image = self._render_text_to_image(text, font_codes)
        # Convert to RGB if needed (JPG doesn't support alpha)
        if image.mode != 'RGB':
            image = image.convert('RGB')
        image.save(filepath, 'JPEG', quality=quality)
        return filepath
    
    def export_gif(self, texts: List[str], filepath: str, 
                   font_codes: List[str] = None,
                   durations: List[int] = None,
                   loop: int = 0):
        """
        Export multiple frames as animated GIF.
        
        Args:
            texts: List of text strings for each frame
            filepath: Output file path
            font_codes: List of font codes for each frame
            durations: List of durations in milliseconds for each frame
            loop: Number of loops (0 = infinite)
        """
        if not PIL_AVAILABLE:
            raise ImportError("PIL/Pillow est requis pour l'export d'images. Installez-le avec: pip install Pillow")
        
        if not texts:
            raise ValueError("Au moins un texte est requis")
        
        # Default font codes and durations
        if font_codes is None:
            font_codes = [""] * len(texts)
        if durations is None:
            durations = [3000] * len(texts)  # 3 seconds default
        
        # Ensure lists are same length
        while len(font_codes) < len(texts):
            font_codes.append("")
        while len(durations) < len(texts):
            durations.append(3000)
        
        # Generate frames
        frames = []
        for i, text in enumerate(texts):
            frame = self._render_text_to_image(text, font_codes[i])
            # Convert to palette mode for GIF
            frame = frame.convert('P', palette=Image.ADAPTIVE, colors=256)
            frames.append(frame)
        
        # Save as animated GIF
        frames[0].save(
            filepath,
            save_all=True,
            append_images=frames[1:] if len(frames) > 1 else [],
            duration=durations,
            loop=loop
        )
        
        return filepath
    
    def export_message_gif(self, message: Message, filepath: str,
                           include_header: bool = True):
        """
        Export a message with all alternances as animated GIF.
        
        Args:
            message: Message to export
            filepath: Output file path
            include_header: Whether to include the header in each frame
        """
        texts = []
        durations = []
        
        for alt in message.alternances:
            if alt.text:
                text = (message.header + alt.text) if include_header else alt.text
                texts.append(text)
                # Convert duration from 1/10 seconds to milliseconds
                durations.append(alt.duration * 100)
        
        if not texts:
            # No alternances, use header only
            if message.header:
                texts = [message.header]
                durations = [3000]
            else:
                raise ValueError("Le message est vide")
        
        return self.export_gif(texts, filepath, durations=durations)


def check_pil_available() -> bool:
    """Check if PIL/Pillow is available."""
    return PIL_AVAILABLE


def get_supported_formats() -> List[str]:
    """Get list of supported export formats."""
    if PIL_AVAILABLE:
        return ['PNG', 'JPG', 'GIF']
    return []
