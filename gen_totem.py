from core_behavior_tree import LOGIC, BTNode, MSG, GEN
from core_bt_interactions import Interaction
from gen_movement import move_to
import numpy as np
from domain_agent import Agent
from gen_common import gen_interaction
from gen_gathering import pick_up_multiple, drop

def biggest_pile(agent: Agent,resource: str):
    
    count = [[np.array([x,y]),agent.objects[x][y].count(resource)] for x in range(agent.size[0]) for y in range(agent.size[1])] 
    max_value = max([x[1] for x in count] )
    largest_piles = [k[0] for k in count if k[1] == max_value]
    return max_value,largest_piles

def mark_totem_gen(agent: Agent, resource: str)-> BTNode:
    print(f"Planning to set Totem at {agent.totem_pos}")
    plan = GEN(lambda x: pick_up_multiple(x, {resource: 5} )) & GEN(lambda x: move_to(agent.totem_pos, x)) & Interaction("pose",resource, 5) & gen_interaction("voir") & MSG("Done with Totem")
    return plan
    return LOGIC(lambda x: False)


def update_mark(agent:Agent, resource):
    agent.totem_size, w = biggest_pile(agent, resource)
    agent.totem_pos = w[0]
    print(f"evaluated totem position at {agent.totem_pos}")
    return True