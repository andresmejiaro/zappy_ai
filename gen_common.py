import core_behavior_tree as ct

def gen_interaction(command,resource = ''):
    return ct.GEN(lambda x: ct.Interaction(command, resource), f"created by gen interaction {command} {resource}")


