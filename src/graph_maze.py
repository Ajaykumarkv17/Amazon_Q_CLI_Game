"""
Graph Maze Module

Handles the procedural generation and rendering of the neural network maze
using NetworkX for graph representation.
"""

import random
import math
import json
import os
import networkx as nx
import pygame

# Constants
NODE_RADIUS = 15
EDGE_WIDTH = 3
NODE_COLOR = (100, 200, 255)
EDGE_COLOR = (70, 130, 180)
NEW_NODE_HIGHLIGHT_COLOR = (255, 255, 100)
HARDENED_TRAIL_COLOR = (150, 255, 150)


class GraphMaze:
    """Manages the neural network maze structure and its procedural growth."""
    
    def __init__(self, width, height):
        """Initialize the graph maze with a seed structure.
        
        Args:
            width (int): Screen width for positioning nodes
            height (int): Screen height for positioning nodes
        """
        self.width = width
        self.height = height
        self.graph = nx.Graph()
        self.node_positions = {}
        self.node_colors = {}
        self.edge_colors = {}
        self.node_highlights = {}  # For visual feedback
        self.highlight_duration = 1.0  # seconds
        self.highlight_timers = {}
        
        # Growth parameters
        self.min_node_distance = 80
        self.max_node_distance = 150
        self.growth_rate = 1  # New nodes per visit
        self.branching_factor = 1.5  # Average branches per node
        
        # Create initial seed graph (ring of 5 nodes)
        self._create_seed_graph()
        
        # Track the start node
        self.start_node = 0
        
    def _create_seed_graph(self):
        """Generate the initial ring-shaped graph with 5 nodes."""
        center_x = self.width // 2
        center_y = self.height // 2
        radius = 100
        num_nodes = 5
        
        # Create nodes in a ring
        for i in range(num_nodes):
            angle = 2 * math.pi * i / num_nodes
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)
            self.graph.add_node(i)
            self.node_positions[i] = (x, y)
            self.node_colors[i] = NODE_COLOR
            
        # Connect nodes in a ring
        for i in range(num_nodes):
            next_node = (i + 1) % num_nodes
            self.graph.add_edge(i, next_node)
            self.edge_colors[(i, next_node)] = EDGE_COLOR
            self.edge_colors[(next_node, i)] = EDGE_COLOR
    
    def get_start_node(self):
        """Return the starting node for the player."""
        return self.start_node
    
    def get_node_position(self, node_id):
        """Get the position of a node.
        
        Args:
            node_id: The identifier for the node
            
        Returns:
            tuple: (x, y) position of the node
        """
        return self.node_positions[node_id]
    
    def get_connected_nodes(self, node_id):
        """Get all nodes connected to the given node.
        
        Args:
            node_id: The identifier for the node
            
        Returns:
            list: List of connected node IDs
        """
        return list(self.graph.neighbors(node_id))
    
    def grow_from_node(self, node_id):
        """Grow the maze by adding new nodes connected to the given node.
        
        Args:
            node_id: The node from which to grow new connections
        """
        # Determine how many new nodes to add
        num_new_nodes = random.randint(1, self.growth_rate + 1)
        
        for _ in range(num_new_nodes):
            # Only add a new node if random chance passes
            if random.random() < self.branching_factor / 2:
                new_node_id = self._add_new_node(node_id)
                
                # Return the new node ID for hazard manager to use
                return new_node_id
        
        return None
    
    def _add_new_node(self, source_node):
        """Add a new node connected to the source node.
        
        Args:
            source_node: The node to connect from
            
        Returns:
            int: ID of the new node, or None if no node was added
        """
        # Get source position
        source_pos = self.node_positions[source_node]
        
        # Generate a random angle and distance
        angle = random.uniform(0, 2 * math.pi)
        distance = random.uniform(self.min_node_distance, self.max_node_distance)
        
        # Calculate new position
        new_x = source_pos[0] + distance * math.cos(angle)
        new_y = source_pos[1] + distance * math.sin(angle)
        
        # Ensure position is within bounds
        new_x = max(NODE_RADIUS, min(self.width - NODE_RADIUS, new_x))
        new_y = max(NODE_RADIUS, min(self.height - NODE_RADIUS, new_y))
        
        # Check if the position is too close to existing nodes
        for pos in self.node_positions.values():
            dx = new_x - pos[0]
            dy = new_y - pos[1]
            if math.sqrt(dx*dx + dy*dy) < self.min_node_distance:
                return None  # Too close, don't add
        
        # Create new node
        new_node_id = len(self.graph.nodes)
        self.graph.add_node(new_node_id)
        self.node_positions[new_node_id] = (new_x, new_y)
        
        # Determine node color based on depth
        depth = nx.shortest_path_length(self.graph, self.start_node, source_node) + 1
        darkness = min(200, depth * 10)
        self.node_colors[new_node_id] = (
            max(20, NODE_COLOR[0] - darkness),
            max(20, NODE_COLOR[1] - darkness),
            max(20, NODE_COLOR[2] - darkness)
        )
        
        # Connect to source node
        self.graph.add_edge(source_node, new_node_id)
        self.edge_colors[(source_node, new_node_id)] = EDGE_COLOR
        self.edge_colors[(new_node_id, source_node)] = EDGE_COLOR
        
        # Highlight the new node
        self.node_highlights[new_node_id] = self.highlight_duration
        self.highlight_timers[new_node_id] = 0
        
        return new_node_id
    
    def add_hardened_trail(self, node1, node2):
        """Add a new edge between nodes from a hardened memory trail.
        
        Args:
            node1: First node to connect
            node2: Second node to connect
        """
        if node1 != node2 and not self.graph.has_edge(node1, node2):
            self.graph.add_edge(node1, node2)
            self.edge_colors[(node1, node2)] = HARDENED_TRAIL_COLOR
            self.edge_colors[(node2, node1)] = HARDENED_TRAIL_COLOR
            
            # Highlight the new connection
            self.node_highlights[node1] = self.highlight_duration / 2
            self.node_highlights[node2] = self.highlight_duration / 2
            self.highlight_timers[node1] = 0
            self.highlight_timers[node2] = 0
    
    def increase_difficulty(self, milestone):
        """Increase difficulty parameters based on milestone reached.
        
        Args:
            milestone (int): Current milestone level
        """
        self.growth_rate = 1 + milestone // 2
        self.branching_factor = 1.5 + milestone * 0.25
    
    def get_average_branching_factor(self):
        """Calculate the current average branching factor of the maze.
        
        Returns:
            float: Average number of connections per node
        """
        total_edges = self.graph.number_of_edges()
        total_nodes = self.graph.number_of_nodes()
        if total_nodes > 0:
            return (2 * total_edges) / total_nodes
        return 0
    
    def save_milestone(self, milestone):
        """Save the current maze state for the given milestone.
        
        Args:
            milestone (int): Current milestone level
        """
        # Create directory if it doesn't exist
        os.makedirs("levels", exist_ok=True)
        
        # Prepare data to save
        data = {
            "nodes": list(self.graph.nodes()),
            "edges": list(self.graph.edges()),
            "node_positions": {str(k): v for k, v in self.node_positions.items()},
            "growth_rate": self.growth_rate,
            "branching_factor": self.branching_factor,
            "milestone": milestone
        }
        
        # Save to file
        with open(f"levels/milestone_{milestone}.json", "w") as f:
            json.dump(data, f)
    
    def update(self, dt):
        """Update node highlights and other time-based effects.
        
        Args:
            dt (float): Time elapsed since last update
        """
        # Update highlight timers
        to_remove = []
        for node, time_left in self.node_highlights.items():
            self.highlight_timers[node] += dt
            if self.highlight_timers[node] >= time_left:
                to_remove.append(node)
                
        for node in to_remove:
            del self.node_highlights[node]
            del self.highlight_timers[node]
    
    def draw(self, surface):
        """Draw the maze graph to the given surface.
        
        Args:
            surface: Pygame surface to draw on
        """
        # Draw edges
        for edge in self.graph.edges():
            start_pos = self.node_positions[edge[0]]
            end_pos = self.node_positions[edge[1]]
            color = self.edge_colors.get((edge[0], edge[1]), EDGE_COLOR)
            pygame.draw.line(surface, color, start_pos, end_pos, EDGE_WIDTH)
        
        # Draw nodes
        for node in self.graph.nodes():
            pos = self.node_positions[node]
            color = self.node_colors.get(node, NODE_COLOR)
            
            # Apply highlight if active
            if node in self.node_highlights:
                highlight_progress = self.highlight_timers[node] / self.node_highlights[node]
                highlight_intensity = 1.0 - highlight_progress
                color = (
                    min(255, int(color[0] + (NEW_NODE_HIGHLIGHT_COLOR[0] - color[0]) * highlight_intensity)),
                    min(255, int(color[1] + (NEW_NODE_HIGHLIGHT_COLOR[1] - color[1]) * highlight_intensity)),
                    min(255, int(color[2] + (NEW_NODE_HIGHLIGHT_COLOR[2] - color[2]) * highlight_intensity))
                )
            
            pygame.draw.circle(surface, color, (int(pos[0]), int(pos[1])), NODE_RADIUS)
            
            # Draw node ID for debugging (can be removed in final version)
            # font = pygame.font.SysFont(None, 20)
            # text = font.render(str(node), True, (255, 255, 255))
            # surface.blit(text, (pos[0] - 5, pos[1] - 5))
