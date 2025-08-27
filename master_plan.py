import core_behavior_tree as ct
import gen_movement as gmov
import gen_gathering as ggat
from gen_common import gen_interaction
import numpy as np
import gen_teaming as gtem
import random 
from typing import Callable
from domain_agent import Agent



def if_else_node(cond: Callable[[Agent], bool] , pos:ct.BTNode, neg: ct.BTNode, comment = "")-> ct.BTNode:
  """
  Creates if else condition in nodes
  """
  return  ct.OR([
        ct.AND([
            ct.LOGIC(cond,"if_else_logic "+ comment),
                pos
                ],"if_else_and pos" + comment),
                ct.AND([
            ct.LOGIC(lambda x: not cond(x),"if_else_logic "+ comment),
                neg
                ],"if_else_and neg" + comment) 
           
         ], "if_else_or "+comment)


def loop_node_blocking(loop_list: list[ct.BTNode], comment= ""):
  """
  loops though the list needs S to move to the next item 
  """
  return ct.GEN(
    lambda _: ct.AND_P(loop_list, f"loop_node_blocking AND_P {comment}")
  , f"looṕ_node_blocking generator {comment}")


def loop_node_non_blocking(loop_list: list[ct.BTNode], comment= ""):
  """
  loops though the list attempts everything once and moves on. 
  """
  loop_list2 = [ct.ALWAYS_S(x, f"looṕ_node_non_blocking block removal {comment}") for x in loop_list]

  return ct.GEN(
    lambda _: ct.AND_P(loop_list2, f"loop_node_non_blocking AND_P {comment}")
  , f"looṕ_node_non_blocking generator {comment}")

false_node = ct.LOGIC(lambda _: False, "false node")

#roam_and_come_back = ct.GEN(lambda x: ct.AND([ct.GEN(lambda x: gmov.move_to(np.array([9,9]),x)), ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x))]), "roam and come back")

tog = ggat.level_up_reqs(7)

# gather_and_come_back = ct.GEN(lambda x:
#                               ct.AND_P([
#                                 ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),
#                                 ct.GEN(lambda x: ggat.drop_drone(x)),
#                               ])
#                               )

def gathering(agent:Agent):
  # information 
  distance_home = gmov.move_to_distance(agent.marco_polo_target,agent)
  resource_distances = {stone:ggat.closest_resource(agent,stone)[0] for stone in agent.inventory.keys()}
  looking_for = agent.needs
  stones_colected = sum(agent.inventory.values()) - agent.inventory["nourriture"]

  considered = {stone:distance for stone,distance in resource_distances.items() if stone in looking_for and looking_for[stone] > 0 and distance is not None}

  if len(considered) == 0 and stones_colected < 3:
    return ct.GEN(gmov.roam)

  closest_resource = [s for s,d in considered.items() if d == min(considered.values())]
  
  if len(considered) > 0  and (stones_colected < 3 or considered[closest_resource[0]] < distance_home):
    return ct.GEN(lambda x: ggat.pick_up(x,closest_resource[0]))
  else:
    return ct.AND_P([ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),ct.GEN(lambda x: ggat.drop_drone(x))])




gather_and_come_back = ct.O_ON_F(ct.GEN(gathering))




level_up_process = ct.GEN(lambda x:
                              ct.AND_P([
                                ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),
                                ct.O_ON_F(ct.GEN(ggat.check_quorum)),
                                gen_interaction("incantation"),
                              ])
                              )

level_up = if_else_node(lambda x: x.level_up and x.marco_polo_target is not None , level_up_process, false_node)


find_queen_or_gather = if_else_node(lambda x: x.marco_polo_target is None or x.marco_polo_confirm < 3, ct.GEN(gmov.marco_polo_follower),gather_and_come_back , "find_queen_or_gather")


fork = if_else_node(lambda x: x.fork, gen_interaction("fork"), false_node)



mark_me_alive = if_else_node(lambda x: x.name not in x.ppl_lv.keys() or x.name not in x.ppl_timeouts or  x.turn - x.ppl_timeouts[x.name] > 550, ct.GEN(gtem.share_inventory),false_node, "mark me alive")

update_needs = ct.GEN(gtem.ready_for_incantation, "update_needs")

queen_logic = loop_node_non_blocking([gen_interaction("voir"), update_needs],"queen logic")

drone_logic = ct.OR([fork, level_up, find_queen_or_gather], "drone logic main node")

role_selector = if_else_node(lambda x: x.name == max(x.ppl_lv.keys()),queen_logic, drone_logic, "role selector node")


master_plan = ct.OR([
  mark_me_alive,
  role_selector,
  gen_interaction("inventaire")
], "master plan")