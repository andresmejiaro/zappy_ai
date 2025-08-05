import core_behavior_tree as ct
import gen_movement as gmov
import gen_gathering as ggat
from gen_common import gen_interaction
import numpy as np
import gen_teaming as gtem
lv2invt = {"linemate":1}
##lv3invt = ["linemate", "deraumere", "sibur"]
##lv4invt = ["linemate","linemate","sibur","phiras", "phiras"]
##lv5invt = ["linemate", "deraumere","sibur","sibur","phiras"]
##lv6invt = ["linemate", "deraumere","sibur","mendiane","mendiane","mendiane"]
##lv7invt = ["linemate", "deraumere","deraumere","sibur","sibur","sibur","phiras"]
##lv8invt = ["linemate","linemate","deraumere","deraumere","sibur","sibur","mendiane","mendiane","phiras","phiras","thystame"]

## 0th plan is to roam

roam_gen = ct.GEN(gmov.roam)

### first plan is to be alive

find_food_vector = [ct.GATE(open_cond= lambda x: x.inventory["nourriture"] < 10,
                 close_cond = lambda x: x.inventory["nourriture"] > 15) , 
                     ct.GEN(lambda x: ggat.pick_up(x,"nourriture"))]

find_food = ct.AND(find_food_vector, name = "find_food")


### second plan is to mark a totem

mark_totem = ct.GEN(ggat.mark_totem)

#### trird plan is to level up to level 2

level2 = ct.AND_P([ct.GEN(lambda x: ggat.level_up(x,lv2invt)),ct.LOGIC(lambda x: False)])

#gate1 = ct.GATE(open_cond= lambda x: ggat.do_i_have_inventory(x,items_to_gather), close_cond= lambda x: False)


#gg = (gate1 | gather_items) & ct.MSG("hit this") & ct.Interaction("pose", "linemate", 4) 

#gg = gg & ct.GEN(gmov.go_to_totem)

teaming = ct.OR([gtem.do_team])


#master_plan = ct.OR([find_food,mark_totem,level2,roam_gen])                         
master_plan = teaming