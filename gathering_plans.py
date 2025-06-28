from Agent import Agent
from ActionTree import Action, Basic
from action_generators import pick_up_multiple, gen_basic
from functools import reduce

def gather(agent: Agent,inventory) -> Action:
    inventory2 = [x for x in inventory if agent.inventory_group[x] == 0]
    if len(inventory) > 0:
        return pick_up_multiple(agent, inventory2)
    

def drop(agent: Agent,inventory) -> Action:
    actions = map(lambda x: gen_basic("pose",x),inventory)
    to_return = reduce(lambda x,y: x & y,actions)
    return to_return

