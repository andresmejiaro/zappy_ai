from ActionTree import GEN, LOGIC, MSG
from action_generators import pick_up, roam
from totem import mark_totem_gen
from gathering_plans import gather, drop
from BasicAction import Basic

##lv2invt = ["linemate"]

##lv3invt = ["linemate", "deraumere", "sibur"]
##lv4invt = ["linemate","linemate","sibur","phiras", "phiras"]
##lv5invt = ["linemate", "deraumere","sibur","sibur","phiras"]
##lv6invt = ["linemate", "deraumere","sibur","mendiane","mendiane","mendiane"]
##lv7invt = ["linemate", "deraumere","deraumere","sibur","sibur","sibur","phiras"]
##lv8invt = ["linemate","linemate","deraumere","deraumere","sibur","sibur","mendiane","mendiane","phiras","phiras","thystame"]





find_food_if_hungry = LOGIC(lambda x: x.inventory["nourriture"] < 10) & MSG("Looking for food") & (GEN(lambda x: pick_up(x, "nourriture")) |  GEN(lambda x: roam(x)))
lucky_stone = LOGIC(lambda x: x.inventory["linemate"] < 1) & MSG("Looking for a lucky stone") & (GEN(lambda x: pick_up(x, "linemate")) | GEN(lambda x: roam(x)))
mark_totem = GEN(lambda x: mark_totem_gen(x,"linemate"))


basic_to_function = find_food_if_hungry | lucky_stone | mark_totem