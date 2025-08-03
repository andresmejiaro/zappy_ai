def level_up(agent):
    go_home =  move_to(agent.totem_pos, agent)
    dmp = drop_my_part(agent, reqs[f"{agent.level + 1}"])
    return MSG("Work to level up") & go_home & MSG("Dumping stuff") & dmp & gen_interaction("incantation")

def drop_my_part(agent, req):
    h = LOGIC(lambda x: False)
    for object in req.keys():
        n_to_drop = agent.inventory[object]
        if object == "linemate":
            n_to_drop = max(n_to_drop - 1, 0)
        if n_to_drop <= 0:
            continue
        z = map(lambda x: Interaction("pose", object), range(n_to_drop))
        z = reduce(lambda x,y: x|y,z)
        h = h | z
    return h