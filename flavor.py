#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
Flavor text for various game events.
"""

# Imports
from random import sample

# Constants
pawn_capture = [
    "I hope you weren't using that.",
    "Oh, was that your piece? Didn't see it there.",
    "If you don't want your pieces captured, don't put them where I'm moving.",
    "You'll win more games if you don't let your pieces get captured.",
    "Like stealing candy from a baby.",
    "You're making this too easy.",
    "Off with their heads!",
    "Another capture! This is fun! For me, anyway.",
    "Ah... it feels good to be good.",
    "Aren't you supposed to protect your pieces?",
    "You should consider trying harder.",
    "TIP: Be better.",
    "You remind me of someone who doesn't know how to play chess.",
    "Oh, so close! You almost got away.",
    "One more capture, one step closer to ending you.",
    "Are you letting me take your pieces, or are you just bad?",
    "Are you having fun? I'm having fun.",
    "Watch, as I make this pawn... disappear!",
    "I know you're just a human, but you shouldn't be making THIS many mistakes.",
    "Another move, another pawn capture...."
    ]

knight_capture = [
    "What a cute little horsey! Too bad it's dead now.",
    "Your bronco has bit the dust. Yeehaw!",
    "I wish I could say your knight was in a better place, but it's probably in horse hell.",
    "Pathetic. They really hand knighthoods out to anyone these days.",
    "Your stupid horse is dead.",
    ]

bishop_capture = [
    "You zigged when you should have zagged, fool.",
    "Bishop down.",
    "Shame about the bishop. Hopefully you have a spare. :)",
    "Bishops can move any distance, but you still managed to lose this one.",
    "Putting the 'die' in 'diagonal.'",
    ]

rook_capture = [
    "It's a castle that moves around, yet it crumbled so easily!",
    "I thought that was supposed to be one of the strong pieces.",
    "I hope you weren't planning on using that for anything.",
    "Oh, did I just take your rook? That's a shame.",
    "You probably didn't want a rook that was captured so easily anyway.",
    ]

queen_capture = [
    "HAHAHAHAHAA!! THAT WAS YOUR QUEEN!!!!! HAHAHAHAHA!",
    "That was literally your strongest piece and I just took it. Sorry. :)",
    "Did you mean for that to happen? Queens are usually useful.",
    "Oh dear, that was your queen wasn't it? Maybe you can get another. Maybe not.",
    "Another one bites the dust!",
    "That's a shame. Remember you can quit at any time!"
    ]

victory = [
    "Well, you are merely human.",
    "The only way to get better is to lose again, and again, and again, and again.",
    "It's okay, I wasn't very good my first game either.",
    "Maybe you'll do better once you learn what the pieces do.",
    "It can't be helped. Some people just weren't meant to play chess.",
    "I hope you didn't spend much time practicing, for your sake.",
    "Stick to checkers.",
    "Maybe you can make a career out of tic-tac-toe.",
    ]

loss = [
    "Yeah, yeah, whatever. I can use stockfish too.",
    "Oh, we're all sooooo impressed. I could do better if I spent 1 hour per move too.",
    "You got lucky.",
    "I wasn't really trying, but good job I guess.",
    "...whatever. I don't even like chess.",
    "THIS IS GARBAGE. HOW DID THIS HAPPEN!?", 
]

castle = [
    "Hiding behind a rook isn't going to save you.",
    "Moving two pieces at once, nobody is impressed.",
    "Coward. If you were really good, you would move your king in front of your pawns.",
    "Do you really think castling will save you?",
    "Castling, really impressive. You're just delaying the inevitable."
    ]

flavor_dict = {
    'pawn': pawn_capture,
    'knight': knight_capture, 
    'bishop': bishop_capture,
    'rook': rook_capture,
    'queen': queen_capture,
    'victory': victory,
    'loss': loss,
    'castle': castle
    }

# Functions
def flavor_spitter(flavor_dict_key):
    """Prints a random flavor text based on the input key for flavor_dict. For
    Some keys, a return is guaranteed, for others, there's a 50/50 shot."""
    if flavor_dict_key in ['victory', 'loss', 'queen', 'castle']:
        print(sample(flavor_dict[flavor_dict_key], 1)[0])
    if sample([0, 1], 1) == [1]:
        print(sample(flavor_dict[flavor_dict_key], 1)[0])


