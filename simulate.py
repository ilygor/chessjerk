#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Logic for simulating and scoring moves. This is the ugliest module, and most
in need of refactoring. That said, it works and is still readable.
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
    mate_score = 0
    check = False
    dead_enemy_king = True # For simulations where the king is killed

    # First loop on opposition's pieces: skip the person who just moved
    for piece in board.alive:
        if piece.color != board.turn:
            continue
        capture_diff -= pvals[piece.type] * 2
        # Part 1 of identifying if you won via checkmate.
        if piece.type == 'king':
            dead_enemy_king = False
            enemy_king = piece
            enemy_king_moves = [(x, y) for move, x, y in piece.v_moves]

    # Now loop on person who just moved's pieces
    for piece in board.alive:
        if piece.color == board.turn:
            continue
        capture_diff += pvals[piece.type] * 2
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
            if piece.type != 'king':
                pval = pvals[piece.type]
                diff = pval * (1/10)
                backup_diff += diff
        # Points for controlling the center/number of moves
        for move, x, y in piece.v_moves:
            if (x, y) in [(3, 3), (3, 4), (4, 3), (4, 4)]:
                center_diff += .4
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
        """ugly function. Looks at all moves, takes the top (self.gen1) then
        looks at all responses. Takes top (self.gen2) of those. Then looks at
        all moves again. For each move1, looks at the worst case scenario based
        on moves 2 and 3. Chooses the move 1 with the best worst-case scenario.
        """
        df = self.simulate() # Looking at available moves for round 1
        sub_df_list = []
        # For each move in round 1, "make" the move and score it.
        for i in range(min(self.gen1, df.shape[0])):
            temp_board_1 = c.deepcopy(self.board)
            temp_board_1.move_piece(temp_board_1[df.loc[i,'orig']].occ,
                                    df.loc[i,'dest'],
                                    True, False, False)
            sim_1 = Simulator(temp_board_1)
            sub_df = sim_1.simulate()
            # Bring in m1 values alongisde the m2 values already in sub_df
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
        # Repeat the process. We make the first and second moves, score the
        # third with simulate() and bring back the old information.
        for i in move1:
            filt = new_df.loc[new_df.m1_concat == i,:].reset_index(drop=True)
            for j in range(min(self.gen2, filt.shape[0])):
                temp_board_2 = c.deepcopy(self.board)
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'m1_orig']].occ,
                    filt.loc[j,'m1_dest'],
                    True, False, False)
                temp_board_2.move_piece(temp_board_2[
                    filt.loc[j,'orig']].occ,
                    filt.loc[j,'dest'],
                    True, False, False)
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
        # Interpret the results. We want the move with the best worst-case scen.
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


        def multi_simulate(self):
            # Analyze first moves
            sim_1 = Simulator(self.board)
            df_1 = self.simulate()
            df_1 = df_1.head(gen_1)
            origs_1 = df_1.orig.to_list()
            dests_1 = df_1.dest.to_list()
            scores_1 = df_1.score.to_list()
            df_2_list = []
            for o, d, s in zip(origs_1, dests_1, scores_1):
                # Make first move
                board_1.move_piece(board_1[o].occ, d, True, False, False)
                # Analyze second moves
                sim_2 = Simulator(sim_1.board)
                df_2 = sim2.simulate()
                df_2 = df_2.head(gen_2)
                df_2['orig_1'] = [o] * df_2.shape[0]
                df_2['dest_1'] = [d] * df_2.shape[0]
                df_2['score_1'] = [s] * df_2.shape[0]
                df_2_list += [df_2]
            df2 = pd.concat(df_2_list, axis=0).sort_values('score',
                ascending=False).reset_index(drop=True)
            grouped_2 = df2.groupby(['orig_1', 'dest_1']).max()['score']
            # Prune round 1
            grouped_2 = grouped_2.reset_index().sort_values('score',
                ascending=True).head(gen_1_p)
            # Prune
            # Use df2 scores to prune first generation.

            # Group by, getting max 'score' holding gen 1 origin and dest
            # The generations with high max gen 2 scores get pruned.

            pass




# I want it to evaluate the first 6 moves...
