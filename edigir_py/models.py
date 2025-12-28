"""
Data models for Edigir.
Defines the core data structures for displays, messages, fonts, and palettes.
"""

from dataclasses import dataclass, field
from typing import List, Dict, Optional, Tuple
from enum import Enum


class DisplayType(Enum):
    """Type of LED display."""
    FRONT = "front"
    SIDE = "side"
    REAR = "rear"
    INTERIOR = "interior"


class AnimationType(Enum):
    """Animation type for text display."""
    STATIC = 0
    SCROLL_LEFT = 1
    SCROLL_RIGHT = 2
    BLINK = 3
    FADE = 4


@dataclass
class DisplayConfig:
    """Configuration for a display (girouette)."""
    name: str
    description: str = ""
    height1: int = 0
    width1: int = 0
    height2: int = 0
    width2: int = 0
    has_icon: int = 0
    is_color: int = 0
    
    @property
    def is_bimode(self) -> bool:
        """Check if display has two sections (bimode)."""
        return self.height2 > 0 and self.width2 > 0


@dataclass
class Alternance:
    """One alternance (variant) of a message."""
    text: str = ""
    fonts: str = ""  # Font codes for each character
    duration: int = 30  # Duration in tenths of second
    animation: AnimationType = AnimationType.STATIC
    text_color: int = 1  # Index in palette
    bg_color: int = 0  # Index in palette


@dataclass  
class Message:
    """A destination message with multiple alternances."""
    number: int  # Message number (1-9999)
    header: str = ""  # Fixed header text
    header_fonts: str = ""  # Font codes for header
    alternances: List[Alternance] = field(default_factory=lambda: [Alternance(), Alternance(), Alternance()])
    
    # Options
    film_number: str = ""
    sae_code: str = ""
    
    # Interior display specific
    terminus: str = ""
    terminus_fonts: str = ""
    next_stop: str = ""
    next_stop_fonts: str = ""
    stop_list_start: int = 0
    stop_list_end: int = 0


@dataclass
class FontCharacter:
    """A single character in a font."""
    char: str
    width: int
    height: int
    pixels: List[List[bool]] = field(default_factory=list)
    
    def __post_init__(self):
        if not self.pixels:
            self.pixels = [[False] * self.width for _ in range(self.height)]


@dataclass
class Font:
    """A complete font for LED display."""
    name: str
    height: int
    is_proportional: bool = True
    characters: Dict[str, FontCharacter] = field(default_factory=dict)
    
    def get_char(self, char: str) -> Optional[FontCharacter]:
        """Get a character from the font."""
        return self.characters.get(char)


@dataclass
class ColorEntry:
    """A color in the palette."""
    rgb_hex: str  # RGB hex color for display
    led_hex: str  # Actual LED color value
    name: str


@dataclass
class Palette:
    """Color palette for LED displays."""
    colors: List[ColorEntry] = field(default_factory=list)
    
    def get_color(self, index: int) -> Optional[ColorEntry]:
        """Get a color by index."""
        if 0 <= index < len(self.colors):
            return self.colors[index]
        return None


@dataclass
class Project:
    """Complete Edigir project."""
    version: str = "2.0"
    font_file: str = ""
    
    # Display configurations
    front_display: Optional[DisplayConfig] = None
    side_display: Optional[DisplayConfig] = None
    rear_display: Optional[DisplayConfig] = None
    
    # Messages indexed by number
    messages: Dict[int, Message] = field(default_factory=dict)
    
    # Fonts (keyed by font code like '0', '1', '2', 'A', 'E', etc.)
    fonts: Dict[str, Font] = field(default_factory=dict)
    
    # Color palette
    palette: Palette = field(default_factory=Palette)
    
    def get_message(self, number: int) -> Optional[Message]:
        """Get a message by number."""
        return self.messages.get(number)
    
    def add_message(self, number: int) -> Message:
        """Add a new message."""
        msg = Message(number=number)
        self.messages[number] = msg
        return msg
    
    def delete_message(self, number: int) -> bool:
        """Delete a message."""
        if number in self.messages:
            del self.messages[number]
            return True
        return False
    
    def get_sorted_message_numbers(self) -> List[int]:
        """Get sorted list of message numbers."""
        return sorted(self.messages.keys())
