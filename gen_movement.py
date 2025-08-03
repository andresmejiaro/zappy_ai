#%%from BasicAction import Interaction
from core_behavior_tree import BTNode, LOGIC
from core_bt_interactions import Interaction
from domain_agent import Agent
import numpy as np
from functools import  reduce
import random 

DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))

#%%
def rotate_create(facing:int, rtarget: int)->list[BTNode]:
    facing = facing % 4
    rtarget = rtarget % 4
    
    c1 = (rtarget - facing)
    c2 = -(-rtarget + facing +4) 
    print(f"c1: {c1} c2:{c2}")
    if abs(c1) >abs(c2):
         c1 = c2
    c2 = abs(c1)
    if c1 == 0:
        return []
    if c1 > 0:
         return list(map(lambda x: Interaction("gauche"), range(c2)))   
    if c1 < 0:
         return list(map(lambda x: Interaction("droite"), range(c2)))   
        
     
#%%
def shorstest_vect(array):
    indmin = np.array(list(map(lambda x: np.sum(np.abs(x)), array)))
    indmin = np.argmin(indmin)
    return array [indmin]


def move_to(target: np.array, agent:Agent) -> BTNode:
        print(f"moving to: {target}")
        facing = agent.facing
        position = agent.pos
        target1 = target + DIRECTIONS[0] * agent.size[0]
        target2 = target - DIRECTIONS[0] * agent.size[0]
        target3 = target + DIRECTIONS[1] * agent.size[1]
        target4 = target - DIRECTIONS[1] * agent.size[1]
        target5 = target + DIRECTIONS[0] * agent.size[0] + DIRECTIONS[1] * agent.size[1]
        target6 = target + DIRECTIONS[0] * agent.size[0] - DIRECTIONS[1] * agent.size[1]
        target7 = target - DIRECTIONS[0] * agent.size[0] + DIRECTIONS[1] * agent.size[1]
        target8 = target - DIRECTIONS[0] * agent.size[0] - DIRECTIONS[1] * agent.size[1]
        targets = [target, target1, target2,target3, target4, target5, target6, target7, target8]
        targets = list(map(lambda x: x - position, targets))
        displacement = shorstest_vect(targets) 
        if np.linalg.norm(displacement) == 0:
             return LOGIC(lambda x: True)  
        plan = []
        ### movement in x
        xfacing = facing
        if  displacement[0] > 0:
            plan += rotate_create(facing, 0)
            xfacing = 0
        elif displacement[0] < 0:
            plan += rotate_create(facing, 2)
            xfacing = 2   
       
        nmoves = np.abs(displacement[0])
        w = map(lambda x: Interaction("avance"), range(nmoves))
        plan.extend(w)

        ### movement in y
        if  displacement[1] > 0:
            plan += rotate_create(xfacing, 3)
        elif displacement[1] < 0:
            plan += rotate_create(xfacing,1)
        
        nmoves = np.abs(displacement[1])
        w = map(lambda x: Interaction("avance"), range(nmoves))
        plan.extend(w)

        return reduce( lambda x,y: x & y, plan)

def roam(agent: Agent):
    r = Interaction("voir") & Interaction("droite") & Interaction("voir") & Interaction("droite") & Interaction("voir") & Interaction("droite") & Interaction("voir") 
    nt = random.randint(0,3)
    for j in range(nt):
        r = r & Interaction("droite")
    for j in range(2*agent.level - 2 + random.randint(0,3)):
        r = r & Interaction("avance")
    return r