#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import random
import queue
import os
import glob
import time
import math
from lib.threads import ImageRotateThread
from lib.util import distance


class Background:
    def __init__(self, width=480, height=320, color=(0, 0, 0), alpha=255):
        self.width = width
        self.height = height
        self.color = color
        self.alpha = alpha

    def update(self):
        pass

    def draw(self, surface):
        surface.fill(self.color)
        surface.set_alpha(self.alpha)

    def enter(self):
        self._on_enter()

    def exit(self):
        self._on_exit()

    def _on_enter(self):
        pass

    def _on_exit(self):
        pass


class DynamicImage(Background):
    def __init__(self, width=480, height=320, color=(0, 0, 0), alpha=255, speed=0.1):
        super(DynamicImage, self).__init__(width=width, height=height, color=color, alpha=alpha)

        self.speed = speed

        self.image_directory = os.path.join("images", "background")
        self.image_size = self.height
        self.images = []
        self.rotated_images = []

        self.x_offset = int((self.width - self.image_size) / 2)
        self.y_offset = int((self.height - self.image_size) / 2)
        self.rotated_image_queue = queue.Queue()

        for image_path in glob.glob(os.path.join(self.image_directory, "*.png")):
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (self.image_size, self.image_size))
            self.images.append(image)
        self.images.reverse()

    def update(self):
        current_time = int(time.time() * 100)

        self.rotated_image_queue = queue.Queue()
        threads = []
        for ind, image in enumerate(self.images):
            image_center = image.get_rect().center
            image_center = (image_center[0] + self.x_offset, image_center[1] + self.y_offset)
            degree = int(current_time / (2 ** ind) * self.speed) % 360
            thread = ImageRotateThread(image, image_center, degree, self.rotated_image_queue)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

    def draw(self, surface):
        for rotated_image, rect in self.rotated_image_queue.queue:
            surface.blit(rotated_image, rect)

        surface.set_alpha(self.alpha)


class DynamicTriangle(Background):
    def __init__(self, width=480, height=320, color=(0, 0, 0), alpha=255,
                 total_points=30, total_triangles=10, repeat_interval=20,
                 filled=False):
        super(DynamicTriangle, self).__init__(width=width, height=height, color=color, alpha=alpha)

        self.total_points = total_points
        self.total_triangles = total_triangles
        self.repeat_interval = repeat_interval
        self.filled = filled

        self.points_padding = 25
        self.points = []
        self.triangles = []

        self._update_interval = 0.1
        self._last_update = time.time()

        self.points_setup()

    def points_setup(self):
        self.points = [MovePoint(self.points_padding, self.points_padding,
                                 self.width - self.points_padding,
                                 self.height - self.points_padding,
                                 radius=50, speed=1, speed_variant=0.2) for _ in range(self.total_points)]
        self.triangles = [Triangle(random.choices(self.points, k=3)) for _ in range(self.total_triangles)]

    def _on_enter(self):
        self.points_setup()

    def update(self):
        current_time = time.time()
        if current_time - self._last_update < self._update_interval:
            return

        for point in self.points:
            point.update()
        self._last_update = time.time()

    def draw(self, surface):
        for triangle in self.triangles:
            points = triangle.get_points()
            triangle_surface = pygame.Surface((self.width, self.height))
            if self.filled:
                pygame.draw.polygon(triangle_surface, self.color, points)
            pygame.draw.lines(triangle_surface, self.color, True, points, 2)
            for point in points:
                pygame.draw.circle(triangle_surface, self.color, point, 4)

            triangle_surface.set_alpha(self.alpha)
            triangle_surface.set_colorkey((0, 0, 0))
            surface.blit(triangle_surface.convert_alpha(), (0, 0))


class DynamicTrace(Background):
    def __init__(self, width=480, height=320, color=(0, 0, 0), alpha=255,
                 color1=(0, 255, 0), color2=(0, 0, 255), steps=10, radius=5, trace_length=20):
        super(DynamicTrace, self).__init__(width=width, height=height, color=color, alpha=alpha)

        self.color1 = color1
        self.color2 = color2
        self.steps = steps
        self.radius = radius
        self.trace_length = trace_length

        self.origin = (self.width // 2, self.height // 2)
        self.x1, self.y1 = self.origin
        self.x2, self.y2 = self.origin
        self.distances1 = [0.5 ** i * min(self.width, self.height) / 2 for i in range(1, self.steps + 1)]
        self.distances2 = [0.333 ** i * min(self.width, self.height) / 2 for i in range(1, self.steps + 1)]
        self.speeds1 = []
        self.speeds2 = []
        self.queue1 = queue.Queue(maxsize=self.trace_length)
        self.queue2 = queue.Queue(maxsize=self.trace_length)
        self.colors1 = [[c - c / self.trace_length * (self.trace_length - i) for c in self.color1]
                        for i in range(self.trace_length)]
        self.colors2 = [[c - c / self.trace_length * (self.trace_length - i) for c in self.color2]
                        for i in range(self.trace_length)]

    def _reset_trace(self):
        self.speeds1 = [random.uniform(0.1 * math.pi, 0.5 * math.pi) for _ in range(self.steps)]
        self.speeds2 = [random.uniform(0.1 * math.pi, 0.5 * math.pi) for _ in range(self.steps)]

        while not self.queue1.empty():
            self.queue1.get_nowait()

        while not self.queue2.empty():
            self.queue2.get_nowait()

    def _on_enter(self):
        self._reset_trace()

    def update(self):
        if self.queue1.full():
            self.queue1.get_nowait()
        if self.queue2.full():
            self.queue2.get_nowait()

        self.queue1.put_nowait((int(self.x1), int(self.y1)))
        self.queue2.put_nowait((int(self.x2), int(self.y2)))

        current_time = time.time()
        self.x1, self.y1 = self.origin
        self.x2, self.y2 = self.origin
        for ind in range(self.steps):
            distance1 = self.distances1[ind]
            speed1 = self.speeds1[ind]
            self.x1 += distance1 * math.cos(speed1 * current_time)
            self.y1 += distance1 * math.sin(speed1 * current_time)

            distance2 = self.distances2[ind]
            speed2 = self.speeds2[ind]
            self.x2 += distance2 * math.cos(2 * math.pi - speed2 * current_time)
            self.y2 += distance2 * math.sin(2 * math.pi - speed2 * current_time)

    def draw(self, surface):
        last_pos1 = None
        last_pos2 = None
        surface1 = pygame.Surface((self.width, self.height))
        surface2 = pygame.Surface((self.width, self.height))
        surface1.set_colorkey((0, 0, 0))
        surface2.set_colorkey((0, 0, 0))
        surface1.set_alpha(self.alpha)
        surface2.set_alpha(self.alpha)

        for ind1, point1 in enumerate(self.queue1.queue):
            pygame.draw.circle(surface1, self.colors1[ind1], point1, self.radius)
            if last_pos1:
                pygame.draw.line(surface1, self.colors1[ind1], point1, last_pos1, self.radius * 2)
            last_pos1 = point1

        for ind2, point2 in enumerate(self.queue2.queue):
            pygame.draw.circle(surface2, self.colors2[ind2], point2, self.radius)
            if last_pos2:
                pygame.draw.line(surface2, self.colors2[ind2], point2, last_pos2, self.radius * 2)
            last_pos2 = point2

        surface.blit(surface1, (0, 0))
        surface.blit(surface2, (0, 0))


class MovePoint:
    def __init__(self, min_x, min_y, max_x, max_y, radius=20, speed=1, speed_variant=0):
        self.min_x = min_x
        self.min_y = min_y
        self.max_x = max_x
        self.max_y = max_y
        self.radius = radius
        self.speed = speed * random.uniform(1 - speed_variant, 1 + speed_variant)

        self.x = random.randrange(self.min_x, self.max_x)
        self.y = random.randrange(self.min_x, self.max_y)

        self.target_x = random.randrange(self.min_x, self.max_x)
        self.target_y = random.randrange(self.min_x, self.max_y)

    def update(self):
        dist = distance((self.x, self.y), (self.target_x, self.target_y))
        if dist < self.speed:
            self.target_x = random.randrange(int(max(self.x - self.radius, self.min_x)),
                                             int(min(self.x + self.radius, self.max_x)))
            self.target_y = random.randrange(int(max(self.y - self.radius, self.min_y)),
                                             int(min(self.y + self.radius, self.max_y)))
            return

        ratio = self.speed / dist
        self.x += (self.target_x - self.x) * ratio
        self.y += (self.target_y - self.y) * ratio


class Triangle:
    def __init__(self, points):
        self.points = points

    def get_points(self):
        return [(int(point.x), int(point.y)) for point in self.points]
