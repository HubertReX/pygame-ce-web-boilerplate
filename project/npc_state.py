from settings import ANIMATION_SPEED, BORED_TIME, RUN_SPEED
import characters


#####################################################################################################################

def get_new_state(current_npc_state: "NPC_State", character: "characters.NPC"):
        if character.is_flying:
            return (Fly() if str(current_npc_state) != "Fly" else None)
        elif character.is_jumping:
            # return (current_npc_state if str(current_npc_state) == "Jump" else Jump())
            return (Jump() if str(current_npc_state) != "Jump" else None)
        elif character.vel.magnitude() > RUN_SPEED:
            character.animation_speed = ANIMATION_SPEED
            return (Run() if str(current_npc_state) != "Run" else None)
        elif character.vel.magnitude() > 1:
            character.animation_speed = ANIMATION_SPEED // 2
            return (Walk() if str(current_npc_state) != "Walk" else None)
        elif current_npc_state.enter_time + BORED_TIME < character.scene.game.time_elapsed or \
                str(current_npc_state) == "Bored":
            # keep shifting the enter_time until player enters another state
            current_npc_state.enter_time = character.scene.game.time_elapsed + BORED_TIME
            return (Bored() if str(current_npc_state) != "Bored" else None)
        else:
            character.animation_speed = ANIMATION_SPEED // 2
            return (Idle() if str(current_npc_state) != "Idle" else None)

#####################################################################################################################

class NPC_State():
    def __init__(self) -> None:
        # by default action (animation name prefix) equals to lower case class name: Run(NPC_State) => run
        self.action = self.__class__.__name__.lower()
        # set in Scene to current elapsed time after new state is created
        # can be used to check, how long character is in given state 
        # (e.g. after some Idle time, character enters Bored state)
        self.enter_time: float = 0.0

    def enter_state(self, character: "characters.NPC"):
        # raise NotImplemented(f"'enter_state' is not implemented. NPC_State should be used only as abstract class")
        return get_new_state(self, character)
    
    def update(self, dt: float, character: "characters.NPC"):
        # raise NotImplemented(f"'update' is not implemented. NPC_State should be used only as abstract class")
        # animation key has 2 parts: action (e.g.: run) and direction player is facing (e.g. left) => "run_left"
        character.animate(f"{self.action}_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)
    
    def __repr__(self) -> str:
        return self.__class__.__name__

#####################################################################################################################

class Idle(NPC_State):
    def __init__(self):
        super().__init__()

    # def update(self, dt: float, character: "characters.NPC"):
    #     # character.animate(f"idle_{character.get_direction_horizontal()}", character.animation_speed * dt)
    #     character.animate(f"idle_{character.get_direction_360()}", character.animation_speed * dt)
    #     character.movement()
    #     character.physics(dt)

#####################################################################################################################

class Bored(NPC_State):
    def __init__(self):
        super().__init__()

    # def update(self, dt: float, character: "characters.NPC"):
    #     character.animate(f"bored_{character.get_direction_360()}", character.animation_speed * dt)
    #     character.movement()
    #     character.physics(dt)

#####################################################################################################################

class Walk(NPC_State):
    def __init__(self):
        super().__init__()
        self.action = "run"
    
    # def update(self, dt: float, character: "characters.NPC"):
    #     # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
    #     character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
    #     character.movement()
    #     character.physics(dt)

#####################################################################################################################

class Run(NPC_State):
    def __init__(self):
        super().__init__()
    
    # def update(self, dt: float, character: "characters.NPC"):
    #     # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
    #     character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
    #     character.movement()
    #     character.physics(dt)

#####################################################################################################################

class Jump(NPC_State):
    def __init__(self):
        super().__init__()
    
    # def update(self, dt: float, character: "characters.NPC"):
    #     # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
    #     character.animate(f"jump_{character.get_direction_360()}", character.animation_speed * dt)
    #     character.movement()
    #     character.physics(dt)

#####################################################################################################################

class Fly(NPC_State):
    def __init__(self):
        super().__init__()
        # no separate animation for fly - using jump
        self.action = "jump"

