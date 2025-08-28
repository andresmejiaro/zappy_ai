from domain_agent import Agent
import core_behavior_tree as ct
from gen_common import gen_interaction
from gen_movement import move_to
import gen_movement as gmov
import numpy as np
import random
import gen_teaming as gtem


def drop(agent: Agent, inventory: dict) -> ct.BTNode:
    actions = []
    for key, value in inventory.items():
        n_to_drop = min(value, agent.inventory[key])
        actions2 = map(
            lambda x: gen_interaction(
                "pose",
                x),
            [key] *
            int(n_to_drop))
        actions.extend(actions2)
    if len(actions) > 0:
        to_return = ct.AND_P(actions, name=f"drop stuff")
        return to_return
    return ct.LOGIC(lambda x: True, "True")


def drop_drone(agent: Agent,) -> ct.BTNode:
    all_inv = agent.inventory.copy()
    all_inv["nourriture"] = 0  # agent.queen hungry
    food_to_remove = int(
        max(0, agent.inventory["nourriture"] - 5)) * (agent.queen_food < 20)

    food_drop = [gen_interaction("pose", "nourriture")] * food_to_remove
    food_drop.append(drop(agent, all_inv))

    return ct.AND_P(food_drop)


def closest_resource(agent: Agent, resource: str):
    """
    Finds the coordinate of the nearest known resource
    """
    if agent.marco_polo_target is None:
        mpt = np.array([-99, -99])
    else:
        mpt = agent.marco_polo_target.copy()

    found = [np.array([x, y]) for x in range(agent.size[0]) for y in range(
        agent.size[1]) if resource in agent.objects[x][y] and not
        np.array_equal(np.array([x, y]), mpt)]
    if len(found) == 0:
        return (None, None)
    distances = [gmov.move_to_distance(x, agent) for x in found]
    idx = min(range(len(distances)), key=distances.__getitem__)
    n = min(distances)

    return (n, found[idx])


def pick_up(agent: Agent, resource: str, just_go=False) -> ct.BTNode:
    def pick_up_plan(agent: Agent):
        _, x = closest_resource(agent, resource)
        if x is None or len(x) == 0 or np.array_equal(
                agent.marco_polo_target, x):
            return ct.LOGIC(lambda x: False)
        actions = move_to(x, agent)
        if just_go:
            return actions
        from master_plan import if_else_node, false_node
        safety = if_else_node(
            lambda x: np.array_equal(
                x.pos, x.marco_polo_target), false_node, ct.Interaction(
                "prend", resource))
        actions = [actions, safety, ct.Interaction("inventaire")]
        return ct.AND(actions, name=f"pick up {resource}")
    return ct.OR([ct.GEN(pick_up_plan),
                  ct.ALWAYS_F(ct.GEN(gmov.roam))])


def pick_up_multiple(
        agent: Agent,
        resources: dict,
        individual=False) -> ct.BTNode:
    """
    This sets up multiple things to find multiple stuff
    to find if any found returns True
    """
    look4 = []
    inv = agent.inventory
    for key, value in resources.items():
        if inv.get(key, 0) < value:
            look4.append(key)
    random.shuffle(look4)
    w = map(
        lambda x: ct.GEN(
            lambda y: pick_up(
                y,
                x),
            name=f"pick_up call on "),
        look4)
    w = list(w)
    if len(w) == 0:
        return ct.LOGIC(lambda x: True, "True")
    z = ct.OR(w, name="pick_up_multiple")
    return ct.AND_P([z,
                     ct.GEN(gtem.share_inventory,
                            "share inventory generator pick up multiple")],
                    name=f"pick up multiple main node ")


def do_i_have_inventory(
        agent: Agent,
        resources: dict,
        individual=None) -> bool:
    inv = agent.inventory
    for key, value in resources.items():
        if inv.get(key, 0) < value:
            return False
    return True


def gather(agent: Agent, resources: dict, individual=False) -> ct.BTNode:
    check = ct.LOGIC(
        lambda x: do_i_have_inventory(
            x,
            resources,
            individual),
        name="gather check Inv")
    gather_node = ct.ALWAYS_F(
        ct.GEN(
            lambda x: pick_up_multiple(
                x,
                resources),
            name="gather collector"))
    return ct.OR([check, gather_node], name=f"gather")


def resource_choose(resources: dict, n=3) -> dict:
    total = sum(resources.values())
    n = min(n, total)
    list_form = []
    for k, v in resources.items():
        list_form.extend([k] * v)
    random.shuffle(list_form)
    list_form = list_form[0:n]
    result = {}
    for x in list_form:
        if result.get(x, 0) == 0:
            result[x] = 1
        else:
            result[x] += 1
    return resources


def level_up_party_size(lv):
    ps = [1, 2, 2, 4, 4, 6, 6, 1]
    return ps[lv - 1]


def level_up_reqs(aclv):
    lreq = [{"linemate": 1},  # 1->2
            {"linemate": 1, "deraumere": 1, "sibur": 1},  # 2->3
            {"linemate": 2, "sibur": 1, "phiras": 2},  # 3->4
            {"linemate": 1, "deraumere": 1, "sibur": 2, "phiras": 1},  # 4->5
            {"linemate": 1, "deraumere": 2, "sibur": 1, "mendiane": 3},  # 5->6
            {"linemate": 1, "deraumere": 2, "sibur": 3, "phiras": 1},  # 6->7
            {"linemate": 2, "deraumere": 2, "sibur": 2,
                "mendiane": 2, "phiras": 2, "thystame": 1},  # 7->8,
            {}  # 8->9 to avoid crash at endgame
            ]
    return lreq[aclv - 1]


def item_ground_count(agent, x, y, reqs: dict) -> bool:
    for key, value in reqs.items():
        if agent.objects[x][y].count(key) < value:
            return False
    return True
