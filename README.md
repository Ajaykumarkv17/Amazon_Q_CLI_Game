# Synaptic Weave

A procedural, shape-and-text-driven PyGame project where players traverse a dynamically growing neural-network maze that evolves in real-time based on the player's path history.

## Features

- Procedurally generated neural network maze using NetworkX
- Dynamic maze growth based on player movement
- Memory trails that harden into new pathways
- Hazards including firing nodes with expanding pulses
- Logic gate puzzles requiring sequence solving
- Progression system with increasing difficulty

## Setup

1. Create and activate a virtual environment:
```
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

2. Install dependencies:
```
pip install -r requirements.txt
```

3. Run the game:
```
python src/main.py
```

## Controls

- Move: Arrow keys or WASD
- Interact with logic gates: Follow on-screen prompts
- Quit: ESC or close window

## Project Structure

- `src/`: Source code
  - `main.py`: Entry point and game loop
  - `graph_maze.py`: Neural network maze generation
  - `player.py`: Player entity and movement
  - `hazards.py`: Firing nodes and logic gates
  - `ui.py`: HUD and visual feedback
- `levels/`: Milestone data storage

## Future Enhancements

- Custom graph implementation for performance optimization
- Sound synthesis for audio feedback
- Teleport mechanic using stored trail energy
- Configuration file for parameter tuning
