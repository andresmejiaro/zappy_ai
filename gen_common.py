import numpy as np
from gen_movement import shorstest_vect, move_to
from core_behavior_tree import LOGIC, BTNode, GEN, MSG
from core_bt_interactions import Interaction
from domain_agent import Agent
from functools import reduce
import random 

def gen_interaction(command,resource = ''):
    return GEN(lambda x: Interaction(command, resource))


