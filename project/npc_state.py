from settings import ANIMATION_SPEED

RUN_SPEED: float = 39.0

class NPC_State():
    def enter_state(self, character: "NPC"):
        raise NotImplemented(f"'enter_state' is not implemented. NPC_State should be used only as abstract class")
    
    def update(self, dt: float, character: "NPC"):
        raise NotImplemented(f"'update' is not implemented. NPC_State should be used only as abstract class")
    
    def __repr__(self) -> str:
        return self.__class__.__name__

class Idle(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.is_jumping:
            return Jump()
        elif character.vel.magnitude() > RUN_SPEED:
            character.animation_speed = ANIMATION_SPEED
            return Run()
        elif character.vel.magnitude() > 1:
            character.animation_speed = ANIMATION_SPEED // 2
            return Walk()

    def update(self, dt: float, character: "NPC"):
        # character.animate(f"idle_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"idle_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class Walk(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.is_jumping:
            return Jump()
        elif character.vel.magnitude() < 1:
            character.animation_speed = ANIMATION_SPEED // 2
            return Idle()
        elif character.vel.magnitude() > RUN_SPEED:
            character.animation_speed = ANIMATION_SPEED
            return Run()
    
    def update(self, dt: float, character: "NPC"):
        # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class Run(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        if character.is_jumping:
            return Jump()
        elif character.vel.magnitude() < 1:
            character.animation_speed = ANIMATION_SPEED // 2
            return Idle()
        elif character.vel.magnitude() < RUN_SPEED:
            character.animation_speed = ANIMATION_SPEED // 2
            return Walk()
    
    def update(self, dt: float, character: "NPC"):
        # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"run_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)

class Jump(NPC_State):
    def __init__(self):
        super().__init__()

    def enter_state(self, character: "NPC"):
        
        if not character.is_jumping:
            if character.vel.magnitude() < 1:
                character.animation_speed = ANIMATION_SPEED // 2
                return Idle()
            elif character.vel.magnitude() < RUN_SPEED:
                character.animation_speed = ANIMATION_SPEED // 2
                return Walk()
            else:
                character.animation_speed = ANIMATION_SPEED
                return Run()
    
    def update(self, dt: float, character: "NPC"):
        # character.animate(f"run_{character.get_direction_horizontal()}", character.animation_speed * dt)
        character.animate(f"jump_{character.get_direction_360()}", character.animation_speed * dt)
        character.movement()
        character.physics(dt)
