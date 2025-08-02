from ActionTree import GEN, LOGIC
from action_generators import pick_up, roam
from totem import mark_totem_gen
from gathering_plans import gather, drop

# Test Basic actions
#plan = Basic("voir") & Basic("avance") & Basic("voir") & Basic("droite") & Basic("avance") & Basic("gauche") & Basic("avance") & Basic("voir")
#test pick up and put down
#plan = Basic("voir") & Basic("prend","linemate") & Basic("voir") & Basic("pose","linemate") & Basic("voir")
#Test move to may need fix
#plan = move_to(np.arrobjettsay([4,6]),agent)
# Test pickup in place
#plan = Basic("voir") & LOOP(lambda x: pick_up(x,"linemate"))
#Test pick up with finding
#plan = Basic("voir") & LOOP(lambda x: pick_up(x,"phiras"))
#Test pick up multiple
#plan = Basic("voir") & LOOP(lambda x: pick_up_multiple(x,["linemate","phiras"]))
#test eternal roam
#plan = LOOP(lambda x: roam(x))
# find food
lv2invt = ["linemate"]
lv3invt = ["linemate", "deraumere", "sibur"]
lv4invt = ["linemate","linemate","sibur","phiras", "phiras"]
lv5invt = ["linemate", "deraumere","sibur","sibur","phiras"]
lv6invt = ["linemate", "deraumere","sibur","mendiane","mendiane","mendiane"]
lv7invt = ["linemate", "deraumere","deraumere","sibur","sibur","sibur","phiras"]
lv8invt = ["linemate","linemate","deraumere","deraumere","sibur","sibur","mendiane","mendiane","phiras","phiras","thystame"]

find_food_if_hungry = LOGIC(lambda x: x.inventory["norriture"] < 10) & (GEN(lambda x: pick_up(x, "norriture")) |  GEN(lambda x: roam(x)))
lucky_stone = LOGIC(lambda x: x.inventory["linemate"] < 1) & (GEN(lambda x: pick_up(x, "linemate")) | GEN(lambda x: roam(x)))
mark_totem = GEN(lambda x: mark_totem_gen(x,"linemate"))
