import numpy as np
from MovementPlans import shorstest_vect



def closest_resource(agent: Agent, resource: str):

    found = [np.array([x,y]) for x in range(agent.size[0] for y in range(agent.size[1]) \
                            if resource in np.objets[x][y])]
    
    if len(found) == 0:
        return None
    
    distances = [agent.pos - x for x in found]
    return -shorstest_vect(distances) + agent.pos


