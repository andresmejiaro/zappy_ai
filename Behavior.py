from ActionTree import Action
from Agent import Agent
from functools import reduce
import operator

elevation_ritual = 1 
soir = 2
droite = 3
avance = 4

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