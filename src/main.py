#!/usr/bin/env python3
"""
Synaptic Weave - Main Entry Point

This module initializes the game window, sets up the game loop,
and coordinates the interaction between all game components.
"""

import sys
import pygame
import time
import math
import random
import os
from graph_maze import GraphMaze
from player import Player
from hazards import HazardManager
from ui import UI

# Constants
SCREEN_WIDTH = 800
SCREEN_HEIGHT = 600
FPS = 60
BACKGROUND_COLOR = (10, 10, 30)
GAME_TITLE = "Synaptic Weave"

# Background particle effect constants
NUM_PARTICLES = 50
PARTICLE_SPEED = 0.5
PARTICLE_SIZE_RANGE = (1, 3)
PARTICLE_COLOR = (30, 50, 100, 100)


class Game:
    """Main game class that manages the game loop and component interactions."""
    
    def __init__(self):
        """Initialize the game window and components."""
        pygame.init()
        self.screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
        pygame.display.set_caption(GAME_TITLE)
        self.clock = pygame.time.Clock()
        self.running = True
        self.game_state = "INTRO"  # States: INTRO, PLAYING, PAUSED, HELP
        
        # Initialize game components
        self.maze = GraphMaze(SCREEN_WIDTH, SCREEN_HEIGHT)
        self.player = Player(self.maze.get_start_node(), self.maze)
        self.hazard_manager = HazardManager(self.maze)
        self.ui = UI(self.screen)
        
        # Game state tracking
        self.last_node_visit_time = time.time()
        self.nodes_visited = 0
        self.milestone_reached = 0
        self.tutorial_step = 0
        self.tutorial_messages = [
            "Welcome to Synaptic Weave!",
            "You are navigating through a neural network maze.",
            "Use ARROW KEYS or WASD to move along the paths.",
            "As you move, the maze grows and evolves.",
            "Your movement leaves trails that harden into new paths.",
            "Watch out for RED PULSES - they'll send you back to start!",
            "GREEN NODES are logic gates - solve them by pressing the numbers shown.",
            "Press SPACE to continue or ENTER to skip tutorial."
        ]
        
        # Background particles
        self.particles = []
        self._init_particles()
        
        # Create sounds directory
        os.makedirs('sounds', exist_ok=True)
        
    def _init_particles(self):
        """Initialize background particle effects."""
        for _ in range(NUM_PARTICLES):
            self.particles.append({
                'x': random.randint(0, SCREEN_WIDTH),
                'y': random.randint(0, SCREEN_HEIGHT),
                'size': random.randint(PARTICLE_SIZE_RANGE[0], PARTICLE_SIZE_RANGE[1]),
                'speed': random.uniform(PARTICLE_SPEED * 0.5, PARTICLE_SPEED * 1.5),
                'angle': random.uniform(0, 2 * math.pi)
            })
    
    def _update_particles(self, dt):
        """Update background particle positions."""
        for p in self.particles:
            p['x'] += math.cos(p['angle']) * p['speed']
            p['y'] += math.sin(p['angle']) * p['speed']
            
            # Wrap around screen edges
            if p['x'] < 0:
                p['x'] = SCREEN_WIDTH
            elif p['x'] > SCREEN_WIDTH:
                p['x'] = 0
            if p['y'] < 0:
                p['y'] = SCREEN_HEIGHT
            elif p['y'] > SCREEN_HEIGHT:
                p['y'] = 0
                
            # Occasionally change direction
            if random.random() < 0.01:
                p['angle'] = random.uniform(0, 2 * math.pi)
    
    def _draw_particles(self):
        """Draw background particle effects."""
        particle_surface = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        for p in self.particles:
            pygame.draw.circle(
                particle_surface,
                PARTICLE_COLOR,
                (int(p['x']), int(p['y'])),
                p['size']
            )
        self.screen.blit(particle_surface, (0, 0))
        
    def handle_events(self):
        """Process pygame events including user input."""
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                self.running = False
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    if self.game_state == "PLAYING":
                        self.game_state = "PAUSED"
                    elif self.game_state == "PAUSED":
                        self.game_state = "PLAYING"
                    else:
                        self.running = False
                
                # Tutorial navigation
                if self.game_state == "INTRO":
                    if event.key == pygame.K_SPACE:
                        self.tutorial_step += 1
                        if self.tutorial_step >= len(self.tutorial_messages):
                            self.game_state = "PLAYING"
                    elif event.key == pygame.K_RETURN:
                        self.game_state = "PLAYING"
                
                # Pause toggle with P key
                if event.key == pygame.K_p:
                    if self.game_state == "PLAYING":
                        self.game_state = "PAUSED"
                    elif self.game_state == "PAUSED":
                        self.game_state = "PLAYING"
                
                # Help screen toggle with H key
                if event.key == pygame.K_h and self.game_state == "PLAYING":
                    self.game_state = "HELP"
                elif event.key == pygame.K_h and self.game_state == "HELP":
                    self.game_state = "PLAYING"
                
                # Process logic gate inputs
                if self.game_state == "PLAYING":
                    if event.key in [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]:
                        self.hazard_manager.process_key_input(event.key)
                    
        # Handle continuous key presses for movement (only when playing)
        if self.game_state == "PLAYING":
            keys = pygame.key.get_pressed()
            direction = [0, 0]
            
            # Arrow keys or WASD
            if keys[pygame.K_LEFT] or keys[pygame.K_a]:
                direction[0] = -1
            if keys[pygame.K_RIGHT] or keys[pygame.K_d]:
                direction[0] = 1
            if keys[pygame.K_UP] or keys[pygame.K_w]:
                direction[1] = -1
            if keys[pygame.K_DOWN] or keys[pygame.K_s]:
                direction[1] = 1
                
            self.player.set_movement_direction(direction)
        else:
            # Stop movement when not in playing state
            self.player.set_movement_direction([0, 0])
        
    def update(self, dt):
        """Update game state based on elapsed time."""
        # Always update particles for background effect
        self._update_particles(dt)
        
        # Update UI animations
        self.ui.update(dt)
        
        # Only update game logic when in PLAYING state
        if self.game_state != "PLAYING":
            return
            
        # Update player position
        node_changed = self.player.update(dt)
        
        # If player reached a new node
        if node_changed:
            self.nodes_visited += 1
            self.last_node_visit_time = time.time()
            
            # Add the node to the hazard manager
            self.hazard_manager.add_node(self.player.current_node, 
                                        self.maze.get_node_position(self.player.current_node))
            
            # Grow the maze from this node
            self.maze.grow_from_node(self.player.current_node)
            
            # Check for milestone
            if self.nodes_visited in [25, 50, 100]:
                new_milestone = self.nodes_visited // 25
                if new_milestone > self.milestone_reached:
                    self.milestone_reached = new_milestone
                    self.maze.increase_difficulty(self.milestone_reached)
                    self.hazard_manager.increase_difficulty(self.milestone_reached)
                    self.maze.save_milestone(self.milestone_reached)
                    self.ui.show_milestone_notification(new_milestone)
                    
                    # Show a warning message
                    self.ui.show_message(f"Difficulty increased! More hazards ahead!", 3.0)
        
        # Update memory trails
        trail_hardened = self.player.update_trail(dt)
        if trail_hardened:
            self.ui.show_message("Trail hardened into new path!", 1.5)
        
        # Update hazards
        pulse_created = self.hazard_manager.update(dt)
        if pulse_created:
            self.ui.show_message("Warning: New pulse detected!", 1.5, "top")
        
        # Check for collisions with hazards
        if self.hazard_manager.check_player_collision(self.player):
            self.player.reset_to_start()
            self.ui.show_message("Hit by pulse! Returning to start...", 3.0)
            
        # Check for logic gate interactions
        self.hazard_manager.check_logic_gate_interaction(self.player)
        
        # Update maze effects
        self.maze.update(dt)
        
    def _draw_intro(self):
        """Draw the tutorial/intro screen."""
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw tutorial message
        if self.tutorial_step < len(self.tutorial_messages):
            message = self.tutorial_messages[self.tutorial_step]
            self.ui.draw_tutorial(message, self.tutorial_step, len(self.tutorial_messages))
    
    def _draw_paused(self):
        """Draw the pause screen."""
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 0, 180))
        self.screen.blit(overlay, (0, 0))
        
        # Draw pause message
        font = pygame.font.SysFont(None, 48)
        text = font.render("PAUSED", True, (255, 255, 255))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2))
        self.screen.blit(text, text_rect)
        
        # Draw instructions
        font = pygame.font.SysFont(None, 24)
        text = font.render("Press ESC or P to resume", True, (200, 200, 200))
        text_rect = text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT // 2 + 40))
        self.screen.blit(text, text_rect)
    
    def _draw_help(self):
        """Draw the help screen."""
        # Draw a semi-transparent overlay
        overlay = pygame.Surface((SCREEN_WIDTH, SCREEN_HEIGHT), pygame.SRCALPHA)
        overlay.fill((0, 0, 30, 220))
        self.screen.blit(overlay, (0, 0))
        
        # Draw help content
        font_title = pygame.font.SysFont(None, 36)
        font_body = pygame.font.SysFont(None, 24)
        
        # Title
        title = font_title.render("SYNAPTIC WEAVE - HELP", True, (255, 255, 100))
        title_rect = title.get_rect(center=(SCREEN_WIDTH // 2, 50))
        self.screen.blit(title, title_rect)
        
        # Help text
        help_texts = [
            "CONTROLS:",
            "- Move: Arrow keys or WASD",
            "- Pause: ESC or P",
            "- Help: H",
            "",
            "GAME CONCEPTS:",
            "- Depth: Number of nodes you've visited",
            "- Active Pulses: Hazardous waves that can send you back to start",
            "- Branching Factor: How interconnected the maze is",
            "",
            "GAMEPLAY:",
            "- The maze grows as you explore",
            "- Your movement trails harden into new paths after a few seconds",
            "- Red nodes emit dangerous pulses - avoid them!",
            "- Green nodes are logic gates - solve them by pressing the numbers shown",
            "- Reach milestones (25, 50, 100 nodes) to progress"
        ]
        
        y_pos = 100
        for text in help_texts:
            if text == "":
                y_pos += 10
                continue
                
            if ":" in text and text.endswith(":"):
                # Section header
                rendered = font_title.render(text, True, (200, 200, 255))
            else:
                # Regular text
                rendered = font_body.render(text, True, (220, 220, 220))
                
            text_rect = rendered.get_rect(topleft=(SCREEN_WIDTH // 4, y_pos))
            self.screen.blit(rendered, text_rect)
            y_pos += 30
        
        # Exit instruction
        exit_text = font_body.render("Press H to return to game", True, (255, 255, 255))
        exit_rect = exit_text.get_rect(center=(SCREEN_WIDTH // 2, SCREEN_HEIGHT - 50))
        self.screen.blit(exit_text, exit_rect)
        
    def render(self):
        """Render all game elements to the screen."""
        # Clear the screen
        self.screen.fill(BACKGROUND_COLOR)
        
        # Draw background particles
        self._draw_particles()
        
        # Draw the maze
        self.maze.draw(self.screen)
        
        # Draw player trails
        self.player.draw_trails(self.screen)
        
        # Draw hazards
        self.hazard_manager.draw(self.screen)
        
        # Draw the player
        self.player.draw(self.screen)
        
        # Draw UI elements
        self.ui.draw(self.nodes_visited, 
                     self.hazard_manager.get_active_pulses_count(),
                     self.maze.get_average_branching_factor())
        
        # Draw state-specific overlays
        if self.game_state == "INTRO":
            self._draw_intro()
        elif self.game_state == "PAUSED":
            self._draw_paused()
        elif self.game_state == "HELP":
            self._draw_help()
        
        # Update the display
        pygame.display.flip()
        
    def run(self):
        """Main game loop with fixed timestep."""
        previous_time = time.time()
        lag = 0.0
        MS_PER_UPDATE = 1.0 / FPS
        
        while self.running:
            current_time = time.time()
            elapsed = current_time - previous_time
            previous_time = current_time
            lag += elapsed
            
            self.handle_events()
            
            # Fixed update step
            while lag >= MS_PER_UPDATE:
                self.update(MS_PER_UPDATE)
                lag -= MS_PER_UPDATE
                
            self.render()
            self.clock.tick(FPS)
            
        pygame.quit()
        sys.exit()


if __name__ == "__main__":
    game = Game()
    game.run()


if __name__ == "__main__":
    game = Game()
    game.run()
