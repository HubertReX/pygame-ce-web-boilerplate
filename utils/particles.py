import pygame
import math
import time
import random
from typing import Tuple, Union, List


class ParticleBox:
    def __init__(self, rect: Tuple[int, int, int, int], shape: Union[str, pygame.Surface], color: Tuple[int, int, int, int], lifetime: float, vel: Tuple[int, int], size: Tuple[int, int], angle: int, shape_width: int = 0, color_overtime: Tuple[Tuple[int, int, int, int], Union[int, None]] = None, vel_overtime: Tuple[Tuple[int, int], Union[int, None]] = None, size_overtime: Tuple[Tuple[int, int], Union[int, None]] = None, angle_overtime: Tuple[int, Union[int, None]] = None):  # shape can be rect (str), circle (str), or sprite (surf)
        self.rect = pygame.FRect(rect[0], rect[1], rect[2], rect[3])
        self.spawn_points = [[self.rect.left, self.rect.right], [
            self.rect.top, self.rect.bottom]]  # [[from x1 to x2], [from y1 to y2]]
        self.particles = []

        self.shape = shape
        self.shape_width = shape_width
        self.color = list(color)
        if len(self.color) == 3:
            self.color.append(255)
        self.lifetime = lifetime
        self.vel = list(vel)
        self.size = list(size)
        self.angle = angle

        self.overtime = {
            "color": color_overtime,
            "vel": vel_overtime,
            "size": size_overtime,
            "angle": angle_overtime
        }

    def spawn_particle(self):
        shape = random.choice(self.shape) if type(self.shape) in (tuple, list) else self.shape

        if type(self.shape_width) in (tuple, list):
            if len(self.shape_width) == 3 and self.shape_width[2] == "minmax":
                shape_width = random.randint(min(self.shape_width[0], self.shape_width[1]), max(
                    self.shape_width[0], self.shape_width[1]))
            else:
                shape_width = random.choice(self.shape_width)
        else:
            shape_width = self.shape_width

        if type(self.color[0]) in (tuple, list):
            if len(self.color) == 3 and self.color[2] == "minmax":
                color = [random.randint(min(self.color[0][0], self.color[1][0]), max(self.color[0][0], self.color[1][0])), random.randint(min(self.color[0][1], self.color[1][1]), max(
                    self.color[0][1], self.color[1][1])), random.randint(min(self.color[0][2], self.color[1][2]), max(self.color[0][2], self.color[1][2]))]

                len_c1 = len(self.color[0])
                len_c2 = len(self.color[1])
                if len_c1 == 4 and len_c2 == 4:
                    color.append(random.randint((min(self.color[0][3], self.color[1][3])), max(
                        self.color[0][3], self.color[1][3])))
                elif (len_c1 == 3 and len_c2 == 4) or (len_c1 == 4 and len_c2 == 3):
                    color.append(random.randint(self.color[int(len_c1 == 3)][3], 255))
            else:
                color = random.choice(self.color)
        else:
            color = self.color

        if type(self.lifetime) in (tuple, list):
            if len(self.lifetime) == 3 and self.lifetime[2] == "minmax":
                lifetime = random.uniform(min(self.lifetime[0], self.lifetime[1]),
                                          max(self.lifetime[0], self.lifetime[1]))
            else:
                lifetime = random.choice(self.lifetime)
        else:
            lifetime = self.lifetime

        if type(self.vel[0]) in (tuple, list):
            if len(self.vel) == 3 and self.vel[2] == "minmax":
                vel = pygame.Vector2(random.uniform(min(self.vel[0][0], self.vel[1][0]), max(self.vel[0][0], self.vel[1][0])), random.uniform(
                    min(self.vel[0][1], self.vel[1][1]), max(self.vel[0][1], self.vel[1][1])))
            else:
                vel = pygame.Vector2(random.choice(self.vel))
        else:
            vel = pygame.Vector2(self.vel)

        if type(self.size[0]) in (tuple, list):
            if len(self.size) == 3 and self.size[2] == "minmax":
                size = [random.uniform(min(self.size[0][0], self.size[1][0]), max(self.size[0][0], self.size[1][0])), random.uniform(
                    min(self.size[0][1], self.size[1][1]), max(self.size[0][1], self.size[1][1]))]
            else:
                size = random.choice(self.size)
        else:
            size = self.size

        if type(self.angle) in (tuple, list):
            if len(self.angle) == 3 and self.angle[2] == "minmax":
                angle = random.uniform(min(self.angle[0], self.angle[1]), max(self.angle[0], self.angle[1]))
            else:
                angle = random.choice(self.angle)
        else:
            angle = self.angle

        self.particles.append(Particle(random.uniform(self.spawn_points[0][0], self.spawn_points[0][1]), random.uniform(
            self.spawn_points[1][0], self.spawn_points[1][1]), shape, shape_width, color, lifetime, vel, size, angle, self.overtime))

    def update(self, dt: float, win: pygame.Surface, scroll: List[int]) -> int:
        total_particles = 0
        blits = []
        curr_time = time.time()
        for particle in reversed(self.particles):
            if curr_time - particle.spawntime >= particle.lifetime:
                self.particles.remove(particle)
                continue

            total_particles += 1

            if type(particle.shape) == str:
                if particle.shape == "rect":
                    pygame.draw.rect(win, particle.color, (particle.pos.x, particle.pos.y,
                                     particle.size[0], particle.size[1]), particle.shape_width)
                else:
                    if particle.size[0] == particle.size[1]:
                        pygame.draw.circle(win, particle.color, (
                            particle.pos.x + particle.size[0] * 0.5, particle.pos.y + particle.size[1] * 0.5), particle.size[0] * 0.5, particle.shape_width)
                    else:
                        pygame.draw.ellipse(win, particle.color, (particle.pos.x, particle.pos.y,
                                            particle.size[0], particle.size[1]), particle.shape_width)
            else:
                blits.append((particle.img, (particle.pos.x - scroll[0], particle.pos.y - scroll[1])))
            particle.update(dt)
        win.fblits(blits)
        return total_particles


class Particle:
    # shape can be rect (str), circle (str), or sprite (surf)
    def __init__(self, x: int, y: int, shape: Union[str, pygame.Surface], shape_width: int, color: Tuple[int, int, int, int], lifetime: float, vel: pygame.Vector2, size: Tuple[int, int], angle: int, overtime):
        self.pos = pygame.Vector2(x, y)

        self.orig_color = color
        self.orig_vel = vel
        self.orig_size = size
        self.orig_angle = angle

        self.shape = shape
        self.shape_width = shape_width
        self.color = color
        self.lifetime = lifetime
        self.spawntime = time.time()
        self.vel = vel
        self.size = size
        self.angle = angle
        self.overtime = overtime
        self.curr_overtime = {
            "color": [0, self.overtime["color"] if not self.overtime["color"] else self.overtime["color"][0]],
            "vel": [0, self.overtime["vel"] if not self.overtime["vel"] else self.overtime["vel"][0]],
            "size": [0, self.overtime["size"] if not self.overtime["size"] else self.overtime["size"][0]],
            "angle": [0, self.overtime["angle"] if not self.overtime["angle"] else self.overtime["angle"][0]],
        }

        if type(self.shape) == pygame.Surface:
            self.orig_img = self.shape
            self.img = pygame.transform.rotate(self.orig_img, angle)

    def change_overtime(self, dt, value_to_change, value_type, lifetime_perc):
        orig_value = getattr(self, f'orig_{value_type}')
        overtime_values = self.overtime[value_type]
        curr_overtime_values = self.curr_overtime[value_type]

        currtime_perc = lifetime_perc / curr_overtime_values[1][1]
        if lifetime_perc >= curr_overtime_values[1][1]:
            if curr_overtime_values[0] < len(overtime_values) - 2:
                curr_overtime_values[0] += 1
                curr_overtime_values[1] = overtime_values[self.curr_overtime[0]]
            else:
                curr_overtime_values = [0, None]
        if curr_overtime_values[1]:
            if value_type == "angle":
                value_to_change = pygame.math.lerp(orig_value, curr_overtime_values[1][0], currtime_perc)
            else:
                value_to_change = [pygame.math.lerp(
                    orig_value[i], curr_overtime_values[1][0][i], currtime_perc) for i in range(len(value_to_change))]

        return value_to_change

    def update(self, dt):
        color = self.color[:]
        size = self.size[:]
        angle = self.angle
        lifetime_perc = (time.time() - self.spawntime) / self.lifetime

        self.pos += self.vel * dt

        if self.curr_overtime["color"][1] and type(self.shape) == str:
            color = self.change_overtime(dt, color, "color", lifetime_perc)
        if self.curr_overtime["vel"][1]:
            self.vel = self.change_overtime(dt, self.vel, "vel", lifetime_perc)
        if self.curr_overtime["size"][1] and type(self.shape) == str:
            size = self.change_overtime(dt, size, "size", lifetime_perc)
        if self.curr_overtime["angle"][1]:
            angle = self.change_overtime(dt, angle, "angle", lifetime_perc)

        if color[:3] != self.color[:3]:
            self.color = color
        if size != self.size:
            self.size = size
        if color[3] != self.color[3]:
            self.img.set_alpha(color[3])
            self.color = color
        if angle != self.angle and type(self.shape) == pygame.Surface:
            self.img = pygame.transform.rotate(self.orig_img, angle)
            self.angle = angle


if __name__ == "__main__":
    win = pygame.display.set_mode((800, 600))
    pbs = [ParticleBox((-10, 540, 800, 60), "circle", [[x + 128, x + 128, x + 128, 255] for x in range(127)], 3, [(0, -50), (0, -100), "minmax"], [15, 15], 0, size_overtime=[[(0, 0), 1]]), ParticleBox((-10, 540, 800, 50), "circle", [255,
                                                                                                                                                                                                                                         128, 0, 255], 1, [(0, -50), (0, -100), "minmax"], [50, 50], 0, size_overtime=[[(0, 0), 1]]), ParticleBox((-10, 540, 800, 60), "circle", [255, 200, 0, 255], 2, [(0, -50), (0, -100), "minmax"], [10, 10], 0, size_overtime=[[(0, 0), 1]])]
    clock = pygame.Clock()

    while True:
        total_particles = 0
        dt = clock.tick(2000) * .001
        mpos = pygame.mouse.get_pos()

        win.fill((0, 0, 0))
        for pb in pbs:
            total_particles += pb.update(dt, win, (0, 0))
            for _ in range(int(1000 * dt)):
                pb.spawn_particle()
            pb.rect.center = mpos
            pb.spawn_points = [[pb.rect.left, pb.rect.right], [pb.rect.top, pb.rect.bottom]]

        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                quit()

        pygame.display.set_caption(f"{clock.get_fps()} | {total_particles}")
        pygame.display.flip()
