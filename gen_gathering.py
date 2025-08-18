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
    return ct.AND_P([z, ct.GEN(gtem.share_inventory, "share inventory generator pick up multiple")], name = f"pick up multiple main node inv:{inv}")

def do_i_have_inventory(agent, resources: dict, individual = False)->bool:
    inv = inventory_selector(agent, individual)
    for key, value in resources.items():
        if inv.get(key,0) < value:
            return False
    return True 

def gather(agent,resources: dict, individual = False)->ct.BTNode:
    inv = inventory_selector(agent, individual)
    check = ct.LOGIC(lambda x: do_i_have_inventory(x,resources, individual), name = "gather check Inv")
    gather_node = ct.ALWAYS_F(ct.GEN(lambda x: pick_up_multiple(x,resources), name = "gather collector"))
    roam = ct.ALWAYS_F(ct.GEN(gmov.roam, name="gather roam"),
                       name = "roam fallback that can't suceed")
    print(f"gather: {resources} inventory:{inv}")
    return ct.OR([check,gather_node,roam], name = f"gather: {resources} inventory:{inv}")

def level_up_reqs(aclv):
    lreq =[{"linemate":1}, #1->2
           {"linemate":1, "deraumere":1, "sibur":1}, #2->3
           {"linemate":2,"sibur":1,"phiras":2}, #3->4
           {"linemate":1, "deraumere":1,"sibur":2,"phiras":1},#4->5
           {"linemate":1, "deraumere":2,"sibur":1,"mendiane":3}, #5->6
           {"linemate":1, "deraumere":2,"sibur":3,"phiras":1}, # 6->7
           {"linemate":2, "deraumere":2,"sibur":2, "mendiane":2,"phiras":2,"thystame":1} #7->8
    ]
    return lreq[aclv - 1]



def level_up_fail_conditions():
    """
    WIP
    """
     
    incantation_ko = ct.LOGIC(lambda x: not x.party.incantation_failed, "level up failed: incantation failed")
    dead_party_member = ct.LOGIC(lambda x: not x.party.dead_member, "anyone died?")
    too_long_to_lvl_up = ct.LOGIC(lambda x: x.turn - x.party.party_join_timeout < 2500)
    too_long_to_put_stuff_down = ct.LOGIC(lambda x: x.turn - x.party.pre_incantation_ts < 70)
    checker_list = ct.AND([incantation_ko, dead_party_member, too_long_to_lvl_up],"level_up_fail_conditions main node")

    return checker_list


def level_up_team_up():
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    team_up = ct.OR([am_i_lone_wolf, gtem.teaming], name = "level up team up master node")
    return team_up

def level_up_gather_items(agent):
    """
    Uses or to decide if it can't see an item then it roams. 
    """
    reqs = level_up_reqs(agent.level)    
    gather_items = ct.OR(
        [ct.GEN(lambda x: gather(x, reqs), "level up gather"),
         ct.ALWAYS_F(ct.GEN(gmov.roam, name = "level up gathering roam"),
                     name = "guard so only first cond can say this is done, level up gather master node")])
    return gather_items

def level_up_meetup():
    """
    Sets up the logic for the meetup phase it separates the roles into lone wolf AKA 
    don't do this, screamer the one they will get to, and follower the one who will get 
    there. The logic on how to do that is on the generators
    """
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    am_i_party_leader = ct.LOGIC(lambda x: x.party.party_role == 3, name = "am I the party Leader")
    
    screamer_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_screamer, name = "generating screaming logic"), name = "don't fail just try again")
    follower_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_follower,reset_on_failure=False, name = "generating follower logic"), name = "don't fail just try again")
    marco_polo = ct.OR([am_i_lone_wolf,
                            ct.AND([am_i_party_leader, screamer_logic], name = "marco polo_role selector AND"), 
                            follower_logic], name = "marco polo role selector OR, level up meetup master node")
    return marco_polo

def level_up_cleanup():
    return ct.GEN(gtem.disband, name ="disbanding level up cleanup level_up_cleanup master")

def level_up_incantation(agent):
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    reqs = level_up_reqs(agent.level)
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
    flag = ct.LOGIC(lambda x: (setattr(x.party,"pre_incantation_ts" , x.turn), True)[1])    
    check_party_before_level_up = ct.OR([ct.AND_P([am_i_lone_wolf,drop_items,flag],"check party before lvl up Selector AND"),
                                         check_quorum(agent)], "check party before lvl up Selector OR")     
    incantation = gen_interaction("incantation")
    return ct.AND_P([check_party_before_level_up,incantation], name = "Drop and Incantate, level up incantation master node")
    

def item_ground_count(agent,x,y,reqs:dict)->bool:
    for key, value in reqs.items():
        if agent.objects[x][y].count(key) < value:
            return False
    return True



def check_quorum(agent):
    reqs = level_up_reqs(agent.level)
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
 

    is_there_enough_ppl = ct.OR([
        ct.LOGIC(lambda l: l.objects[l.pos[0]][l.pos[1]].count("player") >= l.party.party_size - 1, name = "can I see ppl here?"),
        ct.ALWAYS_F(gen_interaction("voir"), "voir not validates problem")
    ])
    are_the_items_in_the_ground = ct.OR([
        ct.LOGIC(lambda l: item_ground_count(l,l.pos[0],l.pos[1],reqs), "is the stuff on the ground?"),
        ct.ALWAYS_F(gen_interaction("voir"), "voir not validates problem")
    ])

    return ct.AND_P([is_there_enough_ppl,
              drop_items,
              are_the_items_in_the_ground
              ], "chack quorum master node")

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
          ], name = "level up fail fallback, level up master node")


