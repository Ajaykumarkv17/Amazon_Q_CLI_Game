"""
Hazards Module

Manages firing nodes, expanding pulses, and logic gate puzzles.
"""

import random
import math
import time
import pygame

# Constants
PULSE_COLOR = (255, 100, 100, 180)
PULSE_BORDER_COLOR = (255, 50, 50)
PULSE_SPEED = 80  # Pixels per second
PULSE_MAX_RADIUS = 150
FIRING_NODE_COLOR = (255, 100, 100)
LOGIC_GATE_COLOR = (100, 255, 100)
LOGIC_GATE_ACTIVE_COLOR = (200, 255, 200)


class Pulse:
    """Expanding circular pulse hazard."""
    
    def __init__(self, center, start_time):
        """Initialize a new pulse.
        
        Args:
            center (tuple): (x, y) center position of the pulse
            start_time (float): Time when the pulse started
        """
        self.center = center
        self.start_time = start_time
        self.radius = 0
        self.active = True
        self.speed = PULSE_SPEED * (0.8 + random.random() * 0.4)  # Randomize speed slightly
    
    def update(self, current_time):
        """Update the pulse radius based on elapsed time.
        
        Args:
            current_time (float): Current game time
            
        Returns:
            bool: True if the pulse is still active, False if it should be removed
        """
        elapsed = current_time - self.start_time
        self.radius = elapsed * self.speed
        
        # Deactivate if radius exceeds maximum
        if self.radius > PULSE_MAX_RADIUS:
            self.active = False
            
        return self.active
    
    def check_collision(self, player_pos, player_radius):
        """Check if the pulse collides with the player.
        
        Args:
            player_pos (tuple): (x, y) player position
            player_radius (float): Player collision radius
            
        Returns:
            bool: True if collision detected, False otherwise
        """
        # Calculate distance between pulse center and player
        dx = player_pos[0] - self.center[0]
        dy = player_pos[1] - self.center[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        # Check if player is within the pulse ring (with some thickness)
        pulse_thickness = 10
        min_distance = self.radius - pulse_thickness - player_radius
        max_distance = self.radius + pulse_thickness + player_radius
        
        return min_distance <= distance <= max_distance and self.active
    
    def draw(self, surface):
        """Draw the pulse on the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Create a surface for the semi-transparent pulse
        pulse_surface = pygame.Surface((surface.get_width(), surface.get_height()), pygame.SRCALPHA)
        
        # Draw the pulse as a semi-transparent circle
        pygame.draw.circle(
            pulse_surface,
            PULSE_COLOR,
            (int(self.center[0]), int(self.center[1])),
            int(self.radius),
            10  # Width of the pulse ring
        )
        
        # Draw the border of the pulse
        pygame.draw.circle(
            surface,
            PULSE_BORDER_COLOR,
            (int(self.center[0]), int(self.center[1])),
            int(self.radius),
            2  # Width of the border
        )
        
        # Blit the pulse surface onto the main surface
        surface.blit(pulse_surface, (0, 0))


class FiringNode:
    """Node that periodically emits expanding pulses."""
    
    def __init__(self, node_id, position, maze):
        """Initialize a firing node.
        
        Args:
            node_id (int): ID of the node in the maze
            position (tuple): (x, y) position of the node
            maze: Reference to the GraphMaze instance
        """
        self.node_id = node_id
        self.position = position
        self.maze = maze
        self.pulses = []
        self.last_fire_time = time.time()
        self.fire_interval = random.uniform(2.0, 4.0)  # Faster firing rate (was 3.0-6.0)
        
        # Immediately fire a pulse when created
        self.pulses.append(Pulse(self.position, self.last_fire_time))
    
    def update(self, current_time):
        """Update the firing node and its pulses.
        
        Args:
            current_time (float): Current game time
        """
        # Check if it's time to fire a new pulse
        if current_time - self.last_fire_time > self.fire_interval:
            self.pulses.append(Pulse(self.position, current_time))
            self.last_fire_time = current_time
            self.fire_interval = random.uniform(3.0, 6.0)  # Randomize next interval
        
        # Update existing pulses and remove inactive ones
        self.pulses = [pulse for pulse in self.pulses if pulse.update(current_time)]
    
    def check_collision(self, player_pos, player_radius):
        """Check if any pulse from this node collides with the player.
        
        Args:
            player_pos (tuple): (x, y) player position
            player_radius (float): Player collision radius
            
        Returns:
            bool: True if collision detected, False otherwise
        """
        for pulse in self.pulses:
            if pulse.check_collision(player_pos, player_radius):
                return True
        return False
    
    def draw(self, surface):
        """Draw the firing node and its pulses.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw each pulse
        for pulse in self.pulses:
            pulse.draw(surface)


class LogicGate:
    """Logic gate puzzle that requires a sequence to solve."""
    
    def __init__(self, node_id, position):
        """Initialize a logic gate puzzle.
        
        Args:
            node_id (int): ID of the node in the maze
            position (tuple): (x, y) position of the node
        """
        self.node_id = node_id
        self.position = position
        self.solved = False
        self.active = False
        self.sequence = self._generate_sequence()
        self.player_sequence = []
        self.interaction_radius = 50  # Distance at which player can interact
    
    def _generate_sequence(self):
        """Generate a random sequence for the puzzle.
        
        Returns:
            list: List of keys in the sequence
        """
        keys = [pygame.K_1, pygame.K_2, pygame.K_3, pygame.K_4]
        sequence_length = random.randint(3, 5)
        return [random.choice(keys) for _ in range(sequence_length)]
    
    def check_interaction(self, player_pos):
        """Check if the player is close enough to interact.
        
        Args:
            player_pos (tuple): (x, y) player position
            
        Returns:
            bool: True if player can interact, False otherwise
        """
        dx = player_pos[0] - self.position[0]
        dy = player_pos[1] - self.position[1]
        distance = math.sqrt(dx*dx + dy*dy)
        
        return distance <= self.interaction_radius
    
    def process_key_input(self, key):
        """Process key input for the puzzle sequence.
        
        Args:
            key (int): Pygame key constant
            
        Returns:
            bool: True if the puzzle is solved, False otherwise
        """
        if not self.active or self.solved:
            return False
            
        # Add key to player sequence
        self.player_sequence.append(key)
        
        # Check if the sequence matches so far
        sequence_length = len(self.player_sequence)
        if self.player_sequence != self.sequence[:sequence_length]:
            # Reset on mistake
            self.player_sequence = []
            return False
            
        # Check if complete sequence entered
        if len(self.player_sequence) == len(self.sequence):
            self.solved = True
            return True
            
        return False
    
    def draw(self, surface):
        """Draw the logic gate and its state.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw the logic gate node
        color = LOGIC_GATE_ACTIVE_COLOR if self.active else LOGIC_GATE_COLOR
        pygame.draw.circle(
            surface,
            color,
            (int(self.position[0]), int(self.position[1])),
            20  # Slightly larger than regular nodes
        )
        
        # If active, draw the sequence UI
        if self.active and not self.solved:
            font = pygame.font.SysFont(None, 24)
            
            # Draw sequence prompt
            prompt = "Enter sequence: " + "".join([str(i+1) for i in range(len(self.sequence))])
            text = font.render(prompt, True, (255, 255, 255))
            surface.blit(text, (self.position[0] - text.get_width() // 2, self.position[1] - 50))
            
            # Draw player progress
            progress = "".join([str((key - pygame.K_0)) for key in self.player_sequence])
            progress_text = font.render(progress, True, (255, 255, 255))
            surface.blit(progress_text, (self.position[0] - progress_text.get_width() // 2, self.position[1] - 25))
        
        # If solved, show completion message
        if self.solved:
            font = pygame.font.SysFont(None, 24)
            text = font.render("Gate Unlocked!", True, (255, 255, 255))
            surface.blit(text, (self.position[0] - text.get_width() // 2, self.position[1] - 30))


class HazardManager:
    """Manages all hazards in the game."""
    
    def __init__(self, maze):
        """Initialize the hazard manager.
        
        Args:
            maze: Reference to the GraphMaze instance
        """
        self.maze = maze
        self.firing_nodes = {}  # Map of node_id to FiringNode
        self.logic_gates = {}   # Map of node_id to LogicGate
        self.nodes_visited = 0
        self.pulse_frequency = 0.1  # Probability of a new node becoming a firing node
        self.gate_frequency = 0.1   # Probability of a new node becoming a logic gate
    
    def update(self, dt):
        """Update all hazards.
        
        Args:
            dt (float): Time elapsed since last update
            
        Returns:
            bool: True if a new pulse was created
        """
        current_time = time.time()
        pulse_created = False
        
        # Update firing nodes
        for node in self.firing_nodes.values():
            old_pulse_count = len(node.pulses)
            node.update(current_time)
            if len(node.pulses) > old_pulse_count:
                pulse_created = True
                
        return pulse_created
    
    def check_player_collision(self, player):
        """Check if the player collides with any hazard.
        
        Args:
            player: Player instance
            
        Returns:
            bool: True if collision detected, False otherwise
        """
        player_pos = player.position
        player_radius = 10  # Player collision radius
        
        # Check collision with each firing node's pulses
        for node in self.firing_nodes.values():
            if node.check_collision(player_pos, player_radius):
                return True
                
        return False
    
    def check_logic_gate_interaction(self, player):
        """Check if the player can interact with a logic gate.
        
        Args:
            player: Player instance
        """
        # Deactivate all gates first
        for gate in self.logic_gates.values():
            gate.active = False
        
        # Check if player is near any gate
        for gate in self.logic_gates.values():
            if gate.check_interaction(player.position):
                gate.active = True
                break
    
    def process_key_input(self, key):
        """Process key input for active logic gates.
        
        Args:
            key (int): Pygame key constant
        """
        for gate in self.logic_gates.values():
            if gate.active:
                gate.process_key_input(key)
    
    def add_node(self, node_id, position):
        """Consider adding a hazard at the given node.
        
        Args:
            node_id (int): ID of the node in the maze
            position (tuple): (x, y) position of the node
        """
        self.nodes_visited += 1
        
        # Every 8 nodes, add a logic gate
        if self.nodes_visited % 8 == 0:
            self.logic_gates[node_id] = LogicGate(node_id, position)
        # Every 4 nodes, add a firing node (increased frequency)
        elif self.nodes_visited % 4 == 0:
            self.firing_nodes[node_id] = FiringNode(node_id, position, self.maze)
            
        # After reaching 20 nodes, occasionally add random firing nodes
        elif self.nodes_visited > 20 and random.random() < self.pulse_frequency:
            self.firing_nodes[node_id] = FiringNode(node_id, position, self.maze)
    
    def increase_difficulty(self, milestone):
        """Increase difficulty parameters based on milestone reached.
        
        Args:
            milestone (int): Current milestone level
        """
        self.pulse_frequency = 0.15 + milestone * 0.1  # Increased base frequency
        # Increase pulse speed based on milestone
        global PULSE_SPEED
        PULSE_SPEED = 100 + milestone * 30  # Faster pulses
        
        # Make existing firing nodes fire more frequently
        for node in self.firing_nodes.values():
            node.fire_interval = max(1.0, node.fire_interval * 0.7)  # Reduce interval by 30%
    
    def get_active_pulses_count(self):
        """Get the total number of active pulses.
        
        Returns:
            int: Count of active pulses
        """
        count = 0
        for node in self.firing_nodes.values():
            count += len(node.pulses)
        return count
    
    def draw(self, surface):
        """Draw all hazards.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw firing nodes and their pulses
        for node in self.firing_nodes.values():
            node.draw(surface)
        
        # Draw logic gates
        for gate in self.logic_gates.values():
            gate.draw(surface)
