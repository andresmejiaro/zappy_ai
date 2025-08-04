import core_behavior_tree as ct
from gen_common import gen_interaction
import json
import random


do_i_have_lfg = ct.LOGIC(lambda x: x.lfg)
do_i_have_team = ct.LOGIC(lambda x: x.team_name is not None)

def join_group_gen(x):
    message = {}
    message["kind"] = "join"
    message["team"] = x.team_name
    message["name"] = x.name
    return gen_interaction("broadcast",json.dumps(message))

def lfg_gen(x):
    message = {}
    message["kind"] = "lfg"
    if x.team_name is None:
        x.team_name = hash(random.randbytes(64))
    message["team"] = x.team_name
    message["lvl"] = x.level + 1
    if not x.name in x.team_members:
        x.team_members.append(x.name)
    return gen_interaction("broadcast",json.dumps(message))

def closed_party_gen(x):
    message = {}
    message["kind"] = "closed"
    message["team"] = x.team_name
    message["members"] = x.team_members
    return gen_interaction("broadcast",json.dumps(message))

def disband(x):
    message = {}
    message["kind"] = "disband"
    message["team"] = x.team_name
    return gen_interaction("broadcast",json.dumps(message))

do_team = ct.OR([ct.AND([do_i_have_lfg,ct.GEN(join_group_gen)]) , ct.GEN(lfg_gen, timeout=10)])