"""
Static evaluation function for chess positions.

This module provides a comprehensive board evaluation function that considers:
- Material balance (piece values)
- Piece-square tables (positional bonuses)
- Piece mobility
- King safety
- Pawn structure
- Center control
"""

import chess


# Piece values (centipawns)
PIECE_VALUES = {
    chess.PAWN: 100,
    chess.KNIGHT: 320,
    chess.BISHOP: 330,
    chess.ROOK: 500,
    chess.QUEEN: 900,
    chess.KING: 0  # King value is not used in material calculation
}

# Piece-square tables for positional evaluation
# Values are from white's perspective (positive = good for white)
# For black pieces, we'll flip the table

# Pawn position table - encourages advancing pawns and controlling center
PAWN_TABLE = [
    0,  0,  0,  0,  0,  0,  0,  0,
    50, 50, 50, 50, 50, 50, 50, 50,
    10, 10, 20, 30, 30, 20, 10, 10,
    5,  5, 10, 25, 25, 10,  5,  5,
    0,  0,  0, 20, 20,  0,  0,  0,
    5, -5,-10,  0,  0,-10, -5,  5,
    5, 10, 10,-20,-20, 10, 10,  5,
    0,  0,  0,  0,  0,  0,  0,  0
]

# Knight position table - encourages knights in center and active squares
KNIGHT_TABLE = [
    -50,-40,-30,-30,-30,-30,-40,-50,
    -40,-20,  0,  0,  0,  0,-20,-40,
    -30,  0, 10, 15, 15, 10,  0,-30,
    -30,  5, 15, 20, 20, 15,  5,-30,
    -30,  0, 15, 20, 20, 15,  0,-30,
    -30,  5, 10, 15, 15, 10,  5,-30,
    -40,-20,  0,  5,  5,  0,-20,-40,
    -50,-40,-30,-30,-30,-30,-40,-50
]

# Bishop position table - encourages bishops on long diagonals
BISHOP_TABLE = [
    -20,-10,-10,-10,-10,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5, 10, 10,  5,  0,-10,
    -10,  5,  5, 10, 10,  5,  5,-10,
    -10,  0, 10, 10, 10, 10,  0,-10,
    -10, 10, 10, 10, 10, 10, 10,-10,
    -10,  5,  0,  0,  0,  0,  5,-10,
    -20,-10,-10,-10,-10,-10,-10,-20
]

# Rook position table - encourages rooks on open files and 7th rank
ROOK_TABLE = [
     0,  0,  0,  0,  0,  0,  0,  0,
     5, 10, 10, 10, 10, 10, 10,  5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
    -5,  0,  0,  0,  0,  0,  0, -5,
     0,  0,  0,  5,  5,  0,  0,  0
]

# Queen position table - encourages queen in center but not too exposed
QUEEN_TABLE = [
    -20,-10,-10, -5, -5,-10,-10,-20,
    -10,  0,  0,  0,  0,  0,  0,-10,
    -10,  0,  5,  5,  5,  5,  0,-10,
     -5,  0,  5,  5,  5,  5,  0, -5,
      0,  0,  5,  5,  5,  5,  0, -5,
    -10,  5,  5,  5,  5,  5,  0,-10,
    -10,  0,  5,  0,  0,  0,  0,-10,
    -20,-10,-10, -5, -5,-10,-10,-20
]

# King position table (middlegame) - encourages king safety
KING_TABLE_MIDDLE = [
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -30,-40,-40,-50,-50,-40,-40,-30,
    -20,-30,-30,-40,-40,-30,-30,-20,
    -10,-20,-20,-20,-20,-20,-20,-10,
     20, 20,  0,  0,  0,  0, 20, 20,
     20, 30, 10,  0,  0, 10, 30, 20
]

# King position table (endgame) - encourages king activity
KING_TABLE_END = [
    -50,-40,-30,-20,-20,-30,-40,-50,
    -30,-20,-10,  0,  0,-10,-20,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 30, 40, 40, 30,-10,-30,
    -30,-10, 20, 30, 30, 20,-10,-30,
    -30,-30,  0,  0,  0,  0,-30,-30,
    -50,-30,-30,-30,-30,-30,-30,-50
]


def _flip_table(table):
    """Flip a piece-square table for black pieces."""
    return [table[63 - i] for i in range(64)]


def _is_endgame(board):
    """Determine if the position is in the endgame."""
    # Count queens and rooks
    queens = len(board.pieces(chess.QUEEN, chess.WHITE)) + len(board.pieces(chess.QUEEN, chess.BLACK))
    rooks = len(board.pieces(chess.ROOK, chess.WHITE)) + len(board.pieces(chess.ROOK, chess.BLACK))
    
    # Endgame if queens and rooks are mostly gone
    return queens == 0 and rooks <= 2


def _get_piece_square_value(piece, square, is_endgame=False):
    """Get the piece-square table value for a piece at a given square."""
    piece_type = piece.piece_type
    color = piece.color
    
    if piece_type == chess.PAWN:
        table = PAWN_TABLE
    elif piece_type == chess.KNIGHT:
        table = KNIGHT_TABLE
    elif piece_type == chess.BISHOP:
        table = BISHOP_TABLE
    elif piece_type == chess.ROOK:
        table = ROOK_TABLE
    elif piece_type == chess.QUEEN:
        table = QUEEN_TABLE
    elif piece_type == chess.KING:
        table = KING_TABLE_END if is_endgame else KING_TABLE_MIDDLE
    else:
        return 0
    
    # Flip table for black pieces
    if color == chess.BLACK:
        table = _flip_table(table)
    
    return table[square]


def _evaluate_material(board):
    """Evaluate material balance."""
    score = 0
    
    for piece_type in [chess.PAWN, chess.KNIGHT, chess.BISHOP, chess.ROOK, chess.QUEEN]:
        white_count = len(board.pieces(piece_type, chess.WHITE))
        black_count = len(board.pieces(piece_type, chess.BLACK))
        score += (white_count - black_count) * PIECE_VALUES[piece_type]
    
    return score


def _evaluate_position(board, is_endgame=False):
    """Evaluate positional factors using piece-square tables."""
    score = 0
    
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece:
            score += _get_piece_square_value(piece, square, is_endgame)
            # Positive for white, negative for black
    
    return score


def _evaluate_mobility(board):
    """Evaluate piece mobility (number of legal moves)."""
    # Count legal moves for each side
    white_moves = len(list(board.legal_moves))
    board.turn = chess.BLACK
    black_moves = len(list(board.legal_moves))
    board.turn = chess.WHITE  # Reset to original turn
    
    # Mobility bonus (small value per move)
    return (white_moves - black_moves) * 2


def _evaluate_pawn_structure(board):
    """Evaluate pawn structure."""
    score = 0
    
    # Doubled pawns (bad)
    for file in chess.FILE_NAMES:
        white_pawns = len([sq for sq in chess.SQUARES 
                          if chess.square_file(sq) == chess.FILE_NAMES.index(file) 
                          and board.piece_at(sq) == chess.Piece(chess.PAWN, chess.WHITE)])
        black_pawns = len([sq for sq in chess.SQUARES 
                          if chess.square_file(sq) == chess.FILE_NAMES.index(file) 
                          and board.piece_at(sq) == chess.Piece(chess.PAWN, chess.BLACK)])
        
        if white_pawns > 1:
            score -= 20 * (white_pawns - 1)  # Penalty for doubled pawns
        if black_pawns > 1:
            score += 20 * (black_pawns - 1)  # Bonus if opponent has doubled pawns
    
    # Isolated pawns (bad)
    for square in chess.SQUARES:
        piece = board.piece_at(square)
        if piece and piece.piece_type == chess.PAWN:
            file = chess.square_file(square)
            is_isolated = True
            
            # Check adjacent files
            for adj_file in [file - 1, file + 1]:
                if 0 <= adj_file < 8:
                    for sq in chess.SQUARES:
                        if chess.square_file(sq) == adj_file:
                            pawn = board.piece_at(sq)
                            if pawn and pawn.piece_type == chess.PAWN and pawn.color == piece.color:
                                is_isolated = False
                                break
                    if not is_isolated:
                        break
            
            if is_isolated:
                if piece.color == chess.WHITE:
                    score -= 15
                else:
                    score += 15
    
    return score


def _evaluate_king_safety(board):
    """Evaluate king safety."""
    score = 0
    
    # Check if kings are castled
    white_king_sq = board.king(chess.WHITE)
    black_king_sq = board.king(chess.BLACK)
    
    if white_king_sq:
        # Bonus for castling (kingside or queenside)
        if white_king_sq in [chess.G1, chess.C1]:
            score += 20
        # Penalty for exposed king
        if board.is_check():
            score -= 10
    
    if black_king_sq:
        # Bonus for castling
        if black_king_sq in [chess.G8, chess.C8]:
            score -= 20
        # Penalty for exposed king
        if board.is_check():
            score += 10
    
    return score


def evaluate_board(board):
    """
    Evaluate a chess position from white's perspective.
    
    Returns:
        int: Evaluation score in centipawns (positive = white advantage, negative = black advantage)
    """
    # Check for terminal positions
    if board.is_checkmate():
        return -99999 if board.turn == chess.WHITE else 99999
    
    if board.is_stalemate() or board.is_insufficient_material():
        return 0
    
    # Determine if we're in endgame
    is_endgame = _is_endgame(board)
    
    # Material evaluation
    material_score = _evaluate_material(board)
    
    # Positional evaluation (piece-square tables)
    positional_score = _evaluate_position(board, is_endgame)
    
    # Mobility evaluation
    mobility_score = _evaluate_mobility(board)
    
    # Pawn structure evaluation
    pawn_structure_score = _evaluate_pawn_structure(board)
    
    # King safety evaluation
    king_safety_score = _evaluate_king_safety(board)
    
    # Total evaluation
    total_score = (material_score + 
                   positional_score + 
                   mobility_score + 
                   pawn_structure_score + 
                   king_safety_score)
    
    return total_score

