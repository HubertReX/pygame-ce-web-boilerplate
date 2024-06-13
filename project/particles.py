import math
import random
from abc import ABC, abstractmethod
from dataclasses import dataclass
from functools import cache
from typing import Any, Callable

import pygame
from camera import Camera
from pygame.math import Vector2 as vec
from pyscroll.group import PyscrollGroup
from settings import HEIGHT, PARTICLES_DIR, WIDTH, ZOOM_LEVEL

###################################################################################################################


def import_sprite_sheet(
    path: str,
    tile_size: int,
    sprite_sheet_definition: list[tuple[int, int]]
) -> list[pygame.Surface]:
    """
        Load sprite sheet and cut it into animation names and frames using SPRITE_SHEET_DEFINITION dict.
        If provided sheet is missing some of the animations from dict, a frame from upper left corner (0, 0)
        will be used.
        If directional variants are missing (e.g.: only idle animation, but no idle left, idle right...)
        the general animation will be copied.
    """
    img: pygame.Surface = pygame.image.load(path).convert_alpha()
    img_rect: pygame.Rect = img.get_rect()
    animation: list[pygame.Surface] = []

    for coord in sprite_sheet_definition:
        x, y = coord
        rec = pygame.Rect(x * tile_size, y * tile_size, tile_size, tile_size)
        if rec.colliderect(img_rect):
            img_part = img.subsurface(rec)
            animation.append(img_part)

    return animation

#####################################################################################################################


@dataclass
# MARK: Particle
class Particle():
    # MARK: Particle
    start_view: pygame.Rect
    x: int = 0
    y: int = 0
    speed_x: int = 0
    speed_y: int = 0
    scale: float = 1.0
    rotation: float = 0.0
    alpha: int = 255
    # 1 = 1 second
    lifetime: float = 1.0
    time_elapsed: float = 0.0

    ###################################################################################################################
    # MARK: x_oscillation
    # def x_oscillation(self) -> int:
    #     return 0

#####################################################################################################################


def static_x_oscillation() -> float:
    return 0.0


class ParticleImageBased:
    # MARK: ParticleImageBased
    def __init__(
        self,
        screen: pygame.Surface,
        image: pygame.Surface,
        group: PyscrollGroup,
        camera: Camera,
        animation: list[pygame.Surface] | None = None,
        animation_speed: float = 0.0,
        freeze_after_nth_frame: int = 10_000,
        rate: int = 1,
        scale_speed: float = 1.0,
        rotation_speed: float = 1.0,
        alpha_speed: float = 1.0,
        spawn_rect: pygame.Rect | None = None,
        x_oscillation: Callable | None = None,
    ):

        self.particles: list[Particle] = []

        self.screen = screen
        self.image = image
        self.group = group
        self.camera = camera
        self.animation = animation
        self.animation_speed = animation_speed
        self.freeze_after_nth_frame = freeze_after_nth_frame
        self.frame_index: float = 0.0
        self.width = self.image.get_rect().width
        self.height = self.image.get_rect().height
        self.rect = pygame.Rect(0, 0, self.width, self.height)
        self.center = self.rect.center

        # amount of new particles per second
        self.rate: int = rate
        self.custom_event_id: int  = pygame.event.custom_type()

        self.interval: int = 1000 // rate
        pygame.time.set_timer(pygame.event.Event(self.custom_event_id), self.interval)

        # scale_speed: 1.0 ==> from 100% to 0% size in 1 second
        self.scale_speed = scale_speed
        # rotation_speed: 1.0 ==> full 360 degree rotation in 1 second
        self.rotation_speed = rotation_speed
        # alpha_speed: 1.0 ==> from not transparent to fully transparent in 1 second
        self.alpha_speed = alpha_speed
        # (optional) if provided, add_particles function will choose random start point from inside this rect
        self.spawn_rect = spawn_rect
        # (optional) if provided, x position will oscillate
        self.x_oscillation: Callable = x_oscillation or (lambda x: 0.0)

    ###################################################################################################################
    # MAR: animate
    def animate(self, time_elapsed: float, loop: bool = True) -> None:
        if not self.animation:
            return

        self.frame_index = (self.animation_speed * time_elapsed)

        if int(self.frame_index) >= len(self.animation):
            self.frame_index = 0.0 if loop else len(self.animation) - 1.0
        # print(f"{len(self.animation)=} {self.frame_index:4.1f} {int(self.frame_index)=}")

        self.image = self.animation[int(self.frame_index)].copy()

    ###################################################################################################################
    # MARK: emit
    def emit(self, dt: float) -> None:
        if not self.particles:
            return

        self.delete_old_particles()
        for particle in self.particles:
            particle.time_elapsed += dt
            if self.animation:
                self.animate(particle.time_elapsed)

            if int(self.frame_index) < self.freeze_after_nth_frame:
                particle.x += int((particle.speed_x * dt) + self.x_oscillation(particle.time_elapsed))
                particle.y += int(particle.speed_y * dt)

            particle.lifetime -= dt

            particle.scale -= dt * self.scale_speed

            if particle.scale <= 0:
                continue

            particle.rotation += self.rotation_speed * 360 * dt
            particle.rotation = particle.rotation % 360

            particle.alpha -= int(self.alpha_speed * 255 * dt)
            particle.alpha = max(particle.alpha, 0)
            self.image.set_alpha(particle.alpha)

            surface  = self.image
            surface = pygame.transform.scale(
                self.image, (self.width * particle.scale, self.height * particle.scale))
            surface = pygame.transform.rotate(surface, particle.rotation)
            self.rect.centerx = particle.x - int(surface.get_width() // 2)
            self.rect.centery = particle.y - int(surface.get_height() // 2)
            # need to compensate for the camera move and zoom change since the creation of particle
            # this ensures that the particles are always in the same place relative to the ground
            view_offset = vec(
                particle.start_view.centerx - self.group.view.centerx,
                particle.start_view.centery - self.group.view.centery) * self.camera.zoom

            self.rect = self.rect.move(view_offset.x, view_offset.y)

            self.screen.blit(surface, self.rect.center)

    ###################################################################################################################
    # MARK: add_particles
    def add_particles(
        self,
        start_pos: tuple[int, int] | None = None,
        move_speed: float = 100.0,
        move_dir: int = 180,
        rotation: int = 0,
        scale: float = 1.0,
        alpha: int = 255,
        lifetime: float = 1.0
    ) -> None:
        # move_speed: 100 ==> 100 px per sec
        # move_dir:     0 ==> up, 90 ==> right (in degrees, clockwise)
        # rotation:     0 ==> no rotation; 180 ==> flip upside down (initial rotation in degrees, clockwise)
        # scale:        1 ==> no change; 2 ==> extend 2 times (initial)
        # lifetime:     1 ==> 1 second

        # if spawn area is provided use it; otherwise use the middle of the screen
        if self.spawn_rect:
            pos_x = self.spawn_rect.x + random.randint(0, self.spawn_rect.width)
            pos_y = self.spawn_rect.y + random.randint(0, self.spawn_rect.height)
        elif start_pos:
            pos_x = int(start_pos[0] - self.width / 2)
            pos_y = int(start_pos[1] - self.height / 2)
        dir_vec = vec(0, -1).rotate(move_dir).normalize() * move_speed
        direction_x = int(dir_vec.x)  # random.randint(-3,3)
        direction_y = int(dir_vec.y)  # random.randint(-3,3)
        # compensate the camera zoom level change
        p = Particle(self.group.view, pos_x, pos_y, direction_x, direction_y,
                     scale * (self.camera.zoom / ZOOM_LEVEL), rotation, alpha, lifetime)
        # if self.x_oscillation:
        #     p.x_oscillation = self.x_oscillation

        self.particles.append(p)

    ###################################################################################################################
    # MARK: delete_particles
    def delete_old_particles(self) -> None:
        particle_copy = [particle for particle in self.particles if particle.lifetime > 0.0]
        self.particles = particle_copy


#######################################################################################################################
# MARK: ParticleSystem
class ParticleSystem(ABC):
    @ abstractmethod
    def __init__(self, canvas: pygame.Surface, group: PyscrollGroup, camera: Camera) -> None:
        self.custom_event_id: int = 0

    @ abstractmethod
    def add(self) -> None:
        ...

    @ abstractmethod
    def emit(self, dt: float) -> None:
        ...

#######################################################################################################################
# MARK: Leaf


class ParticleLeafs(ParticleSystem):
    def __init__(self, canvas: pygame.Surface, group: PyscrollGroup, camera: Camera) -> None:
        # leafs appears at the top half of the screen
        spawn_rect = pygame.Rect(0, 0, WIDTH, HEIGHT // 2)

        leaf_img = pygame.image.load(PARTICLES_DIR / "Leaf_single.png").convert_alpha()
        # emit: 1 particle/second
        self.particle = ParticleImageBased(
            screen=canvas,
            image=leaf_img,
            group=group,
            camera=camera,
            rate=5,
            scale_speed=0.25,
            alpha_speed=0.1,
            rotation_speed=0.0,
            spawn_rect=spawn_rect,
            x_oscillation=self.x_oscillation,
        )
        self.custom_event_id = self.particle.custom_event_id

    @ cache
    @ staticmethod
    def x_oscillation(self: Any, time_elapsed: float) -> float:
        return math.sin(time_elapsed * 10.0) * 4.0

    ###################################################################################################################
    def add(self) -> None:
        # move 80 pixels/seconds into south-west (down-left) +/- 30 degree, enlarge 5 x, kill after 4 seconds
        self.particle.add_particles(
            start_pos=pygame.mouse.get_pos(),
            move_speed=80,
            move_dir=210 + random.randint(-30, 30),
            scale=5.0,
            lifetime=4.0
        )

    ###################################################################################################################
    def emit(self, dt: float) -> None:
        self.particle.emit(dt)

#####################################################################################################################


class ParticleRain(ParticleSystem):
    # MARK: Rain
    def __init__(self, canvas: pygame.Surface, group: PyscrollGroup, camera: Camera) -> None:
        # rain appears at the top of the screen (16 pixels high, full width)
        spawn_rect = pygame.Rect(0, -HEIGHT // 2, WIDTH + 256, HEIGHT)
        # leaf_img = pygame.image.load(PARTICLES_DIR / "Rain.png").convert_alpha()
        sprite_sheet_definition = [(0, 0), (1, 0), (2, 0)]
        animation = import_sprite_sheet(str(PARTICLES_DIR / "Rain.png"), 8, sprite_sheet_definition)
        animation += import_sprite_sheet(str(PARTICLES_DIR / "RainOnFloor.png"), 8, sprite_sheet_definition)
        # emit: 1 particle/second
        self.particle = ParticleImageBased(
            screen=canvas,
            image=animation[0].copy(),
            group=group,
            camera=camera,
            animation=animation,
            animation_speed=6.0,
            freeze_after_nth_frame=3,
            rate=30,  # 30
            scale_speed=0.0,
            alpha_speed=0.0,
            rotation_speed=0.0,
            spawn_rect=spawn_rect,
        )
        self.custom_event_id = self.particle.custom_event_id

    ###################################################################################################################
    def add(self) -> None:
        # move 1500 pixels/seconds into south-west (down-left) enlarge 5 x, kill after half a second
        self.particle.add_particles(
            start_pos=pygame.mouse.get_pos(),
            move_speed=1500,
            move_dir=210,
            scale=4.0,
            lifetime=1.0
        )

    ###################################################################################################################
    def emit(self, dt: float) -> None:
        self.particle.emit(dt)
