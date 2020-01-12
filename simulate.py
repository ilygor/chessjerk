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
        'king':15}

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
            tval = pvals[ttype]
            pval = pvals[piece.type]
            occ = board[x,y].occ
            if occ and occ.backups.len > 0: 
                diff = max((tval - pval), 0)
            else:
                diff = tval
            targeting_diff += diff
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
            capture_diff -= pvals[piece.type] * 2
        else:
            capture_diff += pvals[piece.type] * 2
    
    # Round everything to one decimal
    targeting_diff = round(targeting_diff, 1)
    targeted_diff = round(targeted_diff, 1)
    backup_diff = round(backup_diff, 1)
    center_diff = round(center_diff, 1)
    capture_diff = round(capture_diff, 1)
    
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
    return (capture_diff, center_diff, backup_diff, 
            targeted_diff, targeting_diff, score)


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
            temp_board.move_piece(temp_board[origin].occ, destination, True)
            cap, cent, back, targeted, targeting, score = score_position(
                    temp_board, printer=False)
            df.loc[i,:] = [origin, destination, score, cap, cent, targeting,
                  targeted, back]
        return df.sort_values('score', ascending=False).reset_index(drop=True)
    
    def multi_level_simulate(self):
        """ugly function. Looks at all moves, takes the top (self.gen1) then 
        looks at all responses. Takes top (self.gen2) of those. Then looks at 
        all moves again. For each move1, looks at the worst case scenario based
        on moves 2 and 3. Chooses the move 1 with the best worst-case scenario.
        """
        df = self.simulate() # Looking at available moves
        sub_df_list = []
        for i in range(self.gen1):
            temp_board_1 = c.deepcopy(self.board)
            temp_board_1.move_piece(temp_board_1[df.loc[i,'orig']].occ,
                                    df.loc[i,'dest'],
                                    True, False)
            sim_1 = Simulator(temp_board_1)
            sub_df = sim_1.simulate()
            sub_df['m1_orig'] = [df.loc[i,'orig']] * sub_df.shape[0]
            sub_df['m1_dest'] = [df.loc[i,'dest']] * sub_df.shape[0]
            sub_df['m1_score'] = [df.loc[i,'score']] * sub_df.shape[0]
            sub_df['m1_capture_score'] = [df.loc[i,'capture_score']] * sub_df.shape[0]
            sub_df['m1_control_score'] = [df.loc[i,'control_score']] * sub_df.shape[0]
            sub_df['m1_targeting_score'] = [df.loc[i,'targeting_score']] * sub_df.shape[0]
            sub_df['m1_targeted_score'] = [df.loc[i,'targeted_score']] * sub_df.shape[0]
            sub_df['m1_backup_score'] = [df.loc[i,'backup_score']] * sub_df.shape[0]
            sub_df_list += [sub_df]
        new_df = pd.concat(sub_df_list, axis=0)
        new_df = new_df.sort_values('score', ascending = False)
        # Filter the data frame
        new_df['m1_concat'] = new_df["m1_orig"].map(str) + \
                              new_df["m1_dest"].map(str)
        move1 = new_df.m1_concat.unique().tolist()
        gen2_list = []
        for i in move1:
            filt = new_df.loc[new_df.m1_concat == i,:].reset_index(drop=True)
            for j in range(self.gen2):
                temp_board_2 = c.deepcopy(self.board)
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'m1_orig']].occ,
                    filt.loc[j,'m1_dest'],
                    True)
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'orig']].occ,
                    filt.loc[j,'dest'],
                    True)
                sim_2 = Simulator(temp_board_2)
                sub_df2 = sim_2.simulate()
                sub_df2['m2_orig'] = [filt.loc[j,'orig']] * sub_df2.shape[0]
                sub_df2['m2_dest'] = [filt.loc[j,'dest']] * sub_df2.shape[0]
                sub_df2['m2_score'] = [filt.loc[j,'score']] * sub_df2.shape[0]
                sub_df2['m2_capture_score'] = [filt.loc[j,'capture_score']] * sub_df2.shape[0]
                sub_df2['m2_control_score'] = [filt.loc[j,'control_score']] * sub_df2.shape[0]
                sub_df2['m2_targeting_score'] = [filt.loc[j,'targeting_score']] * sub_df2.shape[0]
                sub_df2['m2_targeted_score'] = [filt.loc[j,'targeted_score']] * sub_df2.shape[0]
                sub_df2['m2_backup_score'] = [filt.loc[j,'backup_score']] * sub_df2.shape[0]
                sub_df2['m1_orig'] = [filt.loc[j,'m1_orig']] * sub_df2.shape[0]
                sub_df2['m1_dest'] = [filt.loc[j,'m1_dest']] * sub_df2.shape[0]
                sub_df2['m1_score'] = [filt.loc[j,'m1_score']] * sub_df2.shape[0]
                sub_df2['m1_capture_score'] = [filt.loc[j,'m1_capture_score']] * sub_df2.shape[0]
                sub_df2['m1_control_score'] = [filt.loc[j,'m1_control_score']] * sub_df2.shape[0]
                sub_df2['m1_targeting_score'] = [filt.loc[j,'m1_targeting_score']] * sub_df2.shape[0]
                sub_df2['m1_targeted_score'] = [filt.loc[j,'m1_targeted_score']] * sub_df2.shape[0]
                sub_df2['m1_backup_score'] = [filt.loc[j,'m1_backup_score']] * sub_df2.shape[0]
                gen2_list += [sub_df2]
        gen2_df = pd.concat(gen2_list, axis=0).reset_index(drop=True)
        # Interpret the results
        gen2_df['m1_concat'] = gen2_df["m1_orig"].map(str) + \
                       gen2_df["m1_dest"].map(str)
        gen2_df['m2_concat'] = gen2_df["m2_orig"].map(str) + \
                               gen2_df["m2_dest"].map(str)
        move1 = gen2_df.m1_concat.unique().tolist()
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
            move2 = filt.m2_concat.unique().tolist()
            for j in move2:
                m1_o += [filt.loc[0,'m1_orig']]
                m1_d += [filt.loc[0,'m1_dest']]
                m1_s += [filt.loc[0,'m1_score']]
                filt2 = filt.loc[filt.m2_concat == j,:].reset_index(drop=True)
                m2_o += [filt2.loc[0,'m2_orig']]
                m2_d += [filt2.loc[0,'m2_dest']]
                m2_s += [filt2.loc[0,'m2_score']]
                filt2 = filt2.sort_values('score', ascending=False).reset_index(drop=True)
                m3_o += [filt2.loc[0, 'orig']]
                m3_d += [filt2.loc[0, 'dest']]
                m3_s += [filt2.loc[0, 'score']]
        final_df = pd.DataFrame({'m1_o':m1_o, 'm1_d':m1_d, 'm1_s':m1_s,
                                 'm2_o':m2_o, 'm2_d':m2_d, 'm2_s':m2_s,
                                 'm3_o':m3_o, 'm3_d':m3_d, 'm3_s':m3_s,})
        temp = final_df.groupby(['m1_o','m1_d']).min().sort_values('m3_s', 
                               ascending=False).reset_index()
        gen2_df.to_csv('ai_move_analysis.csv',index=False)
        return temp.loc[0,'m1_o'], temp.loc[0,'m1_d']
