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
    message = {}
    message["kind"] = "ready"
    message["lvl"] = x.level
    message["name"] = x.name
    x.alive_processer(json.dumps(message))
    x.bc_incantation_ready(message,0)
    return gen_interaction("broadcast",json.dumps(message))


def went_fishing(x):
    message = {}
    message["kind"] = "fishing"
    message["lvl"] = 0
    message["name"] = x.name
    x.alive_processer(json.dumps(message))
    x.bc_incantation_ready(message,0)
    return gen_interaction("broadcast",json.dumps(message))