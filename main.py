#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Some classes for setting up a simple chess-bot.
"""

# Import Statements
import numpy as np
import pandas as pd
from random import sample

# Define Constants
color_list = ['black', 'white']
pawn_dir = dict(zip(color_list, [1, -1]))
x_index = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
y_index = [1, 2, 3, 4, 5, 6, 7, 8]
lookup_dict = {} # Use numbers to get letter/number indices
rev_lookup = {} # Use letter/number indices to get numbers
for x in range(8):
    for y in range(8):
        lookup_dict[(x,y)] = x_index[x] + '_' + str(y_index[y])
        rev_lookup['_'.join([x_index[x], str(y_index[y])])] = (x,y)

# 00 10 20 30 40... br, bk, bb, bq, bk...
# 10 11 21 31 41... bp, bp, bp, bp, bp...
        
# Each piece will have an...
"""
Each piece will have an array for...
    1. empty board moves (ib_moves) name,\
    2. unobstructed moves (uo_moves) (moves with no in between pieces)
    3. valid moves (v_moves) (any legal move, ignoring check)
    4. squares targeting (sq_tgts)
All of these will have "move_type" and "destination"
    5. pieces backed by (backups) ()
    6. pieces targeting (targets)
    7. pieces targeted by (threats)
All of these will have "type" and "origin"


Each square will have an array for...
    1. white threats (w_thrts) (type, origin)
    2. black threats (b_thrts) (type, origin)
"""

        
# Define Functions
def get_btwn(pos, new_pos):
    """Returns list of tuples between pos tuple and new_pos tuple."""
    x_btwn = list(range(pos[0] + 1, new_pos[0]))
    x_btwn = list(range(pos[0] - 1, new_pos[0], -1)) if not x_btwn else x_btwn
    y_btwn = list(range(pos[1] + 1, new_pos[1]))
    y_btwn = list(range(pos[1] - 1, new_pos[1], -1)) if not y_btwn else y_btwn
    # Lists must be equal, even if only moving in x or y direction
    x_btwn = [pos[0]] * len(y_btwn) if len(x_btwn) < len(y_btwn) else x_btwn
    y_btwn = [pos[1]] * len(x_btwn) if len(x_btwn) > len(y_btwn) else y_btwn
    return [(x, y) for x, y in zip(x_btwn, y_btwn)]


# Define Classes
class CustArray:
    """A custom array to hold Piece and Square data."""
    dtype = [('field', (np.str_, 10)), ('x', np.int8), ('y', np.int8)]
    size_dict = {
        'ib_moves': 27, # Most possible moves is 27 by the queen
        'uo_moves': 27,
        'v_moves': 27,
        'hist': 50, # A single piece is not likely to be moved more
        'sq_tgts': 27,
        'backups': 15, # 15 allied pieces
        'targets': 8, # Queen and Knight can only attack 8
        'threats': 16, # 16 enemy pieces
        'w_thrts': 16,
        'b_thrts': 16
        }
    
    def __init__(self, array_type):
        n = CustArray.size_dict[array_type]
        self.array_type = array_type
        self.array = np.empty((n,),dtype=CustArray.dtype)
        self.len = 0
        
    def __repr__(self):
        return repr(self.array)
    
    def __iter__(self):
        self.curr_index = 0
        return self
        
    def __next__(self):
        if self.curr_index < self.len:
            val = self.array[self.curr_index]
            self.curr_index = self.curr_index + 1
            return val
        else:
            raise StopIteration
    
    def add(self, obj):
        """Insert an item into next position of array."""
        self.array = np.insert(self.array, self.len, obj)
        self.len += 1
    
    def reset(self):
        """Reset the array to being filled with zeros."""
        n = CustArray.size_dict[self.array_type]
        self.array = np.empty((n,),dtype=CustArray.dtype)
        self.len = 0
    
    def filt(self, objs):
        """Return filtered array based on list of (field, val) tuples."""
        filt = (self.array[objs[0][0]] == objs[0][1])
        for i in objs[1:]:
            filt = (filt) & (self.array[i[0]] == i[1])
        return self.array[filt]
    
    def __getitem__(self, sliced):
        return self.array[sliced]
        
    
class ChessSquare:
    def __init__(self, color, x, y, occ=None):
        """Class representing game squares with info about surroundings."""
        self.color = color
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.occ = occ
        self.white_atk = CustArray('w_thrts')
        self.black_atk = CustArray('b_thrts')
        
    def __repr__(self):
        return self.color.title() + " square at " + str(self.pos)

class Piece():
    """Class representing game pieces and holding info about their position."""
    def __init__(self, color, piece_type, x, y):
        self.color = color
        self.type = piece_type
        self.x = x
        self.y = y
        self.pos = (x, y)
        self.status = 'alive'
        self.symbol = color[0].upper() + "_" + piece_type.title()
        self.kill_list = []
        self.killed_by = None
        self.last_moved = [] # List in case of castling
        
        self.ib_moves = CustArray('ib_moves')
        self.uo_moves = CustArray('uo_moves')
        self.v_moves = CustArray('v_moves')
        self.hist = CustArray('hist')
        self.sq_tgts = CustArray('sq_tgts')
        self.backups = CustArray('backups')
        self.targets = CustArray('targets')
        self.threats = CustArray('threats')
        self.w_thrts = CustArray('w_thrts')
        self.b_thrts = CustArray('b_thrts')   
        
    def __repr__(self):
        return self.symbol + " at " + str(self.pos)
        
    def info(self):
        """Gets attributes for the piece"""
        return self.__dict__
        
    def get_dest(self, x_diff, y_diff):
        """Returns destination given some difference from the orig. position"""
        return self.x + x_diff, self.y + y_diff
    
    def get_pawn_ib_moves(self):
        """All possible in-bounds moves for pawn. Includes en passant."""
        assert self.type == "pawn"
        p_num, p_dir = (1, 's') if self.color == 'black' else (-1, 'n')
        moves = {
            p_dir + '_1': self.get_dest(0, p_num),
            p_dir + '_2': self.get_dest(0, p_num * 2),
            p_dir + 'e_1': self.get_dest(1, p_num),
            p_dir + 'w_1': self.get_dest(-1, p_num)
            }
        # Add in-bound moves to ib_moves
        for move, dest in moves.items(): 
            if max(dest) <= 7 and min(dest) >= 0: # Ensure in-bounds
                self.ib_moves.add((move, *dest))
    
    def get_rook_ib_moves(self):
        """Get all possible moves for rook (or queen) that stay in-bounds.
        Does not consider castling, which is attributed to the King."""
        assert self.type == 'rook' or self.type == 'queen'
        n_moves = {'n_' + str(i): (self.x, i) for i in range(8) if i < self.y}
        e_moves = {'e_' + str(i): (i, self.y) for i in range(8) if i > self.x}
        s_moves = {'s_' + str(i): (self.x, i) for i in range(8) if i > self.y}
        w_moves = {'w_' + str(i): (i, self.y) for i in range(8) if i < self.x}
        moves = {**n_moves, **e_moves, **s_moves, **w_moves}
        [self.ib_moves.add((move, *dest)) for move, dest in moves.items()]
        
    def get_bishop_ib_moves(self):
        """Get all possible moves for bishop (or queen) that stay in-bounds."""
        assert self.type == 'bishop' or self.type == 'queen'
        ne_dests = {'ne_' + str(i): (self.x + i, self.y - i) for i in 
                    range(1,8) if self.x + i < 8 and self.y - i > -1}
        se_dests = {'se_' + str(i): (self.x + i, self.y + i) for i in 
                    range(1,8) if self.x + i < 8 and self.y + i < 8}
        sw_dests = {'ne_' + str(i): (self.x - i, self.y + i) for i in 
                    range(1,8) if self.x - i > -1 and self.y + i < 8}
        nw_dests = {'ne_' + str(i): (self.x - i, self.y - i) for i in 
                    range(1,8) if self.x - i > -1 and self.y - i > -1}
        moves = {**ne_dests, **se_dests, **sw_dests, **nw_dests}
        [self.ib_moves.add((move, *dest)) for move, dest in moves.items()]
    
    def get_knight_ib_moves(self):
        """Gets all possible moves for knight that stay in-bounds."""
        assert self.type == 'knight'
        diffs = {'nne_': (1, -2), 'ene_': (2, -1), 'ese_':(2, 1), 
                 'sse_': (1, 2), 'ssw_': (-1, 2), 'wsw_':(-2, 1), 
                 'wnw_': (-2, -1), 'nnw_': (-1, -2)}
        moves = {move: self.get_dest(*diff) for move, diff in diffs.items()}
        # Add in-bound moves to ib_moves
        for move, dest in moves.items(): 
            if max(dest) <= 7 and min(dest) >= 0: # Ensure in-bounds
                self.ib_moves.add((move, *dest))
    
    def get_queen_ib_moves(self):
        assert self.type == 'queen'
        self.get_bishop_ib_moves()
        self.get_rook_ib_moves()
    
    def get_king_ib_moves(self):
        """Gets all possible non-castle moves for king that stay in-bounds."""
        assert self.type == 'king'
        diffs = {'n_1': (0, -1), 'ne_1': (1, -1), 'e_1':(1, 0), 
                 'se_1': (1, 1), 's_1': (0, 1), 'sw_1':(-1, 1), 
                 'w_1': (-1, 0), 'nw_1': (-1, -1)}
        moves = {move: self.get_dest(*diff) for move, diff in diffs.items()}
        # Add in-bound moves to ib_moves
        for move, dest in moves.items(): 
            if max(dest) <= 7 and min(dest) >= 0: # Ensure in-bounds
                self.ib_moves.add((move, *dest))
    
    def get_ib_moves(self):
        """Gets all in-bound moves for a piece based on the piece type."""
        move_dict = {
        'pawn':self.get_pawn_ib_moves,
        'rook':self.get_rook_ib_moves,
        'knight':self.get_knight_ib_moves,
        'bishop':self.get_bishop_ib_moves,
        'queen':self.get_queen_ib_moves,
        'king':self.get_king_ib_moves
        }
        return move_dict[self.type]()      
        
        
class Chessboard:
    """A class used to hold squares and pieces as well as help those objects 
    understand their surroundings. Also handles moves."""
    def __init__(self, turn='white', disp_mode = "numpy"):
        flipper = 0 # flips between 0 and 1 each iteration
        row_list = []
        for y in range(8):
            square_list = []
            for x in range(8):
                square = ChessSquare(color_list[flipper], x, y)
                square_list = square_list + [square]
                flipper = flipper * -1 + 1
            row_list = row_list + [square_list]
        self.board = np.array(row_list)
        self.disp_mode = disp_mode
        self.turn = turn
        self.nonturn = 'black' if turn == 'white' else 'white'
        self.turn_num = 1
        self.alive = []
        self.graveyard = []
        
    def __getitem__(self, tup):
        return self.board[tup[1],tup[0]]
        
    def set_up_board(self):
        """Puts pieces in starting positions."""
        piece_list = ['rook', 'knight', 'bishop', 'queen', 
                      'king', 'bishop', 'knight', 'rook']
        for x, piece in enumerate(piece_list):
            for y, color in zip([0, 7], color_list):
                self[x,y].occ = Piece(color, piece, x, y)
            for y, color in zip([1, 6], color_list):
                self[x,y].occ = Piece(color, 'pawn', x, y)
        
    def set_up_board_randomly(self):
        """Puts starting pieces in randomly assigned positions. For testing."""
        full_pos_list = [(x,y) for x in range(8) for y in range(8)]
        pos_list = sample(full_pos_list, 32)
        piece_list = ['rook','knight','bishop']*2+['king','queen']+['pawn']*8
        color_list = np.repeat(sample(['black', 'white'], 2), 16)
        for color, pos, piece in zip(color_list, pos_list, piece_list*2):
            self[pos].occ=Piece(color,piece,pos[0],pos[1])
            self[pos].occ.has_moved = True
    
    def view(self, mode='numpy'):
        """Returns nice-looking view of board. Not used in calculations."""
        df = pd.DataFrame(index=range(8), columns=range(8))
        for pos in [(x, y) for x in range(8) for y in range(8)]:
            occ = self[pos].occ
            if occ and occ.status == 'alive':
                df.loc[pos[::-1]] = self[pos].occ.symbol
            else:
                df.loc[pos[::-1]] = ''
        if mode == 'numpy':
            return df
        elif mode == 'chess':
            df.index = [1, 2, 3, 4, 5, 6, 7, 8]
            df.columns = ['a', 'b', 'c', 'd', 'e', 'f', 'g', 'h']
        return df
    
    def ascii(self):
        """Returns color-coded ascii-printed view of board."""
        
        
    def get_pieces(self, piece_type=[], color=[]):
        """Returns a list of pieces meeting the parameters (and, not or).
        Ex: if you provide king, queen and no color, it gets 4 pieces.
        Ex: If you provide king, queen and white, it gets 2 pieces."""      
        piece_list = []
        for x in range(8):
            for y in range(8):
                if self[x,y].occ:
                    piece_list = piece_list + [self[x,y].occ]
        if color:
            for piece in piece_list.copy():
                if piece.color not in color:
                    piece_list.remove(piece)
        if piece_type:
            for piece in piece_list.copy():
                if piece.type not in piece_type:
                    piece_list.remove(piece)
        return piece_list
    
    def get_alive_pieces(self):
        self.alive = self.get_pieces(
            piece_type=['pawn', 'rook', 'knight','bishop', 'queen', 'king']
        )

    def get_ib_moves(self):
        """Given each piece's position, get all moves for each piece that are
        within the boundaries of the board. Ignores castling."""
        for piece in self.alive:
            piece.ib_moves.reset()
            piece.get_ib_moves()

    def get_unobstructed_moves(self):
        """Given the board's pieces', each piece has its uo_moves attribute
        populated based on which moves have no pieces between it and dest.
        Knight/King/Pawn will always have the same ib_moves and uo_moves."""
        for piece in self.alive:
            piece.uo_moves.reset()
            if piece.type in ['pawn', 'knight', 'king']:
                for move, x, y in piece.ib_moves:
                    piece.uo_moves.add((move, x, y))
            else:
                for move, x, y in piece.ib_moves:
                    add = True
                    for btwn_pos in get_btwn(piece.pos, (x, y)):
                        if self[btwn_pos].occ:
                            add = False
                            break
                    if add: piece.uo_moves.add((move, x, y))
                            
    def get_valid_pawn_moves(self, piece):
        """Get legal moves for pawns including en passant."""
        assert piece.type == 'pawn'
        for move, x, y in piece.uo_moves:
            # Advance Single Space
            if (move == 's_1' or move == 'n_1') and not self[x, y].occ:
                piece.v_moves.add((move, x, y))
            # Advance Two Spaces
            elif move.split('_')[-1] == '2' and piece.hist.len == 0:
                piece.v_moves.add((move, x, y))
            elif len(move) == 4: # Only look at diagonal moves which have len 4
                occ = self[x, y].occ
                # Attacks
                if occ and occ.color != piece.color:
                    piece.v_moves.add((move, x, y))
                    continue
                # En Passant
                elif not occ:
                    # Identify east/west neighbor in attack direction
                    neighbor = self[x, piece.y].occ
                    if (neighbor and neighbor.color != piece.color and
                        neighbor.type == 'pawn' and 
                        neighbor.hist.len == 1 and 
                        '2' in list(iter(neighbor.hist))[0][0]):
                        piece.v_moves.add((move, x, y))
                        
    def get_valid_other_moves(self, piece):
        "Get legal moves for rooks excluding castles."""
        assert piece.type != 'pawn'
        for move, x, y in piece.uo_moves:
            occ = self[x, y].occ
            # If square is occupied by the enemy
            if occ and occ.color != piece.color:
                piece.v_moves.add((move, x, y))
            # IF square is empty
            elif not occ:
                piece.v_moves.add((move, x, y))      
                            
    def get_valid_moves(self):
        """Given the board's pieces', gets all legal moves for each piece.
        Does not consider pinned pieces, which are accounted for later."""
        move_dict = {
        'pawn':self.get_valid_pawn_moves,
        'rook':self.get_valid_other_moves,
        'knight':self.get_valid_other_moves,
        'bishop':self.get_valid_other_moves,
        'queen':self.get_valid_other_moves,
        'king':self.get_valid_other_moves
        }
        for piece in self.alive:
            piece.v_moves.reset()
            move_dict[piece.type](piece)

    def are_squares_safe(self, square_list, color):
        """False if color has valid moves targeting any of squarelist."""
        pos_list = [square.pos for square in square_list]
        color_pieces = self.get_pieces(color=[color])
        for piece in color_pieces:
            for move, x, y in piece.v_moves:
                if (x, y) in pos_list:
                    return False # threatened
        return True

    def get_valid_castles(self):
        # Loop through what OUGHT to be the kings. Confirmed if hist.len==0.
        for k in [self[4,0].occ, self[4,7].occ]:
            if (not k or k.hist.len != 0):
                continue
            y = k.y
            color = list(set(['black','white']) - set([k.color]))[0]
            # Loop through what ought to be the rook's matching k's color
            rooks = [self[0,y].occ, self[7,y].occ]
            safe_sqs = [[2, 3, 4], [6, 5, 4]]
            emp_sqs = [(not self[1,y].occ and not self[2,y].occ 
                       and not self[3,y].occ),
                       (not self[5,y].occ and not self[6,y].occ)]
            moves = ['c_q','c_k']
            # First element of each list has info for queenside castling
            for r, sqs, emp, move in zip(rooks, safe_sqs, emp_sqs, moves):
                if (not r or r.hist.len != 0):
                    continue
                if not emp:
                    continue
                square_list = [self[sq_x, y] for sq_x in sqs]
                if self.are_squares_safe(square_list, color):
                    k.v_moves.add((move, sqs[0], y))
                    
    def full_set_up(self, mode="standard"):
        """Set up board and generate all valid moves. Mode can be "random"."""
        if mode == "standard":
            self.set_up_board()
        elif mode == "random":
            self.set_up_board_randomly()
        self.get_alive_pieces()
        self.get_ib_moves()
        self.get_unobstructed_moves()
        self.get_valid_moves()
        self.get_valid_castles()
        return self.view()
  
    def move_piece(self, piece, dest, validate=True):
        """Move piece, potentially capture, and update all values."""
        # Get move name
        move = piece.v_moves.filt([('x',dest[0]),('y',dest[1])])[0][0]
        # Validate move
        if validate:
            assert dest in [(x, y) for move, x, y in piece.v_moves]
            assert piece.color == self.turn
        # Format print statement
        if self.disp_mode == 'chess': # Format destination to be chess-style
            dest_string = lookup_dict[dest].replace('_',"").upper()
        else:
            dest_string = str(dest)
        statement = "Moved " + piece.symbol + " to " + dest_string + ". "
        dest_piece = self[dest].occ
        if dest_piece: # Handle capture
            statement = statement + dest_piece.symbol + " has been captured!"
            self.graveyard.append(dest_piece)
            self.board.alive.remove(dest_piece)
            dest_piece.status = 'dead'
            dest_piece.killed_by = piece
            piece.kill_list += [dest_piece]
        # Update board information
        self[piece.pos].occ = None
        self[dest].occ = piece
        self.turn, self.nonturn = self.nonturn, self.turn
        self.turn_num += 1
        self.last_moved = [piece]
        # Update piece information
        piece.x, piece.y = dest
        piece.pos = dest
        piece.hist.add((piece.v_moves.filt([('x',dest[0]),('y',dest[1])])))
        # Handle castling
        if move == 'c_k' or move == 'c_q':
            if move == 'c_k':
                print("Kingside castle!")
                rook = self[7, piece.y].occ
                new_dest = (5, piece.y)
            elif move == 'c_q':
                print("Queenside castle!")
                rook = self[0, piece.y].occ
                new_dest = (3, piece.y)
            self.last_moved += [rook]
            self.turn, self.nonturn = self.nonturn, self.turn
            self.turn_num -= 1
            self.move_piece(rook, new_dest, False, 'none')
        # Update in-bound moves for moved pieces
        [lm_piece.get_ib_moves() for lm_piece in self.last_moved]
        # Update board
        self.get_unobstructed_moves()
        self.get_valid_moves()
        self.get_valid_castles()
        # Display
        if self.disp_mode != "none":
            print(statement)
            return self.view(mode=self.disp_mode)
       
#############################################################################
########################### Let's play chess! ###############################
#############################################################################
            
cboard = Chessboard(disp_mode = 'chess')
cboard.full_set_up()
cboard.move_piece(cboard[4,6].occ, (4,4), validate=True)
cboard.move_piece(cboard[1,1].occ, (1,3), validate=True)

#############################################################################

p0 = '     '
p1 = '     '
p2 = '  O  '
p3 = '  B  '
p4 = ' /P\ '

r0 = '     ' 
r1 = '|+++|'
r2 = ' | | ' 
r3 = ' |B| ' 
r4 = '/_R_\\'
   
b0 = '     '
b1 = '  0  '
b2 = ' /^\ '
b3 = ' \B/ '
b4 = ' /B\ '
      
n0 = '     '
n1 = ' ,^^ '
n2 = '< ^ |'
n3 = ' /B |'
n4 = '/_N_\\' 

q0 = '  .  '
q1 = '\/^\/'
q2 = ' { } '
q3 = ' |B| '
q4 = '/_Q_\\'

k0 = ' _+_ '
k1 = ' \ / '
k2 = ' { } '
k3 = ' |B| '
k4 = '/_K_\\'

piece_dict = {
    'pawn':[p0,p1,p2,p3,p4],
    'rook':[r0,r1,r2,r3,r4],
    'knight':[n0,n1,n2,n3,n4],
    'bishop':[b0,b1,b2,b3,b4],
    'queen':[q0,q1,q2,q3,q4],
    'king':[k0,k1,k2,k3,k4],
    }

# Define grid measurements
piece_height = 5
piece_width = 5
row_height = 5 # Ignoring Borders
col_width = 11 # Ignoring Borders
vert_spacer = int((row_height - piece_height) / 2)
lat_spacer = int((col_width - piece_width) / 2)

# Colors
black = '\x1b[30m' # background of entire board and all pieces
gray = '\u001b[30;1m' # color of black pieces
white = '\u001b[32m'
#white = '\x1b[37m' # color of white pieces, borders, and white square fill
reset = '\u001b[0m' # Back to default

# Define pieces to construct grid
raw_row_border =  '-'
raw_col_border = '|'
raw_corner = '+'
raw_fill = '.'
raw_space = ' '

row_border = white + raw_row_border + reset
col_border = white + raw_col_border + reset
corner = white + raw_corner + reset
fill = white + raw_fill + reset
space = white + raw_space + reset
endline = '@' # Will be replaced later, so it's fine unformatted

# Create grid row strings
border_row = "".join([raw_corner + raw_row_border * col_width \
                      for i in range(8)]) + raw_corner + endline    
spacer_row = border_row.replace(raw_row_border, raw_space).replace(
                raw_corner, raw_col_border)

spacer_row_odd_a = ''
spacer_row_odd_b = ''
spacer_row_even_a = ''
spacer_row_even_b = ''
counter = 0
x_pos = -1
for i in spacer_row:
    if i == raw_col_border:
        counter = 0
        x_pos += 1
        spacer_row_odd_a += i
        spacer_row_odd_b += i
        spacer_row_even_a += i
        spacer_row_even_b += i
    elif i == ' ' and x_pos % 2 == 0:
        spacer_row_odd_a += raw_fill if counter % 2 == 1 else ' '
        spacer_row_odd_b += raw_fill if counter % 2 == 0 else ' '
        spacer_row_even_a += i
        spacer_row_even_b += i
        counter += 1
    elif i == ' ' and x_pos % 2 == 1:
        spacer_row_even_a += raw_fill if counter % 2 == 1 else ' '
        spacer_row_even_b += raw_fill if counter % 2 == 0 else ' '
        spacer_row_odd_a += i
        spacer_row_odd_b += i
        counter += 1
    else:
        spacer_row_even_a += i
        spacer_row_even_b += i
        spacer_row_odd_a += i
        spacer_row_odd_b += i
        
border_row_top = list(border_row)
alpha_str = 'ABCDEFGH'
for i in range(8):
    border_row_top[1 + int(col_width / 2) + (col_width + 1) * i] = alpha_str[i]
border_row_top = "".join(border_row_top)

# Create grid and rowlist
# Alternate between even and odd on i
# alternate between a and b on line_num
grid = border_row
for row in range(8):
    for line_num in range(row_height):
        if row % 2 == 0:
            if line_num % 2 == 0:
                grid = grid + spacer_row_even_a
            else: 
                grid = grid + spacer_row_even_b
        else:
            if line_num % 2 == 0:
                grid = grid + spacer_row_odd_a
            else: 
                grid = grid + spacer_row_odd_b
    grid = grid + border_row
row_list = grid.split(endline)[:-1]

# Format grid and insert ascii pieces
new_row_list = []
y = -1 # Tracks what "cell" you're in, 0 to 7 (-1 since it starts on border)
line_num = 0 # Tracks what line of the cell you're in, 0 to row_height
for row in row_list:
    if row[0] == raw_corner:
        if y == -1:
            new_row = "".join([white + i + reset for i in border_row_top[:-1]])
        else:
            new_row = row.replace(raw_corner, corner)
            new_row = new_row.replace(raw_row_border, row_border)
        y += 1
        line_num = 0
        new_row_list += [new_row]
    else:
        string_list = row.split(raw_col_border)[:-1]
        x = -1 # Tracks what "column" we're in, from 0 to 7 (-1 and 8 are borders)
        new_row = ''
        for string in string_list:
            if string == '':
                # Determine if we need to add the rank
                if line_num == int(row_height/2):
                    new_row += white + str(y + 1) + reset
                else:
                    new_row += col_border
            elif line_num >= vert_spacer and line_num < (row_height-vert_spacer):
                # These are valid lines for piece replacement.
                occ = cboard[x,y].occ
                if occ:
                    # Perform no replacements if piece line would be empty.
                    # Like pawn only takes three lines, so we can treat
                    if (occ.type in ['rook', 'knight', 'bishop'] and 
                            line_num <= vert_spacer):
                        new_row_piece = string.replace(raw_fill, fill)
                        new_row_piece = new_row_piece.replace(raw_space, space)
                    elif occ.type == 'pawn' and line_num < (vert_spacer + 2):
                        new_row_piece = string.replace(raw_fill, fill)
                        new_row_piece = new_row_piece.replace(raw_space, space)
                    else:  
                        cpiece_string = piece_dict[occ.type][line_num-vert_spacer]
                        if occ.color == 'black':
                            # Already has a B
                            cpiece_string = gray + cpiece_string + reset
                        elif occ.color == 'white':
                            cpiece_string = cpiece_string.replace('B','W')
                            cpiece_string = white + cpiece_string + reset
                        left = string[:lat_spacer]
                        left = left.replace(raw_fill, fill)
                        left = left.replace(raw_space, space)
                        right = string[-lat_spacer:]
                        right = right.replace(raw_fill, fill)
                        right = right.replace(raw_space, space)
                        new_row_piece = left + cpiece_string + right
                else:
                    new_row_piece = string.replace(raw_fill, fill)
                    new_row_piece = new_row_piece.replace(raw_space, space)
                new_row += new_row_piece + col_border
            else:
                # not valid line for piece replacement, not a border string
                new_row_piece = string.replace(raw_fill, fill)
                new_row_piece = new_row_piece.replace(raw_space, space)
                new_row += new_row_piece + col_border
            x += 1
        new_row_list += [new_row]
        line_num += 1
    
print("\n".join(new_row_list))



######### TO DO ##########
# Incorporate ascii print function into view()
# Maybe remove numpy dependency since it's not useful at all. Filtering is stupid. 