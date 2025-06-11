"""
UI Module

Handles the game's user interface elements including HUD and visual feedback.
"""

import pygame
import time
import math

# Constants
TEXT_COLOR = (220, 220, 220)
HUD_BACKGROUND_COLOR = (20, 20, 40, 180)
HUD_BORDER_COLOR = (100, 100, 200)
FONT_SIZE = 20


class UI:
    """Manages the game's user interface elements."""
    
    def __init__(self, surface):
        """Initialize the UI.
        
        Args:
            surface: Main pygame surface
        """
        self.surface = surface
        self.width = surface.get_width()
        self.height = surface.get_height()
        
        # Initialize font
        pygame.font.init()
        self.font = pygame.font.SysFont(None, FONT_SIZE)
        self.large_font = pygame.font.SysFont(None, 36)
        
        # HUD dimensions
        self.hud_width = 200
        self.hud_height = 120
        self.hud_x = 10
        self.hud_y = 10
        self.padding = 10
        
        # Message system
        self.messages = []  # List of (message, end_time, position) tuples
        
        # Tooltip system
        self.tooltips = {
            "depth": "Depth: Number of nodes you've visited in the maze",
            "pulses": "Active Pulses: Hazardous waves that can send you back to start",
            "branching": "Branching Factor: How interconnected the maze is (avg. connections per node)"
        }
        self.active_tooltip = None
        self.tooltip_timer = 0
        
        # Milestone notification
        self.milestone_notification = None
        self.milestone_timer = 0
        self.milestone_duration = 5.0  # seconds
        
        # Animations
        self.hud_pulse = 0  # For pulsing effect on HUD
    
    def update(self, dt):
        """Update UI animations and timers.
        
        Args:
            dt (float): Time elapsed since last update
        """
        # Update message timers and remove expired messages
        current_time = time.time()
        self.messages = [(msg, end_time, pos) for msg, end_time, pos in self.messages if end_time > current_time]
        
        # Update tooltip timer
        if self.active_tooltip:
            self.tooltip_timer += dt
            if self.tooltip_timer > 5.0:  # Hide tooltip after 5 seconds
                self.active_tooltip = None
                self.tooltip_timer = 0
        
        # Update milestone notification
        if self.milestone_notification:
            self.milestone_timer += dt
            if self.milestone_timer > self.milestone_duration:
                self.milestone_notification = None
                self.milestone_timer = 0
        
        # Update HUD pulse animation
        self.hud_pulse = (self.hud_pulse + dt) % 2.0  # 2-second cycle
    
    def draw(self, nodes_visited, active_pulses, branching_factor):
        """Draw all UI elements.
        
        Args:
            nodes_visited (int): Number of nodes the player has visited
            active_pulses (int): Number of active hazard pulses
            branching_factor (float): Average branching factor of the maze
        """
        self._draw_hud(nodes_visited, active_pulses, branching_factor)
        self._draw_messages()
        self._draw_tooltip()
        
        # Draw milestone notification if active
        if self.milestone_notification:
            self._draw_milestone_notification(self.milestone_notification)
    
    def _draw_hud(self, nodes_visited, active_pulses, branching_factor):
        """Draw the heads-up display with interactive elements.
        
        Args:
            nodes_visited (int): Number of nodes the player has visited
            active_pulses (int): Number of active hazard pulses
            branching_factor (float): Average branching factor of the maze
        """
        # Create a surface for the semi-transparent HUD background
        hud_surface = pygame.Surface((self.hud_width, self.hud_height), pygame.SRCALPHA)
        
        # Fill with semi-transparent background
        hud_surface.fill(HUD_BACKGROUND_COLOR)
        
        # Add pulsing effect to border when there are active pulses
        border_color = HUD_BORDER_COLOR
        if active_pulses > 0:
            # Pulse between normal color and warning color
            pulse_factor = (1 + math.sin(self.hud_pulse * math.pi)) / 2  # 0 to 1
            border_color = (
                int(HUD_BORDER_COLOR[0] + (255 - HUD_BORDER_COLOR[0]) * pulse_factor),
                int(HUD_BORDER_COLOR[1] * (1 - pulse_factor * 0.5)),
                int(HUD_BORDER_COLOR[2] * (1 - pulse_factor * 0.5))
            )
        
        # Draw border
        pygame.draw.rect(
            hud_surface,
            border_color,
            (0, 0, self.hud_width, self.hud_height),
            2  # Border width
        )
        
        # Render text elements with labels
        y_pos = self.padding
        
        # Draw each stat with a hover area for tooltips
        stats = [
            ("Depth", f"{nodes_visited}", "depth"),
            ("Active Pulses", f"{active_pulses}", "pulses"),
            ("Branching", f"{branching_factor:.2f}", "branching")
        ]
        
        for label, value, tooltip_key in stats:
            # Draw label
            label_text = self.font.render(f"{label}:", True, TEXT_COLOR)
            hud_surface.blit(label_text, (self.padding, y_pos))
            
            # Draw value with appropriate color
            value_color = TEXT_COLOR
            if tooltip_key == "pulses" and active_pulses > 0:
                # Make active pulses count red when non-zero
                value_color = (255, 100, 100)
            
            value_text = self.font.render(value, True, value_color)
            hud_surface.blit(value_text, (self.padding + 100, y_pos))
            
            # Create invisible hover area for tooltip
            hover_rect = pygame.Rect(self.hud_x, self.hud_y + y_pos, self.hud_width, FONT_SIZE + 5)
            mouse_pos = pygame.mouse.get_pos()
            if hover_rect.collidepoint(mouse_pos):
                self.active_tooltip = tooltip_key
                self.tooltip_timer = 0
            
            y_pos += FONT_SIZE + 5
        
        # Add help text
        help_text = self.font.render("Press H for Help", True, (180, 180, 220))
        hud_surface.blit(help_text, (self.padding, y_pos + 5))
        
        # Blit HUD surface onto main surface
        self.surface.blit(hud_surface, (self.hud_x, self.hud_y))
    
    def _draw_messages(self):
        """Draw temporary messages on screen."""
        for message, end_time, position in self.messages:
            # Calculate fade-out effect
            time_left = end_time - time.time()
            max_duration = 3.0  # Assume messages last at most 3 seconds
            alpha = min(255, int(255 * time_left / max_duration))
            
            # Render text with fade effect
            text = self.font.render(message, True, TEXT_COLOR)
            text.set_alpha(alpha)
            
            # Position text
            if position == "center":
                text_rect = text.get_rect(center=(self.width // 2, self.height - 50))
            elif position == "top":
                text_rect = text.get_rect(center=(self.width // 2, 50))
            else:
                text_rect = text.get_rect(center=position)
                
            self.surface.blit(text, text_rect)
    
    def _draw_tooltip(self):
        """Draw active tooltip if any."""
        if not self.active_tooltip:
            return
            
        tooltip_text = self.tooltips.get(self.active_tooltip, "")
        if not tooltip_text:
            return
            
        # Create tooltip surface
        font = pygame.font.SysFont(None, 20)
        text = font.render(tooltip_text, True, (255, 255, 255))
        padding = 10
        tooltip_width = text.get_width() + padding * 2
        tooltip_height = text.get_height() + padding * 2
        
        tooltip_surface = pygame.Surface((tooltip_width, tooltip_height), pygame.SRCALPHA)
        tooltip_surface.fill((40, 40, 60, 220))
        pygame.draw.rect(tooltip_surface, (100, 100, 140), (0, 0, tooltip_width, tooltip_height), 1)
        
        # Position tooltip near mouse but ensure it stays on screen
        mouse_pos = pygame.mouse.get_pos()
        tooltip_x = min(mouse_pos[0], self.width - tooltip_width - 10)
        tooltip_y = mouse_pos[1] + 20
        if tooltip_y + tooltip_height > self.height:
            tooltip_y = mouse_pos[1] - tooltip_height - 10
            
        # Add text to tooltip
        tooltip_surface.blit(text, (padding, padding))
        
        # Draw tooltip
        self.surface.blit(tooltip_surface, (tooltip_x, tooltip_y))
    
    def show_message(self, message, duration=2.0, position="center"):
        """Show a temporary message on screen.
        
        Args:
            message (str): Message to display
            duration (float): How long to display the message in seconds
            position (str or tuple): Where to display the message
        """
        end_time = time.time() + duration
        self.messages.append((message, end_time, position))
    
    def show_milestone_notification(self, milestone):
        """Show a notification when a milestone is reached.
        
        Args:
            milestone (int): Milestone level reached
        """
        self.milestone_notification = milestone
        self.milestone_timer = 0
    
    def _draw_milestone_notification(self, milestone):
        """Draw the milestone notification.
        
        Args:
            milestone (int): Milestone level reached
        """
        # Create a surface for the notification
        notif_width = 400
        notif_height = 120
        notif_surface = pygame.Surface((notif_width, notif_height), pygame.SRCALPHA)
        
        # Calculate animation effects
        progress = min(1.0, self.milestone_timer / 0.5)  # 0.5 second fade-in
        fade_out = max(0.0, min(1.0, (self.milestone_timer - (self.milestone_duration - 1.0)) / 1.0))  # 1 second fade-out
        
        alpha = int(255 * progress * (1.0 - fade_out))
        scale = 0.8 + 0.2 * progress  # Scale from 80% to 100%
        
        # Apply scaling
        scaled_width = int(notif_width * scale)
        scaled_height = int(notif_height * scale)
        
        # Fill with semi-transparent background
        notif_surface.fill((40, 40, 80, min(220, alpha)))
        
        # Draw animated border
        border_pulse = (1 + math.sin(self.milestone_timer * 4)) / 2  # Faster pulse
        border_color = (
            150 + int(105 * border_pulse),  # 150-255
            150 + int(105 * border_pulse),  # 150-255
            255
        )
        pygame.draw.rect(
            notif_surface,
            border_color,
            (0, 0, notif_width, notif_height),
            3  # Border width
        )
        
        # Render text with appropriate alpha
        title_font = pygame.font.SysFont(None, 36)
        title_text = title_font.render(f"MILESTONE {milestone} REACHED!", True, (255, 255, 100))
        title_text.set_alpha(alpha)
        
        # Add milestone-specific descriptions
        descriptions = {
            1: "The neural network is growing! Maze complexity increased.",
            2: "Neural pathways are strengthening! More hazards ahead.",
            3: "Synaptic connections at maximum! Can you reach the deepest nodes?",
            4: "Congratulations! You've mastered the Synaptic Weave!"
        }
        
        desc_text = self.font.render(descriptions.get(milestone, "Maze complexity increased"), True, TEXT_COLOR)
        desc_text.set_alpha(alpha)
        
        # Position and blit text
        notif_surface.blit(title_text, (notif_width // 2 - title_text.get_width() // 2, 25))
        notif_surface.blit(desc_text, (notif_width // 2 - desc_text.get_width() // 2, 70))
        
        # Blit notification onto main surface with scaling
        scaled_surface = pygame.transform.scale(notif_surface, (scaled_width, scaled_height))
        self.surface.blit(
            scaled_surface, 
            (self.width // 2 - scaled_width // 2, self.height // 3 - scaled_height // 2)
        )
    
    def draw_tutorial(self, message, step, total_steps):
        """Draw a tutorial message with navigation indicators.
        
        Args:
            message (str): Tutorial message to display
            step (int): Current tutorial step
            total_steps (int): Total number of tutorial steps
        """
        # Create tutorial box
        box_width = 600
        box_height = 200
        box_surface = pygame.Surface((box_width, box_height), pygame.SRCALPHA)
        box_surface.fill((20, 20, 40, 220))
        
        # Draw border
        pygame.draw.rect(
            box_surface,
            (100, 100, 200),
            (0, 0, box_width, box_height),
            2  # Border width
        )
        
        # Draw title
        title_font = pygame.font.SysFont(None, 36)
        title_text = title_font.render("TUTORIAL", True, (255, 255, 100))
        box_surface.blit(title_text, (box_width // 2 - title_text.get_width() // 2, 20))
        
        # Draw message
        message_font = pygame.font.SysFont(None, 28)
        message_text = message_font.render(message, True, TEXT_COLOR)
        box_surface.blit(message_text, (box_width // 2 - message_text.get_width() // 2, 80))
        
        # Draw navigation instructions
        nav_font = pygame.font.SysFont(None, 20)
        nav_text = nav_font.render("Press SPACE to continue or ENTER to skip tutorial", True, (180, 180, 220))
        box_surface.blit(nav_text, (box_width // 2 - nav_text.get_width() // 2, 140))
        
        # Draw progress indicators
        for i in range(total_steps):
            color = (255, 255, 255) if i == step else (100, 100, 100)
            pygame.draw.circle(
                box_surface,
                color,
                (box_width // 2 - (total_steps * 15) // 2 + i * 15, 170),
                5 if i == step else 3
            )
        
        # Blit tutorial box onto main surface
        self.surface.blit(
            box_surface,
            (self.width // 2 - box_width // 2, self.height // 2 - box_height // 2)
        )
