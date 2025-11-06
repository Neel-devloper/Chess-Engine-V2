# NV Chess Engine V2

A high-performance Python chess engine built with advanced search algorithms and optimization techniques. The engine uses the `python-chess` library for board representation and includes a Pygame-based graphical interface for interactive play.

## Features

### Engine Optimizations

The chess engine implements several advanced search optimizations:

1. **Alpha-Beta Pruning** - Dramatically reduces search space by eliminating bad branches
2. **Principal Variation Search (PVS)** - Uses null-window searches for better move ordering
3. **Iterative Deepening** - Gradually increases depth for better time management
4. **Move Ordering** - MVV-LVA captures, killer moves, history heuristic, promotions first
5. **Quiescence Search** - Extends search through captures to avoid horizon effect
6. **Killer Moves Heuristic** - Prioritizes moves that previously caused beta cutoffs
7. **History Heuristic** - Tracks successful moves from previous searches

### Static Evaluation

The engine uses a comprehensive static evaluation function (`static_eval.py`) that considers:

- **Material Balance** - Standard piece values (pawn=100, knight=320, bishop=330, rook=500, queen=900)
- **Positional Evaluation** - Piece-square tables for optimal piece placement
  - Pawns: Encourages center control and advancement
  - Knights: Centralization bonuses
  - Bishops: Long diagonal bonuses
  - Rooks: Open files and 7th rank bonuses
  - Queens: Center control without overexposure
  - King: Safety in middlegame, activity in endgame
- **Mobility** - Bonus for having more legal moves
- **Pawn Structure** - Penalties for doubled and isolated pawns
- **King Safety** - Bonuses for castling, penalties for exposed kings
- **Endgame Detection** - Different evaluation strategies for middlegame vs endgame

### Graphical Interface

The Pygame viewer (`chess_pygame_viewer.py`) provides:

- Visual chess board with piece images
- Click-to-move interface
- Legal move highlighting
- Last move indication
- Pawn promotion dialog
- Game status display (check, checkmate, stalemate)
- Keyboard controls:
  - `u` - Undo move
  - `r` - Reset game
  - `f` - Flip board

## Requirements

- Python 3.8+
- `python-chess` library
- `pygame` library

## Installation

1. Clone or download this repository

2. Create a virtual environment (recommended):
   ```bash
   python -m venv venv
   ```

3. Activate the virtual environment:
   - On macOS/Linux:
     ```bash
     source venv/bin/activate
     ```
   - On Windows:
     ```bash
     venv\Scripts\activate
     ```

4. Install dependencies:
   ```bash
   pip install python-chess pygame
   ```

## Usage

### Interactive GUI (Recommended)

Run the Pygame viewer to play against the engine:

```bash
python chess_pygame_viewer.py
```

The engine will automatically play as Black when it's Black's turn. You can adjust the search depth in the `chess_pygame_viewer.py` file (line 446).

### Programmatic Usage

You can use the engine programmatically:

```python
import chess
from NV_chess_engine_V2 import NV_chess_engine_V2

# Create a board
board = chess.Board()

# Create the engine
engine = NV_chess_engine_V2(board)

# Get the best move (for Black, depth 4)
best_move = engine.get_best_move(depth=4, player_color=chess.BLACK)

# Make the move
if best_move:
    board.push(best_move)
    print(f"Engine played: {best_move.uci()}")
```

### Testing

Run the test script to see the engine in action:

```bash
python test_engine.py
```

This will play a game where White makes random moves and Black uses the engine.

## Project Structure

```
NV chess engine V2/
├── NV_chess_engine_V2.py      # Main chess engine with search algorithms
├── static_eval.py              # Static position evaluation function
├── chess_pygame_viewer.py      # Pygame graphical interface
├── test_engine.py              # Test script
├── *.png                       # Chess piece images
└── README.md                   # This file
```

## Engine Configuration

### Adjusting Search Depth

The search depth controls how many moves ahead the engine looks. Higher depth = stronger play but slower moves.

- **Default depth**: 4-6 moves
- **Quick games**: 3-4 moves
- **Stronger play**: 6-8 moves (may be slow)

Modify the `depth` parameter in `get_best_move()` calls or in `chess_pygame_viewer.py`.

### Iterative Deepening

The engine uses iterative deepening by default, which means it searches depth 1, then 2, then 3, etc., up to the maximum depth. This allows the engine to have a best move ready at any time and can improve move ordering.

## Technical Details

### Search Algorithm

The engine uses a minimax search with alpha-beta pruning. The search is enhanced with:

- **Principal Variation Search**: First move uses full window, subsequent moves use null-window searches
- **Quiescence Search**: Extends search through capture sequences to avoid horizon effect
- **Move Ordering**: Moves are ordered by:
  1. Captures (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
  2. Promotions
  3. Killer moves
  4. History heuristic
  5. Center control

### Evaluation Function

The static evaluation function returns scores in centipawns from White's perspective:
- Positive values = White advantage
- Negative values = Black advantage
- Values around ±99999 = Checkmate

### Performance

The engine's performance depends on:
- Search depth
- Position complexity
- Hardware speed

Typical move times:
- Depth 3: < 1 second
- Depth 4: 1-5 seconds
- Depth 5: 5-30 seconds
- Depth 6+: May take minutes for complex positions

## License

This project is provided as-is for educational and personal use.

## Acknowledgments

- Built using the excellent `python-chess` library
- Pygame for the graphical interface
- Chess piece images included in the project

## Future Improvements

Potential enhancements:
- Transposition tables for position caching
- Opening book
- Endgame tablebases integration
- Time management
- Multi-threading support
- UCI protocol support

