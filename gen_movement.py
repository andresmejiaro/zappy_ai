#%%from BasicAction import Interaction
from core_behavior_tree import BTNode, LOGIC
import core_behavior_tree as ct
from domain_agent import Agent
import numpy as np
import random 
import gen_teaming as gtem
from gen_common import gen_interaction

DIRECTIONS = list(map(np.array,[[1,0],[0,-1],[-1,0],[0,1]]))
import random 

#%%
def rotate_create(facing:int, rtarget: int)->list[BTNode]:
    facing = facing % 4
    rtarget = rtarget % 4
    
    c1 = (rtarget - facing)
    c2 = -(-rtarget + facing +4) 
    #print(f"c1: {c1} c2:{c2}")
    if abs(c1) >abs(c2):
         c1 = c2
    c2 = abs(c1)
    if c1 == 0:
        return []
    if c1 > 0:
         return list(map(lambda x: ct.Interaction("gauche"), range(c2)))   
    if c1 < 0:
         return list(map(lambda x: ct.Interaction("droite"), range(c2)))   
        
     
#%%
def shorstest_vect(array):
    indmin = np.array(list(map(lambda x: np.sum(np.abs(x)), array)))
    indmin = np.argmin(indmin)
    return array [indmin]


def move_to(target: np.array, agent:Agent, name: None|str = None) -> BTNode:
        #print(f"moving to: {target}")
        if name is None:
             name =f"move_to->{target}"
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
       
        nmoves = int(np.abs(displacement[0]))
        w = map(lambda x: ct.Interaction("avance"), range(nmoves))
        plan.extend(list(w))

        ### movement in y
        if  displacement[1] > 0:
            plan += rotate_create(xfacing, 3)
        elif displacement[1] < 0:
            plan += rotate_create(xfacing,1)
        
        nmoves = int(np.abs(displacement[1]))
        w = map(lambda x: ct.Interaction("avance"), range(nmoves))
        plan.extend(list(w))
        return ct.AND(plan, "move to plan")

def roam(agent: Agent):
    r = [ct.Interaction("voir"), ct.Interaction("droite"), ct.Interaction("voir") , ct.Interaction("droite") , ct.Interaction("voir") , ct.Interaction("droite") , ct.Interaction("voir") ] 
    nt = random.randint(0,3)
    for j in range(nt):
        r.append( ct.Interaction("droite"))
    for j in range(2*agent.level - 2 + random.randint(0,3)):
        r.append(ct.Interaction("avance"))
    return ct.AND(actions= r , name="roam Generated")



def marco_polo_screamer(agent: Agent):
    is_everyone_ready = ct.LOGIC(lambda x: len(x.party.party_members_ready) == len(x.party.party_members), name = "Is everyone here?")
    keep_screaming = ct.ALWAYS_F(ct.GEN(gtem.ready_for_incantation, name = "scream so you get here"),
                                 name = "screaming does not make you succeed")
    return ct.OR([is_everyone_ready, keep_screaming], name = "marco polo screamer selector")
    

def marco_polo_step(agent:Agent):
    if agent.party.sound_direction is not None:
        target = agent.sound_direction(agent.party.sound_direction) + agent.pos
    else:
        return ct.LOGIC(lambda x: False, "No direction to step")
    print(f"pos:{agent.pos} to:{target}")
    return ct.GEN(lambda x: move_to(target,x),"step towards screamer")


def marco_polo_follower(agent: Agent):
     
    do_i_have_direction = ct.LOGIC(lambda x: x.party.sound_direction is not None, name = "do i have direction")
    
    
    
    ### am I there is more layered than before le old sound_direction is zero does not cut it 
    is_the_it_inside_the_house = ct.LOGIC(lambda x: x.party.sound_direction == 0, name = "is the direction 0?")
    is_anyone_here = ct.LOGIC(lambda a: a.objects[a.pos[0]][a.pos[1]].count("player")  > 0 , "is_anyone_here")
    am_i_there = ct.GEN(lambda x:ct.AND_P([is_the_it_inside_the_house,
                                  gen_interaction("voir"),
                                  is_anyone_here,
                                  is_the_it_inside_the_house]
                                    ,"am i there logic"
                                ),
                                "am I there generator (for reset)"
                        )
    
    
    
    move = ct.GEN(marco_polo_step)
    scream = ct.GEN(gtem.ready_for_incantation, name = "scream I arrived")
    step3 = ct.ALWAYS_F(move, "move Success does not mean we are there")
    step2 = ct.OR([ct.AND([am_i_there,scream], "if we are there scream"), step3], "if we are not there move ")
    step1 = ct.OR([ct.AND([do_i_have_direction,step2]),ct.ALWAYS_F(gen_interaction("inventaire"))],name = "If we don't know ")

    
    return step1


     

