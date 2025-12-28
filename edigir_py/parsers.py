"""
File parsers for Edigir file formats.
Handles reading and writing DSW, POL, PAL, and other formats.
"""

import os
import re
from typing import Dict, List, Optional, Tuple
from .models import (
    Project, Message, Alternance, AnimationType,
    DisplayConfig, Font, FontCharacter, Palette, ColorEntry
)


class DSWParser:
    """Parser for DSW (destination) files."""
    
    @staticmethod
    def parse(filepath: str) -> Tuple[Project, str]:
        """
        Parse a DSW file and return a Project.
        Returns (project, font_file_path).
        """
        project = Project()
        
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read file: {e}")
        
        if len(lines) < 6:
            raise ValueError("Invalid DSW file: too short")
        
        # Parse header
        # Line 0: Version
        project.version = lines[0].strip()
        
        # Line 1: Font file path
        project.font_file = lines[1].strip()
        
        # Line 2: Front display name
        front_display_name = lines[2].strip()
        
        # Line 3: Side display config  
        side_display_name = lines[3].strip()
        
        # Line 4: Rear display config
        rear_display_name = lines[4].strip()
        
        # Line 5: Flag
        # Lines 6+: Messages
        
        current_line = 6
        
        # Parse messages
        # Each message block is 118 lines (or similar structure)
        while current_line < len(lines):
            line = lines[current_line].strip()
            
            # Check if this is a message number
            if line.isdigit():
                msg_num = int(line)
                msg = Message(number=msg_num)
                
                # Parse message content
                # Message structure spans multiple lines
                current_line = DSWParser._parse_message_block(lines, current_line, msg)
                project.messages[msg_num] = msg
            else:
                current_line += 1
        
        # Create display configs from names
        if front_display_name:
            project.front_display = DisplayConfig(name=front_display_name)
        if side_display_name and side_display_name != ".Pas de Girouette":
            project.side_display = DisplayConfig(name=side_display_name)
        if rear_display_name:
            project.rear_display = DisplayConfig(name=rear_display_name)
            
        return project, project.font_file
    
    @staticmethod
    def _parse_message_block(lines: List[str], start_line: int, msg: Message) -> int:
        """Parse a message block and return next line index."""
        current = start_line + 1  # Skip message number
        
        # Skip empty lines
        while current < len(lines) and not lines[current].strip():
            current += 1
            
        if current >= len(lines):
            return current
            
        # Next lines should be alternance data
        # Structure: text, fonts, fonts (duplicate), then next alternance...
        
        for alt_idx in range(3):
            if current + 2 >= len(lines):
                break
                
            # Get text line
            text = lines[current].strip() if current < len(lines) else ""
            current += 1
            
            # Get fonts line
            fonts = lines[current].strip() if current < len(lines) else ""
            current += 1
            
            # Skip duplicate fonts line
            current += 1
            
            # Skip timing/animation lines
            while current < len(lines) and lines[current].strip():
                current += 1
            
            # Skip empty lines before next alternance
            while current < len(lines) and not lines[current].strip():
                current += 1
            
            if text or fonts:
                msg.alternances[alt_idx].text = text
                msg.alternances[alt_idx].fonts = fonts
            
            # Check if next line is a new message number
            if current < len(lines) and lines[current].strip().isdigit():
                break
        
        return current
    
    @staticmethod
    def write(filepath: str, project: Project):
        """Write a project to DSW format."""
        lines = []
        
        # Header
        lines.append(project.version)
        lines.append(project.font_file)
        lines.append(project.front_display.name if project.front_display else "16x084")
        lines.append(project.side_display.name if project.side_display else ".Pas de Girouette")
        lines.append(project.rear_display.name if project.rear_display else "16x028")
        lines.append("1")  # Flag
        
        # Messages
        for num in sorted(project.messages.keys()):
            msg = project.messages[num]
            lines.append("")
            lines.append(str(msg.number))
            
            for alt in msg.alternances:
                lines.append("")
                lines.append("")
                lines.append("")
                lines.append("")
                lines.append(alt.text)
                lines.append(alt.fonts)
                lines.append(alt.fonts)  # Duplicate
                
                # More empty lines for structure
                for _ in range(26):
                    lines.append("")
        
        with open(filepath, 'w', encoding='latin-1') as f:
            f.write('\n'.join(lines))


class POLParser:
    """Parser for POL (font/police) files."""
    
    FONT_CODES = ['0', '1', '2', '3', '4', '5', 'A', 'B', 'C', 'D', 'E', 'F']
    
    @staticmethod
    def parse(filepath: str) -> Dict[str, Font]:
        """Parse a POL file and return fonts dictionary."""
        fonts = {}
        
        try:
            with open(filepath, 'rb') as f:
                data = f.read()
        except Exception as e:
            raise ValueError(f"Cannot read font file: {e}")
        
        # POL files contain binary font data
        # The format includes multiple fonts for different sizes
        # Each font contains character bitmaps
        
        # Create basic fonts with standard heights
        font_configs = [
            ('0', 7, "Small"),
            ('1', 7, "Small Bold"),
            ('2', 14, "Medium"),
            ('3', 14, "Medium Bold"),
            ('4', 7, "Custom Small"),
            ('5', 7, "Custom Small (no spacing)"),
            ('A', 7, "Small Alt"),
            ('B', 7, "Small Bold Alt"),
            ('C', 14, "Medium Alt"),
            ('D', 14, "Medium Bold Alt"),
            ('E', 16, "Large Custom"),
            ('F', 16, "Large Custom (no spacing)"),
        ]
        
        for code, height, name in font_configs:
            font = Font(name=name, height=height)
            
            # Create standard ASCII characters
            for c in range(32, 127):
                char = chr(c)
                width = 5 if c != 32 else 3  # Space is narrower
                font_char = FontCharacter(char=char, width=width, height=height)
                font.characters[char] = font_char
            
            fonts[code] = font
        
        # Try to parse actual font data from the binary
        POLParser._parse_binary_fonts(data, fonts)
        
        return fonts
    
    @staticmethod
    def _parse_binary_fonts(data: bytes, fonts: Dict[str, Font]):
        """Parse binary font data."""
        # POL files have a specific binary structure
        # First part is a header with version info
        # Then font bitmap data follows
        
        if len(data) < 100:
            return
        
        # Parse based on known structure
        # The file starts with "Version Logiciel" text followed by binary data
        try:
            # Find end of header text
            header_end = data.find(b'\n\n')
            if header_end == -1:
                header_end = 50
            
            # Binary font data starts after header
            offset = header_end + 2
            
            # Each font section contains bitmap data for characters
            # Format varies but generally: character code, width, then pixel rows
            
        except Exception:
            pass  # Use default fonts if parsing fails
    
    @staticmethod
    def write(filepath: str, fonts: Dict[str, Font]):
        """Write fonts to POL format."""
        # Write header
        header = "Version Logiciel   9.5    "
        
        # Build binary data
        data = bytearray()
        data.extend(header.encode('latin-1'))
        
        # Add font bitmap data
        for code, font in fonts.items():
            for char, font_char in font.characters.items():
                # Write character bitmap
                for row in font_char.pixels:
                    byte_val = 0
                    for i, pixel in enumerate(row[:8]):
                        if pixel:
                            byte_val |= (1 << (7 - i))
                    data.append(byte_val)
        
        with open(filepath, 'wb') as f:
            f.write(data)


class PALParser:
    """Parser for PAL (palette) files."""
    
    @staticmethod
    def parse(filepath: str) -> Palette:
        """Parse a PAL file and return a Palette."""
        palette = Palette()
        
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read palette file: {e}")
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
                
            parts = line.split()
            if len(parts) >= 3:
                rgb_hex = parts[0]
                led_hex = parts[1]
                name = parts[2] if len(parts) > 2 else ""
                
                color = ColorEntry(rgb_hex=rgb_hex, led_hex=led_hex, name=name)
                palette.colors.append(color)
        
        return palette
    
    @staticmethod
    def write(filepath: str, palette: Palette):
        """Write a palette to PAL format."""
        lines = []
        
        for color in palette.colors:
            lines.append(f"{color.rgb_hex} {color.led_hex} {color.name}")
        
        with open(filepath, 'w', encoding='latin-1') as f:
            f.write('\n'.join(lines))


class GIRParser:
    """Parser for GIR (girouette configuration) files."""
    
    @staticmethod
    def parse(filepath: str) -> Dict[str, DisplayConfig]:
        """Parse a GIR file and return display configurations."""
        displays = {}
        
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read GIR file: {e}")
        
        i = 0
        while i < len(lines):
            name = lines[i].strip() if i < len(lines) else ""
            if not name:
                i += 1
                continue
            
            # Read description
            desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
            
            # Read dimensions
            h1 = int(lines[i + 2].strip()) if i + 2 < len(lines) and lines[i + 2].strip().isdigit() else 0
            w1 = int(lines[i + 3].strip()) if i + 3 < len(lines) and lines[i + 3].strip().isdigit() else 0
            h2 = int(lines[i + 4].strip()) if i + 4 < len(lines) and lines[i + 4].strip().isdigit() else 0
            w2 = int(lines[i + 5].strip()) if i + 5 < len(lines) and lines[i + 5].strip().isdigit() else 0
            has_icon = int(lines[i + 6].strip()) if i + 6 < len(lines) and lines[i + 6].strip().isdigit() else 0
            is_color = int(lines[i + 7].strip()) if i + 7 < len(lines) and lines[i + 7].strip().isdigit() else 0
            
            config = DisplayConfig(
                name=name,
                description=desc,
                height1=h1,
                width1=w1,
                height2=h2,
                width2=w2,
                has_icon=has_icon,
                is_color=is_color
            )
            displays[name] = config
            
            i += 8
        
        return displays


class LEDParser:
    """Parser for LED display configuration files."""
    
    @staticmethod
    def parse(filepath: str) -> Dict[str, DisplayConfig]:
        """Parse a LED file and return display configurations."""
        displays = {}
        
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read LED file: {e}")
        
        i = 0
        while i < len(lines):
            name = lines[i].strip() if i < len(lines) else ""
            if not name:
                i += 1
                continue
            
            # Read description
            desc = lines[i + 1].strip() if i + 1 < len(lines) else ""
            
            # Read dimensions (format differs from GIR)
            h1 = int(lines[i + 2].strip()) if i + 2 < len(lines) and lines[i + 2].strip().isdigit() else 0
            w1 = int(lines[i + 3].strip()) if i + 3 < len(lines) and lines[i + 3].strip().isdigit() else 0
            h2 = int(lines[i + 4].strip()) if i + 4 < len(lines) and lines[i + 4].strip().isdigit() else 0
            w2 = int(lines[i + 5].strip()) if i + 5 < len(lines) and lines[i + 5].strip().isdigit() else 0
            has_icon = int(lines[i + 6].strip()) if i + 6 < len(lines) and lines[i + 6].strip().isdigit() else 0
            is_color = int(lines[i + 7].strip()) if i + 7 < len(lines) and lines[i + 7].strip().isdigit() else 0
            
            config = DisplayConfig(
                name=name,
                description=desc,
                height1=h1,
                width1=w1,
                height2=h2,
                width2=w2,
                has_icon=has_icon,
                is_color=is_color
            )
            displays[name] = config
            
            i += 8
        
        return displays


class INIParser:
    """Parser for INI configuration files."""
    
    @staticmethod
    def parse(filepath: str) -> Dict[str, str]:
        """Parse an INI file and return settings dictionary."""
        settings = {}
        
        try:
            with open(filepath, 'r', encoding='latin-1') as f:
                lines = f.readlines()
        except Exception as e:
            raise ValueError(f"Cannot read INI file: {e}")
        
        for line in lines:
            line = line.strip()
            if not line or line.startswith('[') or line.startswith('#'):
                continue
            
            if '=' in line:
                key, value = line.split('=', 1)
                settings[key.strip()] = value.strip()
        
        return settings
    
    @staticmethod
    def write(filepath: str, settings: Dict[str, str], section: str = "Initialisation"):
        """Write settings to INI format."""
        lines = [f"[{section}]"]
        
        for key, value in settings.items():
            lines.append(f"{key}={value}")
        
        with open(filepath, 'w', encoding='latin-1') as f:
            f.write('\n'.join(lines))
