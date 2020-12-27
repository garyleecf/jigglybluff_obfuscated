'''
Tale of A Mongoose Agent

BIO:
A wise sage once said, "If a bomb is about to boom, you better GTFO!"
Countless knights and wizards have never understood what "GTFO" meant -- go to fetch ore? get the floor ornaments?

But over generations of evolution, after observing the neverending cycle of life and death of its comrades,
this mongoose knight/wizard (no one really knows who or what it is) has attained enlightenment.
And knowing when to "GTFO" became the mantra it lives by even up to today.
(Rumor has it that it has even developed some of the most advanced GTFO theory anyone has ever seen.)

GTFO is necessary, but not sufficient to thrive in this booming world...
To be truly successful, you will need to be a mongoose of many talents, such as knowing how to
* think like your enemy
* trap the prey
* hunting for resources
* know the answer to the ultimate question -- "to bomb or not to bomb"

These are life-changing skills, but no ordinary mongoose will ever learn it off the bat!
This mongoose has lived among experts for many generations, convincing them through relentless buggering
to impart their respective skills and specialties to it.

And of course, the mongoose has one last trick up its sleeve -- when it senses danger creeping up on it,
it will thrash and struggle, and its haunting voice will echo in your head for eternity, screaming the words:
"RUNNNNNNN BEFORE IT'S TOO LATEEEE"

'''

# import any external packages by un-commenting them
# if you'd like to test / request any additional packages - please check with the Coder One team
import random
#import time
import numpy as np
# import pandas as pd
# import sklearn
from copy import deepcopy

from .bombmapper import *
from .oremapper import *
from .mapvertex import *
from .utils import *

_DEBUG_PRINT = False

class Agent:
    def __init__(self):
        self.name = "ARGHHHHH"
        self.bombmapper = BombMapper()
        self.oremapper = OreMapper()
        self.idle = None
        self.hp = 3
        self.hp_lost_tick = -100
        self.prev_tick = -1
        self.im_trapped = False
        self.trap_opp_cooldown = 0
        self.skrrrt = False
        self.skrrrt_pos = None


    def next_move(self, game_state, player_state):
        """ This method is called each time the agent is required to choose an action
        """
        if game_state.tick_number - self.prev_tick != 1:
            print(f'Skipped a Tick: Tick #{game_state.tick_number}, skipped {game_state.tick_number - self.prev_tick}')
        self.prev_tick = game_state.tick_number
        opp_pos = game_state.opponents(10)[1-player_state.id]
        player_pos = deepcopy(player_state.location)

        # Add more info into game_state:
        game_state.opp_pos = opp_pos
        game_state.player_pos = player_state.location
        game_state.player_id = player_state.id
        self.trap_opp_cooldown = max(0,self.trap_opp_cooldown-1)


        if self.hp < player_state.hp:
            self.hp_lost_tick = game_state.tick_number
        lost_health = (game_state.tick_number - self.hp_lost_tick < 10)
        self.hp = player_state.hp
        skrrrted = self.skrrrt
        self.skrrrt = False

        conservative = True
        if conservative:
            player_ammo = player_state.ammo
            opp_ammo = 7 - player_ammo - len(game_state.bombs) - len(game_state.ammo)
        else:
            player_ammo = 7
            opp_ammo = 7
        #print(player_pos,opp_pos)
        num_blocks = len(game_state.all_blocks)
        #Get a ttl-sorted bomb list that accounts for chain reactions
        self.bombmapper.update(game_state)
        self.oremapper.update(game_state)
        #print(self.oremapper)

        bomb_list, game_map = get_bomb_list(game_state, self.bombmapper.bombs, player_state)
        self.bombmapper.correct_for_chains(bomb_list)
        #print(array_to_str(game_map))

        #Get all valid actions
        valid_actions, game_map = get_valid_actions(player_state, game_map, bomb_list)
        bomb_map = get_bomb_map(game_state, game_map, bomb_list, [])
        #If standing in the path of a bomb, gtfo
        if bomb_map[player_pos] == 1 or bomb_map[player_pos] == 2:
            lost_health = True
        safe_tile_exists = False
        for tile in neighbouring_tiles(player_pos)[0]:
            if (bomb_map[tile] == 0 or bomb_map[tile] >= 2) and game_map[tile] not in blockages:
                safe_tile_exists = True
                break
        for bomb in bomb_list:
            if bomb.ttl >= 1 if safe_tile_exists else 2:
                break
            if in_bomb_range(bomb.pos, player_pos, game_map):
                return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)
        #print(self.bombmapper.exploded_bombs)
        for bomb in self.bombmapper.exploded_bombs:
            if in_bomb_range(bomb.pos, player_pos, game_map):
                return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)
        #If not, start pathing
        #Get vertices of all accessible ammo, treasures, and reward squares next to walls
        action = random.choice(valid_actions)
        while action == 'p':
            action = random.choice(valid_actions)
        ammo_list = []
        treasure_list = []
        reward_list_1 = []
        reward_list_2 = []
        reward_list_3 = []

        available_tiles = get_available_tiles(game_state,player_pos,game_map,ore_map=self.oremapper.oremap,owned_bombs = [self.bombmapper.player_bombs, self.bombmapper.opp_bombs],ammo=player_ammo)
        immediate_targets = []
        for vertex in available_tiles:
            if vertex.tile_type == 1:
                reward_list_1.append(vertex)
            elif vertex.tile_type == 2:
                reward_list_2.append(vertex)
            elif vertex.tile_type >= 3 and vertex.tile_type < 50:
                reward_list_3.append(vertex)
                if vertex.tile_type >= 10:
                    immediate_targets.append(vertex)
            elif vertex.tile_type == 50:
                treasure_list.append(vertex)
            elif vertex.tile_type == 51:
                ammo_list.append(vertex)
        #Sort the lists by distance
        reward_list_1 = sort_vertices(reward_list_1)
        reward_list_2 = sort_vertices(reward_list_2)
        reward_list_3 = sort_vertices(reward_list_3)
        treasure_list = sort_vertices(treasure_list)
        ammo_list = sort_vertices(ammo_list)
        immediate_targets = sort_vertices(immediate_targets)
        #print([ammo.pos for ammo in ammo_list])

        temp_game_map = deepcopy(game_map)
        temp_game_map[player_pos], temp_game_map[opp_pos] = temp_game_map[opp_pos], temp_game_map[player_pos]
        enemy_available_tiles = get_available_tiles(game_state,opp_pos,temp_game_map,ore_map=self.oremapper.oremap,owned_bombs = [self.bombmapper.player_bombs, self.bombmapper.opp_bombs],ammo=opp_ammo)
        oal = []
        otl = []
        orl1 = []
        orl2 = []
        orl3 = []

        for vertex in enemy_available_tiles:
            if vertex.tile_type == 1:
                orl1.append(vertex)
            elif vertex.tile_type == 2:
                orl2.append(vertex)
            elif vertex.tile_type >= 3 and vertex.tile_type < 50:
                orl3.append(vertex)
            elif vertex.tile_type == 50:
                otl.append(vertex)
            elif vertex.tile_type == 51:
                oal.append(vertex)

        orl1 = sort_vertices(orl1)
        orl2 = sort_vertices(orl2)
        orl3 = sort_vertices(orl3)
        otl = sort_vertices(otl)
        oal = sort_vertices(oal)

        nearest_dist = [1e5,1e5,1e5]
        if len(reward_list_1) > 0:
            if len(orl1) > 0 and orl1[0].pos == reward_list_1[0].pos and orl1[0].dist < reward_list_1[0].dist:
                if len(reward_list_1) > 1:
                    del reward_list_1[0]
            nearest_dist[0] = reward_list_1[0].dist
        if len(reward_list_2) > 0:
            if len(orl2) > 0 and orl2[0].pos == reward_list_2[0].pos and orl2[0].dist < reward_list_2[0].dist:
                if len(reward_list_2) > 1:
                    del reward_list_2[0]
            nearest_dist[1] = reward_list_2[0].dist
        if len(reward_list_3) > 0:
            if len(orl3) > 0 and orl3[0].pos == reward_list_3[0].pos and orl3[0].dist < reward_list_3[0].dist:
                if len(reward_list_3) > 1:
                    del reward_list_3[0]
            nearest_dist[2] = reward_list_3[0].dist

        if len(ammo_list) > 0:
            if len(oal) > 0 and oal[0].pos == ammo_list[0].pos and oal[0].dist < ammo_list[0].dist:
                if len(ammo_list) > 1:
                    del ammo_list[0]

        if len(treasure_list) > 0:
            if len(otl) > 0 and otl[0].pos == treasure_list[0].pos and otl[0].dist < treasure_list[0].dist:
                if len(treasure_list) > 1:
                    del treasure_list[0]


        #See where opponent is
        opp_vertex = available_tiles[0]
        trap_opp = False
        im_trapped = False
        opp_dist = 1e5
        for vertex in available_tiles:
            if hamming_dist(vertex.pos, opp_pos) == 1:
                opp_vertex = Vertex(opp_pos,vertex.dist+1,available_tiles.index(vertex),1)
                opp_dist = vertex.dist + 1
                available_tiles.append(opp_vertex)
                break

        if death_trap(opp_pos,game_map):
            for coord,direction in neighbouring_tiles(opp_pos):
                if len(available_tiles) >= 3 and game_map[coord] == 8 and game_state.is_in_bounds(resultant_tile(resultant_tile(opp_pos,direction),direction)) and player_pos == resultant_tile(resultant_tile(opp_pos,direction),direction) and 'p' in valid_actions:
                    return 'p'
        if self.trap_opp_cooldown == 0 and should_trap_opp(game_state,game_map,opp_dist,opp_vertex,available_tiles):
            if _DEBUG_PRINT:
                print("TRAP OPP")
            action = move_to_vertex(opp_vertex,available_tiles)
            if action not in valid_actions:
                if 'p' in valid_actions:
                    action = 'p'
            if action == '' or action not in valid_actions:
                if self.idle is None:
                    self.idle = game_state.tick_number
            else:
                self.idle = None
            opp_next_to_bomb = False
            for tile in neighbouring_tiles(opp_pos)[0]:
                if game_map[tile] in [8,9,10]:
                    opp_next_to_bomb = True
            if ((action == '' or action not in valid_actions) and (game_state.tick_number - self.idle <= 35 or opp_next_to_bomb or len(ammo_list)+len(treasure_list)+player_state.ammo == 0)) or action == 'p' or (action not in ['','p'] and (bomb_map[resultant_tile(player_pos,action)] >= 3 or bomb_map[resultant_tile(player_pos,action)] == 0) and len(get_available_tiles(game_state,resultant_tile(player_pos,action),game_map,max_depth=8)) > 6):
                if action not in valid_actions and bomb_map[resultant_tile(player_pos,action)] in [1,2]:
                    action = ''
                return action
            if not ((action == '' or action not in valid_actions) and (game_state.tick_number - self.idle <= 35 or opp_next_to_bomb)):
                self.trap_opp_cooldown = 10


        if should_escape(game_state,game_map,opp_dist,opp_vertex,available_tiles):
            if _DEBUG_PRINT:
                print("RUNNNNNNN")
            im_trapped = True

        walls = 1*np.logical_or(game_map==block_type.SOFT_BLOCKS, game_map==block_type.ORE_BLOCKS)
        if self.oremapper.oremap is not None:
            for ore in game_state.ore_blocks:
                walls[ore] = self.oremapper.oremap[ore]
        else:
            for ore in game_state.ore_blocks:
                walls[ore] = 3
        if player_state.ammo == 0:
            if len(ammo_list) > 0:
                action = move_to_vertex(ammo_list[0],available_tiles)
            elif len(treasure_list) > 0:
                action = move_to_vertex(treasure_list[0],available_tiles)
            else:
                #Try to centralise and not get into corners? (bombs are precious)
                action = centralise(game_state,game_map,player_pos,available_tiles,bomb_map)
        elif len(immediate_targets) > 0:
            if immediate_targets[0].dist == 0:
                action = 'p'
            else:
                action = move_to_vertex(immediate_targets[0],available_tiles)
        elif len(ammo_list) > 0 and (nearest_dist[2] > 3 or opp_dist <= 3) and ((ammo_list[0].dist <= 15 and player_state.ammo < walls.sum() and len(reward_list_1+reward_list_2+reward_list_3) != 0) or len(reward_list_1+reward_list_2+reward_list_3+treasure_list) == 0):
            action = move_to_vertex(ammo_list[0],available_tiles)
        elif len(treasure_list) > 0 and (nearest_dist[2] > 3 or opp_dist <= 3) and (treasure_list[0].dist <= 10 or len(reward_list_1+reward_list_2+reward_list_3) == 0):
            action = move_to_vertex(treasure_list[0],available_tiles)
        else:
            if sum(nearest_dist) == 3e5:
                action = centralise(game_state,game_map,player_pos,available_tiles,bomb_map)
            elif min(nearest_dist) == 0:
                if nearest_dist[2] == 0:
                    action = 'p'
                elif nearest_dist[1] == 0:
                    if nearest_dist[2] <= 10:
                        action = move_to_vertex(reward_list_3[0],available_tiles)
                    else:
                        action = 'p'
                else:
                    if nearest_dist[2] <= 20:
                        action = move_to_vertex(reward_list_3[0],available_tiles)
                    elif nearest_dist[1] <= 12:
                        action = move_to_vertex(reward_list_2[0],available_tiles)
                    else:
                        action = 'p'
            else:
                if np.argmin(nearest_dist) == 0:
                    if nearest_dist[2] - nearest_dist[0] <= 20:
                        action = move_to_vertex(reward_list_3[0],available_tiles)
                    elif nearest_dist[1] - nearest_dist[0] <= 12:
                        action = move_to_vertex(reward_list_2[0],available_tiles)
                    else:
                        action = move_to_vertex(reward_list_1[0],available_tiles)
                elif np.argmin(nearest_dist) == 1:
                    if nearest_dist[2] - nearest_dist[1] <= 10:
                        action = action = move_to_vertex(reward_list_3[0],available_tiles)
                    else:
                        action = move_to_vertex(reward_list_2[0],available_tiles)
                else:
                    action = move_to_vertex(reward_list_3[0],available_tiles)

        gonna_be_trapped = False
        if not im_trapped and opp_dist <= 6 and not trap_opp:
            if action_is_trappable(game_state,game_map,action):
                print("RUNNNNNNN BEFORE IT'S TOO LATEEEE")
                gonna_be_trapped = True

        #Ensure the actions chosen above does not lead to being trapped in a dead end, or walking past an exploding bomb
        skrrrting = False
        if im_trapped:
            action = move_to_vertex(opp_vertex,available_tiles)

        elif gonna_be_trapped:
            if action != move_to_vertex(opp_vertex,available_tiles):
                action = move_to_vertex(opp_vertex,available_tiles)
                if (action not in valid_actions or action == ''):
                    temp_game_map = deepcopy(game_map)
                    temp_game_map[player_pos] = 3
                    for tile in neighbouring_tiles(opp_pos)[0]:
                        for vertex in available_tiles:
                            if vertex.pos == tile and len(get_available_tiles(game_state,vertex.pos,temp_game_map,max_depth=8)) > 5:
                                action = move_to_vertex(vertex,available_tiles)
                                if action in valid_actions and action != '':
                                    skrrrting = True
                                    self.skrrrt = True
                                    self.skrrrt_pos = player_pos
                                    if _DEBUG_PRINT:
                                        print("Skrrrting around - ",action)
                                    break
                        if skrrrting:
                            break
            else:
                action = ''

        if game_map[player_pos] == 9 and len(get_available_tiles(game_state, resultant_tile(player_pos,action), game_map, max_depth=5)) <= 3:
            if _DEBUG_PRINT:
                print("Find alternative spot!")
            action_space={}
            max_space = 2
            reward = -1
            cur_action = action
            for a in valid_actions:
                if a == cur_action or (a == '' and opp_dist != 1):
                    continue
                action_space[a] = len(get_available_tiles(game_state,resultant_tile(player_pos,a),game_map,max_L1_dist=5))
                if action_space[a] >= max_space:
                    max_space = action_space[a]
                    vertex = find_vertex(resultant_tile(player_pos,a),available_tiles)
                    if vertex.tile_type > reward:
                        action = a
                        reward = vertex.tile_type

        if game_map[player_pos] == 9 and opp_dist <= 6 and action_is_trappable(game_state,game_map,action):
            remaining_actions = []
            for a in valid_actions:
                if a != action and not action_is_trappable(game_state,game_map,a) and not death_trap(resultant_tile(player_pos,a),game_map):
                    remaining_actions.append(a)
            if _DEBUG_PRINT:
                print("TRAPPABLE!", action, remaining_actions, valid_actions)
            if len(remaining_actions) == 1:
                action = a
            elif len(remaining_actions) == 0:
                print("IT'S OVERRRRRR!")
            else:
                action_space={}
                max_space = 2
                reward = -1
                print("FINDING ESCAPE!")
                for a in remaining_actions:
                    if a == '':
                        continue
                    action_space[a] = len(get_available_tiles(game_state,resultant_tile(player_pos,action),game_map,max_L1_dist=5))
                    if action_space[a] >= max_space:
                        max_space = action_space[a]
                        vertex = find_vertex(resultant_tile(player_pos,a),available_tiles)
                        if vertex.tile_type > reward:
                            action = a
                            reward = vertex.tile_type

        if skrrrted and opp_pos == self.skrrrt_pos:
            action = ''

        action_space={}
        if bomb_map[resultant_tile(player_pos,action)] <= 2 and bomb_map[resultant_tile(player_pos,action)] > 0:
            #print("Walking into bomb")
            for a in valid_actions:
                action_space[a] = bomb_map[resultant_tile(player_pos,a)]
            if action_space[''] <= 0 or action_space[''] > 2:
                action = ''
            else:
                if action not in valid_actions:
                    action = ''
                space = action_space[action]
                for a in action_space:
                    #print(space,action_space[a],a)
                    if action_space[a] > space and a != 'p' and a!= '':
                        space = action_space[a]
                        action = a
                    elif action_space[a] == 0:
                        action = a
                        break
            if action == 'p':
                if _DEBUG_PRINT:
                    print("NOOOOOOOOOOOOOOOOOOOO")
                #action = ''
                return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)

        if ((not safe_to_bomb(available_tiles,player_pos,game_map)) or im_trapped or (get_available_tiles(game_state,player_pos,game_map,max_L1_dist=1)==2 and opp_dist==2)) and action == 'p':
            if len(available_tiles) >= 4 and self.idle is not None and game_state.tick_number-self.idle >= 40:
                if _DEBUG_PRINT:
                    print("Fine - go ahead and bomb!")
            elif get_available_tiles(game_state,player_pos,game_map,max_L1_dist=1)==2 and opp_dist==2:
                action = move_to_vertex(opp_vertex,available_tiles)
            else:
                if _DEBUG_PRINT:
                    print("Don't be stupid!")
                return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)
        temp_game_map = deepcopy(game_map)
        temp_game_map[player_pos] = 0 if temp_game_map[player_pos] == 1 else 8
        if game_map[player_pos] == 9 and len(get_available_tiles(game_state,resultant_tile(player_pos,action),temp_game_map)) <= 2:
            print("Don't do it!")
            action = move_to_vertex(opp_vertex,available_tiles)
            if opp_dist == 1e5 and action == '':
                return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)

        if im_trapped and action == 'p':
            temp_game_map = deepcopy(game_map)
            temp_game_map[player_pos] = 0 if temp_game_map[player_pos] == 1 else 8
            action = move_to_vertex(opp_vertex,available_tiles)
            if len(get_available_tiles(game_state,resultant_tile(player_pos,action),temp_game_map)) <= 2:
                action = ''

        temp_game_map = deepcopy(game_map)
        temp_game_map[player_pos] = 3
        if len(get_available_tiles(game_state,resultant_tile(player_pos,action),temp_game_map)) <= 2 and im_trapped:
            action = move_to_vertex(opp_vertex,available_tiles)
            if bomb_map[resultant_tile(player_pos,action)] <= 5:
                action = ''
        if player_state.ammo == 7 and self.idle is not None and self.idle > 10 and len(available_tiles)  > 10:
            action = 'p'

        #if action not in valid_actions:
        #    action = ''

        if action == '' or action not in valid_actions:
            if self.idle is None:
                self.idle = game_state.tick_number
        else:
            self.idle = None

        if (self.im_trapped or im_trapped) and action == 'p':
            action = ''

        if im_trapped:
            self.im_trapped = True
        else:
            if len(available_tiles) > 8:
                self.im_trapped = False


        if lost_health and action == 'p':
            print("NO BUENO! NO BOMBO!")
            return advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions)

        return validate_actions(action, valid_actions)
