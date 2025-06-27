from Agent import Agent
from ActionTree import Action
from action_generators import pick_up_multiple

def gather(agent: Agent,inventory) -> Action:
    inventory2 = [x for x in inventory if agent.inventory_group[x] == 0]
    if len(inventory) > 0:
        return pick_up_multiple(agent, inventory2)
    
