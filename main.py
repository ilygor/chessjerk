#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""The m ain file through which chess can be played."""

# Import packages
from time import sleep
import os
import pandas as pd

# Import modules
from pretty_board import pretty_board
from classes import Chessboard
from simulate import Simulator

# Define constants        
wait = 0 # Amount of time to wait between printouts. Good for comedy and drama.
letter_list = ['a','b','c','d','e','f','g','h']
# For each difficulty how many moves to consider, and responses to consider
difficulty_map = {
        1: (1,1),
        2: (2,1),
        3: (3,1),
        4: (2,2), 
        5: (3,2), 
        6: (4,2),
        7: (5,2),
        8: (5,3),
        9: (6,3),
        }

# Useful functions
def interpret_string(string):
    """Given a string like "A2" returns "(0,1)" so that we can use it."""
    x = letter_list.index(string[0].lower())
    y = int(string[1]) - 1
    return (x,y)

# Main code begins here
os.system('cls' if os.name == 'nt' else 'clear')
print("Welcome to jerk chess! The chess bot that insults you.")
sleep(wait)
print("You'll be prompted to submit moves, questions, and decisions via text.")
sleep(wait)
print("If you want to quit, just type 'quit' at any time.\n\n")
sleep(wait)

# Difficulty selection
failed_input_count = 0
valid_input_list = [str(i) for i in [1,2,3,4,5,6,7,8,9]]
difficulty = input("To begin, enter a difficulty between 1 and 9, with 9 "
                   "being the most difficult: ")
if difficulty == 'quit':
        quit()
while difficulty not in valid_input_list:
    failed_input_count += 1
    if failed_input_count == 1:
        difficulty = input("Seriously, it's not that hard. If you want "
                           "difficult enter 9, if you want easy enter 1. "
                           "Simple. Now go ahead: ")
    elif failed_input_count == 2:
        difficulty = input("I am beginning to suspect you're doing this "
                           "on purpose. One more time. Enter a number "
                           "between 1 and 9, 9 being the hardest difficulty: ")
    elif failed_input_count == 3:
        print("You're being difficult. Well, that makes two of us.")
        sleep(wait)
        difficulty = '9'
    if difficulty == 'quit':
        quit()
print("You have chosen difficulty: " + difficulty + "!")
sleep(wait)
if difficulty in ['1','2','3']:
    print("I didn't expect to have to play against cowards. Oh well.\n\n")
elif difficulty in ['4','5','6','7']:
    print("Pretty boring difficulty selection, not gonna lie.\n\n")
elif difficulty in ['8','9']:
    print("I'm certain you will regret your decision.\n\n")
sleep(wait)

gen1, gen2 = difficulty_map[int(difficulty)]

# Color selection
failed_color_input_count = 0
statement = ("Now it's time to select a color. Enter 'black' or 'white' "
             "without quotes and we can begin playing: ")
if failed_input_count >= 2:
    statement = statement[:-2] + (". Please don't waste my time again. Just "
                "enter a value: ")
color = input(statement)
if color == 'quit':
    quit()
while color not in ['black', 'white']:
    failed_input_count += 1
    failed_color_input_count += 1
    if failed_color_input_count == 1:
        print("You only get one more chance. #SorryNotSorry.")
        sleep(wait)
        color = input("Enter black or white. It's not hard: ")
    elif failed_color_input_count == 2:
        print("I warned you.")
        sleep(wait)
        color = 'black'
    if color == 'quit':
        quit()
print("You have chosen " + color + "!\n\n")
sleep(wait)

# Begin game
cboard = Chessboard(player_color = color)
cboard.full_set_up()
print("The game is afoot! You can always say 'help' for help, or 'quit' to "
      "quit.")
sleep(wait)
print("You make moves by entering the origin square followed by the "
      "destination square. \nFor instance, 'B7 B5' is a valid opener for white.")
sleep(wait * 2)
print("I hope you're ready to lose.")
sleep(int(wait/2))
print("3")
sleep(int(wait/2))
print("2")
sleep(int(wait/2))
print("1")
sleep(int(wait/2))
os.system('cls' if os.name == 'nt' else 'clear')
if color == 'black':
    pretty_board(cboard, False)
else:
    pretty_board(cboard, True)
print("It is white's turn to play.")

# Game loop
df = 0
fails = 0
check = False
while True:
    if check:
        sim = Simulator(cboard)
        df = sim.simulate()
        print(df)
        if df.score.max() < -100:
            print("That's checkmate! " + cboard.nonturn.upper() + " wins!")
            input("Press enter to quit.")
            quit()
    if cboard.turn == color:
        move = input("\nEnter a move, 'help', or 'quit': ")
        if move == 'quit':
            quit()
        elif move == 'help':
            info = ("I figured you'd probably need help. Here are some of the "
                    "things you can do, besides lose.\n\n"
                    "quit\t-\tQuits the game, like the pathetic quitter you are.\n"
                    "help\t-\tYou should already know what this does.\n"
                    "info a1\t-\tGives information about the piece on a1.\n"
                    "a7 a6\t-\tMoves the piece on a7 to a6, if possible.\n"
                    )
            print(info)
        elif ' ' in move and move.split(' ')[0] == 'info':
            try:
                position = interpret_string(move.split(' ')[1])
                occ = cboard[position].occ
                if occ:
                    occ.info()
                else:
                    print("There's no piece there... use your head.")
            except:
                print("Invalid input.")
                fails += 1
        elif ' ' in move:
            try:
                piece = interpret_string(move.split(' ')[0])
                dest = interpret_string(move.split(' ')[1])
                if check:
                    try: 
                        score = df.loc[(df.orig==piece) & 
                                       (df.dest==dest),
                                       'score'].values[0]
                        if score < -100:
                            print("Still in check! Try another move.")
                        else:
                            check, dummy = cboard.move_piece(cboard[piece].occ, 
                                                         (dest), True, True)
                    except Exception as e:
                        print("Invalid move. 1")
                else:
                    check, dummy = cboard.move_piece(cboard[piece].occ, 
                                                     (dest), True, True)
            except:
                print("Invalid move.")
                fails += 1
        else:
            print("Invalid input.")
            fails += 1
    else:
        sim = Simulator(cboard, gen1, gen2)
        print("My turn. :)")
        sleep(int(wait/2))
        print("Let me think...")
        orig, dest = sim.multi_level_simulate()
        check, dummy = cboard.move_piece(cboard[orig].occ, 
                                         (dest), True, True, False)
        
        
        






