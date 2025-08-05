import core_behavior_tree as ct
from gen_common import gen_interaction
import json
import random

def join_party_gen(x):
    message = {}
    message["kind"] = "join"
    message["team_name"] = x.party_name
    message["name"] = x.name
    return gen_interaction("broadcast",json.dumps(message))

def lfg_gen(x):
    message = {}
    message["kind"] = "lfg"
    if x.party_name is None:
        x.party_name = hash(random.randbytes(64))
    message["party_name"] = x.party_name
    message["lvl"] = x.level + 1
    x.lfg = T
    if not x.name in x.party_members:
        x.party_members.append(x.name)
    return gen_interaction("broadcast",json.dumps(message))

def closed_party_gen(x):
    message = {}
    message["kind"] = "closed"
    message["party_name"] = x.party_name
    message["members"] = x.party_members
    return gen_interaction("broadcast",json.dumps(message))

def disband(x):
    message = {}
    message["kind"] = "disband"
    message["party_name"] = x.party_name
    return gen_interaction("broadcast",json.dumps(message))

do_i_have_party = ct.LOGIC(lambda x: x.party_name is not None)
do_i_have_ppl = ct.LOGIC(lambda x: len(x.party_members) > x.party_size )
is_party_closed = ct.LOGIC(lambda x: x.party_closed)

party_lead_closed = ct.AND() #step0
step1 = ct.AND([do_i_have_party,ct.GEN(join_party_gen)  ])





