from __future__ import annotations

from typing import TYPE_CHECKING

from settings import ANIMATION_SPEED, BORED_TIME, RUN_SPEED

from pygame.math import Vector2 as vec

if TYPE_CHECKING:
    from characters import NPC


#################################################################################################################
def get_new_state(current_npc_state: NPC_State, character: NPC) -> NPC_State | None:
    # MARK: get_new_state
    if character.is_stunned:
        character.set_emote("shocked_anim")
        return (Stunned() if str(current_npc_state) != "Stunned" else None)
    elif character.is_dead:
        character.set_emote("dead")
        return (Dead() if str(current_npc_state) != "Dead" else None)
    elif character.is_attacking:
        character.set_emote("fight_anim")
        return (Attacking() if str(current_npc_state) != "Attacking" else None)
    elif character.is_flying:
        return (Fly() if str(current_npc_state) != "Fly" else None)
    elif character.is_jumping:
        # return (current_npc_state if str(current_npc_state) == "Jump" else Jump())
        return (Jump() if str(current_npc_state) != "Jump" else None)
    elif character.is_talking:
        if str(current_npc_state) != "Talk":
            character.acc = vec(0, 0)
            character.vel = vec(0, 0)

        #     if character.npc_met and character.is_talking:
        #         direction = character.npc_met.pos - character.pos
        #         angle = direction.angle_to(vec(0, 1))
        #     # print(f"{angle:5.2f}")
        #     else:
        #         angle = 0.0
        #     print(character.name, f"{angle:5.2f}", character.get_direction_360())
        return (Talk() if str(current_npc_state) != "Talk" else None)
    elif character.vel.magnitude() > RUN_SPEED:
        character.animation_speed = ANIMATION_SPEED
        # character.set_emote("walk")
        if str(current_npc_state) != "Run":
            character.set_emote("clear")
        return (Run() if str(current_npc_state) != "Run" else None)
    elif character.vel.magnitude() > 1:
        character.animation_speed = ANIMATION_SPEED // 2
        if str(current_npc_state) != "Walk":
            character.set_emote("clear")
        return (Walk() if str(current_npc_state) != "Walk" else None)
    elif current_npc_state.enter_time + BORED_TIME < character.scene.game.time_elapsed or \
            str(current_npc_state) == "Bored":
        # keep shifting the enter_time until player enters another state
        current_npc_state.enter_time = character.scene.game.time_elapsed + BORED_TIME
        character.set_emote("zzz_anim")
        return (Bored() if str(current_npc_state) != "Bored" else None)
    else:
        character.animation_speed = ANIMATION_SPEED // 2
        character.set_emote("clear")
        return (Idle() if str(current_npc_state) != "Idle" else None)


#################################################################################################################
class NPC_State():
    # MARK: NPC_State
    def __init__(self) -> None:
        # by default action (animation name prefix) equals to lower case class name: Run(NPC_State) => run
        self.action = self.__class__.__name__.lower()
        # set in Scene to current elapsed time after new state is created
        # can be used to check, how long character is in given state
        # (e.g. after some Idle time, character enters Bored state)
        self.enter_time: float = 0.0

    #############################################################################################################
    def enter_state(self, character: NPC) -> NPC_State | None:
        # raise NotImplemented(f"'enter_state' is not implemented. NPC_State should be used only as abstract class")
        return get_new_state(self, character)

    #############################################################################################################
    def update(self, dt: float, character: NPC) -> None:
        # raise NotImplemented(f"'update' is not implemented. NPC_State should be used only as abstract class")
        # animation key has 2 parts: action (e.g.: run) and direction player is facing (e.g. left) => "run_left"
        character.check_cooldown()
        character.animate(f"{self.action}_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)
        character.check_scene_exit()

    #############################################################################################################
    def __repr__(self) -> str:
        return self.__class__.__name__

#################################################################################################################


class Idle(NPC_State):
    def __init__(self) -> None:
        super().__init__()

#################################################################################################################


class Bored(NPC_State):
    def __init__(self) -> None:
        super().__init__()

#################################################################################################################


class Walk(NPC_State):
    def __init__(self) -> None:
        super().__init__()
        self.action = "run"

#################################################################################################################


class Run(NPC_State):
    def __init__(self) -> None:
        super().__init__()

#################################################################################################################


class Jump(NPC_State):
    def __init__(self) -> None:
        super().__init__()

#################################################################################################################


class Fly(NPC_State):
    def __init__(self) -> None:
        super().__init__()
        # no separate animation for fly - using jump
        self.action = "jump"

#################################################################################################################


class Stunned(NPC_State):
    def __init__(self) -> None:
        super().__init__()
        # no separate animation for stunned - using idle
        self.action = "idle"

#################################################################################################################


class Attacking(NPC_State):
    def __init__(self) -> None:
        super().__init__()
        self.action = "weapon"

#################################################################################################################


class Talk(NPC_State):
    def __init__(self) -> None:
        super().__init__()
#################################################################################################################


class Dead(NPC_State):
    def __init__(self) -> None:
        super().__init__()
