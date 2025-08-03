from core_behavior_tree import GEN, LOGIC, MSG, GATE
from gen_movement import roam
from gen_totem import mark_totem_gen
from gen_gathering import pick_up, pick_up_multiple
from core_bt_interactions import Interaction

##lv2invt = ["linemate"]

##lv3invt = ["linemate", "deraumere", "sibur"]
##lv4invt = ["linemate","linemate","sibur","phiras", "phiras"]
##lv5invt = ["linemate", "deraumere","sibur","sibur","phiras"]
##lv6invt = ["linemate", "deraumere","sibur","mendiane","mendiane","mendiane"]
##lv7invt = ["linemate", "deraumere","deraumere","sibur","sibur","sibur","phiras"]
##lv8invt = ["linemate","linemate","deraumere","deraumere","sibur","sibur","mendiane","mendiane","phiras","phiras","thystame"]




pick_up_multiple_plan = GEN(lambda x: pick_up_multiple(x,{"linemate":1, "deraumere":1,"sibur":1} ))
mark_totem = GEN (lambda x: mark_totem_gen(x,"linemate"), sticky=True)
find_food = GATE(open_cond= lambda x: x.inventory["nourriture"] < 10,
                 close_cond = lambda x: x.inventory["nourriture"] > 15) & GEN(lambda x: pick_up(x,"nourriture"))
master_plan = mark_totem | GEN(roam)