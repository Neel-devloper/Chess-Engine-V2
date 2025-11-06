from NV_chess_engine_V2 import NV_chess_engine_V2
import chess
import random
import time

"""
Tester for the chess engine.
"""

board = chess.Board()


engine = NV_chess_engine_V2(board)

while not board.is_game_over():
    
    print('-'*20)
    print(board)

    if board.turn == chess.WHITE:
        board.push(random.choice(list(board.legal_moves)))
    else:
        start_time = time.time()
        board.push(engine.get_best_move(4, chess.BLACK))
        print(f"Time taken for move: {time.time() - start_time} seconds")
    
    

