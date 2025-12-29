"""
Fullscreen Display Mode for Edigir.
Turns the computer screen into a virtual girouette (bus display) with animations.
"""

import tkinter as tk
from tkinter import ttk
from typing import Dict, List, Optional, Callable
import time

from .models import DisplayConfig, Font, FontCharacter, Message, Project, Palette, AnimationType
from .renderer import BUILTIN_FONT_5X7, get_builtin_char_bitmap


# Help text constant for fullscreen mode
FULLSCREEN_HELP_TEXT = (
    "ESC: Quitter | ←/→: Message | ↑/↓: Alternance | "
    "ESPACE: Play/Pause | C: Couleur | S: Scroll | F: Plein écran | G: Glow"
)


class FullscreenGirouette(tk.Toplevel):
    """
    Fullscreen window that displays the computer screen as a girouette.
    This allows the screen to be used as a real bus destination display with smooth animations.
    """
    
    # LED colors
    LED_OFF = "#0a0a0a"
    LED_AMBER = "#ff6600"
    LED_GREEN = "#00ff00"
    LED_RED = "#ff0000"
    LED_YELLOW = "#ffff00"
    LED_WHITE = "#ffffff"
    
    # Dim versions for glow effect
    LED_DIM_AMBER = "#4d2200"
    LED_DIM_GREEN = "#004d00"
    LED_DIM_RED = "#4d0000"
    LED_DIM_YELLOW = "#4d4d00"
    LED_DIM_WHITE = "#4d4d4d"
    
    def __init__(self, parent, project: Project, display_config: DisplayConfig = None):
        super().__init__(parent)
        
        self.project = project
        self.display_config = display_config or DisplayConfig(
            name="Écran", height1=16, width1=84
        )
        
        # State
        self.current_message_num: int = 1
        self.current_alternance: int = 0
        self.animation_running: bool = False
        self.scroll_offset: int = 0
        self.alternance_timer: Optional[str] = None
        self.scroll_timer: Optional[str] = None
        self.animation_frame: int = 0
        
        # Animation settings
        self.scroll_speed = 30  # ms per pixel
        self.use_glow = True
        
        # Colors
        self.led_on_color = self.LED_AMBER
        self.led_off_color = self.LED_OFF
        self.bg_color = "#000000"
        
        # Fonts for rendering
        self.fonts: Dict[str, Font] = project.fonts if project.fonts else {}
        
        # Pixel cache for faster rendering
        self._pixel_cache: Dict[str, int] = {}
        
        # Setup fullscreen
        self._setup_window()
        self._create_ui()
        self._bind_events()
        
        # Start display
        self._update_display()
    
    def _setup_window(self):
        """Configure the fullscreen window."""
        self.title("Girouette - Mode Plein Écran")
        self.configure(bg=self.bg_color)
        
        # Get screen dimensions
        self.screen_width = self.winfo_screenwidth()
        self.screen_height = self.winfo_screenheight()
        
        # Calculate optimal pixel size based on screen
        self._calculate_pixel_size()
        
        # Set fullscreen
        self.attributes('-fullscreen', True)
        self.attributes('-topmost', True)
        
        # Hide cursor in fullscreen
        self.config(cursor="none")
    
    def _calculate_pixel_size(self):
        """Calculate the optimal LED pixel size for the screen."""
        # Calculate maximum pixel size that fits the display
        margin = 100  # Margin for controls
        available_width = self.screen_width - margin
        available_height = self.screen_height - margin
        
        # Calculate pixel size based on display dimensions
        max_width_px = available_width // (self.display_config.width1 + 2)
        max_height_px = available_height // (self.display_config.height1 + 4)
        
        # Use the smaller to ensure it fits
        self.pixel_size = min(max_width_px, max_height_px)
        self.pixel_size = max(self.pixel_size, 4)  # Minimum 4 pixels
        self.pixel_gap = max(1, self.pixel_size // 8)  # Proportional gap
    
    def _create_ui(self):
        """Create the fullscreen UI."""
        # Main frame
        self.main_frame = tk.Frame(self, bg=self.bg_color)
        self.main_frame.pack(fill=tk.BOTH, expand=True)
        
        # Top info bar (semi-transparent)
        self.info_frame = tk.Frame(self.main_frame, bg="#1a1a1a")
        self.info_frame.pack(fill=tk.X, side=tk.TOP)
        
        self.info_label = tk.Label(
            self.info_frame,
            text=FULLSCREEN_HELP_TEXT,
            fg="#666666",
            bg="#1a1a1a",
            font=("Helvetica", 10)
        )
        self.info_label.pack(pady=5)
        
        # Message number display
        self.msg_label = tk.Label(
            self.info_frame,
            text="Message: 1",
            fg="#ff6600",
            bg="#1a1a1a",
            font=("Helvetica", 14, "bold")
        )
        self.msg_label.pack(pady=2)
        
        # LED Display canvas - centered
        self.canvas_frame = tk.Frame(self.main_frame, bg=self.bg_color)
        self.canvas_frame.pack(fill=tk.BOTH, expand=True)
        
        # Calculate canvas size
        canvas_width = self.display_config.width1 * (self.pixel_size + self.pixel_gap) + 40
        canvas_height = self.display_config.height1 * (self.pixel_size + self.pixel_gap) + 40
        
        self.canvas = tk.Canvas(
            self.canvas_frame,
            width=canvas_width,
            height=canvas_height,
            bg=self.bg_color,
            highlightthickness=0
        )
        self.canvas.place(relx=0.5, rely=0.5, anchor=tk.CENTER)
        
        # Bottom status
        self.status_frame = tk.Frame(self.main_frame, bg="#1a1a1a")
        self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
        
        self.status_label = tk.Label(
            self.status_frame,
            text="Mode: Statique | Alternance: 1/3",
            fg="#666666",
            bg="#1a1a1a",
            font=("Helvetica", 10)
        )
        self.status_label.pack(pady=5)
    
    def _bind_events(self):
        """Bind keyboard and mouse events."""
        self.bind('<Escape>', lambda e: self._exit_fullscreen())
        self.bind('<F11>', lambda e: self._toggle_fullscreen())
        self.bind('<Left>', lambda e: self._prev_message())
        self.bind('<Right>', lambda e: self._next_message())
        self.bind('<Up>', lambda e: self._prev_alternance())
        self.bind('<Down>', lambda e: self._next_alternance())
        self.bind('<space>', lambda e: self._toggle_animation())
        self.bind('<c>', lambda e: self._cycle_color())
        self.bind('<C>', lambda e: self._cycle_color())
        self.bind('<s>', lambda e: self._toggle_scroll())
        self.bind('<S>', lambda e: self._toggle_scroll())
        self.bind('<f>', lambda e: self._toggle_fullscreen())
        self.bind('<F>', lambda e: self._toggle_fullscreen())
        self.bind('<h>', lambda e: self._toggle_info())
        self.bind('<H>', lambda e: self._toggle_info())
        self.bind('<g>', lambda e: self._toggle_glow())
        self.bind('<G>', lambda e: self._toggle_glow())
        
        # Mouse click to toggle info
        self.canvas.bind('<Button-1>', lambda e: self._toggle_info())
    
    def _exit_fullscreen(self):
        """Exit fullscreen mode."""
        self._stop_animation()
        self.destroy()
    
    def _toggle_fullscreen(self):
        """Toggle fullscreen mode."""
        is_fullscreen = self.attributes('-fullscreen')
        self.attributes('-fullscreen', not is_fullscreen)
        
        if is_fullscreen:
            self.config(cursor="")
        else:
            self.config(cursor="none")
    
    def _toggle_info(self):
        """Toggle info bar visibility."""
        if self.info_frame.winfo_viewable():
            self.info_frame.pack_forget()
            self.status_frame.pack_forget()
        else:
            self.info_frame.pack(fill=tk.X, side=tk.TOP, before=self.canvas_frame)
            self.status_frame.pack(fill=tk.X, side=tk.BOTTOM)
    
    def _toggle_glow(self):
        """Toggle LED glow effect."""
        self.use_glow = not self.use_glow
        self._update_display()
    
    def _prev_message(self):
        """Go to previous message."""
        nums = self.project.get_sorted_message_numbers()
        if not nums:
            return
        
        try:
            idx = nums.index(self.current_message_num)
            if idx > 0:
                self.current_message_num = nums[idx - 1]
                self.current_alternance = 0
                self._stop_animation()
                self._update_display()
        except ValueError:
            self.current_message_num = nums[0]
            self._update_display()
    
    def _next_message(self):
        """Go to next message."""
        nums = self.project.get_sorted_message_numbers()
        if not nums:
            return
        
        try:
            idx = nums.index(self.current_message_num)
            if idx < len(nums) - 1:
                self.current_message_num = nums[idx + 1]
                self.current_alternance = 0
                self._stop_animation()
                self._update_display()
        except ValueError:
            self.current_message_num = nums[-1]
            self._update_display()
    
    def _prev_alternance(self):
        """Go to previous alternance."""
        if self.current_alternance > 0:
            self.current_alternance -= 1
            self._update_display()
    
    def _next_alternance(self):
        """Go to next alternance."""
        msg = self.project.get_message(self.current_message_num)
        if msg and self.current_alternance < 2:
            self.current_alternance += 1
            self._update_display()
    
    def _cycle_color(self):
        """Cycle through LED colors."""
        colors = [
            self.LED_AMBER,
            self.LED_GREEN,
            self.LED_RED,
            self.LED_YELLOW,
            self.LED_WHITE,
        ]
        
        try:
            idx = colors.index(self.led_on_color)
            self.led_on_color = colors[(idx + 1) % len(colors)]
        except ValueError:
            self.led_on_color = colors[0]
        
        self._update_display()
    
    def _toggle_animation(self):
        """Toggle alternance cycling animation."""
        if self.animation_running:
            self._stop_animation()
        else:
            self._start_alternance_animation()
    
    def _toggle_scroll(self):
        """Toggle scroll animation for current text."""
        if self.scroll_timer:
            self._stop_scroll()
        else:
            self._start_scroll_animation()
    
    def _start_alternance_animation(self):
        """Start alternance cycling animation."""
        self.animation_running = True
        self._cycle_alternance()
        self._update_status()
    
    def _start_scroll_animation(self):
        """Start scrolling animation for current text."""
        self.scroll_offset = 0
        self._animate_scroll()
        self._update_status()
    
    def _stop_animation(self):
        """Stop all animations."""
        self.animation_running = False
        
        if self.alternance_timer:
            self.after_cancel(self.alternance_timer)
            self.alternance_timer = None
        
        self._stop_scroll()
        self._update_status()
    
    def _stop_scroll(self):
        """Stop scroll animation."""
        if self.scroll_timer:
            self.after_cancel(self.scroll_timer)
            self.scroll_timer = None
            self.scroll_offset = 0
            self._update_display()
    
    def _cycle_alternance(self):
        """Cycle through alternances based on their duration."""
        if not self.animation_running:
            return
        
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Get current alternance duration (in 1/10 seconds)
        alt = msg.alternances[self.current_alternance]
        duration_ms = alt.duration * 100  # Convert to milliseconds
        
        # Update display
        self._update_display()
        
        # Schedule next alternance
        self.alternance_timer = self.after(duration_ms, self._advance_alternance)
    
    def _advance_alternance(self):
        """Advance to next alternance."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Find next non-empty alternance
        for _ in range(3):
            self.current_alternance = (self.current_alternance + 1) % 3
            if msg.alternances[self.current_alternance].text:
                break
        
        self._cycle_alternance()
    
    def _animate_scroll(self):
        """Animate scrolling text."""
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            return
        
        # Get text to display
        alt = msg.alternances[self.current_alternance]
        text = msg.header + alt.text
        
        if not text:
            return
        
        # Calculate text width
        text_width = self._get_text_width(text)
        
        # Update display with scroll offset
        self._draw_led_matrix(text)
        
        self.scroll_offset += 1
        
        # Reset when text scrolls off screen - use negative offset for seamless loop
        if self.scroll_offset > text_width + self.display_config.width1:
            self.scroll_offset = -self.display_config.width1
        
        # Schedule next frame
        self.scroll_timer = self.after(self.scroll_speed, self._animate_scroll)
    
    def _get_text_width(self, text: str) -> int:
        """Calculate the total width of text in pixels."""
        total_width = 0
        for char in text:
            if char == '|' or char == '¦':
                continue
            elif char == '²':
                total_width += 1
            else:
                total_width += 6  # 5 pixels + 1 spacing
        return total_width
    
    def _update_display(self):
        """Update the LED display."""
        self.canvas.delete("all")
        
        msg = self.project.get_message(self.current_message_num)
        if not msg:
            self._draw_empty_matrix()
            return
        
        # Get text to display
        alt = msg.alternances[self.current_alternance]
        text = msg.header + alt.text
        
        if not text:
            # Try other alternances
            for i in range(3):
                if msg.alternances[i].text:
                    text = msg.header + msg.alternances[i].text
                    break
        
        if not text:
            self._draw_empty_matrix()
            return
        
        # Draw the LED matrix with text
        self._draw_led_matrix(text)
        
        # Update labels
        self._update_labels(msg, text)
    
    def _draw_empty_matrix(self):
        """Draw an empty LED matrix."""
        offset_x = 20
        offset_y = 20
        
        for y in range(self.display_config.height1):
            for x in range(self.display_config.width1):
                self._draw_pixel(x, y, self.led_off_color, offset_x, offset_y)
    
    def _draw_led_matrix(self, text: str):
        """Draw the LED matrix with text."""
        offset_x = 20
        offset_y = 20
        
        # First draw empty matrix
        self._draw_empty_matrix()
        
        # Then render text
        current_x = -self.scroll_offset
        
        for char in text:
            # Handle special characters
            if char == '|' or char == '¦':
                continue
            elif char == '²':
                current_x += 1
                continue
            
            # Get character bitmap from built-in font
            bitmap = get_builtin_char_bitmap(char)
            char_width = 5
            char_height = 7
            
            # Center vertically
            y_start = (self.display_config.height1 - char_height) // 2
            
            # Render character pixels
            for y, row in enumerate(bitmap):
                for x, pixel in enumerate(row):
                    if pixel:
                        screen_x = current_x + x
                        screen_y = y_start + y
                        
                        if 0 <= screen_x < self.display_config.width1:
                            if 0 <= screen_y < self.display_config.height1:
                                self._draw_pixel(
                                    screen_x, screen_y,
                                    self.led_on_color,
                                    offset_x, offset_y
                                )
            
            current_x += char_width + 1  # Add spacing
    
    def _get_glow_color(self) -> str:
        """Get dim glow color for current LED color."""
        glow_map = {
            self.LED_AMBER: self.LED_DIM_AMBER,
            self.LED_GREEN: self.LED_DIM_GREEN,
            self.LED_RED: self.LED_DIM_RED,
            self.LED_YELLOW: self.LED_DIM_YELLOW,
            self.LED_WHITE: self.LED_DIM_WHITE,
        }
        return glow_map.get(self.led_on_color, self.LED_DIM_AMBER)
    
    def _draw_pixel(self, x: int, y: int, color: str, offset_x: int, offset_y: int):
        """Draw a single LED pixel with glow effect."""
        px = offset_x + x * (self.pixel_size + self.pixel_gap)
        py = offset_y + y * (self.pixel_size + self.pixel_gap)
        
        # Draw glow for lit pixels
        if self.use_glow and color != self.led_off_color and self.pixel_size > 6:
            glow_color = self._get_glow_color()
            glow_size = self.pixel_size + 2
            self.canvas.create_oval(
                px - 1, py - 1,
                px + glow_size, py + glow_size,
                fill=glow_color,
                outline=""
            )
        
        # Draw LED
        self.canvas.create_oval(
            px, py,
            px + self.pixel_size, py + self.pixel_size,
            fill=color,
            outline=""
        )
    
    def _update_labels(self, msg: Message, text: str):
        """Update info labels."""
        self.msg_label.config(
            text=f"Message: {self.current_message_num} | {text[:30]}{'...' if len(text) > 30 else ''}"
        )
        self._update_status()
    
    def _update_status(self):
        """Update status label."""
        mode = "Lecture" if self.animation_running else ("Défilant" if self.scroll_timer else "Statique")
        color_name = {
            self.LED_AMBER: "Ambre",
            self.LED_GREEN: "Vert",
            self.LED_RED: "Rouge",
            self.LED_YELLOW: "Jaune",
            self.LED_WHITE: "Blanc",
        }.get(self.led_on_color, "Ambre")
        
        glow_state = "On" if self.use_glow else "Off"
        
        self.status_label.config(
            text=f"Mode: {mode} | Alternance: {self.current_alternance + 1}/3 | Couleur: {color_name} | Glow: {glow_state}"
        )
    
    def set_message(self, message_num: int):
        """Set the current message to display."""
        if message_num in self.project.messages:
            self.current_message_num = message_num
            self.current_alternance = 0
            self._update_display()
    
    def set_display_config(self, config: DisplayConfig):
        """Update display configuration."""
        self.display_config = config
        self._calculate_pixel_size()
        
        # Resize canvas
        canvas_width = config.width1 * (self.pixel_size + self.pixel_gap) + 40
        canvas_height = config.height1 * (self.pixel_size + self.pixel_gap) + 40
        
        self.canvas.config(width=canvas_width, height=canvas_height)
        self._update_display()


class ScreenDetectionDialog(tk.Toplevel):
    """Dialog to detect and configure screen as girouette."""
    
    def __init__(self, parent, callback: Callable[[DisplayConfig], None]):
        super().__init__(parent)
        
        self.callback = callback
        
        self.title("Détection de l'écran comme girouette")
        self.geometry("500x400")
        self.transient(parent)
        self.grab_set()
        
        self._create_ui()
    
    def _create_ui(self):
        """Create the dialog UI."""
        # Header
        header = ttk.Label(
            self,
            text="Configuration de l'écran comme afficheur de bus",
            font=("Helvetica", 12, "bold")
        )
        header.pack(pady=15)
        
        # Screen info
        info_frame = ttk.LabelFrame(self, text="Informations écran")
        info_frame.pack(fill=tk.X, padx=20, pady=10)
        
        screen_width = self.winfo_screenwidth()
        screen_height = self.winfo_screenheight()
        
        ttk.Label(
            info_frame,
            text=f"Résolution: {screen_width} x {screen_height} pixels"
        ).pack(pady=5)
        
        # Display configuration
        config_frame = ttk.LabelFrame(self, text="Configuration girouette virtuelle")
        config_frame.pack(fill=tk.X, padx=20, pady=10)
        
        # Height
        height_frame = ttk.Frame(config_frame)
        height_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(height_frame, text="Hauteur (LEDs):").pack(side=tk.LEFT)
        self.height_var = tk.StringVar(value="16")
        height_spin = ttk.Spinbox(
            height_frame,
            textvariable=self.height_var,
            from_=7,
            to=32,
            width=10
        )
        height_spin.pack(side=tk.LEFT, padx=10)
        
        # Width
        width_frame = ttk.Frame(config_frame)
        width_frame.pack(fill=tk.X, padx=10, pady=5)
        
        ttk.Label(width_frame, text="Largeur (LEDs):").pack(side=tk.LEFT)
        self.width_var = tk.StringVar(value="84")
        width_spin = ttk.Spinbox(
            width_frame,
            textvariable=self.width_var,
            from_=20,
            to=200,
            width=10
        )
        width_spin.pack(side=tk.LEFT, padx=10)
        
        # Presets
        preset_frame = ttk.LabelFrame(self, text="Préréglages")
        preset_frame.pack(fill=tk.X, padx=20, pady=10)
        
        presets = [
            ("16x84 (Standard)", 16, 84),
            ("16x112 (Large)", 16, 112),
            ("16x140 (Extra large)", 16, 140),
            ("24x40 (Couleur)", 24, 40),
            ("8x84 (Petit)", 8, 84),
            ("7x80 (Mini)", 7, 80),
        ]
        
        for name, h, w in presets:
            ttk.Button(
                preset_frame,
                text=name,
                command=lambda h=h, w=w: self._set_preset(h, w)
            ).pack(side=tk.LEFT, padx=5, pady=5)
        
        # Color option
        color_frame = ttk.Frame(self)
        color_frame.pack(fill=tk.X, padx=20, pady=10)
        
        self.color_var = tk.BooleanVar(value=False)
        ttk.Checkbutton(
            color_frame,
            text="Afficheur LED couleur",
            variable=self.color_var
        ).pack(side=tk.LEFT)
        
        # Buttons
        btn_frame = ttk.Frame(self)
        btn_frame.pack(pady=20)
        
        ttk.Button(
            btn_frame,
            text="Lancer l'affichage plein écran",
            command=self._apply
        ).pack(side=tk.LEFT, padx=10)
        
        ttk.Button(
            btn_frame,
            text="Annuler",
            command=self.destroy
        ).pack(side=tk.LEFT, padx=10)
    
    def _set_preset(self, height: int, width: int):
        """Set a preset configuration."""
        self.height_var.set(str(height))
        self.width_var.set(str(width))
    
    def _apply(self):
        """Apply the configuration and launch fullscreen."""
        try:
            height = int(self.height_var.get())
            width = int(self.width_var.get())
            
            config = DisplayConfig(
                name=f"Écran {height}x{width}",
                description="Écran virtuel comme girouette",
                height1=height,
                width1=width,
                is_color=1 if self.color_var.get() else 0
            )
            
            self.callback(config)
            self.destroy()
            
        except ValueError:
            from tkinter import messagebox
            messagebox.showerror("Erreur", "Valeurs invalides")
