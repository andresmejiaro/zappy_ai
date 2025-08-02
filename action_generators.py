import numpy as np
from MovementPlans import shorstest_vect, move_to
from ActionTree import LOGIC, Action, GEN
from BasicAction import Basic
from Agent import Agent
from functools import reduce
import random 

def closest_resource(agent: Agent, resource: str):

    found = [np.array([x,y]) for x in range(agent.size[0]) for y in range(agent.size[1]) if resource in agent.objects[x][y]]
    if agent.totem_pos is not None:
        for i,x in enumerate(found):
            if np.array_equal(x,agent.totem_pos):
                del found[i]
                break
    if len(found) == 0:
        return None
    
    distances = [agent.pos - x for x in found]
    return -shorstest_vect(distances) + agent.pos


def pick_up(agent: Agent, resource: str) -> Action:
    x = closest_resource(agent, resource)
    if x is None or len(x) == 0:
        return LOGIC(lambda x: False)
    actions = move_to(x, agent)
    return actions & Basic("prend",resource)


def pick_up_multiple(agent, resources)->Action:
    w = map(lambda x: pick_up(agent, x), resources)
    z = reduce(lambda x,y: x|y, w)
    return z


def roam(agent: Agent):
    r = Basic("voir") & Basic("droite") & Basic("voir") & Basic("droite") & Basic("voir") & Basic("droite") & Basic("voir") 
    nt = random.randint(0,3)
    for j in range(nt):
        r = r & Basic("droite")
    for j in range(2*agent.level - 2 + random.randint(0,3)):
        r = r & Basic("avance")
    return r

def gen_basic(command,resource = ''):
    return GEN(lambda x: Basic(command, resource))
