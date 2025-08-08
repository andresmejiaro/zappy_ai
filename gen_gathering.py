from domain_agent import Agent
import  core_behavior_tree as ct
from gen_common import gen_interaction
from gen_movement import shorstest_vect, move_to
import gen_movement as gmov
import numpy as np
import random
import gen_teaming as gtem

def inventory_selector(agent, indivudual = False)->dict:
    #what inventory to use
    if agent.party.party_closed == True and not indivudual:
        agent.party.update_party_inventory()
        inv = agent.party.party_inventory
    else:
        inv = agent.inventory
    return inv


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
        return ct.GEN(gmov.roam)
    actions = move_to(x, agent)
    actions = [actions, ct.Interaction("prend",resource)]
    return ct.AND(actions, name = f"pick up {resource}")  


def pick_up_multiple(agent, resources: dict, individual = False)->ct.BTNode:
    """
    This sets up multiple things to find multiple stuff 
    to find if any found returns True
    """
    look4 = []
    inv = inventory_selector(agent, individual)
    for key, value in resources.items():
        if inv.get(key,0) < value:
            look4.append( key)
    random.shuffle(look4)
    w = map(lambda x: ct.GEN(lambda y: pick_up(y, x)), look4)
    w = list(w)
    if len(w) == 0:
        return ct.LOGIC(lambda x: True)
    z = ct.OR(w, name="pick_up_multiple")
    if agent.party.party_name is None:
        return z
    return ct.AND_P([z, ct.GEN(gtem.share_inventory)], name = "sharing after finding")

def do_i_have_inventory(agent, resources: dict, individual = False)->bool:
    inv = inventory_selector(agent, individual)
    for key, value in resources.items():
        if inv.get(key,0) < value:
            return False
    return True 

def gather(agent,resources: dict, individual = False)->ct.BTNode:
    check = ct.LOGIC(lambda x: do_i_have_inventory(x,resources, individual), name = "gather check Inv")
    gather_node = ct.GEN(lambda x: pick_up_multiple(x,resources), name = "gather collector")
    roam = ct.GEN(gmov.roam, name="gather roam")
    return ct.OR([check,gather_node,roam], name = f"gather {resources}")

def mark_totem(agent):
    if not np.array_equal(agent.totem_pos, agent.new_totem):
        agent.totem_pos = agent.new_totem
        print("New Totem Found!°")
    else:
        return ct.LOGIC(lambda x: False)
    pick_a_stone = ct.GEN(lambda x: gather(x,{"linemate":1}, individual = True), name = "mark totem pickup")
    go_to_totem = ct.GEN(gmov.go_to_totem, name = "mark totem movement")
    drop_stone = ct.GEN(lambda x: drop(x,{"linemate":1}), name= "mark totem drop")
    return ct.AND_P([pick_a_stone,go_to_totem,drop_stone],name= "mark totem sequence")

def level_up_reqs(aclv):
    lreq =[{"linemate":1},
           {"linemate":1, "deraumere":1, "sibur":1},
           {"linemate":2,"sibur":1,"phiras":2},
           {"linemate":1, "deraumere":1,"sibur":2,"phiras":1},
           {"linemate":1, "deraumere":1,"sibur":1,"mendiane":3},
           {"linemate":1, "deraumere":2,"sibur":3,"phiras":1},
           {"linemate":2, "deraumere":2,"sibur":2, "mendiane":2,"phiras":2,"thystame":1}
    ]
    return lreq[aclv - 1]

logic1 = lambda x: x.party.party_name is None or len(x.party.party_members_ready) == len(x.party.party_members)


def level_up(agent):
    reqs = level_up_reqs(agent.level)
    
    do_i_need_team = ct.LOGIC(lambda x: x.level <= 1, name = "do I need to team up")
    team_up = ct.OR([do_i_need_team, gtem.teaming], name = "level up teaming up")
    gather_items = ct.GEN(lambda x: gather(x, reqs), "level up gather")
    go_to_totem = ct.GEN(gmov.go_to_totem, name = "level up movement")
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
    i_am_ready = ct.GEN(gtem.ready_for_incantation)
    wait_for_team_mates = ct.LOGIC(logic1)
    incantation = gen_interaction("incantation")
    disband = ct.GEN(gtem.disband, name ="disbanding after level up")
    return ct.AND_P([team_up,gather_items, go_to_totem, drop_items,i_am_ready,wait_for_team_mates, incantation,disband], name="level up sequence")