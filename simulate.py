#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logic for simulating and scoring moves.
"""

# Imports
import copy as c
import pandas as pd
import sys, os

# Constants:
pvals = {'pawn':1,
        'bishop':3,
        'knight':3,
        'rook':5,
        'queen':9,
        'king':9}

# Top level functions;
def score_position(board, printer=True):
    """Given a board, scores the position of the player who just moved."""
    score = 0
    targeting_diff = 0
    targeted_diff = 0
    backup_diff = 0
    center_diff = 0
    capture_diff = 0
    mate_score = 0
    check = False
    dead_enemy_king = True # For simulations where the king is killed

    # First loop on opposition's pieces: skip the person who just moved
    for piece in board.alive:
        if piece.color != board.turn:
            continue
        capture_diff -= pvals[piece.type] * 3
        # Part 1 of identifying if you won via checkmate.
        if piece.type == 'king':
            dead_enemy_king = False
            enemy_king = piece
            enemy_king_moves = [(x, y) for move, x, y in piece.v_moves]

    # Now loop on person who just moved's pieces
    for piece in board.alive:
        if piece.color == board.turn:
            continue
        capture_diff += pvals[piece.type] * 3
        # Determine if in check. If so, sets score to -10000.
        if piece.type == 'king':
            if piece.threats.len > 0:
                check = True
                if printer: print("In check! Score is -1000")
                break
        # Points for targeting their pieces (diff for backed up else 1)
        for ttype, x, y in piece.targets:
            tval = pvals[ttype]
            pval = pvals[piece.type]
            occ = board[x,y].occ
            if occ and occ.backups.len > 0:
                diff = max((tval - pval), 0)
            else:
                diff = tval
            targeting_diff += (diff/2)
        # Points for being targeted. Checked.
        for ttype, x, y in piece.threats:
            tval = pvals[ttype]
            pval = pvals[piece.type]
            if piece.backups.len > 0:
                diff = min((-pval + tval),0) * 2
            else:
                diff = -pval * 2
            targeted_diff += diff
        # Points for pieces being backed up. Checked.
        for backup, x, y in piece.backups:
            if piece.type != 'king':
                pval = pvals[piece.type]
                diff = pval * (1/20)
                backup_diff += diff
        # Points for controlling the center/number of moves
        for move, x, y in piece.v_moves:
            if (x, y) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                center_diff += .2
            else:
                center_diff += .1
            # Second part of checkmate logic
            if not dead_enemy_king and (x, y) in enemy_king_moves:
                enemy_king_moves.remove((x,y))

    # Final part of checkmate logic
    if (dead_enemy_king or
            (len(enemy_king_moves) == 0 and enemy_king.threats.len > 0)):
        mate_score = 500
        if printer: "Checkmate detected!"

    # Round everything to one decimal
    targeting_diff = round(targeting_diff, 1)
    targeted_diff = round(targeted_diff, 1)
    backup_diff = round(backup_diff, 1)
    center_diff = round(center_diff, 1)
    capture_diff = round(capture_diff, 1)

    # Print
    score = (targeting_diff + targeted_diff + backup_diff + center_diff \
             + capture_diff + mate_score) if not check else -1000
    if printer:
        print_part = "Points from {}: {}"
        print(print_part.format("targeting",str(targeting_diff)))
        print(print_part.format("being targeted",str(targeted_diff)))
        print(print_part.format("backups",str(backup_diff)))
        print(print_part.format("board control",str(center_diff)))
        print(print_part.format("captures",str(capture_diff)))
        print("Total score is: " + str(score))
    return (capture_diff, center_diff, backup_diff,
            targeted_diff, targeting_diff, mate_score, score)

class Simulator:
    def __init__(self, cboard, gen1 = 3, gen2 = 2):
        self.n = 50 # max moves to consider
        self.gen1 = gen1 # moves to go forward with if good
        self.gen2 = gen2
        self.board = c.deepcopy(cboard)

    def get_all_moves(self):
        """Get all moves for current player's turn. Returns list of tuple
        tuples in the form of [((origin1),(dest1)),((o2),(dest2))]"""
        board = self.board
        mlist = []
        for i in board.alive:
            if i.color != board.turn:
                continue
            mlist += [((i.pos),(i.v_moves[j][1],i.v_moves[j][2])) \
                      for j in range(i.v_moves.len)]
        return mlist

    def simulate(self):
        """Given the current board, score all possible moves and rank them."""
        board = self.board
        moves = self.get_all_moves()
        df = pd.DataFrame({'orig':[(0,0)] * len(moves),
                           'dest':[(0,0)] * len(moves),
                           'score':[0] * len(moves),
                           'capture_score':[0] * len(moves),
                           'control_score':[0] * len(moves),
                           'targeting_score':[0] * len(moves),
                           'targeted_score':[0] * len(moves),
                           'backup_score':[0] * len(moves),
                           })
        for i, (origin, destination) in enumerate(moves):
            temp_board = c.deepcopy(board)
            temp_board.move_piece(temp_board[origin].occ, destination, True,
                                  False, False)
            cap, cent, back, targeted, targeting, mate_score, score = score_position(
                    temp_board, printer=False)
            df.loc[i,:] = [origin, destination, score, cap, cent, targeting,
                  targeted, back]
        return df.sort_values('score', ascending=False).reset_index(drop=True)

    def multi_level_simulate(self):
        """Runs simulate in nested loops! First simulates all moves for AI
        player. Then makes top 6 of those moves (at difficulty 9). Looks at all
        responses to those 6. Then makes top 3 responses to those (at diff 9).
        Finally looks at all moves available in response to those 3. Selects
        the FIRST move with the highest MOVE 3 score."""
        cols = ['m1_orig', 'm1_dest', 'm1_score',
                'm2_orig', 'm2_dest', 'm2_score',
                'orig', 'dest', 'score']
        results = pd.DataFrame({i:[] for i in cols})
        df1 = self.simulate()
        for i in range(self.gen1):
            copy1 = c.deepcopy(self.board)
            copy1.move_piece(copy1[df1.loc[i,'orig']].occ,
                              df1.loc[i,'dest'],
                              True, False, False)
            sim1 = Simulator(copy1)
            df2 = sim1.simulate() # Scores all responses to first move
            for j in range(self.gen2):
                copy2 = c.deepcopy(copy1)
                copy2.move_piece(copy2[df2.loc[j,'orig']].occ,
                                 df2.loc[j,'dest'],
                                 True, False, False)
                sim2 = Simulator(copy2)
                df3 = sim2.simulate()
                for k in range(df3.shape[0]):
                    row = [df1.loc[i, 'orig'], df1.loc[i, 'dest'],
                           df1.loc[i, 'score'], df2.loc[j, 'orig'],
                           df2.loc[j, 'dest'], df2.loc[j, 'score'],
                           df3.loc[k, 'orig'], df3.loc[k, 'dest'],
                           df3.loc[k, 'score']]
                    results.loc[len(results)] = row
        results = results.sort_values('score', ascending=False)
        results.to_csv('ai_move_analysis.csv', index=False)
        return results.loc[0, 'm1_orig'], results.loc[0, 'm1_dest']
