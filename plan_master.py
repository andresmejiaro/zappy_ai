import core_behavior_tree as ct
import gen_movement as gmov
import gen_gathering as ggat
from gen_common import gen_interaction
import numpy as np
import gen_teaming as gtem


## 0th plan is to roam

roam_gen = ct.GEN(gmov.roam)

### first plan is to be alive


open_cond= lambda x: x.inventory["nourriture"] < 10
close_cond = lambda x: x.inventory["nourriture"] > 15


find_food_vector = [ct.GATE(open_cond= open_cond,close_cond=close_cond, name="open hunger") , 
                     ct.OR([ct.GEN(lambda x: ggat.pick_up(x,"nourriture")),ct.GEN(gmov.roam)])]

find_food = ct.AND(find_food_vector, name = "find_food")



#### trird plan is to level up to level 2

level_up = ct.GEN(lambda x: ggat.level_up(x), name = "level up main", reset_on_failure=False)


###

gooble = ct.AND([ct.LOGIC(lambda x: np.array_equal(ggat.closest_resource(x,"nourriture"),x.pos ) ), gen_interaction("prend", "nourriture") ], name = "oportunistic food")



#master_plan = ct.OR([find_food, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
master_plan = ct.OR([ level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         

