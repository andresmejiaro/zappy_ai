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

gather_and_come_back = ct.GEN(lambda x:
                              ct.AND_P([
                                ct.GEN(lambda x: ggat.drone_gather(x)),
                                ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),
                                ct.GEN(lambda x: ggat.drop_drone(x)),
                              ])
                              )


find_queen_or_gather = if_else_node(lambda x: x.marco_polo_target is None, ct.GEN(gmov.marco_polo_follower),gather_and_come_back , "find_queen_or_gather")


mark_me_alive = if_else_node(lambda x: x.name not in x.ppl_lv.keys(), ct.GEN(gtem.share_inventory),false_node, "mark me alive")

update_needs = ct.GEN(gtem.ready_for_incantation, "update_needs")

queen_logic = loop_node_non_blocking([gen_interaction("voir"), update_needs],"queen logic")

drone_logic = ct.OR([find_queen_or_gather], "drone logic main node")

role_selector = if_else_node(lambda x: x.name == max(x.ppl_lv.keys()),queen_logic, drone_logic, "role selector node")


master_plan = ct.OR([
  mark_me_alive,
  role_selector,
  gen_interaction("inventaire")
])