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
n = 50 # Max number of moves to consider
opt_moves = 6 # Optimal moves to take

pvals = {'pawn':1,
        'bishop':3,
        'knight':3,
        'rook':5,
        'queen':9, 
        'king':9}

#Simulation logic:
#On first iteration, score all moves if there are fewer than 50 moves.
#Take the top 8 and 4 random remainders. This starts 12 trees.
#Now simulate a turn for the opponent, using the same paramters, for each of the
#12 trees. Take top 8 and 4 for the opponent. But use the score at this point to
#eliminate 6 of the original trees, so we have 4 of the best moves and 2 best 
#random moves. Now simulate another turn for the original player. 8 and 4 again.
#We will score (12)*(12)*(6)=864 moves this round. On the next round, prune 
#again. (12)*(12)*(6)*(6)=5184. This is about the max imo.

import os, sys

class HiddenPrints:
    def __enter__(self):
        self._original_stdout = sys.stdout
        sys.stdout = open(os.devnull, 'w')

    def __exit__(self, exc_type, exc_val, exc_tb):
        sys.stdout.close()
        sys.stdout = self._original_stdout


# Top level functions;
def score_position(board, printer=True):
    """Given a board, scores the position of the player who just moved."""
    score = 0
    targeting_diff = 0
    targeted_diff = 0
    backup_diff = 0
    center_diff = 0
    capture_diff = 0
    # Points based on living pieces
    for piece in board.alive:
        check = False
        if piece.color == board.turn:
            continue # This is the person who did not just move!
        # Determine if in check. If so, sets score to -10000.
        if piece.type == 'king':
            if piece.threats.len > 0:
                check = True
                if printer: print("In check! Score is -1000")
                break
        # Points for targeting their pieces (diff for backed up else 1)
        for ttype, x, y in piece.targets:
            occ = board[x,y].occ
            tval = pvals[occ.type]
            pval = pvals[piece.type]
            if occ.backups.len > 0: 
                diff = max((tval - pval), 0)
            else:
                diff = tval
            targeting_diff += diff
        # Points for being targeted. Checked.
        for ttype, x, y in piece.threats:
            occ = board[x,y].occ
            tval = pvals[occ.type]
            pval = pvals[piece.type]
            if piece.backups.len > 0:
                diff = min((-pval + tval),0) * 2
            else:
                diff = -pval * 2
            targeted_diff += diff
        # Points for pieces being backed up. Checked.
        for backup, x, y in piece.backups:
            pval = pvals[piece.type]
            diff = pval * (1/10)
            backup_diff += diff
        # Points for controlling the center/number of moves
        for move, x, y in piece.v_moves:
            if (x, y) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                center_diff += .4
            else:
                center_diff += .1
                
    # Points for pieces already captured. Checked.
    for piece in board.graveyard:
        if piece.color == board.nonturn:
            continue # only look at pieces of player who did not just move
        #print('capture', piece.symbol)
        capture_diff += pvals[piece.type] * 2
    
    # Print
    score = (targeting_diff + targeted_diff + backup_diff + center_diff \
             + capture_diff) if not check else -1000
    if printer:
        print_part = "Points from {}: {}"
        print(print_part.format("targeting",str(targeting_diff)))
        print(print_part.format("being targeted",str(targeted_diff)))
        print(print_part.format("backups",str(backup_diff)))
        print(print_part.format("board control",str(center_diff)))
        print(print_part.format("captures",str(capture_diff)))
        print("Total score is: " + str(score))
    return score


class Simulator:
    def __init__(self, cboard):
        self.n = 50 # max moves to consider
        self.gen1 = 6 # moves to go forward with if good
        self.gen2 = 3
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
        df = pd.DataFrame({'origin':[(0,0)] * len(moves),
                           'destination':[(0,0)] * len(moves),
                           'score':[0] * len(moves)})
        for i, (origin, destination) in enumerate(moves):
            temp_board = c.deepcopy(board)
            # Prevent Printing
            og_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            temp_board.move_piece(temp_board[origin].occ, destination, True)
            sys.stdout = og_stdout
            # Printing enabled again
            score = score_position(temp_board, printer=False)
            df.loc[i,:] = [origin, destination, score]
        return df.sort_values('score', ascending=False).reset_index(drop=True)
    
    def multi_level_simulate(self):
        print("Looking at available moves.")
        df = self.simulate() # Looking at available moves
        sub_df_list = []
        for i in range(self.gen1):
            temp_board_1 = c.deepcopy(self.board)
            og_stdout = sys.stdout
            sys.stdout = open(os.devnull, "w")
            temp_board_1.move_piece(temp_board_1[df.loc[i,'origin']].occ,
                                    df.loc[i,'destination'],
                                    True)
            sys.stdout = og_stdout
            sim_1 = Simulator(temp_board_1)
            sub_df = sim_1.simulate()
            sub_df['move1_origin'] = [df.loc[i,'origin']] * sub_df.shape[0]
            sub_df['move1_destination'] = [df.loc[i,'destination']] * sub_df.shape[0]
            sub_df['move1_score'] = [df.loc[i,'score']] * sub_df.shape[0]
            sub_df_list += [sub_df]
        new_df = pd.concat(sub_df_list, axis=0)
        new_df = new_df.sort_values('score', ascending = False)
        # Filter the data frame
        new_df['m1_concat'] = new_df["move1_origin"].map(str) + \
                              new_df["move1_destination"].map(str)
        move1 = new_df.m1_concat.unique().tolist()
        gen2_list = []
        for i in move1:
            filt = new_df.loc[new_df.m1_concat == i,:].reset_index(drop=True)
            for j in range(self.gen2):
                temp_board_2 = c.deepcopy(self.board)
                og_stdout = sys.stdout
                sys.stdout = open(os.devnull, "w")
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'move1_origin']].occ,
                    filt.loc[j,'move1_destination'],
                    True)
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'origin']].occ,
                    filt.loc[j,'destination'],
                    True)
                sys.stdout = og_stdout
                sim_2 = Simulator(temp_board_2)
                sub_df2 = sim_2.simulate()
                sub_df2['m2_orig'] = [filt.loc[j,'origin']] * sub_df2.shape[0]
                sub_df2['m2_dest'] = [filt.loc[j,'destination']] * sub_df2.shape[0]
                sub_df2['m2_scre'] = [filt.loc[j,'score']] * sub_df2.shape[0]
                sub_df2['m1_orig'] = [filt.loc[j,'move1_origin']] * sub_df2.shape[0]
                sub_df2['m1_dest'] = [filt.loc[j,'move1_destination']] * sub_df2.shape[0]
                sub_df2['m1_scre'] = [filt.loc[j,'move1_score']] * sub_df2.shape[0]
                gen2_list += [sub_df2]
        gen2_df = pd.concat(gen2_list, axis=0)
        # Interpret the results
        gen2_df['m1_concat'] = gen2_df["m1_orig"].map(str) + \
                               gen2_df["m1_dest"].map(str)
        gen2_df['m2_concat'] = gen2_df["m2_orig"].map(str) + \
                               gen2_df["m2_dest"].map(str)
        move1 = gen2_df.m1_concat.unique().tolist()
        move2 = gen2_df.m2_concat.unique().tolist()
        m3_o = []
        m3_d = []
        m3_s = []
        m2_o = []
        m2_d = []
        m2_s = []
        m1_o = []
        m1_d = []
        m1_s = []
        for i in move1:
            filt = gen2_df.loc[gen2_df.m1_concat == i,:].reset_index(drop=True)
            for j in move2:
                m1_o += [filt.loc[0,'m1_orig']]
                m1_d += [filt.loc[0,'m1_dest']]
                m1_s += [filt.loc[0,'m1_scre']]
                filt2 = filt.loc[filt.m2_concat == j,:].reset_index(drop=True)
                m2_o += [filt2.loc[0,'m2_orig']]
                m2_d += [filt2.loc[0,'m2_dest']]
                m2_s += [filt2.loc[0,'m2_scre']]
                filt2 = filt2.sort_values('score', ascending=False).reset_index(drop=True)
                m3_o += [filt2.loc[0, 'origin']]
                m3_d += [filt2.loc[0, 'destination']]
                m3_s += [filt2.loc[0, 'score']]
        final_df = pd.DataFrame({'m1_o':m1_o, 'm1_d':m1_d, 'm1_s':m1_s,
                                 'm2_o':m2_o, 'm2_d':m2_d, 'm2_s':m2_s,
                                 'm3_o':m3_o, 'm3_d':m3_d, 'm3_s':m3_s,})
        return final_df


sim = Simulator(cboard)
#df = sim.simulate()
#df.sort_values('score', ascending=False)
a = time.time()
new_df = sim.multi_level_simulate()
b = time.time()

        
