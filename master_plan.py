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

# gather_and_come_back = ct.GEN(lambda x:find_
#                               ct.AND_P([
#                                 ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),
#                                 ct.GEN(lambda x: ggat.drop_drone(x)),
#                               ])
#                               )


def do_i_roam(agent: Agent):
  resource_distances = {stone:ggat.closest_resource(agent,stone)[0] for stone in agent.inventory.keys()}
  looking_for = agent.needs
  considered = {stone:distance for stone,distance in resource_distances.items() if stone in looking_for and looking_for[stone] > 0 and distance is not None}
  stones_colected = sum(agent.inventory.values()) - agent.inventory["nourriture"]
  
  return len(considered) == 0 and stones_colected < 3 and agent.inventory["nourriture"] > 10


def do_i_pick_something(agent: Agent):
  if agent.queen_fishing:
    return True
  if agent.marco_polo_target is None:
    return True
  is_queen_hungry_and_can_feed = agent.inventory["nourriture"] > 13 and agent.queen_food < 10
  if is_queen_hungry_and_can_feed:
    return False
  distance_home = gmov.move_to_distance(agent.marco_polo_target,agent)
  resource_distances = {stone:ggat.closest_resource(agent,stone)[0] for stone in agent.inventory.keys()}
  looking_for = agent.needs
  considered = {stone:distance for stone,distance in resource_distances.items() if stone in looking_for and looking_for[stone] > 0 and distance is not None}
  stones_colected = sum(agent.inventory.values()) - agent.inventory["nourriture"]
  closest_resource = [s for s,d in considered.items() if d == min(considered.values())]  
  away_from_home = not np.array_equal(agent.pos,agent.marco_polo_target) and stones_colected < 3
  at_home =  np.array_equal(agent.pos,agent.marco_polo_target) and stones_colected == 0 and not is_queen_hungry_and_can_feed


  return away_from_home or at_home or (len(considered) > 0 and considered[closest_resource[0]] < distance_home)  


def closest_resource_pickout(agent: Agent):
  resource_distances = {stone:ggat.closest_resource(agent,stone)[0] for stone in agent.inventory.keys()}
  looking_for = agent.needs.copy()
  if agent.inventory["nourriture"] < 15:
    looking_for ={"nourriture":1}
  considered = {stone:distance for stone,distance in resource_distances.items() if stone in looking_for and looking_for[stone] > 0 and distance is not None}
  closest_resource = [s for s,d in considered.items() if d == min(considered.values())]
  if len(closest_resource) == 0:
    rock = "nourriture"
  else:
    rock = closest_resource[0] 
  return ct.GEN(lambda x: ggat.pick_up(x,rock))


def go_base(agent: Agent):
  return  ct.AND_P([ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),ct.GEN(lambda x: ggat.drop_drone(x))])




gather_or_home = if_else_node(do_i_pick_something,ct.GEN(closest_resource_pickout),ct.GEN(go_base) )




# def gathering(agent:Agent):
#   # information 
#   distance_home = gmov.move_to_distance(agent.marco_polo_target,agent)
#   resource_distances = {stone:ggat.closest_resource(agent,stone)[0] for stone in agent.inventory.keys()}
#   looking_for = agent.needs
#   stones_colected = sum(agent.inventory.values()) - agent.inventory["nourriture"]

#   considered = {stone:distance for stone,distance in resource_distances.items() if stone in looking_for and looking_for[stone] > 0 and distance is not None}

#   if len(considered) == 0 and stones_colected < 3:
#     return ct.GEN(gmov.roam)

#   closest_resource = [s for s,d in considered.items() if d == min(considered.values())]
  
#   if len(considered) > 0  and (stones_colected < 3 or considered[closest_resource[0]] < distance_home):
#     return ct.GEN(lambda x: ggat.pick_up(x,closest_resource[0]))
#   else:
#     return ct.AND_P([ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),ct.GEN(lambda x: ggat.drop_drone(x))])


# gather_and_come_back = ct.O_ON_F(ct.GEN(gathering))





# open_cond= lambda x: x.inventory["nourriture"] < 10 or x.queen_fishing
# close_cond = lambda x: x.inventory["nourriture"] > 15
# hunger_not_party = ct.GATE(open_cond= open_cond,close_cond=close_cond, name="open hunger")



# find_food_vector = [ ct.OR([hunger_not_party],"conditions to find food"), 
#                      (ct.OR([
#                          ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator")]))]

# find_food = ct.AND(find_food_vector, name = "find_food")

find_food = if_else_node(lambda x: x.inventory["nourriture"] < 10 or x.queen_fishing,ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator"), false_node, "find food" )


open_cond_q= lambda x: x.inventory["nourriture"] < 5 
close_cond_q = lambda x: x.inventory["nourriture"] > 15
hunger_queen = ct.GATE(open_cond= open_cond_q,close_cond=close_cond_q, name="open hunger")



find_food_vector_q = [ ct.OR([hunger_queen],"conditions to find food queen"), 
                     (ct.OR([
                         ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator queen")]))]

find_food_q = ct.AND(find_food_vector_q, name = "find_food")










level_up_process = ct.GEN(lambda x:
                              ct.AND_P([
                                ct.GEN(lambda x: gmov.move_to(x.marco_polo_target,x)),
                                ct.GEN(ggat.check_quorum),
                                gen_interaction("incantation"),
                              ])
                              )

level_up = if_else_node(lambda x: x.level_up and x.marco_polo_target is not None , level_up_process, false_node, "level up main node")


find_queen = if_else_node(lambda x: (x.marco_polo_target is None or x.marco_polo_confirm < 3) and not  x.inventory["nourriture"] < 3, ct.GEN(gmov.marco_polo_follower),false_node , "find_queen")


fork = if_else_node(lambda x: (x.fork or x.free_egg) and x.nb_client == 0, gen_interaction("fork"), false_node)

queen_snack = if_else_node(lambda x: "nourriture" in x.objects[x.pos[0]][x.pos[1]], gen_interaction("prend", "nourriture"), false_node)



drone_snack = if_else_node(lambda x: "nourriture" in x.objects[x.pos[0]][x.pos[1]] and not np.array_equal(x.marco_polo_target, x.pos), gen_interaction("prend", "nourriture"), false_node, "drone snack")

mark_me_alive = if_else_node(lambda x: x.name not in x.ppl_lv.keys() or x.name not in x.ppl_timeouts or  x.turn - x.ppl_timeouts[x.name] > 550, ct.GEN(gtem.share_inventory),false_node, "mark me alive")

update_needs = if_else_node(lambda x: x.queen_totem is None or np.array_equal(x.pos, x.queen_totem), ct.GEN(gtem.ready_for_incantation, "update_needs"),ct.GEN(lambda x: gmov.move_to(x.queen_totem,x, "back to totem")))


voir_after_settled = if_else_node(lambda x: x.turn > 300, gen_interaction("voir"),ct.LOGIC(lambda x:True), "voir only after the 300th turn")


#queen_find_food = if_else_node(lambda x: x.turn < 3700, find_food, false_node , "queen find food")


queen_logic = ct.OR([find_food_q,loop_node_non_blocking([queen_snack,voir_after_settled, update_needs],"queen logic")],"queen food or main")

drone_logic = ct.OR([drone_snack,  find_food,find_queen, level_up, gather_or_home], "drone logic main node")

role_selector = if_else_node(lambda x: x.name == max(x.ppl_lv.keys()) and x.turn > 40 ,queen_logic, drone_logic, "role selector node")


lv2 = ct.AND_P([ct.GEN(lambda x: ggat.pick_up(x, "linemate", just_go=True)), gen_interaction("incantation")])


first = if_else_node(lambda x: x.level <2, lv2,false_node)

connect_nbr = if_else_node(lambda x: random.random()<0.01,gen_interaction("connect_nbr"),false_node)

master_plan = lv2


master_plan = ct.OR([
  connect_nbr,
  fork,
  first,
  mark_me_alive,
  role_selector,
  gen_interaction("inventaire")
], "master plan")

