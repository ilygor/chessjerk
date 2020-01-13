# chessjerk
A simple chess bot using Python. With very few packages required, you can run an interactive chess game in the terminal, complete with this lovely board printout.

![ASCII chessboard showing how the game looks in the terminal.](https://github.com/rossbrian120/chessjerk/blob/master/preview.png?raw=true)

### Features
All the bells and whistles you know and love about chess are present. Castling, en passant, pawn promotion. Use these moves to try and beat a simple AI I have constructed. While it's by no means amazing, make a mistake and you can be sure that the AI will capitalize on it. Select your color, a difficulty from 1 to 9, and the game starts. AI rarely takes more than 20 seconds to consider a move at the highest difficulty level.

### Organization
This program is broken into 4 key files:
* main.py - This contains the logic for running the application. It receives inputs from the user to take moves, difficulty selections, etc.
* classes.py - This defines the key classes of the program, such as Piece and Chessboard.
* pretty_board.py - Getting the ASCII board formatted nicely took a lot of code. The logic and functions responsible for that were separated into this file.
* simulate.py - Classes and functions responsible for the AI. It takes a copy of the chessboard object and runs simulations on it, returning a pandas dataframe.

### Details about the AI
If you were curious how the "AI" works, I'll start by saying it's quite generous to even call it an AI. It doesn't learn. It simply applies a set of rules to the game whenever it gets a turn. It first evaluates every possible move and assigns it a score based on how many pieces it captures as well as how many pieces it targets. It is penalized for being targeted by the enemy. Finally additional points are granted for backing up pieces with other pieces and controlling more squares than the opposition.

After evaluating each move, it takes the top *n* of them and does the same thing from the perspective of the opposition, given that one of those *n* moves has been made. After analyzing all possible responses by the opposition and scoring them, it takes the top *m* of those.

In this way, it creates trees. First we have n branches representing the AI's moves, then m branches representing the best responses to those moves, and then it evaluates every possible move in response to those. It then selects the move with the best worst-case scenario, given the opposition choosing the best move.

Ideally I'd prune these trees and continue going deeper, but I don't want it to take longer to make moves than it already does.

### To be added
 - Improved endgame AI
 - Guardrails to prevent the user from moving into check
 - Stalemate recognition (and AI to avoid stalemate)
 - Various other bugfixes (AI pawn promotion, printed messages when the AI puts you in check)
 - Flavor text where the bot insults you if you make a bad move (hence the name of the repository)
 
### Notes
This was my first object-oriented programming project, and I learned a lot. For those reasons, there's also quite a few things I would have done differently. I think the biggest lesson was probably to understand how you want the application to be structured before you start on it. :)

Feel free to use this code or any part of it to your heart's content.
