
import sys
import pygame
import chess

from NV_chess_engine_V2 import NV_chess_engine_V2

"""
Chess Viewer & Minimal GUI using pygame + python-chess

Features:
- Draws a chess.Board() visually.
- Click to select a piece and click a destination square to make a legal move.
- Legal target squares are highlighted.
- Highlights the last move.
- Handles pawn promotion with an in-window mini prompt (choose: q, r, b, n).
- Undo with 'u', reset with 'r', flip board with 'f'.
- Shows side-to-move and basic game status (check, checkmate, stalemate).

Requirements:
    pip install pygame python-chess

Run:
    python chess_pygame_viewer.py

Notes:
- By default, pieces are rendered using Unicode chess glyphs. If your system
  font lacks them, the code will gracefully fall back to letter pieces (e.g., 'K','Q')
  with colors to differentiate sides.
"""

# ----------------------- Configuration -----------------------
TILE_SIZE = 80
BOARD_SIZE = TILE_SIZE * 8
STATUS_BAR_H = 36
WINDOW_SIZE = (BOARD_SIZE, BOARD_SIZE + STATUS_BAR_H)

LIGHT_SQ = (240, 217, 181)   # light brown
DARK_SQ  = (181, 136,  99)   # dark brown
HL_SRC   = (246, 246, 105)   # yellowish for selected
HL_DST   = (106, 135,  89)   # green for legal targets
HL_LAST  = (246, 246, 105)   # highlight last move squares
GRID     = (60, 60, 60)
TEXT_CLR = (20, 20, 20)
WHITE_CLR = (250, 250, 250)
BLACK_CLR = (20, 20, 20)

# Circle for legal target markers
DOT_RADIUS = TILE_SIZE // 8

# Try to use a font with chess glyphs; fallback gracefully.
PREF_FONTS = ["DejaVu Sans", "Segoe UI Symbol", "Noto Sans Symbols2", "Arial Unicode MS", "Apple Symbols"]
PIECE_FONT_SIZE = int(TILE_SIZE * 0.75)
LABEL_FONT_SIZE = int(TILE_SIZE * 0.24)
STATUS_FONT_SIZE = 18

# Unicode symbols mapping
UNICODE_WHITE = {
    chess.PAWN:   "\u2659",
    chess.KNIGHT: "\u2658",
    chess.BISHOP: "\u2657",
    chess.ROOK:   "\u2656",
    chess.QUEEN:  "\u2655",
    chess.KING:   "\u2654",
}
UNICODE_BLACK = {
    chess.PAWN:   "\u265F",
    chess.KNIGHT: "\u265E",
    chess.BISHOP: "\u265D",
    chess.ROOK:   "\u265C",
    chess.QUEEN:  "\u265B",
    chess.KING:   "\u265A",
}





def best_font(size):
    pygame.font.init()
    for name in PREF_FONTS:
        try:
            f = pygame.font.SysFont(name, size)
            if f is not None:
                # quick sanity glyph check for king/queen
                if f.render("\u2654\u265A", True, (0,0,0)):
                    return f
        except Exception:
            pass
    # final fallback: default font
    return pygame.font.SysFont(None, size)

def piece_to_unicode(piece, fonts_ok=True):
    if not piece:
        return ""
    if fonts_ok:
        if piece.color == chess.WHITE:
            return UNICODE_WHITE[piece.piece_type]
        else:
            return UNICODE_BLACK[piece.piece_type]
    else:
        # Fallback to letter representation
        letter = piece.symbol().upper() if piece.color == chess.WHITE else piece.symbol().lower()
        return letter

def square_at(mouse_pos, flipped):
    mx, my = mouse_pos
    if my >= BOARD_SIZE:
        return None
    file = mx // TILE_SIZE
    rank = my // TILE_SIZE
    if flipped:
        file = 7 - file
        rank = 7 - rank
    sq = chess.square(file, 7 - rank)
    return sq

def sq_to_xy(sq, flipped):
    file = chess.square_file(sq)
    rank = chess.square_rank(sq)
    display_rank = 7 - rank
    display_file = file
    if flipped:
        display_rank = 7 - display_rank
        display_file = 7 - display_file
    x = display_file * TILE_SIZE
    y = display_rank * TILE_SIZE
    return x, y

def draw_labels(surface, label_font, flipped):
    # Draw ranks/files labels along edges
    files = "abcdefgh"
    ranks = "12345678"

    for f in range(8):
        for r in range(8):
            display_file = f if not flipped else 7 - f
            display_rank = r if not flipped else 7 - r
            x = display_file * TILE_SIZE
            y = display_rank * TILE_SIZE

            # Only draw bottom-left labels to avoid clutter
            if r == 7:
                txt = label_font.render(files[f], True, TEXT_CLR)
                surface.blit(txt, (x + 4, y + TILE_SIZE - txt.get_height() - 2))
            if f == 0:
                txt = label_font.render(ranks[7 - r], True, TEXT_CLR)
                surface.blit(txt, (x + 2, y + 2))

# Declare globals at module level, assign safe placeholder or None
screen = None
selected_sq = None
legal_targets = []
last_move = None
flipped = False
piece_font = None
label_font = None
fonts_ok = False

def draw_board(board):
    # These are now defined at module scope and set in main()
    global screen, selected_sq, legal_targets, last_move, flipped, piece_font, label_font, fonts_ok

    # Piece image cache: {(color, type): image}
    if not hasattr(draw_board, "piece_image_cache"):
        cache = {}
        def load_piece_image(color, piece_type, path):
            img = pygame.image.load(path).convert_alpha()
            img = pygame.transform.smoothscale(img, (TILE_SIZE, TILE_SIZE))
            cache[(color, piece_type)] = img
        # Piece image files
        white_piece_paths = {
            chess.PAWN: "white pawn.png",
            chess.KNIGHT: "white knight.png",
            chess.BISHOP: "white bishop.png",
            chess.ROOK: "white rook.png",
            chess.QUEEN: "white queen.png",
            chess.KING: "white king.png",
        }
        black_piece_paths = {
            chess.PAWN: "black pawn.png",
            chess.KNIGHT: "black knight.png",
            chess.BISHOP: "black bishop.png",
            chess.ROOK: "black rook.png",
            chess.QUEEN: "black queen.png",
            chess.KING: "black king.png",
        }
        for pt, path in white_piece_paths.items():
            load_piece_image(chess.WHITE, pt, path)
        for pt, path in black_piece_paths.items():
            load_piece_image(chess.BLACK, pt, path)
        draw_board.piece_image_cache = cache

    piece_image_cache = draw_board.piece_image_cache

    # Background
    screen.fill((30, 30, 30))

    # Draw squares
    for r in range(8):
        for f in range(8):
            display_file = f if not flipped else 7 - f
            display_rank = r if not flipped else 7 - r
            x = display_file * TILE_SIZE
            y = display_rank * TILE_SIZE

            color = LIGHT_SQ if (f + r) % 2 == 0 else DARK_SQ
            pygame.draw.rect(screen, color, (x, y, TILE_SIZE, TILE_SIZE))

    # Highlight last move
    if last_move is not None:
        for sq in [last_move.from_square, last_move.to_square]:
            x, y = sq_to_xy(sq, flipped)
            s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
            s.fill((*HL_LAST, 80))
            screen.blit(s, (x, y))

    # Selected square
    if selected_sq is not None:
        x, y = sq_to_xy(selected_sq, flipped)
        s = pygame.Surface((TILE_SIZE, TILE_SIZE), pygame.SRCALPHA)
        s.fill((*HL_SRC, 120))
        screen.blit(s, (x, y))

        # Legal moves dots
        for dst in legal_targets:
            dx, dy = sq_to_xy(dst, flipped)
            cx = dx + TILE_SIZE // 2
            cy = dy + TILE_SIZE // 2

            pygame.draw.circle(screen, HL_DST, (cx, cy), DOT_RADIUS)

    # Draw pieces using images
    for sq in chess.SQUARES:
        piece = board.piece_at(sq)
        if not piece:
            continue
        x, y = sq_to_xy(sq, flipped)

        # Get image for this piece
        img = piece_image_cache.get((piece.color, piece.piece_type))
        if img:
            screen.blit(img, (x, y))
        else:
            glyph = piece_to_unicode(piece, fonts_ok)
            if glyph and fonts_ok and len(glyph) == 1:
                img_txt = piece_font.render(glyph, True, BLACK_CLR if piece.color == chess.BLACK else BLACK_CLR)
                rect = img_txt.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2 + 2))
                screen.blit(img_txt, rect)
            else:
                color = WHITE_CLR if piece.color == chess.WHITE else BLACK_CLR
                inv   = BLACK_CLR if piece.color == chess.WHITE else WHITE_CLR
                pygame.draw.circle(screen, color, (x + TILE_SIZE // 2, y + TILE_SIZE // 2), int(TILE_SIZE * 0.36))
                letter = piece.symbol().upper() if piece.color == chess.WHITE else piece.symbol().lower()
                txt = piece_font.render(letter, True, inv)
                rect = txt.get_rect(center=(x + TILE_SIZE // 2, y + TILE_SIZE // 2))
                screen.blit(txt, rect)

    # Grid overlay (optional subtle lines)
    for i in range(9):
        pygame.draw.line(screen, GRID, (i*TILE_SIZE, 0), (i*TILE_SIZE, BOARD_SIZE), 1)
        pygame.draw.line(screen, GRID, (0, i*TILE_SIZE), (BOARD_SIZE, i*TILE_SIZE), 1)

    # File/rank labels
    draw_labels(screen, label_font, flipped)

def draw_status(surface, board, status_font):
    pygame.draw.rect(surface, (245, 245, 245), (0, BOARD_SIZE, BOARD_SIZE, STATUS_BAR_H))
    status = "Side to move: " + ("White" if board.turn == chess.WHITE else "Black")
    if board.is_check():
        status += " • CHECK!"
    if board.is_game_over():
        if board.is_checkmate():
            status += " • Checkmate"
        elif board.is_stalemate():
            status += " • Stalemate"
        elif board.is_insufficient_material():
            status += " • Draw (insufficient material)"
        elif board.can_claim_threefold_repetition():
            status += " • Draw (threefold)"
        elif board.can_claim_fifty_moves():
            status += " • Draw (50-move)"
        else:
            status += " • Game over"
    txt = status_font.render(status, True, (10, 10, 10))
    surface.blit(txt, (8, BOARD_SIZE + (STATUS_BAR_H - txt.get_height()) // 2))

def promotion_choice(surface, flipped, from_sq, to_sq, board, status_font):
    """
    Show a tiny overlay to pick promotion piece: q, r, b, n
    Returns the promotion piece type or None to cancel.
    """
    # build rect near destination square
    x, y = sq_to_xy(to_sq, flipped)
    width = TILE_SIZE * 2
    height = STATUS_BAR_H * 2
    px = max(0, min(BOARD_SIZE - width, x + TILE_SIZE//2 - width//2))
    py = max(0, min(BOARD_SIZE - height, y + TILE_SIZE//2 - height//2))

    overlay = pygame.Surface((width, height))
    overlay.fill((250, 250, 250))
    pygame.draw.rect(overlay, (30, 30, 30), overlay.get_rect(), 2)

    text = status_font.render("Promote to: Q R B N", True, (30,30,30))
    overlay.blit(text, (8, 8))
    hint  = status_font.render("(press q/r/b/n or click)", True, (80,80,80))
    overlay.blit(hint, (8, 8 + text.get_height() + 4))

    # buttons
    buttons = []
    labels = [('Q', chess.QUEEN), ('R', chess.ROOK), ('B', chess.BISHOP), ('N', chess.KNIGHT)]
    start_x = 10
    by = 8 + text.get_height() + 4 + hint.get_height() + 8
    bw = (width - start_x*2 - 3*8) // 4
    bh = height - by - 10
    for i,(label,ptype) in enumerate(labels):
        bx = start_x + i*(bw + 8)
        rect = pygame.Rect(bx, by, bw, bh)
        pygame.draw.rect(overlay, (230,230,230), rect)
        pygame.draw.rect(overlay, (60,60,60), rect, 1)
        t = status_font.render(label, True, (20,20,20))
        overlay.blit(t, t.get_rect(center=rect.center))
        buttons.append((rect, ptype))

    surface.blit(overlay, (px, py))
    pygame.display.flip()

    while True:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit(0)
            elif event.type == pygame.KEYDOWN:
                if event.key in (pygame.K_ESCAPE, pygame.K_RETURN):
                    return None
                if event.unicode:
                    ch = event.unicode.lower()
                    if ch == 'q': return chess.QUEEN
                    if ch == 'r': return chess.ROOK
                    if ch == 'b': return chess.BISHOP
                    if ch == 'n': return chess.KNIGHT
            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                mx, my = event.pos
                if px <= mx <= px+width and py <= my <= py+height:
                    local = (mx - px, my - py)
                    for rect, ptype in buttons:
                        if rect.collidepoint(local):
                            return ptype
                else:
                    return None

def main():
    global screen, selected_sq, legal_targets, last_move, flipped, piece_font, label_font, fonts_ok

    board = chess.Board()
    engine = NV_chess_engine_V2(board)

    pygame.init()
    screen = pygame.display.set_mode(WINDOW_SIZE)
    pygame.display.set_caption("python-chess + pygame — Chess Board Viewer")

    clock = pygame.time.Clock()

    piece_font = best_font(PIECE_FONT_SIZE)
    label_font = best_font(LABEL_FONT_SIZE)
    status_font = best_font(STATUS_FONT_SIZE)

    # Quick test if chess glyphs look okay: render white king + black king and check width
    test_surface = piece_font.render("\u2654\u265A", True, (0,0,0))
    fonts_ok = test_surface.get_width() > 0


    flipped = False

    selected_sq = None
    legal_targets = []
    last_move = None

    running = True
    while running:
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                running = False

            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_u:
                    # undo last move
                    if board.move_stack:
                        last_move = board.pop()
                        selected_sq = None
                        legal_targets = []
                elif event.key == pygame.K_r:
                    board.reset()
                    last_move = None
                    selected_sq = None
                    legal_targets = []
                elif event.key == pygame.K_f:
                    flipped = not flipped

            elif event.type == pygame.MOUSEBUTTONDOWN and event.button == 1:
                sq = square_at(event.pos, flipped)
                if sq is None:
                    continue

                if selected_sq is None:
                    # select if there's a piece of the side to move
                    piece = board.piece_at(sq)
                    if piece and piece.color == board.turn:
                        selected_sq = sq
                        # gather legal targets
                        legal_targets = [m.to_square for m in board.legal_moves if m.from_square == sq]
                else:
                    # try to make a move from selected_sq to sq
                    move = chess.Move(selected_sq, sq)
                    # If it's a promotion move, ask
                    if chess.square_rank(selected_sq) in (6,) and chess.square_rank(sq) in (7,) and board.piece_at(selected_sq) and board.piece_at(selected_sq).piece_type == chess.PAWN and board.turn == chess.WHITE:
                        # white promoting
                        if board.is_legal(move):
                            ptype = promotion_choice(screen, flipped, selected_sq, sq, board, status_font)
                            if ptype:
                                move = chess.Move(selected_sq, sq, promotion=ptype)
                    elif chess.square_rank(selected_sq) in (1,) and chess.square_rank(sq) in (0,) and board.piece_at(selected_sq) and board.piece_at(selected_sq).piece_type == chess.PAWN and board.turn == chess.BLACK:
                        # black promoting
                        if board.is_legal(move):
                            ptype = promotion_choice(screen, flipped, selected_sq, sq, board, status_font)
                            if ptype:
                                move = chess.Move(selected_sq, sq, promotion=ptype)

                    if move in board.legal_moves:
                        board.push(move)
                        last_move = move
                        selected_sq = None
                        legal_targets = []
                    else:
                        # reselect if clicked another own piece
                        piece = board.piece_at(sq)
                        if piece and piece.color == board.turn:
                            selected_sq = sq
                            legal_targets = [m.to_square for m in board.legal_moves if m.from_square == sq]
                        else:
                            # clear selection
                            selected_sq = None
                            legal_targets = []
        
        if board.turn == chess.BLACK:
            move = engine.get_best_move(depth=4)
            if move:
                board.push(move)
                last_move = move
                selected_sq = None
                legal_targets = []

        draw_board(board)
        draw_status(screen, board, status_font)

        pygame.display.flip()
        clock.tick(60)

    pygame.quit()

if __name__ == "__main__":
    main()
