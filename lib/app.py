#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import time
import glob
import yaml
import random
import pygame
from datetime import datetime as dt
from lib.panels import MainPanel, NightPanel, NewsPanel, SearchPanel, \
    SystemInfoPanel, StockPanel, MapPanel, CameraPanel, GamePanel, \
    CalculatorPanel, QRCodePanel
from lib.backgrounds import Background, DynamicImage, \
    DynamicTriangle, DynamicTrace, VideoPlayer
from lib.util import log_to_file, shift_pressed, ctrl_pressed


class App:
    def __init__(self, args=None):
        pygame.init()

        self.args = args

        self._screen_width = 480
        self._screen_height = 320
        self._screen_size = (self._screen_width, self._screen_height)
        self._performance_mode = self.args.performance if self.args else False
        self._normal_frame_rate = 60 if self._performance_mode else 10
        self._game_frame_rate = 60 if self._performance_mode else 30
        self._frame_rate = self._normal_frame_rate
        self._fullscreen = self.args.fullscreen if self.args else False
        self._debug_mode = self.args.debug if self.args else False
        self._dryrun_timeout = self.args.dryrun if self.args else -1
        self._dryrun_background_timeout = 2
        self._dryrun_background_last_update = time.time()

        if self._fullscreen:
            self.display = pygame.display.set_mode(self._screen_size, pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode(self._screen_size)

        self._window_icon = pygame.image.load(os.path.join('images', 'icon', 'small-rpi.png')).convert_alpha()
        pygame.display.set_icon(self._window_icon)
        pygame.display.set_caption('rpi interface')

        self.screen = pygame.Surface(self._screen_size)
        self._invert_screen = self.args.invert if self.args else False

        self._setting_file = 'settings.yaml'
        self._settings = None
        self._load_settings()

        self._main_brightness = self.get_setting('main_brightness', default=9)
        self._night_brightness = self.get_setting('night_brightness', default=3)

        self._done = False

        self._mouse_last_move = time.time()
        self._mouse_timeout = 5
        self._mouse_visible = False
        pygame.mouse.set_cursor(*pygame.cursors.arrow)

        self.clock = pygame.time.Clock()

        self.main_panel = MainPanel(self)
        self.main_panel.always_update = True
        self.night_panel = NightPanel(self)
        self.news_panel = NewsPanel(self)
        self.news_panel.always_update = True
        self.search_panel = SearchPanel(self)
        self.system_info_panel = SystemInfoPanel(self)
        self.system_info_panel.always_update = True
        self.stock_panel = StockPanel(self)
        self.map_panel = MapPanel(self)
        self.camera_panel = CameraPanel(self)
        self.game_panel = GamePanel(self)
        self.calculator_panel = CalculatorPanel(self)
        self.qrcode_panel = QRCodePanel(self)
        self.panels = [self.main_panel, self.night_panel, self.news_panel, self.search_panel,
                       self.system_info_panel, self.stock_panel, self.map_panel, self.camera_panel,
                       self.game_panel, self.calculator_panel, self.qrcode_panel]
        self.active_panel = None

        self.blank_background = Background(width=self._screen_width,
                                           height=self._screen_height,
                                           color=(0, 0, 0))
        self.image_background = DynamicImage(width=self._screen_width,
                                             height=self._screen_height,
                                             alpha=180, speed=0.1)
        self.triangle_background = DynamicTriangle(width=self._screen_width,
                                                   height=self._screen_height,
                                                   color=(255, 165, 0), alpha=120,
                                                   total_points=30, total_triangles=10,
                                                   repeat_interval=20, line_width=2,
                                                   point_size=4)
        self.trace_background = DynamicTrace(width=self._screen_width,
                                             height=self._screen_height,
                                             alpha=160, color1=(255, 215, 0),
                                             color2=(135, 200, 255),
                                             steps=50, radius=4, trace_length=75)
        self.video_background1 = VideoPlayer(width=self._screen_width,
                                             height=self._screen_height,
                                             color=(0, 0, 0), alpha=160,
                                             video_path=os.path.join('videos', 'city.mov'),
                                             fps=10)
        self.video_background2 = VideoPlayer(width=self._screen_width,
                                             height=self._screen_height,
                                             color=(0, 0, 0), alpha=160,
                                             video_path=os.path.join('videos', 'car.mov'),
                                             fps=10)
        self.video_background3 = VideoPlayer(width=self._screen_width,
                                             height=self._screen_height,
                                             color=(0, 0, 0), alpha=160,
                                             video_path=os.path.join('videos', 'wireframe.mov'),
                                             fps=24)
        self.backgrounds = [self.video_background1, self.video_background2, self.video_background3,
                            self.triangle_background, self.image_background,
                            self.trace_background, self.blank_background]
        self._background_type = self.get_setting('background_type', default=0)
        if self._background_type >= len(self.backgrounds) or \
           self._background_type < 0:
            self._background_type = 0
            self.set_setting('background_type', self._background_type)

        self._frame_rate_font = pygame.font.Font('fonts/FreeSans.ttf', 15)
        self._actual_frame_rate = 0
        self._frame_last_update = time.time()
        self._frame_text_last_update = time.time()

        self._start_time = time.time()

        self._setup()

    def _setup(self):
        if self.backgrounds:
            self.backgrounds[self._background_type].enter()

        for panel in self.panels:
            panel.setup()
        self.set_active_panel(self.main_panel)

    def _handle_events(self):
        for event in pygame.event.get():
            handled = self.active_panel.handle_events(event)

            if event.type == pygame.QUIT:
                self._done = True
                return
            elif event.type == pygame.KEYDOWN:
                if event.key == pygame.K_q and ctrl_pressed():
                    self._done = True
                    return
            
            if event.type == pygame.KEYDOWN and \
               self.active_panel is self.main_panel and \
               not handled:
                if event.key == pygame.K_d:
                    self.set_active_panel(self.night_panel)
                elif event.key == pygame.K_n:
                    self.set_active_panel(self.news_panel)
                elif event.key == pygame.K_b:
                    self.set_active_panel(self.search_panel)
                elif event.key == pygame.K_i:
                    self.set_active_panel(self.system_info_panel)
                elif event.key == pygame.K_s:
                    self.set_active_panel(self.stock_panel)
                elif event.key == pygame.K_m:
                    self.set_active_panel(self.map_panel)
                elif event.key == pygame.K_v:
                    self.set_active_panel(self.camera_panel)
                elif event.key == pygame.K_g:
                    self.set_active_panel(self.game_panel)
                elif event.key == pygame.K_a:
                    self.set_active_panel(self.calculator_panel)
                elif event.key == pygame.K_r:
                    self.set_active_panel(self.qrcode_panel)
                elif event.key == pygame.K_p:
                    reverse_dir = False
                    if shift_pressed(): 
                        reverse_dir = True
                    self._toggle_background_type(reverse=reverse_dir)

            if event.type == pygame.MOUSEMOTION:
                self._mouse_last_move = time.time()
                self._set_mouse_visible(True)

    def _draw_screen(self):
        self.screen.fill((0, 0, 0))

        self._draw_background(self.screen)
        self.active_panel.draw(self.screen)
        if self._debug_mode:
            self._draw_frame_rate(self.screen)
        if self._invert_screen:
            self.screen = pygame.transform.rotate(self.screen, 180)
        self.display.blit(self.screen, (0, 0))

        pygame.display.flip()

    def _update_screen(self):
        current_time = time.time()
        
        if self._mouse_visible and current_time - self._mouse_last_move > self._mouse_timeout:
            self._set_mouse_visible(False)

        self.backgrounds[self._background_type].update()

        for panel in self.panels:
            if panel == self.active_panel or panel.is_always_update():
                panel.update()

    def _toggle_background_type(self, reverse=False):
        self.backgrounds[self._background_type].exit()
        if reverse:
            self._background_type -= 1
        else:
            self._background_type += 1
        
        total_backgrounds = len(self.backgrounds)
        if self._background_type >= total_backgrounds:
            self._background_type = 0
        elif self._background_type < 0:
            self._background_type = total_backgrounds - 1

        self.backgrounds[self._background_type].enter()
        self.set_setting('background_type', self._background_type)

    def _draw_background(self, screen):
        background_surface = pygame.Surface((self._screen_width, self._screen_height))
        self.backgrounds[self._background_type].draw(background_surface)
        screen.blit(background_surface, (0, 0))
        self._apply_brightness(screen)

    def _apply_brightness(self, screen):
        if self.active_panel is self.camera_panel:
            return

        brightness = self._night_brightness if self.active_panel is self.night_panel else self._main_brightness

        brightness_surface = pygame.Surface((self._screen_width, self._screen_height))
        brightness_surface.fill((0, 0, 0))
        alpha_factor = min(0.1 + 0.9 / 9 * brightness, 1)
        brightness_surface.set_alpha(int((1 - alpha_factor) * 255))
        screen.blit(brightness_surface, (0, 0))

    def _draw_frame_rate(self, screen):
        current_time = time.time()
        update_interval = time.time() - self._frame_last_update
        self._frame_last_update = current_time

        if current_time - self._frame_text_last_update > 1:
            self._actual_frame_rate = int(1 / update_interval)
            self._frame_text_last_update = current_time

        framerate_text = self._frame_rate_font.render('FPS: {}'.format(self._actual_frame_rate), True, (0, 255, 0))
        pygame.draw.rect(screen, (0, 0, 0), (10, 10, framerate_text.get_width(), framerate_text.get_height()))
        screen.blit(framerate_text, (10, 10))
    
    def _set_mouse_visible(self, status):
        self._mouse_visible = status
        pygame.mouse.set_visible(self._mouse_visible)

    def _cleanup(self):
        # clean up background
        self.backgrounds[self._background_type].exit()
        
        # delete cached news images
        if os.path.isdir('news_images'):
            for image_file in glob.glob('news_images/*'):
                os.remove(image_file)

    def _load_settings(self):
        settings = {}
        if not os.path.isfile(self._setting_file):
            self._settings = settings
            return

        with open(self._setting_file, 'r') as f:
            try:
                settings = yaml.safe_load(f)
            except yaml.YAMLError as e:
                print("Unable to load settings from {}".format(self._setting_file))

        self._settings = settings

    def _save_settings(self):
        with open(self._setting_file, 'w') as f:
            yaml.dump(self._settings, f)
        log_to_file("Settings saved to {}".format(self._setting_file))

    def get_setting(self, name, default=None):
        if self._settings is None:
            log_to_file("Unable to get value for {}. Setting is not ready.".format(name))
            return default

        if name not in self._settings:
            self._settings[name] = default
            self._save_settings()

        return self._settings[name]

    def set_setting(self, name, value):
        if self._settings is None:
            log_to_file("Unable to set {}={}. Setting is not ready.".format(name, value))
            return False

        self._settings[name] = value
        self._save_settings()
        return True

    def set_active_panel(self, panel):
        if self.active_panel is not panel:
            if self.active_panel is not None:
                self.active_panel.exit()
            panel.enter()
            panel.update()
            self.active_panel = panel

    def get_screen(self):
        return self.screen

    def get_width(self):
        return self._screen_width

    def get_height(self):
        return self._screen_height

    def game_frame_rate(self, status):
        if status:
            self._frame_rate = self._game_frame_rate
        else:
            self._frame_rate = self._normal_frame_rate

    def get_brightness(self):
        return self._main_brightness, self._night_brightness

    def set_brightness(self, main, night):
        if not (0 <= main <= 9 and 0 <= night <= 9):
            return

        self._main_brightness = main
        self._night_brightness = night
        self.set_setting("main_brightness", main)
        self.set_setting("night_brightness", night)

    def start(self):
        while not self._done:
            self._handle_events()
            self._update_screen()
            self._draw_screen()
            self.clock.tick(self._frame_rate)

            curr_time = time.time()
            if self._dryrun_timeout != -1:
                if curr_time - self._dryrun_background_last_update > self._dryrun_background_timeout:
                    self._toggle_background_type()
                    self._dryrun_background_last_update = curr_time

                if curr_time - self._start_time > self._dryrun_timeout:
                    self._done = True

        self._cleanup()
