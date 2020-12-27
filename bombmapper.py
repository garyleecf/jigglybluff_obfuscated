'''
BombMapper
'''

# import any external packages by un-commenting them
# if you'd like to test / request any additional packages - please check with the Coder One team
import random
import time
import numpy as np
# import pandas as pd
# import sklearn
from copy import deepcopy


class Bomb:
    def __init__(self, pos, ttl):
        self.pos = pos
        self.ttl = ttl

class BombMapper:
    def __init__(self):
        self.bombmap = None
        self.bombset = []
        self.game_tick = 0
        self.bombs = []
        self.exploded_bombs = []
        self.player_bombs = []
        self.opp_bombs = []

    def update(self, game_state):
        self.game_tick = game_state.tick_number
        if self.bombmap is None:
            self.bombmap = np.zeros(game_state.size,dtype=np.int8)*np.nan
        for b in game_state.bombs:
            if b not in self.bombset:
                self.bombmap[b] = game_state.tick_number
                self.bombs.append(Bomb(b,35))
                if b == game_state.player_pos:
                    self.player_bombs.append(Bomb(b,35))
                elif b == game_state.opp_pos:
                    self.opp_bombs.append(Bomb(b,35))
                else:
                    print("Uhhhhhh")

        self.exploded_bombs = []
        del_idx = []
        for bomb in self.bombs:
            #print("*",bomb.pos,bomb.ttl)
            bomb.ttl = min(bomb.ttl-1,self.timeleft()[bomb.pos]) if self.timeleft()[bomb.pos] >= 0 else self.timeleft()[bomb.pos]
            #print("**",bomb.pos,bomb.ttl)
            if not bomb.ttl >= 0:
                del_idx.append(self.bombs.index(bomb))
            elif bomb.ttl == 0:
                self.exploded_bombs.append(bomb)

        for bomb in self.player_bombs:
            bomb.ttl = min(bomb.ttl-1,self.timeleft()[bomb.pos]) if self.timeleft()[bomb.pos] >= 0 else self.timeleft()[bomb.pos]
        for bomb in self.opp_bombs:
            bomb.ttl = min(bomb.ttl-1,self.timeleft()[bomb.pos]) if self.timeleft()[bomb.pos] >= 0 else self.timeleft()[bomb.pos]
        self.bombset = [bomb.pos for bomb in self.bombs]
        #print(len(self.bombset),len(self.bombs))


        del_idx.sort(reverse=True)
        for idx in del_idx:
            if self.bombs[idx] in self.player_bombs:
                del self.player_bombs[self.player_bombs.index(self.bombs[idx])]
            elif self.bombs[idx] in self.opp_bombs:
                del self.opp_bombs[self.opp_bombs.index(self.bombs[idx])]
            del self.bombs[idx]

    def correct_for_chains(self, bomb_list):
        ttl_map = np.zeros(self.bombmap.shape,dtype=np.int8)
        for bomb in bomb_list:
            ttl_map[bomb.pos] = bomb.ttl
        for bomb in self.player_bombs:
            bomb.ttl = ttl_map[bomb.pos]
        for bomb in self.opp_bombs:
            bomb.ttl = ttl_map[bomb.pos]

    def timeleft(self):
        return 35 - (self.game_tick - self.bombmap)

    def __str__(self):
        return np.rot90(self.timeleft()).__str__()
