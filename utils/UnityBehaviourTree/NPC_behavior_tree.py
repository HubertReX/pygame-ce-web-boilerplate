from rich import print
from node import Node
import random

from behavior_tree_base import Action, BehaviorTreeBase, Condition, Selector, Sequence

#############################################################################################################


def is_healthy(node: Node) -> bool:
    res = True  # random.randint(0, 2) == 0
    # print(f"'is_healthy' {res}")

    return res

#############################################################################################################


def is_enemy_in_attack_range(node: Node) -> bool:
    res = random.randint(0, 2) == 0
    # print(f"'is_enemy_in_attack_range' {res}")

    return res

#############################################################################################################


def is_enemy_in_FOV_range(node: Node) -> bool:
    res = random.randint(0, 2) == 0
    return res

#############################################################################################################


def approach_enemy(node: Node) -> bool:
    return True

#############################################################################################################


def is_tired(node: Node) -> bool:
    tiredness = node.get_context("tiredness", 0)
    time_to_rest = node.get_context("time_to_rest", 0)
    if tiredness >= 15:
        if time_to_rest == 0:
            node.set_context("time_to_rest", 3)
        result = True
    else:
        result = False
    # print(f"'is_tired' {tiredness}")
    return result

#############################################################################################################


def rest(node: Node) -> bool:
    time_to_rest = node.get_context("time_to_rest", 0)
    time_to_rest -= 1
    if time_to_rest <= 0:
        node.set_context("tiredness", 0)
        node.set_context("time_to_rest", 0)
        result = True
    else:
        node.set_context("time_to_rest", time_to_rest)
        result = False
    # print(f"'is_tired' {tiredness}")
    return result

#############################################################################################################


def patrol_area(node: Node) -> bool:
    tiredness = node.get_context("tiredness", 0)
    node.set_context("tiredness", tiredness + 10)

    res = False  # random.randint(0, 2) == 0
    return res

#############################################################################################################


def attack(node: Node) -> bool:
    res = True  # random.randint(0, 2) == 0
    # print("'attack'")

    return res

#############################################################################################################


def wander(node: Node) -> bool:
    res = False  # random.randint(0, 2) == 0
    # print("'wandering...'")

    return res

#############################################################################################################


class PatrolBehaviorTree(BehaviorTreeBase):

    def setup(self) -> Node:
        self._root = Selector(
            Sequence(
                Condition(is_tired),
                Action(rest),
            ),
            Sequence(
                Condition(is_enemy_in_attack_range),
                Action(attack),
            ),
            Sequence(
                Condition(is_enemy_in_FOV_range),
                Action(approach_enemy),
            ),
            Action(patrol_area)
        )
