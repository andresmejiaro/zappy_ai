from ActionTree import Action
from Agent import Agent
from functools import reduce
import operator


def pose(object):
    pass

forage = (soir & droite & soir & droite & soir & droite & soir & avance(lv)).loop


def drop(set):
    return reduce(operator.and_, (pose(x) for x in set))

    



lv2 = find("linemate") & elevation_ritual

lv3 = team_up ("lv 3") & forage & team_meet("nest") & drop("lv 3") & elevation_ritual

lv4 = team_up ("lv 4") & forage & team_meet("nest") & drop("lv 4") & elevation_ritual

lv5 = team_up ("lv 5") & forage & team_meet("nest") & drop("lv 5") & elevation_ritual

lv6 = team_up ("lv 6") & forage & team_meet("nest") & drop("lv 6") & elevation_ritual & disband

lv7 = team_up ("lv 7") & forage & team_meet("nest") & drop("lv 7") & elevation_ritual

lv8 = team_up ("lv 8") & forage & team_meet("nest") & drop("lv 8") & elevation_ritual

starving = forage("nourriture")

oportunistic = mark_nest | pick_if_in_place | pick_if_needed 

plan = lv2 & lv3 & lv4 & lv5 & lv6 & lv7 & lv8

life = starving | oportunistic | plan


# Test Basic actions
#plan = Basic("soir") & Basic("avance") & Basic("soir") & Basic("droite") & Basic("avance") & Basic("gauche") & Basic("avance") & Basic("soir")
#test pick up and put down
#plan = Basic("soir") & Basic("prend","linemate") & Basic("soir") & Basic("pose","linemate") & Basic("soir")
#Test move to may need fix
#plan = move_to(np.arrobjettsay([4,6]),agent)
# Test pickup in place
#plan = Basic("soir") & LOOP(lambda x: pick_up(x,"linemate"))
#Test pick up with finding
#plan = Basic("soir") & LOOP(lambda x: pick_up(x,"phiras"))
#Test pick up multiple
#plan = Basic("soir") & LOOP(lambda x: pick_up_multiple(x,["linemate","phiras"]))
#test eternal roam
#plan = LOOP(lambda x: roam(x))
# find food
#plan = GEN(lambda x: pick_up(x, "norriture")) |  LOOP(lambda x: roam(x))