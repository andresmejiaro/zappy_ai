from domain_agent import Agent
import  core_behavior_tree as ct
from gen_common import gen_interaction
from gen_movement import shorstest_vect, move_to
import gen_movement as gmov
import numpy as np

def drop(agent: Agent,inventory: dict) -> ct.BTNode:
    actions = []
    for key, value in inventory.items():
        n_to_drop = min(value, agent.inventory[key])
        actions2 = map(lambda x: gen_interaction("pose",x),[key] * n_to_drop)
        actions.extend(actions2)
    if len(actions) > 0:
        to_return = ct.AND_P(actions, name=f"drop {inventory}" )
        return to_return
    return ct.LOGIC(lambda x: True)

def closest_resource(agent: Agent, resource: str):
    """
    Finds the coordinate of the nearest known resource that
    is not the totem
    """

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


def pick_up(agent: Agent, resource: str) -> ct.BTNode:
    x = closest_resource(agent, resource)
    if x is None or len(x) == 0:
        return ct.LOGIC(lambda x: False)
    actions = move_to(x, agent)
    actions = [actions, ct.Interaction("prend",resource), ct.Interaction("inventaire")]
    return ct.AND(actions, name = f"pick up {resource}")  


def pick_up_multiple(agent, resources: dict)->ct.BTNode:
    """
    This sets up multiple things to find multiple stuff 
    to find if any found returns True
    """
    look4 = []
    for key, value in resources.items():
        if agent.inventory[key] < value:
            look4.append( key)
    w = map(lambda x: ct.GEN(lambda y: pick_up(y, x)), look4)
    w = list(w)
    if len(w) == 0:
        return ct.LOGIC(lambda x: True)
    z = ct.OR(w, name="pick_up_multiple")
    return z

def do_i_have_inventory(agent, resources: dict)->bool:
    for key, value in resources.items():
        if agent.inventory[key] < value:
            return False
    return True 

def gather(agent,resources: dict)->ct.BTNode:
    check = ct.LOGIC(lambda x: do_i_have_inventory(x,resources), name = "gather check Inv")
    gather_node = ct.GEN(lambda x: pick_up_multiple(x,resources),ret=ct.Status.F, name = "gather collector")
    roam = ct.GEN(gmov.roam,ret=ct.Status.F, name="gather roam")
    return ct.OR([check,gather_node,roam], name = f"gather {resources}")

def mark_totem(agent):
    if not np.array_equal(agent.totem_pos, agent.new_totem):
        agent.totem_pos = agent.new_totem
        print("New Totem Found!°")
    else:
        return ct.LOGIC(lambda x: False)
    pick_a_stone = ct.GEN(lambda x: gather(x,{"linemate":1}), name = "mark totem pickup")
    go_to_totem = ct.GEN(gmov.go_to_totem, name = "mark totem movement")
    drop_stone = ct.GEN(lambda x: drop(x,{"linemate":1}), name= "mark totem drop")
    return ct.AND_P([pick_a_stone,go_to_totem,drop_stone],name= "mark totem sequence")

def level_up(agent, reqs, players = 1):
    gather_items = ct.GEN(lambda x: gather(x, reqs), "level up gather")
    go_to_totem = ct.GEN(gmov.go_to_totem, name = "level up movement")
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
    incantation = gen_interaction("incantation")
    return ct.AND_P([gather_items, go_to_totem, drop_items, incantation], name="level up sequence")