from rich import print
from dataclasses import dataclass

# from utils.BehaviourTree.ai_behaviour import AIBehaviour
from ai_behaviour import AIBehaviour
from behaviour.cow_behaviour_tree import (
    CowConditionalBehaviourTree,
    CowContinuousBehaviourTree,
    CowIndividualContext
)
from npc.base import NPCBase
from behaviour.npc_behaviour_tree import (
    NPCBehaviourTree,
    NPCIndividualContext
)


@dataclass
class NPC(NPCBase):
    name = "NPC"
    ai: AIBehaviour | None = None

    def init_ai(self) -> None:
        ctx = NPCIndividualContext(self)
        self.ai = AIBehaviour(ctx)
        # self.ai.conditional_behaviour_tree = NPCBehaviourTree.Farming
        # self.ai.conditional_behaviour_tree = NPCBehaviourTree.Woodcutting
        self.ai.conditional_behaviour_tree = NPCBehaviourTree.Patrol
        # ai.continuous_behaviour_tree = NPCContinuousBehaviourTree.Flee


@dataclass
class Cow(NPCBase):
    name = "Cow"
    ai: AIBehaviour | None = None

    def init_ai(self) -> None:
        ctx = CowIndividualContext(self)
        self.ai = AIBehaviour(ctx)
        self.ai.conditional_behaviour_tree = CowConditionalBehaviourTree.Wander
        # ai.continuous_behaviour_tree = CowContinuousBehaviourTree.Flee
