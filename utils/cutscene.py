from functools import partial
from typing import Any, Callable
import pygame
import sys
from animation import Animation, Task, remove_animations_of, animator

# https://www.codewithc.com/advanced-cutscene-creation-in-pygame/
#   plus
# https://github.com/bitcraft/animation

# just for testing, move to ../project folder before running

# Initialize Pygame
pygame.init()

# Screen dimensions and creating a window
SCREEN_WIDTH, SCREEN_HEIGHT = 800, 600
screen = pygame.display.set_mode((SCREEN_WIDTH, SCREEN_HEIGHT))
pygame.display.set_caption('Advanced Cutscene Creator')

# Colors (RGB)
BLACK = (0, 0, 0)
WHITE = (255, 255, 255)

# Frame rate
FPS = 60
clock = pygame.time.Clock()

# Cutscene manager class
class CutsceneManager:
    def __init__(self):
        self.scenes = []
        self.active_scene = None
        self.scene_index = 0

    def add_scene(self, scene):
        self.scenes.append(scene)

    def start(self):
        if self.scenes:
            self.active_scene = self.scenes[0]
            self.scene_index = 0
            self.active_scene.start()

    def update(self):
        if self.active_scene is not None:
            if self.active_scene.is_finished():
                self.scene_index += 1
                if self.scene_index < len(self.scenes):
                    self.active_scene = self.scenes[self.scene_index]
                    self.active_scene.start()
                else:
                    self.active_scene = None
            else:
                self.active_scene.update()
        
        return bool(self.active_scene)

    def draw(self, screen):
        if self.active_scene is not None:
            self.active_scene.draw(screen)

# Base class for scenes
class Scene:
    def start(self):
        pass

    def update(self):
        pass

    def draw(self, screen):
        pass

    def is_finished(self):
        return True

# Example of a specific scene
class DialogueScene(Scene):
    def __init__(self, text, duration):
        self.text = text
        self.r = 255
        self.g = 0
        self.b = 0
        self.color = (self.r, self.g, self.b)
        self.duration = duration
        self.font_size = 32
        self.font = pygame.font.SysFont('Arial', self.font_size)
        self.start_ticks = pygame.time.get_ticks()
        self.elapsed_time = 0
        self.render_text = self.font.render(self.text, True, self.color)
        self.text_rect = self.render_text.get_rect(center=(SCREEN_WIDTH//2, SCREEN_HEIGHT//2))

    def change_font(self, _min, _max):
        if self.font_size == _min:
            self.font_size = _max
        else:
            self.font_size = _min
        self.font = pygame.font.SysFont('Arial', self.font_size)
        
    def set_color(self, r, g=0, b=0):
        self.color = (self.r, self.g, self.b)
        # self.color = [r, g, b]
        
    def start(self):
        self.start_ticks = pygame.time.get_ticks()

    def update(self):
        current_ticks = pygame.time.get_ticks()
        self.elapsed_time = (current_ticks - self.start_ticks) / 1000

    def draw(self, screen):
        screen.fill(BLACK)
        self.color = (self.r, self.g, self.b)
        self.render_text = self.font.render(self.text, True, self.color)
        screen.blit(self.render_text, self.text_rect)

    def is_finished(self):
        return self.elapsed_time >= self.duration

# Create a cutscene manager and add scenes
cutscene_manager = CutsceneManager()
cutscene_manager.add_scene(DialogueScene('It was a dark and stormy night...', 5))
cutscene_manager.add_scene(DialogueScene('Suddenly, a shot rang out!', 4))
cutscene_manager.add_scene(DialogueScene('The maid screamed.', 3))
cutscene_manager.add_scene(DialogueScene('And all was silent...', 5))
cutscene_manager.start()


# a1 = Animation(cutscene_manager.active_scene.text_rect, x=700, y=500, duration=1000, transition="in_out_quint")
# a2 = Animation(cutscene_manager.active_scene, r=150, g=250, b=200, duration=2000)

intro_cutscene = {
    "steps": [
        {
            "name": "step_01",
            "description": "move text to upper left corner",
            "type": "animation",
            "target": cutscene_manager.active_scene.text_rect, 
            "args": {"x":10,  "y":10}, 
            "duration": 1000, 
            "transition": "in_out_cubic", 
            "from": "<root>", 
            "trigger": "<begin>"
        },
        {
            "name": "step_05",
            "description": "change font size",
            "type": "task",
            "target": cutscene_manager.active_scene.change_font, 
            "args": {"_min": 64, "_max": 32}, 
            "interval": 1000, 
            "times": 2, 
            "from": "step_02", 
            # "trigger": "on finish"
        },
        {
            "name": "step_02",
            "description": "move text to lower right corner",
            "type": "animation",
            "target": cutscene_manager.active_scene.text_rect, 
            "args": {"x":700,  "y":500}, 
            "duration": 1000, 
            "transition": "in_out_cubic", 
            "from": "step_01", 
            "trigger": "on finish"
        },
        {
            "name": "step_03",
            "description": "change font color from red to blue",
            "type": "animation",
            "target": cutscene_manager.active_scene, 
            "args": {"r":50,  "g":250, "b":200}, 
            "duration": 3000, 
            # "transition": "in_out_cubic", 
            "from": "step_01", 
            "trigger": "on start"
        },
        {
            "name": "step_04",
            "type": "animation",
            "description": "move text to lower left corner",
            "target": cutscene_manager.active_scene.text_rect, 
            "args": {"x":70,  "y":500}, 
            "duration": 1000, 
            "transition": "in_out_cubic", 
            "from": "step_02", 
            "trigger": "on finish"
        },
    ]
}

# a1  = Animation(x=10,  y=10,        duration=1000, transition="in_out_cubic")
# a2  = Animation(x=700, y=500,       duration=1000, transition="in_out_quint")
# a3  = Animation(r=50, g=250, b=200, duration=3000)
# a4  = Animation(x=70, y=500,        duration=1000, transition="in_out_quint")

# a1.schedule(partial(a3.start, cutscene_manager.active_scene), "on start")
# a1.schedule(partial(a2.start, cutscene_manager.active_scene.text_rect))
# a2.schedule(partial(a4.start, cutscene_manager.active_scene.text_rect))
# a1.start(cutscene_manager.active_scene.text_rect)

animations = pygame.sprite.Group()
# animations.add([a1, a2, a3, a4])
first_anim = animator(intro_cutscene, animations)


# animations.add(a2)
# animations.add(a3)

# a2.start(cutscene_manager.active_scene)
# animations.add(ani2)
# animations.add(ani3)
# Game loop
running = True
while running:
    dt = clock.tick(FPS)
    for event in pygame.event.get():
        if event.type == pygame.QUIT:
            running = False
        elif event.type == pygame.KEYDOWN:
            if event.key in [pygame.K_ESCAPE, pygame.K_q]:
                running = False
                # pygame.quit()
                # sys.exit()
                
            elif event.key == pygame.K_SPACE:
                if cutscene_manager.active_scene:
                    cutscene_manager.active_scene.duration = -1
            
    screen.fill(BLACK)
                
    if running:
        running = cutscene_manager.update()
    animations.update(dt)
    cutscene_manager.draw(screen)
    
    pygame.display.flip()

pygame.quit()
sys.exit()