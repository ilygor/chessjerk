#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Constants and function for creating a beautiful chess board.
"""

# Imports and setup
import colorama
colorama.init()

#### Define constants
# Piece Strings
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

# Grid measurements
piece_height = 5
piece_width = 5
row_height = 5 # Ignoring Borders
col_width = 11 # Ignoring Borders
vert_spacer = int((row_height - piece_height) / 2)
lat_spacer = int((col_width - piece_width) / 2)

# Colors
black = '\x1b[30m' # background of entire board and all pieces
gray = '\u001b[30;1m' # color of black pieces
white = '\x1b[37m' # color of white pieces, borders, and white square fill
reset = '\u001b[0m' # Back to default

# Define formatted and unformatted pieces to construct grid
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

# Create list of unformatted row strings
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


#### Functions
# Format grid and insert ascii pieces
def pretty_board(cboard, black_first = False):
    """Takes a Chessboard object and prints a beautiful, color-coded string 
    using constants defined in pretty_board.py. Returns nothing."""
    new_row_list = []
    y = -1 # Tracks what "cell" you're in, 0 to 7 (-1 since it starts on border)
    line_num = 0 # Tracks what line of the cell you're in, 0 to row_height
    for row in row_list:
        if row[0] == raw_corner:
            if y == -1:
                new_row = "".join([white + i + reset for i in 
                                   border_row_top[:-1]])
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
                                if line_num-vert_spacer == 3:
                                    cpiece_string=cpiece_string.replace('B','W')
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
    if not black_first:
        print("\n".join(new_row_list))
    elif black_first:
        first = new_row_list.pop(0)
        cells0 = new_row_list[0:row_height+1]
        cells1 = new_row_list[row_height+1:(row_height+1)*2]
        cells2 = new_row_list[(row_height+1)*2:(row_height+1)*3]
        cells3 = new_row_list[(row_height+1)*3:(row_height+1)*4]
        cells4 = new_row_list[(row_height+1)*4:(row_height+1)*5]
        cells5 = new_row_list[(row_height+1)*5:(row_height+1)*6]
        cells6 = new_row_list[(row_height+1)*6:(row_height+1)*7]
        cells7 = new_row_list[(row_height+1)*7:(row_height+1)*8]
        new_row_list = [first] + cells7 + cells6 + cells5 + cells4 + cells3 + \
                       cells2 + cells1 + cells0
        print("\n".join(new_row_list))