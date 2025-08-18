import core_behavior_tree as ct
import gen_movement as gmov
import gen_gathering as ggat
from gen_common import gen_interaction
import numpy as np
import gen_teaming as gtem


## 0th plan is to roam

#roam_gen = ct.GEN(gmov.roam)

### first plan is to be alive


open_cond= lambda x: x.inventory["nourriture"] < 10 and x.party.party_name is None
close_cond = lambda x: x.inventory["nourriture"] > 15
hunger_not_party = ct.GATE(open_cond= open_cond,close_cond=close_cond, name="open hunger")


open_cond= lambda x: x.inventory["nourriture"] < 5 and x.party.party_name is not None and x.party.party_role >= 2
close_cond = lambda x: x.inventory["nourriture"] > 15
hunger_party = ct.GATE(open_cond= open_cond,close_cond=close_cond, name="open hunger")


hungry_party = ct.AND([
        hunger_party,
        ct.GEN(gtem.disband),
])





find_food_vector = [ ct.OR([hungry_party , hunger_not_party],"conditions to find food"), 
                     ct.ALWAYS_F(ct.OR([ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator")]))]

find_food = ct.AND(find_food_vector, name = "find_food")



#### trird plan is to level up to level 2

level_up = ct.GEN(lambda x: ggat.level_up(x), name = "level up main", reset_on_failure=False)


###

#gooble = ct.AND([ct.LOGIC(lambda x: np.array_equal(ggat.closest_resource(x,"nourriture"),x.pos ) ), gen_interaction("prend", "nourriture") ], name = "oportunistic food")

am_I_almost_declared_dead = ct.AND([ct.LOGIC(lambda x: x.turn - x.ppl_timeouts.get(x.name,x.turn)  >= 350, "am I missing?"),
                                    ct.GEN(gtem.share_inventory)
                                    ])




master_plan = ct.OR([am_I_almost_declared_dead, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
#master_plan = ct.OR([am_I_almost_declared_dead, find_food, level_up, ct.ALWAYS_F( gen_interaction("inventaire"), name = "ending inventaire")], name = "master plan")                         
#master_plan = ct.ALWAYS_F(ct.OR([ct.GEN(lambda x: ggat.pick_up(x,"nourriture"),"pick up food generator"),ct.GEN(gmov.roam)]))
