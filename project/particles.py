from dataclasses import dataclass
import math
import pygame, random
from pygame.math import Vector2 as vec

#####################################################################################################################

@dataclass
class Particle():
    x: int = 0
    y: int = 0
    speed_x: int = 0
    speed_y: int = 0
    scale: float = 1.0
    rotation: float = 0.0
    alpha: float = 255
    # 1 = 1 second
    lifetime: int = 1
    time_elapsed: float = 0.0

#####################################################################################################################

class ParticleImageBased:
    def __init__(
            self,
            screen: pygame.Surface,
            img: pygame.Surface, 
            rate: int = 1, 
            scale_speed: float = 1.0, 
            rotation_speed: float = 1.0, 
            alpha_speed: float = 1.0,
            spawn_rect: pygame.Rect | None = None,
        ):
        
        
        self.particles: list[Particle] = []
        
        self.screen = screen
        self.img = img
        self.width = self.img.get_rect().width
        self.height = self.img.get_rect().height
        self.rect = pygame.Rect(0,0,self.width,self.height)
        self.center = self.rect.center
        
        # amount of new particles per second
        self.rate = rate
        self.custom_event_id  = pygame.event.custom_type() # pygame.USEREVENT + 1
        # pygame.time.set_timer(self.custom_event_id, int(1000 / rate))
        self.interval: float = 1 / rate
        self.next_run: float = 0.0
        
        # scale_speed: 1.0 ==> from 100% to 0% size in 1 second
        self.scale_speed = scale_speed
        # rotation_speed: 1.0 ==> full 360 degree rotation in 1 second
        self.rotation_speed = rotation_speed
        # alpha_speed: 1.0 ==> from not transparent to fully transparent in 1 second
        self.alpha_speed = alpha_speed
        # (optional) if provided, add_particles function will choose random start point from inside this rect
        self.spawn_rect = spawn_rect

    def emit(self, dt: float):
        
        MILI_SEC = 1.001
        if self.particles:
            self.delete_particles()
            for particle in self.particles:
                particle.time_elapsed += dt
                particle.x += (particle.speed_x * MILI_SEC * dt) +  (math.sin(particle.time_elapsed * MILI_SEC * 10) * 4)
                particle.y += particle.speed_y * MILI_SEC * dt
                
                particle.lifetime -= MILI_SEC * dt
                
                
                particle.scale -= MILI_SEC * dt * self.scale_speed                
                if particle.scale <=0:
                    continue
                
                particle.rotation += self.rotation_speed * 360 * MILI_SEC * dt
                particle.rotation = particle.rotation % 360
                
                particle.alpha -= self.alpha_speed * 255 * MILI_SEC * dt
                if particle.alpha < 0:
                    particle.alpha = 0
                self.img.set_alpha(particle.alpha)
                
                self.rect.centerx = particle.x - self.width 
                self.rect.centery = particle.y - self.height
                surface  = self.img 
                surface = pygame.transform.scale(self.img, (self.width * particle.scale, self.height * particle.scale))
                surface = pygame.transform.rotate(surface, particle.rotation)
                self.screen.blit(surface, (particle.x - int(surface.get_width()//2), particle.y - int(surface.get_height()//2)))

    def add_particles(
            self,
            start_pos: list[int] | None = None, 
            move_speed: float = 100.0, 
            move_dir: int = 180, 
            rotation: int = 0, 
            scale: float = 1, 
            alpha: int = 255, 
            lifetime: int = 1
        ):
        # move_speed: 100 ==> 100 px per sec
        # move_dir:     0 ==> up, 90 ==> right (in degrees, clockwise)
        # rotation:     0 ==> no rotation; 180 ==> flip upside down (initial rotation in degrees, clockwise)
        # scale:        1 ==> no change; 2 ==> extend 2 times (initial)
        # lifetime:     1 ==> 1 second
        if self.spawn_rect:
            pos_x = self.spawn_rect.x + random.randint(0, self.spawn_rect.width)
            pos_y = self.spawn_rect.y + random.randint(0, self.spawn_rect.height)
        else:
            pos_x = start_pos[0] - self.width / 2
            pos_y = start_pos[1] - self.height / 2
        dir_vec = vec(0,-1).rotate(move_dir).normalize() * move_speed
        direction_x = dir_vec.x # random.randint(-3,3)
        direction_y = dir_vec.y # random.randint(-3,3)
        p = Particle(pos_x, pos_y, direction_x, direction_y, scale, rotation, alpha, lifetime)
        self.particles.append(p)

    def delete_particles(self):
        particle_copy = [particle for particle in self.particles if particle.lifetime > 0]
        self.particles = particle_copy


