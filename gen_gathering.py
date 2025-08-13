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
    return ct.LOGIC(lambda x: True, "True")

def closest_resource(agent: Agent, resource: str):
    """
    Finds the coordinate of the nearest known resource 
    """

    found = [np.array([x,y]) for x in range(agent.size[0]) for y in range(agent.size[1]) if resource in agent.objects[x][y]]
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
    w = map(lambda x: ct.GEN(lambda y: pick_up(y, x), name = f"pick_up call on {x}"), look4)
    w = list(w)
    if len(w) == 0:
        return ct.LOGIC(lambda x: True, "True")
    z = ct.OR(w, name="pick_up_multiple")
    if agent.party.party_name is None:
        return z
    return ct.AND_P([z, ct.GEN(gtem.share_inventory, "share inventory generator")], name = "sharing after finding")

def do_i_have_inventory(agent, resources: dict, individual = False)->bool:
    inv = inventory_selector(agent, individual)
    for key, value in resources.items():
        if inv.get(key,0) < value:
            return False
    return True 

def gather(agent,resources: dict, individual = False)->ct.BTNode:
    check = ct.LOGIC(lambda x: do_i_have_inventory(x,resources, individual), name = "gather check Inv")
    gather_node = ct.ALWAYS_F(ct.GEN(lambda x: pick_up_multiple(x,resources), name = "gather collector"))
    roam = ct.ALWAYS_F(ct.GEN(gmov.roam, name="gather roam"),
                       name = "roam fallback that can't suceed")
    return ct.OR([check,gather_node,roam], name = f"gather {resources}")

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


# logic1 = lambda x: x.party.party_name is None or len(x.party.party_members_ready) == len(x.party.party_members)


# def level_up(agent):
#     reqs = level_up_reqs(agent.level)
#     do_i_need_team = ct.LOGIC(lambda x: x.level <= 1, name = "do I need to team up")
#     team_up = ct.OR([do_i_need_team, gtem.teaming], name = "level up teaming up")
#     marco_polo= ct.OR([do_i_need_team,ct.GEN(gmov.marco_polo, name = "marco polo")], name = "no team no marco polo")
#     marco_polo2 = ct.O_ON_F(marco_polo)
#     gather_items = ct.OR([ct.GEN(lambda x: gather(x, reqs), "level up gather"),ct.ALWAYS_F(ct.GEN(gmov.roam))])
#     #i_am_ready = ct.GEN(gtem.ready_for_incantation)
#     drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
#     wait_for_team_mates = ct.OR([ct.LOGIC(logic1),ct.ALWAYS_F(ct.GEN(gtem.ready_for_incantation))])
#     incantation = gen_interaction("incantation")
#     disband = ct.GEN(gtem.disband, name ="disbanding after level up")
#     return ct.AND_P([team_up,gather_items, marco_polo2,wait_for_team_mates,drop_items, incantation,disband], name="level up sequence")


def level_up_fail_conditions():
    """
    WIP
    """
    return ct.LOGIC(lambda x: True, "True")


def level_up_team_up():
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    team_up = ct.OR([am_i_lone_wolf, gtem.teaming], name = "level up teaming up")
    return team_up

def level_up_gather_items(agent):
    """
    Uses or to decide if it can't see an item then it roams. 
    """
    reqs = level_up_reqs(agent.level)    
    gather_items = ct.OR(
        [ct.GEN(lambda x: gather(x, reqs), "level up gather"),
         ct.ALWAYS_F(ct.GEN(gmov.roam, name = "level up gathering roam"),
                     name = "guard so only first cond can say this is done")])
    return gather_items

def level_up_meetup():
    """
    Sets up the logic for the meetup phase it separates the roles into lone wolf AKA 
    don't do this, screamer the one they will get to, and follower the one who will get 
    there. The logic on how to do that is on the generators
    """
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    am_i_party_leader = ct.LOGIC(lambda x: x.party.party_role == 3, name = "am I the party Leader")
    
    screamer_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_screamer, name = "ng screaming logic"), name = "don't fail just try again")
    follower_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_follower, name = "generating follower logic"), name = "don't fail just try again")
    marco_polo = ct.OR([am_i_lone_wolf,
                            ct.AND([am_i_party_leader, screamer_logic], name = "marco polo_role selector AND"), 
                            follower_logic], name = "marco polo role selector OR")
    return marco_polo

def level_up_cleanup():
    return ct.GEN(gtem.disband, name ="disbanding level up cleanup")

def level_up_incantation(agent):
    reqs = level_up_reqs(agent.level)
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
    incantation = gen_interaction("incantation")
    return ct.AND_P([drop_items,incantation], name = "Drop and Incantate")
    

def level_up(agent):
    """
    level up fail conditions return Status.F if the plan should be regenerated true 
    if it needs to go on.
    """
    level_up_plan = ct.O_ON_F(ct.AND_P([level_up_team_up(),
                              level_up_gather_items(agent),
                              level_up_meetup(),
                              level_up_incantation(agent),
                              level_up_cleanup()
                              ], name= "level up plan"),
                              name = "guard failure means working for true failure see fail conditions")
    
    return ct.OR([
        ct.AND([level_up_fail_conditions() ,
                level_up_plan], name = "proceed unless hard fail"),
          level_up_cleanup()
          ], name = "level up fail fallback")


