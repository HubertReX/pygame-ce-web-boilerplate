from rich import print
from dataclasses import dataclass

from npc.base import NPCBase
# # from utils.BehaviourTree.ai_behaviour import AIBehaviour
# from ai_behaviour import AIBehaviour
# from behaviour.cow_behaviour_tree import (
#     CowConditionalBehaviourTree,
#     CowContinuousBehaviourTree,
#     CowIndividualContext
# )


# @dataclass
# class Cow:
#     name = "Cow"
#     ai: AIBehaviour | None = None

#     def init_ai(self) -> None:
#         cow_ctx = CowIndividualContext(self)
#         self.ai = AIBehaviour(cow_ctx)
#         self.ai.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
#         # ai.continuous_behaviour_tree = CowContinuousBehaviourTree.Flee

def stat(npc: NPCBase) -> str:
    return f"[yellow]{npc.name}[/]([magenta]{npc.ai.pf_state:<4}[/]:{npc.ai.pf_state_duration:5.1f})"


def pf_wander(npc: NPCBase) -> bool:
    print(f"{stat(npc)} 'wandering...'")
    return True


def pf_walk_to(npc: NPCBase) -> bool:
    npc.ai.start_moving()
    print(f"{stat(npc)} 'walking...'")
    return True
