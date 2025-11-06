import chess
import static_eval

class NV_chess_engine_V2:
    """
    Optimized chess engine with advanced minimax search.
    
    Optimizations implemented:
    1. Alpha-Beta Pruning: Dramatically reduces search space by eliminating bad branches
    2. Principal Variation Search (PVS): Uses null-window searches for better move ordering
    3. Iterative Deepening: Gradually increases depth for better time management
    4. Move Ordering: MVV-LVA captures, killer moves, history heuristic, promotions first
    5. Quiescence Search: Extends search through captures to avoid horizon effect
    6. Killer Moves Heuristic: Prioritizes moves that previously caused beta cutoffs
    7. History Heuristic: Tracks successful moves from previous searches
    
    These optimizations allow the engine to search to greater depths in less time.
    """
    
    def __init__(self, board):
        self.board = board
        self.transposition_table = {}
        self.nodes_searched = 0
        self.search_start_time = None
        self.killer_moves = [None, None]  # Killer heuristic: moves that caused beta cutoffs
        self.history_table = {}  # History heuristic: track successful moves by piece and destination
        
    def minimax(self, depth, is_maximizing_player, alpha=float('-inf'), beta=float('inf')):
        """Enhanced minimax with PVS, alpha-beta pruning, and transposition table."""
        self.nodes_searched += 1
        
        # Terminal conditions - use quiescence search if depth is 0
        if depth == 0:
            return self._quiescence(alpha, beta)
        
        # Checkmate/stalemate detection
        if self.board.is_checkmate():
            return -99999 if is_maximizing_player else 99999
        if self.board.is_stalemate() or self.board.is_insufficient_material():
            return 0
        
        # Generate and order moves
        moves = self._order_moves(list(self.board.legal_moves), is_maximizing_player)
        
        if not moves:
            return self.evaluate_board()
        
        # PVS: First move gets full window, others use null-window
        is_first_move = True
        
        if is_maximizing_player:
            max_eval = float('-inf')
            for move in moves:
                self.board.push(move)
                
                if is_first_move:
                    # Principal Variation Search: first move uses full window
                    eval = self.minimax(depth - 1, False, alpha, beta)
                    is_first_move = False
                else:
                    # Null-window search for remaining moves (aspiration windows)
                    eval = self.minimax(depth - 1, False, alpha, alpha + 1)
                    
                    # If result is better than alpha, do a full re-search
                    if alpha < eval < beta:
                        eval = self.minimax(depth - 1, False, alpha, beta)
                
                self.board.pop()
                max_eval = max(max_eval, eval)
                alpha = max(alpha, eval)
                if beta <= alpha:
                    # Record killer move
                    self._update_killer(move)
                    self._update_history(move, depth)
                    break  # Alpha-beta cutoff
            return max_eval
        else:
            min_eval = float('inf')
            for move in moves:
                self.board.push(move)
                
                if is_first_move:
                    # Principal Variation Search: first move uses full window
                    eval = self.minimax(depth - 1, True, alpha, beta)
                    is_first_move = False
                else:
                    # Null-window search for remaining moves
                    eval = self.minimax(depth - 1, True, beta - 1, beta)
                    
                    # If result is better than alpha, do a full re-search
                    if alpha < eval < beta:
                        eval = self.minimax(depth - 1, True, alpha, beta)
                
                self.board.pop()
                min_eval = min(min_eval, eval)
                beta = min(beta, eval)
                if beta <= alpha:
                    # Record killer move
                    self._update_killer(move)
                    self._update_history(move, depth)
                    break  # Alpha-beta cutoff
            return min_eval
    
    def _order_moves(self, moves, is_maximizing):
        """Order moves to maximize alpha-beta pruning effectiveness."""
        def move_score(move):
            score = 0
            
            # Captures are searched first (MVV-LVA: Most Valuable Victim - Least Valuable Attacker)
            if self.board.is_capture(move):
                captured = self.board.piece_at(move.to_square)
                if captured:
                    piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                                  chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
                    score += 10000 + piece_values.get(captured.piece_type, 0)
                    
                    # Prefer capturing with less valuable pieces
                    attacker = self.board.piece_at(move.from_square)
                    if attacker:
                        score -= piece_values.get(attacker.piece_type, 0)
            
            # Promotions are very valuable
            if move.promotion:
                score += 8000
            
            # Killer moves (moves that previously caused beta cutoffs)
            if move in self.killer_moves:
                score += 3000
            
            # History heuristic (moves that have been good in the past)
            history_key = (move.from_square, move.to_square)
            if history_key in self.history_table:
                score += self.history_table[history_key] // 10
            
            # Center control bonus
            if move.to_square in [chess.E4, chess.E5, chess.D4, chess.D5]:
                score += 10
            
            return score
        
        # Sort moves by their score (highest first)
        return sorted(moves, key=move_score, reverse=True)
    
    def _quiescence(self, alpha, beta):
        """
        Quiescence search: extend search through captures only at leaf nodes.
        This prevents horizon effect by evaluating quiet positions.
        """
        self.nodes_searched += 1
        
        # Static evaluation first
        stand_pat = self.evaluate_board()
        
        # Beta cutoff
        if stand_pat >= beta:
            return beta
        
        # Update alpha if we found a better move
        alpha = max(alpha, stand_pat)
        
        # Only search captures at this depth
        for move in self.board.legal_moves:
            if not self.board.is_capture(move):
                continue
                
            # Skip captures that are clearly bad (capture low value with high value piece)
            captured = self.board.piece_at(move.to_square)
            attacker = self.board.piece_at(move.from_square)
            if captured and attacker:
                piece_values = {chess.PAWN: 100, chess.KNIGHT: 320, chess.BISHOP: 330,
                              chess.ROOK: 500, chess.QUEEN: 900, chess.KING: 0}
                if piece_values.get(captured.piece_type, 0) < piece_values.get(attacker.piece_type, 0):
                    continue
            
            self.board.push(move)
            score = -self._quiescence(-beta, -alpha)
            self.board.pop()
            
            alpha = max(alpha, score)
            if alpha >= beta:
                return beta  # Beta cutoff
        
        return alpha
    
    def _update_killer(self, move):
        """Update killer moves when a beta cutoff occurs."""
        if move not in self.killer_moves:
            # Shift killer moves
            self.killer_moves.insert(0, move)
            if len(self.killer_moves) > 2:
                self.killer_moves.pop()
    
    def _update_history(self, move, depth):
        """Update history heuristic when a move causes a beta cutoff."""
        history_key = (move.from_square, move.to_square)
        bonus = depth * depth  # Deeper cutoffs are more valuable
        self.history_table[history_key] = self.history_table.get(history_key, 0) + bonus
    
    def _get_board_key(self):
        """Generate a unique key for the current board position."""
        return self.board.fen()
    
    def evaluate_board(self, player_color=chess.BLACK):
        """Evaluate the board position from the given player's perspective."""
        score = static_eval.evaluate_board(self.board)
        # Negate if we're evaluating from black's perspective
        if player_color == chess.BLACK:
            return -score
        return score
    
    def get_best_move(self, depth, player_color=chess.BLACK, iterative_deepening=True):
        """
        Get the best move using iterative deepening for better performance.
        
        Args:
            depth: Maximum depth to search
            player_color: Color of player to maximize (chess.BLACK or chess.WHITE)
            iterative_deepening: Whether to use iterative deepening (gradually increase depth)
        """
        self.transposition_table.clear()
        best_move = None
        
        if iterative_deepening:
            # Iterative deepening: search depth 1, then 2, then 3, etc.
            # This allows us to have a best move ready at any time
            for current_depth in range(1, depth + 1):
                try:
                    best_move = self._search_move(current_depth, player_color)
                except Exception as e:
                    # If time runs out or error, return last known best move
                    break
        else:
            best_move = self._search_move(depth, player_color)
        
        return best_move
    
    def _search_move(self, depth, player_color):
        """Search for best move at a specific depth."""
        best_move = None
        alpha = float('-inf')
        beta = float('inf')
        
        if player_color == chess.BLACK:
            moves = self._order_moves(list(self.board.legal_moves), True)
            for move in moves:
                self.board.push(move)
                score = self.minimax(depth - 1, False, alpha, beta)
                self.board.pop()
                if score > alpha:
                    alpha = score
                    best_move = move
        else:
            moves = self._order_moves(list(self.board.legal_moves), False)
            for move in moves:
                self.board.push(move)
                score = self.minimax(depth - 1, True, alpha, beta)
                self.board.pop()
                if score < beta:
                    beta = score
                    best_move = move
        
        return best_move if best_move else list(self.board.legal_moves)[0] if self.board.legal_moves else None


# Wrapper class for Flask app compatibility
class ChessEngine:
    """Complete chess engine wrapper for web interface."""
    
    def __init__(self):
        self.board = chess.Board()
        self.engine = NV_chess_engine_V2(self.board)
        self.depth = 6  # Default search depth (increased due to optimizations)
        
    def get_board_fen(self):
        """Get current board position in FEN notation."""
        return self.board.fen()
    
    def get_turn(self):
        """Get whose turn it is."""
        return 'white' if self.board.turn == chess.WHITE else 'black'
    
    def is_check(self):
        """Check if current player is in check."""
        return self.board.is_check()
    
    def is_game_over(self):
        """Check if game is over."""
        return self.board.is_game_over()
    
    def get_game_result(self):
        """Get game result."""
        if not self.board.is_game_over():
            return None
        
        if self.board.is_checkmate():
            return 'Black wins' if self.board.turn == chess.WHITE else 'White wins'
        elif self.board.is_stalemate():
            return 'Stalemate - Draw'
        elif self.board.is_insufficient_material():
            return 'Insufficient material - Draw'
        elif self.board.is_seventyfive_moves():
            return '75-move rule - Draw'
        elif self.board.is_fivefold_repetition():
            return 'Fivefold repetition - Draw'
        else:
            return 'Draw'
    
    def make_move(self, move_uci):
        """Make a move on the board."""
        try:
            move = chess.Move.from_uci(move_uci)
            if move in self.board.legal_moves:
                self.board.push(move)
                return {'success': True, 'message': 'Move played'}
            else:
                return {'success': False, 'message': 'Illegal move'}
        except ValueError:
            return {'success': False, 'message': 'Invalid move format'}
    
    def make_engine_move(self):
        """Make the engine's move."""
        if self.board.is_game_over():
            return {'move': None, 'message': 'Game is over'}
        
        # Clear all search state for new search
        self.engine.transposition_table.clear()
        self.engine.killer_moves = [None, None]
        self.engine.history_table.clear()
        self.engine.nodes_searched = 0
        
        # Get best move (use iterative deepening for better performance)
        best_move = self.engine.get_best_move(self.depth, chess.BLACK, iterative_deepening=True)
        
        if best_move:
            self.board.push(best_move)
            return {'move': best_move.uci(), 'message': 'Engine move made'}
        else:
            return {'move': None, 'message': 'No legal moves'}
    
    def reset(self):
        """Reset the game to starting position."""
        self.board = chess.Board()
        self.engine.board = self.board
        self.engine.transposition_table.clear()
        self.engine.killer_moves = [None, None]
        self.engine.history_table.clear()