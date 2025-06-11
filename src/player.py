"""
Player Module

Handles player movement, rendering, and trail generation.
"""

import time
import math
import pygame

# Constants
PLAYER_RADIUS = 10
PLAYER_COLOR = (0, 255, 200)
TRAIL_COLOR = (0, 255, 200, 80)  # Semi-transparent
TRAIL_SEGMENT_LENGTH = 5
TRAIL_LIFETIME = 5.0  # Seconds before hardening
MOVEMENT_SPEED = 150  # Pixels per second


class Player:
    """Player entity that moves along the graph edges and leaves memory trails."""
    
    def __init__(self, start_node, maze):
        """Initialize the player at the start node.
        
        Args:
            start_node: Initial node ID
            maze: Reference to the GraphMaze instance
        """
        self.current_node = start_node
        self.target_node = None
        self.maze = maze
        self.position = maze.get_node_position(start_node)
        self.movement_direction = [0, 0]
        self.movement_progress = 0.0  # Progress along current edge (0.0 to 1.0)
        self.start_position = self.position
        self.target_position = self.position
        
        # Trail system
        self.trail_segments = []  # List of (position, creation_time) tuples
        self.last_trail_time = time.time()
        self.trail_interval = 0.05  # Time between trail segments
        
        # Node history for trail hardening
        self.node_history = [start_node]
        self.last_hardened_index = 0
    
    def set_movement_direction(self, direction):
        """Set the player's movement direction.
        
        Args:
            direction: [x, y] normalized direction vector
        """
        self.movement_direction = direction
        
        # If we're at a node, determine the next target node based on direction
        if self.target_node is None and (direction[0] != 0 or direction[1] != 0):
            self._choose_target_node()
    
    def _choose_target_node(self):
        """Choose a target node based on the current movement direction."""
        connected_nodes = self.maze.get_connected_nodes(self.current_node)
        if not connected_nodes:
            return
            
        current_pos = self.maze.get_node_position(self.current_node)
        
        # Find the node that best matches our direction
        best_node = None
        best_score = -1
        
        for node in connected_nodes:
            node_pos = self.maze.get_node_position(node)
            dx = node_pos[0] - current_pos[0]
            dy = node_pos[1] - current_pos[1]
            
            # Skip if zero distance
            if dx == 0 and dy == 0:
                continue
                
            # Normalize
            length = math.sqrt(dx*dx + dy*dy)
            dx /= length
            dy /= length
            
            # Calculate dot product with movement direction
            dot_product = dx * self.movement_direction[0] + dy * self.movement_direction[1]
            
            # If this is a better match than what we've seen so far
            if dot_product > best_score:
                best_score = dot_product
                best_node = node
        
        # If we found a good match and it's in roughly the right direction
        if best_node is not None and best_score > 0.3:
            self.target_node = best_node
            self.start_position = current_pos
            self.target_position = self.maze.get_node_position(best_node)
            self.movement_progress = 0.0
    
    def update(self, dt):
        """Update player position and state.
        
        Args:
            dt (float): Time elapsed since last update
            
        Returns:
            bool: True if the player reached a new node, False otherwise
        """
        node_changed = False
        
        # If we have a target node, move toward it
        if self.target_node is not None:
            # Calculate distance between nodes
            dx = self.target_position[0] - self.start_position[0]
            dy = self.target_position[1] - self.start_position[1]
            distance = math.sqrt(dx*dx + dy*dy)
            
            # Update progress along edge
            self.movement_progress += (MOVEMENT_SPEED * dt) / distance
            
            # If we've reached the target node
            if self.movement_progress >= 1.0:
                self.position = self.target_position
                self.current_node = self.target_node
                self.target_node = None
                self.movement_progress = 0.0
                
                # Record node in history
                self.node_history.append(self.current_node)
                node_changed = True
                
                # If we're still moving, choose a new target
                if self.movement_direction[0] != 0 or self.movement_direction[1] != 0:
                    self._choose_target_node()
            else:
                # Interpolate position
                self.position = (
                    self.start_position[0] + dx * self.movement_progress,
                    self.start_position[1] + dy * self.movement_progress
                )
        
        # Add trail segments at regular intervals
        current_time = time.time()
        if current_time - self.last_trail_time > self.trail_interval:
            self.trail_segments.append((self.position, current_time))
            self.last_trail_time = current_time
            
        # Process trail hardening
        self._process_trail_hardening()
        
        return node_changed
    
    def _process_trail_hardening(self):
        """Check for trails that should harden into new edges."""
        current_time = time.time()
        
        # Check if we have enough history to create a hardened trail
        if len(self.node_history) - self.last_hardened_index >= 3:
            # Get the oldest unhardened node
            old_node = self.node_history[self.last_hardened_index]
            
            # Check if enough time has passed
            if current_time - self.last_trail_time > TRAIL_LIFETIME:
                # Find nodes that are at least 2 steps away in history
                for i in range(self.last_hardened_index + 2, len(self.node_history)):
                    distant_node = self.node_history[i]
                    
                    # Add a hardened trail between these nodes
                    self.maze.add_hardened_trail(old_node, distant_node)
                
                # Update the hardening index
                self.last_hardened_index = len(self.node_history) - 2
    
    def update_trail(self, dt):
        """Update trail segments, removing old ones.
        
        Args:
            dt (float): Time elapsed since last update
            
        Returns:
            bool: True if a trail was hardened into a new path
        """
        current_time = time.time()
        trail_hardened = False
        
        # Remove trail segments that are too old
        self.trail_segments = [
            (pos, time) for pos, time in self.trail_segments
            if current_time - time < TRAIL_LIFETIME
        ]
        
        # Check if we should harden a trail
        if len(self.node_history) - self.last_hardened_index >= 3:
            # Get the oldest unhardened node
            old_node = self.node_history[self.last_hardened_index]
            
            # Check if enough time has passed
            if current_time - self.last_trail_time > TRAIL_LIFETIME:
                # Find nodes that are at least 2 steps away in history
                for i in range(self.last_hardened_index + 2, len(self.node_history)):
                    distant_node = self.node_history[i]
                    
                    # Add a hardened trail between these nodes if not already connected
                    if not self.maze.graph.has_edge(old_node, distant_node):
                        self.maze.add_hardened_trail(old_node, distant_node)
                        trail_hardened = True
                
                # Update the hardening index
                self.last_hardened_index = len(self.node_history) - 2
                
        return trail_hardened
    
    def draw(self, surface):
        """Draw the player on the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw the player as a circle with a pulsing effect
        base_radius = PLAYER_RADIUS
        pulse = (math.sin(time.time() * 5) + 1) * 2  # Pulsing effect
        
        # Draw outer glow
        glow_radius = base_radius + pulse
        glow_surface = pygame.Surface((glow_radius*2, glow_radius*2), pygame.SRCALPHA)
        pygame.draw.circle(
            glow_surface,
            (PLAYER_COLOR[0], PLAYER_COLOR[1], PLAYER_COLOR[2], 100),  # Semi-transparent
            (glow_radius, glow_radius),
            glow_radius
        )
        surface.blit(
            glow_surface,
            (int(self.position[0] - glow_radius), int(self.position[1] - glow_radius))
        )
        
        # Draw the main player circle
        pygame.draw.circle(
            surface, 
            PLAYER_COLOR, 
            (int(self.position[0]), int(self.position[1])), 
            base_radius
        )
    
    def draw_trails(self, surface):
        """Draw the player's memory trails.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Create a surface for the trails
        trail_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        
        # Draw each trail segment
        current_time = time.time()
        for i in range(1, len(self.trail_segments)):
            prev_pos, prev_time = self.trail_segments[i-1]
            curr_pos, curr_time = self.trail_segments[i]
            
            # Calculate alpha based on age
            age_ratio = (current_time - curr_time) / TRAIL_LIFETIME
            alpha = int(80 * (1 - age_ratio))  # Using 80 as the alpha value
            
            # Draw line segment with appropriate alpha
            color = (TRAIL_COLOR[0], TRAIL_COLOR[1], TRAIL_COLOR[2], alpha)
            pygame.draw.line(
                trail_surface, 
                color, 
                (int(prev_pos[0]), int(prev_pos[1])), 
                (int(curr_pos[0]), int(curr_pos[1])), 
                3
            )
        
        # Blit the trail surface onto the main surface
        surface.blit(trail_surface, (0, 0))
    
    def reset_to_start(self):
        """Reset the player to the start node after collision with hazard."""
        self.current_node = self.maze.get_start_node()
        self.target_node = None
        self.position = self.maze.get_node_position(self.current_node)
        self.movement_direction = [0, 0]
        self.movement_progress = 0.0
        self.start_position = self.position
        self.target_position = self.position
        
        # Clear trails
        self.trail_segments = []
        self.last_trail_time = time.time()
        
        # Reset node history but keep hardened trails
        self.node_history = [self.current_node]
        self.last_hardened_index = 0
