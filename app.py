#!/usr/bin/python
# -*- coding: utf-8 -*-
import pygame
import requests
import time
import math
import os
import glob
import Queue
from threads import *
from panels import *
from util import *

class App:
    def __init__(self, args=None):
        pygame.init()

        self.args = args

        self._screen_width = 480
        self._screen_height = 320
        self._screen_size = (self._screen_width, self._screen_height)
        self._frame_rate = 10
        self._fullscreen = self.args.fullscreen if self.args else False
        pygame.display.set_caption("rpi interface")

        if self._fullscreen:
            self.display = pygame.display.set_mode(self._screen_size, pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode(self._screen_size)

        self.screen = pygame.Surface(self._screen_size)
        self._invert_screen = self.args.invert if self.args else False

        self._done = False

        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        self.main_panel = MainPanel(self)
        self.night_panel = NightPanel(self)
        self.news_panel = NewsPanel(self)
        self.search_panel = SearchPanel(self)
        self.system_info_panel = SystemInfoPanel(self)
        self.system_info_panel.always_update = True
        self.panels = [self.main_panel, self.night_panel, self.news_panel, self.search_panel, self.system_info_panel]
        self.active_panel = self.main_panel
        self._night_mode = False

        self._background_image_directory = os.path.join("images", "background")
        self._background_image_size = self._screen_height
        self._background_alpha = 180
        self._background_speed_rate = 1.2
        self._background_images = []

        self._setup()

    def _setup(self):
        self._background_image_sets = []
        for image_path in glob.glob(os.path.join(self._background_image_directory, "*.png")):
            image = pygame.image.load(image_path)
            image = pygame.transform.scale(image, (self._background_image_size, self._background_image_size))
            self._background_images.append(image)
        self._background_images.reverse()

        for panel in self.panels:
            panel.setup()

    def _handle_events(self):
        for event in pygame.event.get():
            self.active_panel.handle_events(event)

            if event.type == pygame.QUIT:
                self._done = True
            if event.type == pygame.KEYDOWN and self.active_panel is self.main_panel:
                if event.key == pygame.K_d:
                    self.set_active_panel(self.night_panel)
                if event.key == pygame.K_n:
                    self.set_active_panel(self.news_panel)
                if event.key == pygame.K_b:
                    self.set_active_panel(self.search_panel)
                if event.key == pygame.K_s:
                    self.set_active_panel(self.system_info_panel)

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_q] and (pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]):
            self._done = True

    def _update_screen(self):
        self.screen.fill((0, 0, 0))

        self._draw_background(self.screen)
        self.active_panel.draw(self.screen)
        if self._invert_screen:
            self.screen = pygame.transform.rotate(self.screen, 180)
        self.display.blit(self.screen, (0, 0))

        pygame.display.flip()

    def _on_update(self):
        for panel in self.panels:
            if panel == self.active_panel or panel.is_always_update():
                panel.update()

    def _draw_background(self, screen):
        x_offset = (self._screen_width - self._background_image_size) / 2
        y_offset = (self._screen_height - self._background_image_size) / 2
        current_time = int(time.time() * self._frame_rate)
        background_surface = pygame.Surface((self._screen_width, self._screen_height))
        rotated_image_queue = Queue.Queue()
        threads = []
        for ind, image in enumerate(self._background_images):
            image_center = image.get_rect().center
            image_center = (image_center[0] + x_offset, image_center[1] + y_offset)
            degree = int(current_time / (2 ** ind) * self._background_speed_rate) % 360
            thread = ImageRotateThread(image, image_center, degree, rotated_image_queue)
            threads.append(thread)
            thread.start()

        for thread in threads:
            thread.join()

        for rotated_image, rect in rotated_image_queue.queue:
            background_surface.blit(rotated_image, rect)

        background_surface.set_alpha(self._background_alpha)
        screen.blit(background_surface.convert(), (0, 0))

    def set_active_panel(self, panel):
        if self.active_panel is not panel:
            self.active_panel.on_exit()
            panel.on_enter()
            self.active_panel = panel

    def get_screen(self):
        return self.screen

    def get_width(self):
        return self._screen_width

    def get_height(self):
        return self._screen_height

    def start(self):
        while not self._done:
            self._handle_events()
            self._update_screen()
            self._on_update()
            self.clock.tick(self._frame_rate)
