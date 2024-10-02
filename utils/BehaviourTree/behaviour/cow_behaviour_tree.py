from __future__ import annotations

from dataclasses import dataclass
from enum import Enum
import random

from attrs import field

from npc.base import NPCBase
from behaviour.ai_behaviour_tree_base import (
    Action,
    Condition,
    Context,
    NodeWrapper,
    Selector,
    Sequence,
)
from npc.utils import pf_wander, pf_walk_to, stat
from rich import print


@dataclass
class CowIndividualContext(Context):
    cow: NPCBase
    range_grid: list[list[int]] = field(factory=list)


def wander(context: CowIndividualContext) -> bool:
    # print("cow wander")
    # pf_grid=CowIndividualContext.range_grid
    return pf_wander(context.cow)


# region flee behaviour
def player_nearby(context: CowIndividualContext) -> bool:
    is_player_nearby = random.random() < 0.2
    print(f"{stat(context.cow)} 'player_nearby': {is_player_nearby}")
    return is_player_nearby


def flee_from_player(context: CowIndividualContext) -> bool:
    print(f"{stat(context.cow)} 'flee_from_player'")
    pf_walk_to(context.cow)
    return True


class CowConditionalBehaviourTree(NodeWrapper, Enum):
    Flee = Selector(
        Sequence(
            Condition(player_nearby),
            Action(flee_from_player)
        )
    )
    Wander = Selector(Flee, Action(wander))


class CowContinuousBehaviourTree(NodeWrapper, Enum):
    Flee = Selector(
        Sequence(
            Condition(player_nearby),
            Action(flee_from_player)
        )
    )
