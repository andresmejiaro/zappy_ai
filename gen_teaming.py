from gen_common import gen_interaction
import json

def share_inventory(x):
    message = {}
    message["kind"] = "inventory"
    message["lvl"] = x.level
    message["name"] = x.name
    message["inventory"] = x.inventory
    x.bc_inventory_processer(message,0)
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))


def ready_for_incantation(x):
    if x.queen_totem is None:
        x.queen_totem = x.pos.copy()
    message = {}
    message["kind"] = "ready"
    message["lvl"] = x.level
    message["name"] = x.name
    message["food"] = x.inventory["nourriture"]
    if x.inventory["nourriture"] < 6:
        message["fishing"] = True
    else:
        message["fishing"] = False
    if x.inventory["nourriture"] <10:
        message["needs"] = {}
        message["level_up"] = []
        message["fork"] = False
    else:
        message["needs"] = x.queen_needs_generator()
        message["level_up"] = x.call_to_level_up()
        message["fork"] = x.fork_generator()
    x.alive_processer(json.dumps(message))
    x.bc_incantation_ready(message,0)
    return gen_interaction("broadcast",json.dumps(message))


