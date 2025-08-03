from domain_agent import Agent
from core_behavior_tree import BTNode, LOGIC, GEN
from core_bt_interactions import Interaction
from gen_common import gen_interaction
from gen_movement import shorstest_vect, move_to
from functools import reduce
import numpy as np

def drop(agent: Agent,inventory: dict) -> BTNode:
    actions = []
    for key, value in inventory.items:
        n_to_drop = min(value, agent.inventory[key])
        actions2 = map(lambda x: gen_interaction("pose",x),[key] * n_to_drop)
        actions.extend(actions2)
    if len(actions) > 0:
        to_return = reduce(lambda x,y: x & y,actions)
        return to_return
    return LOGIC(lambda x: True)

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


def pick_up(agent: Agent, resource: str) -> BTNode:
    x = closest_resource(agent, resource)
    if x is None or len(x) == 0:
        return LOGIC(lambda x: False)
    actions = move_to(x, agent)
    return actions & Interaction("prend",resource) & Interaction("inventaire")


def pick_up_multiple(agent, resources: dict)->BTNode:
    look4 = []
    for key, value in resources.items():
        if agent.inventory[key] < value:
            look4.append( key)
    w = map(lambda x: GEN(lambda y: pick_up(y, x)), look4)
    w = list(w)
    if len(w) == 0:
        return LOGIC(lambda x: True)
    z = reduce(lambda x,y: x|y, w)
    return z
