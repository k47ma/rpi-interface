#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import random
import queue
import os
import glob
import time
import copy
from lib.threads import ImageRotateThread


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
                 total_points=30, total_triangles=10, repeat_interval=20):
        super(DynamicTriangle, self).__init__(width=width, height=height, color=color, alpha=alpha)

        self.total_points = total_points
        self.total_triangles = total_triangles
        self.repeat_interval = repeat_interval

        self.points = [[random.choice(range(self.width)), random.choice(range(self.height))] for _ in range(self.total_points)]
        self.target_points = [[random.choice(range(self.width)), random.choice(range(self.height))] for _ in range(self.total_points)]
        self.triangles = [random.choices(self.points, k=3) for _ in range(self.total_triangles)]

    def update(self):
        pass

    def draw(self, surface):
        curr_time = time.time()
        for triangle in self.triangles:
            triangle_copy = copy.deepcopy(triangle)
            for ind, point in enumerate(triangle):
                weighted_point = [0, 0]
                target_point = self.target_points[self.points.index(point)]
                curr_ind = curr_time - int(curr_time / self.repeat_interval) * self.repeat_interval
                half_interval = self.repeat_interval // 2
                if curr_ind < half_interval:
                    weight = curr_ind / half_interval
                else:
                    weight = 1 - (curr_ind - half_interval) / half_interval
                triangle_copy[ind][0] = weight * point[0] + (1 - weight) * target_point[0]
                triangle_copy[ind][1] = weight * point[1] + (1 - weight) * target_point[1]

            triangle_surface = pygame.Surface((self.width, self.height))
            #pygame.draw.polygon(triangle_surface, self.color, triangle_copy)
            pygame.draw.lines(triangle_surface, self.color, True, triangle_copy, 2)
            triangle_surface.set_alpha(self.alpha)
            triangle_surface.set_colorkey((0, 0, 0))
            surface.blit(triangle_surface.convert_alpha(), (0, 0))
