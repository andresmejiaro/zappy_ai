from ActionTree import LOGIC, Action
from MovementPlans import move_to, shorstest_vect, route_torus
import numpy as np
from Agent import Agent
from action_generators import gen_basic

def biggest_pile(agent: Agent,resource: str):
    
    count = [[np.array([x,y]),agent.objects[x][y].count(resource)] for x in range(agent.size[0]) for y in range(agent.size[1])] 
    max_value = max([x[1] for x in count] )
    largest_piles = [k[0] for k in count if k[1] == max_value]
    return max_value,largest_piles

def mark_totem_gen(agent: Agent, resource: str)-> Action:
    size, position = biggest_pile(agent, resource)
    for i, item in enumerate(position):
        if np.array_equal(item,agent.totem_pos):
            del position[i]
            break
    if size >= agent.totem_size and len(position) > 0 and size > 0 and agent.inventory[resource]>=1:
        plan = move_to(position[0], agent) & gen_basic("pose", resource) & LOGIC(lambda x:update_mark(agent,resource)) & gen_basic("voir")
        return plan
    return LOGIC(lambda x: False)


def update_mark(agent:Agent, resource):
    agent.totem_size, w = biggest_pile(agent, resource)
    agent.totem_pos = w[0]
    return True