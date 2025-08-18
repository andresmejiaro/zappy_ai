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
    
    c1 = (rtarget - facing) % 4
    if c1 == 0:
        return []
    if c1 == 1:
        return[ct.Interaction("gauche")]
    if c1 == 2:
        return[ct.Interaction("droite"), ct.Interaction("droite")]
    return [ct.Interaction("droite")]
            
     
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
        
                       
        ### movement in x
        xfacing = facing
        if  displacement[0] > 0:
            xoption = rotate_create(facing, 0)
            xfacing = 0
        elif displacement[0] < 0:
            xoption = rotate_create(facing, 2)
            xfacing = 2
        else:
            xoption = []
            xfacing = facing   
       
        nmovesx = int(np.abs(displacement[0]))
        movesx = list(map(lambda x: ct.Interaction("avance"), range(nmovesx)))
        
        ### movement in y
        if  displacement[1] > 0:
            yoption = rotate_create(facing, 3)
            yfacing = 3
        elif displacement[1] < 0:
            yoption = rotate_create(facing,1)
            yfacing = 1
        else:
            yoption = []
            yfacing = facing

        nmovesy = int(np.abs(displacement[1]))
        movesy = list(map(lambda x: ct.Interaction("avance"), range(nmovesy)))
        
        if len(xoption) < len(yoption): #the one you have turn less
            plan = xoption + movesx + rotate_create(xfacing,yfacing) + movesy
        else:
            plan = yoption + movesy + rotate_create(yfacing,xfacing) + movesx
        
        
        return ct.AND(plan, f"move to plan for target {target}")


# def distace_matrix(self, agent: Agent)
#     def distance(target):
#             position = agent.pos
#             target1 = target + DIRECTIONS[0] * agent.size[0]
#             target2 = target - DIRECTIONS[0] * agent.size[0]
#             target3 = target + DIRECTIONS[1] * agent.size[1]
#             target4 = target - DIRECTIONS[1] * agent.size[1]
#             target5 = target + DIRECTIONS[0] * agent.size[0] + DIRECTIONS[1] * agent.size[1]
#             target6 = target + DIRECTIONS[0] * agent.size[0] - DIRECTIONS[1] * agent.size[1]
#             target7 = target - DIRECTIONS[0] * agent.size[0] + DIRECTIONS[1] * agent.size[1]
#             target8 = target - DIRECTIONS[0] * agent.size[0] - DIRECTIONS[1] * agent.size[1]
#             targets = [target, target1, target2,target3, target4, target5, target6, target7, target8]
#             targets = list(map(lambda x: x - position, targets))
#             displacement = shorstest_vect(targets) 
#             return np.abs(displacement).sum(axis = -1):
#     return np.array([distance(np.array([x,y],shape= self.size)) for x in range(self.size[0]) for y in range(self.size[1]) ])  





# def roam(agent: Agent):
#     r = []
#     nt = random.randint(0,3)
#     for j in range(nt):
#         r.append( ct.Interaction("droite"))
#     for j in range(2*agent.level - 2 + random.randint(0,3)):
#         r.append(ct.Interaction("avance"))
#     r.extend([ct.Interaction("voir") ]) 
#     return ct.AND(actions= r , name="roam master node")



# def roam (agent:Agent):
#     target = agent.pos.copy()
#     nt = random.randint(-2,2)
#     target[0] = (target[0] + nt) % agent.size[0]
#     nt = random.randint(-2,2)
#     target[1] = (target[1] + nt) % agent.size[1]
#     plan = ct.AND([
#         ct.GEN(lambda x: move_to(target,x)),
#         gen_interaction("voir"),
#         gen_interaction("droite"),
#         gen_interaction("voir"),
#         gen_interaction("droite"),
#         gen_interaction("voir"),
#         gen_interaction("droite"),
#         gen_interaction("voir")
#     ], "roam brownian")
#     return plan



def roam(agent: Agent):
    U = agent.uncertanty_mask()
    D = agent.distance_matrix()
    score = U #/ (1.0 + D)**2
    score[agent.pos[0], agent.pos[1]] = -np.inf   # <-- force D>=1
    tx, ty = np.unravel_index(np.argmax(score), score.shape)
    target = np.array([tx, ty], dtype=int)
    r = [ct.GEN(lambda a: move_to(target, a), "roam move to target"),
         ct.Interaction("voir"),gen_interaction("droite"),
         gen_interaction("voir"),
         gen_interaction("droite"),
         gen_interaction("voir"),
         gen_interaction("droite"),
         gen_interaction("voir")]
    return ct.AND(actions=r, name="roam master node infobased")



def marco_polo_screamer(agent: Agent):
    is_everyone_ready = ct.LOGIC(lambda x: len(x.party.party_members_ready) == len(x.party.party_members), name = "Is everyone here?")
    keep_screaming = ct.ALWAYS_F(ct.GEN(gtem.ready_for_incantation, name = "scream so you get here"),
                                 name = "screaming does not make you succeed")
    return ct.OR([is_everyone_ready, keep_screaming], name = "marco polo screamer selector")
    

def marco_polo_step(agent:Agent):
    if agent.party.marco_polo_target is not None:
        target = agent.party.marco_polo_target  
    elif agent.party.sound_direction is not None:
        target = agent.sound_direction(agent.party.sound_direction) + agent.party.pos_at_sound
    else:
        return ct.LOGIC(lambda x: False, "No direction to step")
    print(f"pos:{agent.pos} to:{target}")
    return ct.GEN(lambda x: move_to(target,x),"step towards screamer, marco_polo_step main node")


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
    
    
    
    move = ct.GEN(marco_polo_step, "generator for marco polo step")
    scream = ct.GEN(gtem.ready_for_incantation, name = "scream I arrived")
    step3 = ct.ALWAYS_F(move, "move Success does not mean we are there")
    step2 = ct.OR([ct.AND([am_i_there,scream], "if we are there scream"), step3], "if we are not there move ")
    step1 = ct.OR([ct.AND([do_i_have_direction,step2]),ct.ALWAYS_F(gen_interaction("inventaire"), "fallback marco polo step")],name = "Marco follower main node")

    
    return step1


     

