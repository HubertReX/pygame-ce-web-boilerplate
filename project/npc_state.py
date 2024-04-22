class NPC_State():
    def enter_state(self, character: "NPC"):
        raise NotImplemented(f"'enter_state' is not implemented. NPC_State should be used only as abstract class")
    
    def update(self, dt: float, character: "NPC"):
        raise NotImplemented(f"'update' is not implemented. NPC_State should be used only as abstract class")

class Idle(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.vel.magnitude() > 1:
            return Run()

    def update(self, dt: float, character: "NPC"):
        # character.animate(f"idle_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"idle_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class Run(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.vel.magnitude() < 1:
            return Idle()
    
    def update(self, dt: float, character: "NPC"):
        # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)
