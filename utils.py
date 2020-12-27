'''
Utils
'''

import random
#import time
import numpy as np
from copy import deepcopy
# import pandas as pd
# import sklearn

from .mapvertex import Vertex

class block_type:
    OPPONENT_ON_BOMB = 10
    PLAYER_ON_BOMB = 9
    BOMB = 8
    TREASURE = 7
    AMMO = 6
    SOFT_BLOCKS = 5
    ORE_BLOCKS = 4
    HARD_BLOCKS = 3
    OPPONENT = 2
    PLAYER = 1

# 0 is Player 1, 1 is Player 2, DOES NOT CORRESPOND TO PLAYER ID
block_type_dict = {None: 0, 'ib':block_type.HARD_BLOCKS, 'sb':block_type.SOFT_BLOCKS, 'ob':block_type.ORE_BLOCKS, 'b':block_type.BOMB, 'a':block_type.AMMO, 't':block_type.TREASURE}
blockages = [block_type.OPPONENT, block_type.HARD_BLOCKS, block_type.ORE_BLOCKS, block_type.SOFT_BLOCKS,
            block_type.BOMB, block_type.PLAYER_ON_BOMB, block_type.OPPONENT_ON_BOMB]
blockage_types = [0, 1, 'ib', 'sb', 'ob', 'b']

##################################################
# General Util Methods
##################################################

def array_to_str(array_to_print):
    return np.rot90(array_to_print)

def hamming_dist(p1, p2):
    if p1 is None or p2 is None:
        return 120
    return np.abs(p1[0]-p2[0])+np.abs(p1[1]-p2[1])

def closest_object(loc, list_of_objects, exceptions=[]):
    dist = 120
    target_pos = None
    for a in list_of_objects:
        if a in exceptions:
            continue
        new_dist = hamming_dist(loc, a)
        if dist > new_dist:
            target_pos = a
            dist = new_dist
    return target_pos

def state_to_array(game_state, player_id, match_gui=False):
    game_map = np.zeros(game_state.size,dtype=np.int8)
    objects = [game_state.bombs, game_state.ammo, game_state.indestructible_blocks, game_state.soft_blocks, game_state.ore_blocks, game_state.treasure]
    keys = [block_type.BOMB, block_type.AMMO, block_type.HARD_BLOCKS, block_type.SOFT_BLOCKS, block_type.ORE_BLOCKS, block_type.TREASURE]
    for obj_list, k in zip(objects, keys):
        for obj in obj_list:
            game_map[obj] = k
    for i, opp in enumerate(game_state.opponents(2)):
        game_map[opp] += block_type.PLAYER if i == player_id else block_type.OPPONENT

    if match_gui:
        game_map = array_to_str(game_map)
    return game_map

def get_valid_actions(player_state, game_map, bomb_list):
    valid_actions = ['']
    #game_map = state_to_array(game_state, player_state.id)

    for coord, direction in zip(*neighbouring_tiles(player_state.location)):
        if game_map[coord] not in blockages:
            valid_actions.append(direction)

    if player_state.ammo > 0:
        on_bomb = False
        for bomb in bomb_list:
            if bomb.pos == player_state.location:
                on_bomb = True
                break
        if not on_bomb:
            valid_actions.append('p')
    return valid_actions, np.array(game_map)

def validate_actions(action, valid_actions):
    if action in valid_actions:
        return action
    elif '' in valid_actions:
        return ''
    return random.choice(valid_actions)

def get_direction(cur_pos, next_pos):
    if next_pos[0] == cur_pos[0] + 1:
        return 'r'
    elif next_pos[0] == cur_pos[0] - 1:
        return 'l'
    elif next_pos[1] == cur_pos[1] + 1:
        return 'u'
    elif next_pos[1] == cur_pos[1] - 1:
        return 'd'
    return ''

##################################################
# Util Methods
##################################################
def get_available_tiles(game_state, start_coord, game_map, ore_map=None, owned_bombs = None, max_L1_dist=30, max_depth=120, ammo=None):
    if ore_map is not None:
        reward_map = get_reward_map(game_state, game_map, ore_map, owned_bombs, ammo)
    else:
        reward_map = np.zeros(game_map.shape,dtype=np.int8)
    vertices = [Vertex(start_coord,0,0,reward_map[start_coord])]
    visited_board = np.zeros(game_map.shape,dtype=np.int8)
    visited_board[start_coord] = 1
    L1_dist = 0
    cur_tiles, _ = neighbouring_tiles(start_coord)
    visiting_board = deepcopy(visited_board)
    prev_tiles = [0 for _ in range(len(cur_tiles))]

    while len(cur_tiles) != 0 and L1_dist < max_L1_dist and len(vertices) < max_depth:
        L1_dist += 1
        new_cur_tiles, new_prev_tiles = [], []
        for coord, prev in zip(cur_tiles, prev_tiles):
            # if game_state.entity_at(coord) not in blockage_types and visited_board[coord] != 1:
            if game_map[coord] not in blockages and visited_board[coord] != 1:
                vertices.append(Vertex(coord,L1_dist,prev,reward_map[coord]))
                visited_board[coord] = 1
                for new_tile in neighbouring_tiles(coord)[0]:
                    if visiting_board[new_tile] == 0:
                        visiting_board[new_tile] = 1
                        new_cur_tiles.append(new_tile)
                        new_prev_tiles.append(len(vertices)-1)
        cur_tiles = deepcopy(new_cur_tiles)
        prev_tiles = deepcopy(new_prev_tiles)
    return vertices


def get_reward_map(game_state,game_map,ore_map,owned_bombs,ammo_count):
    reward_map = np.zeros(game_map.shape,dtype=np.int8)
    walls = 1*np.logical_or(game_map==block_type.SOFT_BLOCKS, game_map==block_type.ORE_BLOCKS)

    ore_list = game_state.ore_blocks
    if ore_map is None:
        for ore in ore_list:
            walls[ore] = 3
    else:
        for ore in ore_list:
            if ore_map[ore] > 0:
                walls[ore] = ore_map[ore]


    bombs = 1*(game_map>=block_type.BOMB)
    bomb_list = game_state.bombs
    player_bombs = [bomb.pos for bomb in owned_bombs[0]]
    opp_bombs = [bomb.pos for bomb in owned_bombs[1]]
    all_bombs = owned_bombs[0] + owned_bombs[1]
    all_bombs_pos = [bomb.pos for bomb in all_bombs]

    for bomb in bomb_list:
        for coord, direction in zip(*neighbouring_tiles(bomb,steps=2)):
            if in_bomb_range(bomb,coord,game_map):
                if hamming_dist(bomb,coord) == 1:
                    walls[coord] = max(0, walls[coord]-1)
                elif hamming_dist(bomb,coord) == 2 and walls[coord] > 0:
                    if resultant_tile(bomb,direction) not in all_bombs_pos:
                        walls[coord] = max(0, walls[coord]-1)
                    else:
                        ttl1 = all_bombs[all_bombs_pos.index(resultant_tile(bomb,direction))].ttl
                        ttl2 = all_bombs[all_bombs_pos.index(bomb)].ttl
                        if ttl1 < ttl2:
                            walls[coord] = max(0, walls[coord]-1)

    wall_list = [tuple(coord) for coord in np.array(np.where(walls>0)).T.tolist()]
    for wall in wall_list:
        if walls[wall] == 3 and ammo_count < 3:
            continue
        elif walls[wall] == 2 and ammo_count < 2:
            continue
        elif walls[wall] == 2 and ammo_count >= 2:
            walls[wall] = 1
        coords, directions = neighbouring_tiles(wall, steps=2)
        dir_dict = {}
        ore_val = 10 if (ore_map[wall] > 0 and walls[wall] == 1) else 0
        for i in range(len(directions)):
            if walls[coords[i]] == 0:
                d = directions[i]
                if d in dir_dict:
                    dir_dict[d] += 1
                else:
                    dir_dict[d] = 1
        for d in dir_dict:
            if dir_dict[d] == 1:
                reward_map[resultant_tile(wall,d)] += 1 + ore_val
            else:
                if bombs[resultant_tile(resultant_tile(wall,d),d)] == 0 and in_bomb_range(wall,resultant_tile(resultant_tile(wall,d),d),game_map):
                    reward_map[resultant_tile(wall,d)] += 1 + ore_val
                    reward_map[resultant_tile(resultant_tile(wall,d),d)] += 1 + ore_val


    ammo_list = game_state.ammo
    treasure_list = game_state.treasure
    #print(ammo_list)
    for treasure in treasure_list:
        reward_map[treasure] = 50
    for ammo in ammo_list:
        reward_map[ammo] = 51

    player_pos = game_state.player_pos
    if game_state.entity_at(player_pos) == 'b':
        reward_map[player_pos] = 0
    single_rewards = [tuple(coord) for coord in np.array(np.where(reward_map==1)).T.tolist()]
    for single_reward in single_rewards:
        next_to_wall = False
        for coord,direction in zip(*neighbouring_tiles(single_reward)):
            if walls[coord] >= 1 or (bombs[coord] == 1 and game_state.is_in_bounds(resultant_tile(coord,direction)) and ore_map[resultant_tile(coord,direction)] >= 1):
                next_to_wall = True
                break
        if not next_to_wall:
            reward_map[single_reward] = 0

    treble_rewards = [tuple(coord) for coord in np.array(np.where(reward_map>=10)).T.tolist()]
    for treble_reward in treble_rewards:
        next_to_wall = False
        for coord,direction in zip(*neighbouring_tiles(treble_reward)):
            if walls[coord] >= 1:
                continue
            else:
                two_steps = resultant_tile(coord,direction)
                if game_state.is_in_bounds(two_steps):
                    if bombs[coord] == 0 and ore_map[two_steps] >= 1 and walls[two_steps] == 1:
                        reward_map[treble_reward] -= 11
                    if bombs[coord] == 1 and ore_map[two_steps] == 3 and walls[two_steps] == 1:
                        for tile in neighbouring_tiles(two_steps)[0]:
                            if tile in opp_bombs and tile != coord:
                                ttl2 = 35
                                ttl1 = owned_bombs[1][opp_bombs.index(tile)].ttl
                                if coord in player_bombs:
                                    ttl2 = owned_bombs[0][player_bombs.index(coord)].ttl
                                elif coord in opp_bombs:
                                    ttl2 = owned_bombs[1][opp_bombs.index(coord)].ttl
                                else:
                                    pass
                                if ttl1 > ttl2 + 2:
                                    reward_map[treble_reward] -= 11
                                break

    #Find snipeable positions
    if ore_map is not None:
        temp_walls = 1*np.logical_or(game_map==block_type.SOFT_BLOCKS, game_map==block_type.ORE_BLOCKS)
        for wall in [tuple(coord) for coord in np.array(np.where(walls==0)).T.tolist() if temp_walls[tuple(coord)] == 1]:
            if ore_map[wall] > 0:
                ore_hp = ore_map[wall]
                ore_bomb_list = []
                for tile in neighbouring_tiles(wall,steps=2)[0]:
                    if tile in all_bombs_pos and in_bomb_range(wall,tile,game_map):
                        b = all_bombs[all_bombs_pos.index(tile)]
                        ore_bomb_list.append([b.pos[0], b.pos[1], b.ttl])
                ore_bomb_list = np.array(ore_bomb_list)
                ore_bomb_list = [tuple(coord) for coord in (ore_bomb_list[ore_bomb_list[:,2].argsort()])[:,:2].tolist()]
                count = 0
                for ore_bomb_idx in range(len(ore_bomb_list)):
                    ore_bomb = ore_bomb_list[ore_bomb_idx]
                    mid_tile = tuple([int((ore_bomb[0]+wall[0])/2),int((ore_bomb[1]+wall[1])/2)])
                    if hamming_dist(wall,ore_bomb) == 1:
                        count += 1
                    elif mid_tile not in ore_bomb_list or mid_tile in ore_bomb_list[:ore_bomb_idx]:
                        count += 1
                    if count == ore_hp:
                        if hamming_dist(wall,ore_bomb) == 2 and ore_bomb not in player_bombs:
                            reward_map[mid_tile] += 11
                        break

            elif ore_map[wall] == 0:
                snipeable = True
                for tile in neighbouring_tiles(wall)[0]:
                    if tile in bomb_list:
                        snipeable = False
                        break
                if snipeable:
                    lowest_ttl = 50
                    snipeable_tiles = []
                    tile_bombs = []
                    for tile, direction in zip(*neighbouring_tiles(wall,steps=2)):
                        if tile in all_bombs_pos and in_bomb_range(tile,wall,game_map):
                            ttl = all_bombs[all_bombs_pos.index(tile)].ttl
                            if ttl <= lowest_ttl:
                                if ttl < lowest_ttl:
                                    lowest_ttl = ttl
                                    snipeable_tiles = [resultant_tile(wall,direction)]
                                    tile_bombs = [all_bombs[all_bombs_pos.index(tile)]]
                                else:
                                    snipeable_tiles.append(resultant_tile(wall,direction))
                                    tile_bombs.append(all_bombs[all_bombs_pos.index(tile)])
                    if len(snipeable_tiles) == 1 and tile_bombs[0].pos in opp_bombs:
                        reward_map[snipeable_tiles[0]] += 1


    for coord in game_state.all_blocks + game_state.bombs + [game_state.opp_pos]:
        reward_map[coord] = 0
    if reward_map.sum() == 0 and False:
        for tile in neighbouring_tiles(game_state.opp_pos)[0]:
            reward_map[tile] = 1
    return reward_map



def neighbouring_tiles(coord, board_size=(12,10), steps=1):
    tiles, directions = [], []
    for step in range(1, steps+1):
        if coord[0] > step-1:
            tiles.append((coord[0]-step,coord[1]))
            directions.append('l')
        if coord[1] > step-1:
            tiles.append((coord[0],coord[1]-step))
            directions.append('d')
        if coord[0] < board_size[0]-step:
            tiles.append((coord[0]+step,coord[1]))
            directions.append('r')
        if coord[1] < board_size[1]-step:
            tiles.append((coord[0],coord[1]+step))
            directions.append('u')
    return tiles, directions

def resultant_tile(coord,action):
    tile = list(deepcopy(coord))
    if action == 'u':
        tile[1] += 1
    elif action == 'd':
        tile[1] -= 1
    elif action == 'l':
        tile[0] -= 1
    elif action == 'r':
        tile[0] += 1
    return tuple(tile)


##################################################
# Vertex Methods
##################################################
def sort_vertices(vertex_list):
    if len(vertex_list) <= 1:
        return vertex_list
    sorted_list = []
    for idx in range(len(vertex_list)):
        sorted_list.append([vertex_list[idx].dist,idx])
    sorted_list = np.array(sorted_list)
    sorted_list = sorted_list[sorted_list[:,0].argsort()]
    return [vertex_list[i] for i in sorted_list[:,1]]

def move_to_vertex(target,vertex_list):
    prev = target.prev
    if prev == 0:
        action = get_direction(vertex_list[0].pos,target.pos)
    else:
        while vertex_list[prev].prev != 0:
            prev = vertex_list[prev].prev
        action = get_direction(vertex_list[0].pos,vertex_list[prev].pos)
    return action

def find_vertex(coord,vertex_list):
    for vertex in vertex_list:
        if vertex.pos == coord:
            return vertex
    return None

##################################################
# Bomb Methods
##################################################
def in_bomb_range(bomb_pos, tile_pos, game_map, power=2):
    #if more than 1 distance away, check if there's a wall in between
    if (abs(bomb_pos[0] - tile_pos[0]) <= 1 and abs(bomb_pos[1] - tile_pos[1]) == 0) or (abs(bomb_pos[0] - tile_pos[0]) == 0 and abs(bomb_pos[1] - tile_pos[1]) <= 1):
        return True
    elif (abs(bomb_pos[0] - tile_pos[0]) <= power and abs(bomb_pos[1] - tile_pos[1]) == 0):
        for i in range(1,power):
            coord = (min(bomb_pos[0],tile_pos[0])+i,bomb_pos[1])
            if game_map[coord] in [3,4,5]:
                return False
        return True
    elif (abs(bomb_pos[0] - tile_pos[0]) == 0 and abs(bomb_pos[1] - tile_pos[1]) <= power):
        for i in range(1,power):
            coord = (bomb_pos[0],min(bomb_pos[1],tile_pos[1])+i)
            if game_map[coord] in [3,4,5]:
                return False
        return True

def get_bomb_map(game_state, game_map, bomb_list, exploded_bomb_list):
    bomb_map = np.array([-1*((i-1)%7 < 5) for i in game_map])
    player_pos = game_state.player_pos
    bomb_map[player_pos] = 0
    for bomb in bomb_list + exploded_bomb_list:
        if bomb_map[bomb.pos] == -1:
            bomb_map[bomb.pos] = bomb.ttl+1
        for coord in neighbouring_tiles(bomb.pos, steps=2)[0] + [bomb.pos]:
            if in_bomb_range(bomb.pos, coord, game_map):
                if bomb_map[coord] > 0:
                    bomb_map[coord] = min(bomb_map[coord],bomb.ttl+1)
                elif bomb_map[coord] == 0:
                    bomb_map[coord] = bomb.ttl+1
        if in_bomb_range(bomb.pos, player_pos, game_map):
            if bomb_map[player_pos] == 0:
                bomb_map[player_pos] = bomb.ttl+1
            else:
                bomb_map[player_pos] = min(bomb_map[player_pos], bomb.ttl+1)
    return bomb_map


def get_bomb_list(game_state, bombs, player_state):
    #Returns an updated bomb list that accounts for explosion chains, sorted in order of time-to-live
    game_map = state_to_array(game_state, player_state.id)
    neighbours = [[] for _ in range(len(bombs))]
    for i in range(len(bombs)-1):
        for j in range(i+1,len(bombs)):
            if in_bomb_range(bombs[i].pos, bombs[j].pos, game_map):
                neighbours[i].append(j)
                neighbours[j].append(i)
    updated = True
    while updated:
        updated = False
        for b in range(len(bombs)):
            for n in neighbours[b]:
                if bombs[b].ttl > bombs[n].ttl + 1:
                    updated = True
                    bombs[b].ttl = bombs[n].ttl + 1

    sb = np.zeros((len(bombs),2),dtype=int)
    for idx in range(len(bombs)):
        sb[idx,0] = bombs[idx].ttl
        sb[idx,1] = idx
    sb = sb[sb[:,0].argsort()]
    sorted_bombs = [bombs[i] for i in sb[:,1]]
    return deepcopy(sorted_bombs), game_map

def safe_to_bomb(vertex_list, player_pos, game_map):
    for vertex in vertex_list[1:]:
        if not in_bomb_range(player_pos, vertex.pos, game_map):
            return True
    return False

##################################################
# Strategies
##################################################
def gtfo(game_state, valid_actions, bomb_map, game_map, player_pos):
    actions = []
    remaining_actions = []
    for a in valid_actions:
        if a != 'p':
            remaining_actions.append(a)
    for idx in range(len(remaining_actions)):
        actions.append([bomb_map[resultant_tile(player_pos,remaining_actions[idx])], idx])
        if death_trap(resultant_tile(player_pos,remaining_actions[idx]),game_map):
            actions[-1][0] = -500
        elif actions[-1][0] == 0:
            actions[-1][0] = 500
        elif remaining_actions[idx] == '' and actions[-1][0] == 1:
            actions[-1][0] = -300
    random.shuffle(actions)
    actions = np.array(actions,dtype=np.int8)
    actions = actions[actions[:,0].argsort()][::-1]
    action = remaining_actions[actions[0,1]]
    return action


def advanced_gtfo(game_state, player_pos, game_map, bomb_map, valid_actions):
    available_tiles = get_available_tiles(game_state,player_pos,game_map,max_depth=5)
    ttl = -1
    if len(available_tiles) <= 3:
        for vertex in available_tiles:
            if bomb_map[vertex.pos] == 0:
                return move_to_vertex(vertex,available_tiles)
            elif bomb_map[vertex.pos] > ttl:
                ttl = bomb_map[vertex.pos]
                action = move_to_vertex(vertex,available_tiles)
        return action
    available_tiles = get_available_tiles(game_state,player_pos,game_map,max_L1_dist=1)
    action = None
    for vertex in available_tiles:
        if (bomb_map[vertex.pos] == 0 or bomb_map[vertex.pos] > 5) and not death_trap(vertex.pos,game_map):
            action = move_to_vertex(vertex,available_tiles)

    if action == None:
        for vertex in available_tiles:
            if bomb_map[vertex.pos] > bomb_map[player_pos] and bomb_map[vertex.pos] >= 2 and not death_trap(vertex.pos,game_map):
                action = move_to_vertex(vertex,available_tiles)

    if action == None:
        return gtfo(game_state,valid_actions,bomb_map,game_map,player_pos)
    return action


def centralise(game_state, game_map, player_pos, vertex_list, bomb_map):
    if game_state.opp_pos == vertex_list[-1].pos and vertex_list[-1].dist > 2:
        return move_to_vertex(vertex_list[-1],vertex_list)
    action = ''
    space = 0
    action_space={}
    temp_game_map = deepcopy(game_map)
    temp_game_map[player_pos] = 3
    for vertex in vertex_list:
        if vertex.dist >= 2:
            break
        elif vertex.dist == 0:
            continue
        else:
            a = get_direction(player_pos,vertex.pos)
            at_sum = 0
            for vertex in get_available_tiles(game_state,vertex.pos,temp_game_map,max_L1_dist=30)[1:]:
                at_sum += (1+vertex.tile_type)/(vertex.dist+1)**2
            action_space[a] = at_sum
    for a in action_space:
        if action_space[a] > space:
            action = a
            space = action_space[a]

    return action

def should_trap_opp(game_state,game_map,opp_dist,opp_vertex,available_tiles):
    if opp_dist > 5 or game_map[available_tiles[0].pos] == 9:
        return False
    if opp_dist <= 3:
        for tile in neighbouring_tiles(game_state.opp_pos)[0] + [game_state.opp_pos]:
            if game_map[tile] in [0,2,6,7] and death_trap(tile,game_map):
                return True
    temp_game_map = deepcopy(game_map)
    temp_game_map[game_state.player_pos] = 0 if temp_game_map[game_state.player_pos] == 1 else 8
    temp_game_map[game_state.opp_pos] = 0 if temp_game_map[game_state.opp_pos] == 2 else 9
    temp_game_map[available_tiles[opp_vertex.prev].pos] = 3
    if len(get_available_tiles(game_state,game_state.opp_pos,temp_game_map,max_depth=8)) <= 5:
        return True
    return False

def should_escape(game_state,game_map,opp_dist,opp_vertex,available_tiles):
    if opp_dist > 8:
        return False
    pathing = [opp_vertex]
    cur_idx = len(available_tiles) - 1
    while available_tiles[cur_idx].prev != 0:
        cur_idx = available_tiles[cur_idx].prev
        cur_vertex = deepcopy(available_tiles[cur_idx])
        pathing.append(cur_vertex)
    pathing.append(available_tiles[0])
    for i in range(int(-(-len(pathing)//2))):
        j = len(pathing)-i-1
        if j == i:
            j = i + 1
        temp_game_map = deepcopy(game_map)
        temp_game_map[game_state.player_pos] = 0 if temp_game_map[game_state.player_pos] == 1 else 8
        temp_game_map[game_state.opp_pos] = 0 if temp_game_map[game_state.opp_pos] == 2 else 9
        temp_game_map[pathing[i].pos] = 3
        if len(get_available_tiles(game_state,pathing[j].pos,temp_game_map,max_depth=8)) <= 6:
            return True
    return False

def death_trap(coord,game_map):
    for tile in neighbouring_tiles(coord)[0]:
        if tile not in blockages + [block_type.PLAYER]:
            return False
    return True

def action_is_trappable(game_state,game_map,action):
    temp_game_map = deepcopy(game_map)
    temp_game_map[game_state.player_pos] = 0 if game_map[game_state.player_pos] == 1 else 8
    temp_player_pos = resultant_tile(game_state.player_pos,action)
    if temp_player_pos == game_state.opp_pos:
        temp_player_pos = game_state.player_pos
    temp_game_map[temp_player_pos] = 0
    temp_available_tiles = get_available_tiles(game_state,game_state.opp_pos,temp_game_map)

    pathing = []
    found_path = False
    for vertex in temp_available_tiles:
        if vertex.pos == temp_player_pos:
            found_path = True
            pathing.append(vertex)
            cur_vertex = vertex
            while cur_vertex.prev != 0:
                cur_vertex = temp_available_tiles[cur_vertex.prev]
                pathing.append(cur_vertex)
            break

    if not found_path:
        return False

    if temp_player_pos == game_state.player_pos:
        temp_game_map[temp_player_pos] = game_map[temp_player_pos]
    else:
        temp_game_map[temp_player_pos] = 1
    if pathing[-1].pos == temp_player_pos:
        temp_opp_pos = game_state.opp_pos
    else:
        temp_opp_pos = pathing[-1].pos
        temp_game_map[game_state.opp_pos] = 0 if game_map[game_state.opp_pos] == 2 else 9
        temp_game_map[temp_opp_pos] = 2

    temp_game_state = deepcopy(game_state)
    temp_game_state.player_pos = temp_player_pos
    temp_game_state.opp_pos = temp_opp_pos

    temp_available_tiles = get_available_tiles(temp_game_state,temp_player_pos,temp_game_map)
    for vertex in temp_available_tiles:
        if hamming_dist(vertex.pos, temp_opp_pos) == 1:
            temp_opp_vertex = Vertex(temp_opp_pos,vertex.dist+1,temp_available_tiles.index(vertex),1)
            temp_opp_dist = vertex.dist + 1
            temp_available_tiles.append(temp_opp_vertex)
            break

    return should_escape(temp_game_state,temp_game_map,temp_opp_dist,temp_opp_vertex,temp_available_tiles)
