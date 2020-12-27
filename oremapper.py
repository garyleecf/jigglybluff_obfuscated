'''
OreMapper
'''

# import any external packages by un-commenting them
# if you'd like to test / request any additional packages - please check with the Coder One team
import random
import time
import numpy as np
# import pandas as pd
# import sklearn
from .utils import hamming_dist

ORE_INIT_HP = 3

class OreMapper:
    def __init__(self):
        self.oremap = None
        self.running_bombset = set()

    def update(self, game_state):
        if self.oremap is None:
            self.oremap = np.zeros(game_state.size,dtype=np.int8)
            for o in game_state.ore_blocks:
                self.oremap[o] = ORE_INIT_HP

        for boom in self.running_bombset.difference(set(game_state.bombs)):
            for o in game_state.ore_blocks:
                if hamming_dist(boom, o) == 1:
                    self.oremap[o] -= 1
                if hamming_dist(boom, o) == 2:
                    if (np.abs(boom[0] - o[0]) == 2):
                        if game_state.entity_at(((boom[0]+o[0])/2, boom[1])) not in ['ob', 'sb', 'ib', 'b']:
                            self.oremap[o] -= 1
                    elif (np.abs(boom[1] - o[1]) == 2):
                        if game_state.entity_at((boom[0], (boom[1]+o[1])/2)) not in ['ob', 'sb', 'ib', 'b']:
                            self.oremap[o] -= 1

        self.running_bombset = set(game_state.bombs)

    def ore_hp_left(self):
        return self.oremap

    def __str__(self):
        return np.rot90(self.oremap).__str__()
