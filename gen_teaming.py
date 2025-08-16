import core_behavior_tree as ct
from gen_common import gen_interaction
import json
import random
import secrets

def join_party_gen(x):
    message = {}
    message["kind"] = "join"
    message["lvl"] = x.level
    message["party_name"] = x.party.party_name
    message["name"] = x.name
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))

def lfg_gen(x):
    message = {}
    message["kind"] = "lfg"
    if x.party.party_name is None:
        x.party.party_name = secrets.token_urlsafe(12)
    message["party_name"] = x.party.party_name
    message["lvl"] = x.level
    message["name"] = x.name
    x.party.party_role = 3
    if not x.name in x.party.party_members:
        x.party.party_members.append(x.name)
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))

def closed_party_gen(x):
    message = {}
    message["kind"] = "closed"
    message["lvl"] = x.level
    message["party_name"] = x.party.party_name
    message["members"] = x.party.party_members
    x.party.party_closed = True
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))

def disband(x):
    ret = 1
    if x.party.party_name is None:
        ret = 0
    message = {}
    message["kind"] = "disband"
    message["lvl"] = x.level
    message["party_name"] = x.party.party_name
    x.party.reset_party()
    if ret == 0:
        return ct.LOGIC(lambda x: True, "True")
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))

def share_inventory(x):
    message = {}
    message["kind"] = "inventory"
    message["lvl"] = x.level
    message["party_name"] = x.party.party_name
    message["name"] = x.name
    message["inventory"] = x.inventory
    x.party.bc_inventory_processer(message,0)
    x.alive_processer(json.dumps(message))
    return gen_interaction("broadcast",json.dumps(message))


def ready_for_incantation(x):
    message = {}
    message["kind"] = "ready"
    message["lvl"] = x.level
    message["party_name"] = x.party.party_name
    message["name"] = x.name
    if x.name not in x.party.party_members_ready: 
        x.party.party_members_ready.append(x.name)
    
    return gen_interaction("broadcast",json.dumps(message))


am_i_leader = ct.LOGIC(lambda x: x.party.party_name is None or (x.party.party_role == 3 and len(x.party.party_members)< x.party.party_size),name = "am_i_leader logic")
is_party_not_closed_can_close = ct.LOGIC(lambda x: not x.party.party_closed and x.party.party_role == 3 and len(x.party.party_members) >= x.party.party_size , name = "is_party_not_closed_can_close")
do_i_join =ct.LOGIC(lambda x: x.party.party_role == 1, name ="am I a silent applicant?")
do_i_share_inv =ct.LOGIC(lambda x: x.party.party_closed and len(x.party.party_inventories.keys()) < x.party.party_size - 1,"is everyone ready to share")
did_i_do_it =  ct.LOGIC(lambda x: x.party.party_closed and len(x.party.party_inventories.keys()) >= x.party.party_size -1 , "did teaming succeeed?")

#party_lead_closed = ct.AND() #step0
step1 = ct.AND([am_i_leader,ct.GEN(lfg_gen, name = "lfg generator"),
                ct.LOGIC(lambda x:False, "False")  ], name = "join step leader spam lfg")


step2 = ct.AND([is_party_not_closed_can_close,ct.GEN(closed_party_gen, name = "closed party generator"),
                 ct.LOGIC(lambda x:False, "False")], name = "close party condition ok")

stale_check = ct.OR([ ct.LOGIC(lambda x: x.turn - x.party.party_join_timeout < 50),
                     ct.LOGIC(lambda x: (x.party.reset_party(),False)[1])
],"stale join party checks")


step3 = ct.AND([ do_i_join,stale_check,  ct.GEN(join_party_gen, name = "Join party generator"), ct.LOGIC(lambda x:False, "False")], name="joining logic")


step4 = ct.AND([do_i_share_inv,ct.GEN(share_inventory, name = "share inventory generator"), ct.LOGIC(lambda x:False, "False")], name = "sync inv")


teaming = ct.OR([step1,step2, step3, step4, did_i_do_it], name = "teaming main selector")
   