from domain_agent import Agent
import  core_behavior_tree as ct
from gen_common import gen_interaction
from gen_movement import shorstest_vect, move_to
import gen_movement as gmov
import numpy as np
import random
import gen_teaming as gtem

def inventory_selector(agent, indivudual = None)->dict:
    #what inventory to use
    if indivudual is not None and agent.level >= 2:
        agent.update_level_inventory()
        inv = agent.level_inventory
    elif indivudual == "ready":
        inv = agent.update_ready_inventory()
    else:
        inv = agent.inventory
    
    return inv


def drop(agent: Agent,inventory: dict) -> ct.BTNode:
    actions = []
    for key, value in inventory.items():
        n_to_drop = min(value, agent.inventory[key])
        actions2 = map(lambda x: gen_interaction("pose",x),[key] * int(n_to_drop))
        actions.extend(actions2)
    if len(actions) > 0:
        to_return = ct.AND_P(actions, name=f"drop stuff" )
        return to_return
    return ct.LOGIC(lambda x: True, "True")


def drop_drone(agent: Agent,) -> ct.BTNode:
    all_inv = agent.inventory.copy()
    all_inv["nourriture"] = 0 # agent.queen hungry
    food_to_remove = int(max(0,agent.inventory["nourriture"] - 5))*(agent.queen_food < 20)

    food_drop = [gen_interaction("pose","nourriture") ] * food_to_remove
    food_drop.append(drop(agent,all_inv))

    return ct.AND_P(food_drop)
    


def closest_resource(agent: Agent, resource: str):
    """
    Finds the coordinate of the nearest known resource 
    """
    if agent.marco_polo_target is None:
        mpt = np.array([-99,-99])
    else:
        mpt = agent.marco_polo_target.copy()

    found = [np.array([x,y]) for x in range(agent.size[0]) for y in range(agent.size[1]) if resource in agent.objects[x][y] and not np.array_equal(np.array([x,y]), mpt)]
    if len(found) == 0:
        return (None,None)
    distances = [gmov.move_to_distance(x,agent) for x in found]
    idx  = min(range(len(distances)), key= distances.__getitem__)
    n = min(distances)

    return (n,found[idx])


def pick_up(agent: Agent, resource: str, just_go = False) -> ct.BTNode:
    def pick_up_plan(agent: Agent):
        _,x = closest_resource(agent, resource)
        if x is None or len(x) == 0 or np.array_equal(agent.marco_polo_target, x):
            return ct.LOGIC(lambda x: False)
        actions = move_to(x, agent)
        if just_go:
            return actions
        from master_plan import if_else_node, false_node
        safety = if_else_node(lambda x: np.array_equal(x.pos,x.marco_polo_target),false_node,ct.Interaction("prend",resource) )
        actions = [actions,safety , ct.Interaction("inventaire")]
        return ct.AND(actions, name = f"pick up {resource}")  
    return  ct.OR([ct.GEN(pick_up_plan), 
                   ct.ALWAYS_F(ct.GEN(gmov.roam))])

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
    w = map(lambda x: ct.GEN(lambda y: pick_up(y, x), name = f"pick_up call on "), look4)
    w = list(w)
    if len(w) == 0:
        return ct.LOGIC(lambda x: True, "True")
    z = ct.OR(w, name="pick_up_multiple")
    return ct.AND_P([z, ct.GEN(gtem.share_inventory, "share inventory generator pick up multiple")], name = f"pick up multiple main node ")

def do_i_have_inventory(agent, resources: dict, individual = None)->bool:
    inv = inventory_selector(agent, individual)
    for key, value in resources.items():
        if inv.get(key,0) < value:
            return False
    return True 

def gather(agent,resources: dict, individual = False)->ct.BTNode:
    inv = inventory_selector(agent, individual)
    check = ct.LOGIC(lambda x: do_i_have_inventory(x,resources, individual), name = "gather check Inv")
    gather_node = ct.ALWAYS_F(ct.GEN(lambda x: pick_up_multiple(x,resources), name = "gather collector")) 
    return ct.OR([check,gather_node], name = f"gather: inventory:")

def resource_choose(resources: dict, n = 3)-> dict:
        total = sum(resources.values())
        n = min(n, total)
        list_form =[]
        for k,v in resources.items():
            list_form.extend([k]*v)
        random.shuffle(list_form)
        list_form = list_form[0:n]
        result = {}
        for x in list_form:
            if result.get(x,0) == 0:
                result[x] = 1
            else:
                result[x] +=1
        #return result
        return resources

# def drone_gather(agent)->ct.BTNode:
#     choice = resource_choose(agent.needs)
#     choice["nourriture"] = 0 # + self.hungry + self.queen_hungry
#     plan = gather(agent,choice,individual=True)
#     fp = []
#     fp.append(plan)
#     fp.extend([ct.GEN(lambda x: pick_up(x, "nourriture"))])
#     return ct.AND_P(fp)

def level_up_party_size(lv):
    ps =[1,2,2,4,4,6,6,1]
    return ps[lv-1]




def level_up_reqs(aclv):
    lreq =[{"linemate":1}, #1->2
           {"linemate":1, "deraumere":1, "sibur":1}, #2->3
           {"linemate":2,"sibur":1,"phiras":2}, #3->4
           {"linemate":1, "deraumere":1,"sibur":2,"phiras":1},#4->5
           {"linemate":1, "deraumere":2,"sibur":1,"mendiane":3}, #5->6
           {"linemate":1, "deraumere":2,"sibur":3,"phiras":1}, # 6->7
           {"linemate":2, "deraumere":2,"sibur":2, "mendiane":2,"phiras":2,"thystame":1}, #7->8,
           {} # 8->9 to avoid crash at endgame
        
    ]
    return lreq[aclv - 1]

def level_up_gather_items(agent):
    """
    Wrapper for reqs based on level 
    """
    reqs = level_up_reqs(agent.level)    
    gather_items =ct.O_ON_F( ct.GEN(lambda x: gather(x, reqs), "level up gather"), "F means gathering")
    return gather_items

def level_up_meetup():
    """
    Sets up the logic for the meetup phase it separates the roles into lone wolf AKA 
    don't do this, screamer the one they will get to, and follower the one who will get 
    there. The logic on how to do that is on the generators
    """
    def am_I_screamer_helper(agent: Agent):
        for key, value in agent.ppl_lv.items():
            if key > agent.name and value == agent.level:
                return False
        return True
    
    



    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    am_i_screamer = ct.LOGIC(am_I_screamer_helper, name = "am I the party Leader")
    
    screamer_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_screamer, name = "generating screaming logic"), name = "don't fail just try again")
    follower_logic = ct.O_ON_F(ct.GEN(gmov.marco_polo_follower,reset_on_failure=False, name = "generating follower logic"), name = "don't fail just try again")
    marco_polo = ct.OR([am_i_lone_wolf,
                            ct.AND([am_i_screamer, screamer_logic], name = "marco polo_role selector AND"), 
                            follower_logic], name = "marco polo role selector OR, level up meetup master node")
   

    return marco_polo


def level_up_incantation(agent):
    am_i_lone_wolf = ct.LOGIC(lambda x: x.level <= 1, name = "am_i_lone_wolf")
    reqs = level_up_reqs(agent.level)
    drop_items = ct.GEN(lambda x: drop(x,reqs), name= "level up drop")
    check_party_before_level_up = ct.OR([ct.AND_P([am_i_lone_wolf,drop_items],"check party before lvl up Selector AND"),
                                         check_quorum(agent)], "check party before lvl up Selector OR")     
    incantation = gen_interaction("incantation")
    incantation_logic = ct.AND_P([check_party_before_level_up,incantation], name = "Drop and Incantate, level up incantation master node")
    set_timeout = ct.LOGIC( lambda x: (setattr(x,"timeout",x.turn),True)[1], "timeout for incantation")
    il2 = ct.O_ON_F(ct.AND_P([set_timeout, incantation_logic], "timeout lead to incantation logic"), "so only to makes it fail")
    fail = ct.LOGIC(lambda x: (x.level_reset(), False)[1],"reset parameters at fail")

    return ct.OR([ct.AND([ct.LOGIC(lambda x: x.timeout is None or x.turn - x.timeout <150, "gate"), il2],"and il2"),fail], "level up incantation main node")


def item_ground_count(agent,x,y,reqs:dict)->bool:
    for key, value in reqs.items():
        if agent.objects[x][y].count(key) < value:
            return False
    return True



def check_quorum(agent):
    reqs = level_up_reqs(agent.level)
    
 
    voir_y_inventory = ct.AND_P([gen_interaction("voir"),gen_interaction("inventaire")],"voir and inventaire loop")


    is_there_enough_ppl = ct.OR([
        ct.LOGIC(lambda l: l.objects[l.pos[0]][l.pos[1]].count("player") >= level_up_party_size(l.level) , name = "can I see ppl here?"),
        ct.ALWAYS_F(voir_y_inventory, f"voir not validate problem: not enough ppl problem")
    ])
    are_the_items_in_the_ground = ct.OR([
        ct.LOGIC(lambda l: item_ground_count(l,l.pos[0],l.pos[1],reqs), "is the stuff on the ground?"),
        ct.ALWAYS_F(voir_y_inventory, f"voir not validate problem: not enough stuff")
    ])

    return ct.AND_P([is_there_enough_ppl,
              are_the_items_in_the_ground
              ], "chack quorum master node")

def level_up(agent):
    """
    
    """ 
  
    announce = ct.AND([ct.LOGIC(lambda x: x.name not in x.ppl_lv, "should I share inv"),
                      ct.ALWAYS_F(ct.GEN(gtem.share_inventory, "sharing inv"))], "share inv to be seen")


    
    main_plan = ct.AND_P([level_up_gather_items(agent),
                              level_up_meetup(),
                              level_up_incantation(agent)], name= "level up plan")

    level_up_plan = ct.OR([announce,
            main_plan
    ], "level_up_plan main node")                         
    
    return level_up_plan


   