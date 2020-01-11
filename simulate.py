#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logic for simulating and scoring moves.
"""

# Imports
import copy as c

# Constants:
n = 50 # Max number of moves to consider
opt_moves = 7 # Optimal moves to take
ran_moves = 3 # Random moves to take

def get_all_moves(cboard):
    """Get all moves for current player's turn. Returns list of tuple tuples 
    in the form of [((origin1),(dest1)),((o2),(dest2))]"""
    mlist = []
    for i in board.alive:
        if i.color != board.turn:
            continue
        mlist += [((i.pos),(i.v_moves[j][1],i.v_moves[j][2])) \
                  for j in range(i.v_moves.len)]
    return mlist

def score_position(cboard):
    """Given a board, scores the positions of black and white.
    Returns opposing player's score minus current players turn.
    This is because after a move, it shifts to opposing player."""
    
    # Determine if in check. If so, sets score to -100000000. 
    
    # Points for targeting their pieces
    
    # Points for being targeted by their pieces
    
    # Points for pieces being backed up
    
    # Points for controlling the center
    
    # Points for 

def simulator(cboard, iterations=4):
    """Takes a chessboard object. Creates a copy and considers various moves
    scoring them. It chooses the move with the best outcomes and returns it."""
    
    # Create a copy so as not to change the state of our current board.
    board = c.deepcopy(cboard)
    
    # Get all moves for the current player's turn.
    mlist = get_all_moves(board)
    print(board.turn + " has " + len(mlist) + " moves to consider.")







        
