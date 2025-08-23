import core_behavior_tree as ct
import gen_movement as gmov
import gen_gathering as ggat
from gen_common import gen_interaction
import numpy as np
import gen_teaming as gtem
import random 

## 0th plan is to roam

#roam_gen = ct.GEN(gmov.roam)

### first plan is to be alive

very_hungry_will_drop_anything = 10
tank_full = 40
prefer_food_over_lvup_if_not_party = 16

open_cond= lambda x: x.inventory["nourriture"] < prefer_food_over_lvup_if_not_party 
close_cond = lambda x: x.inventory["nourriture"] > tank_full
hunger_not_party = ct.GATE(open_cond= open_cond,close_cond=close_cond, name="open hunger")





find_food_vector = [ ct.OR([hunger_not_party],"conditions to find food"), 
                     (ct.OR([ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator")]))]

find_food = ct.AND(find_food_vector, name = "find_food")



#### trird plan is to level up to level 2

level_up = ct.GEN(lambda x: ggat.level_up(x), name = "level up main", reset_on_failure=False, timeout=3000, timeout_callback= lambda x: x.level_reset())


###

#gooble = ct.AND([ct.LOGIC(lambda x: np.array_equal(ggat.closest_resource(x,"nourriture"),x.pos ) ), gen_interaction("prend", "nourriture") ], name = "oportunistic food")

am_I_almost_declared_dead = ct.AND([ct.LOGIC(lambda x: x.turn - x.ppl_timeouts.get(x.name,x.turn)  >= 350, "am I missing?"),
                                    ct.GEN(gtem.share_inventory, "share inv so they know ur good")
                                    ], "am_I_almost_declared_dead logic")



#######
p_lay_egg = 0.004
lay_an_egg =ct.GEN(lambda _: ct.AND_P([ct.LOGIC(lambda x: random.random()< p_lay_egg and len(x.ppl_lv)<12 and x.level > 1, "lay an egg lottery"),
                    gen_interaction("fork")
                    ]), "lay_an_egg main node"
                    )




#master_plan = ct.OR([am_I_almost_declared_dead, lay_an_egg, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
master_plan = ct.OR([am_I_almost_declared_dead,find_food, lay_an_egg, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
#master_plan = ct.OR([am_I_almost_declared_dead,find_food, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                     
#master_plan = ct.OR([am_I_almost_declared_dead, find_food, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
#master_plan = ct.ALWAYS_F(ct.OR([ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator"),ct.GEN(gmov.roam)]))
