'''
Map Vertex
'''
# import any external packages by un-commenting them
# if you'd like to test / request any additional packages - please check with the Coder One team
import random
import time
import numpy as np
# import pandas as pd
# import sklearn


class Vertex:
    def __init__(self,pos,dist,prev,tile_type):
        self.pos = pos
        self.dist = dist
        self.prev = prev
        self.tile_type = tile_type # 0 = empty, 1/2/3 = next to 1/2/3 soft/ore blocks, 4 = treasure, 5 = ammo

## Copied from utils for reference:
# class block_type:
#     OPPONENT_ON_BOMB = 10
#     PLAYER_ON_BOMB = 9
#     BOMB = 8
#     TREASURE = 7
#     AMMO = 6
#     SOFT_BLOCKS = 5
#     ORE_BLOCKS = 4
#     HARD_BLOCKS = 3
#     OPPONENT = 2
#     PLAYER = 1
#
# block_type_dict = {None: 0, 0:block_type.PLAYER, 1:block_type.OPPONENT, 'ib':block_type.HARD_BLOCKS, 'sb':block_type.SOFT_BLOCKS, 'ob':block_type.ORE_BLOCKS, 'b':block_type.BOMB, 'a':block_type.AMMO, 't':block_type.TREASURE}
# blockages = [block_type.OPPONENT, block_type.HARD_BLOCKS, block_type.ORE_BLOCKS, block_type.SOFT_BLOCKS,
#             block_type.BOMB, block_type.PLAYER_ON_BOMB, block_type.OPPONENT_ON_BOMB]
