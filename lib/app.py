#!/usr/bin/python3
# -*- coding: utf-8 -*-
import numpy as np
from lib.panels import *
from lib.backgrounds import Background, DynamicImage, DynamicTriangle, DynamicTrace


class App:
    def __init__(self, args=None):
        pygame.init()

        self.args = args

        self._screen_width = 480
        self._screen_height = 320
        self._screen_size = (self._screen_width, self._screen_height)
        self._frame_rate = 10
        self._fullscreen = self.args.fullscreen if self.args else False

        if self._fullscreen:
            self.display = pygame.display.set_mode(self._screen_size, pygame.FULLSCREEN)
        else:
            self.display = pygame.display.set_mode(self._screen_size)

        self._window_icon = pygame.image.load(os.path.join('images', 'icon', 'small-rpi.png')).convert_alpha()
        pygame.display.set_icon(self._window_icon)
        pygame.display.set_caption("rpi interface")

        self.screen = pygame.Surface(self._screen_size)
        self._invert_screen = self.args.invert if self.args else False

        self._done = False

        pygame.mouse.set_visible(False)

        self.clock = pygame.time.Clock()

        self.camera = cv2.VideoCapture(0)

        self.main_panel = MainPanel(self)
        self.night_panel = NightPanel(self)
        self.night_panel.always_update = True
        self.news_panel = NewsPanel(self)
        self.search_panel = SearchPanel(self)
        self.system_info_panel = SystemInfoPanel(self)
        self.system_info_panel.always_update = True
        self.stock_panel = StockPanel(self)
        self.map_panel = MapPanel(self)
        self.camera_panel = CameraPanel(self, self.camera)
        self.panels = [self.main_panel, self.night_panel, self.news_panel, self.search_panel,
                       self.system_info_panel, self.stock_panel, self.map_panel, self.camera_panel]
        self.active_panel = self.main_panel
        self._night_mode = False

        self.blank_background = Background(width=self._screen_width,
                                           height=self._screen_height,
                                           color=(0, 0, 0))
        self.image_background = DynamicImage(width=self._screen_width,
                                             height=self._screen_height,
                                             alpha=180, speed=0.1)
        self.triangle_background = DynamicTriangle(width=self._screen_width,
                                                   height=self._screen_height,
                                                   color=(255, 165, 0), alpha=120,
                                                   total_points=30,
                                                   total_triangles=10,
                                                   repeat_interval=20)
        self.trace_background = DynamicTrace(width=self._screen_width,
                                             height=self._screen_height,
                                             alpha=160, color1=(255, 215, 0),
                                             color2=(135, 200, 255),
                                             steps=50, radius=4, trace_length=75)
        self.backgrounds = [self.image_background, self.triangle_background,
                            self.trace_background, self.blank_background]
        self._background_type = 0

        self._brightness_last_update = time.time()
        self._brightness_update_interval = 1
        self._brightness_thres = 80
        self._brightness = 1.0

        self._setup()

    def _setup(self):
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
                elif event.key == pygame.K_p:
                    self._toggle_background_type()

        pressed = pygame.key.get_pressed()
        if pressed[pygame.K_q] and (pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]):
            self._done = True

    def _draw_screen(self):
        self.screen.fill((0, 0, 0))

        self._draw_background(self.screen)
        self.active_panel.draw(self.screen)
        self._apply_brightness(self.screen)
        if self._invert_screen:
            self.screen = pygame.transform.rotate(self.screen, 180)
        self.display.blit(self.screen, (0, 0))

        pygame.display.flip()

    def _update_screen(self):
        if self.camera and time.time() - self._brightness_last_update > self._brightness_update_interval:
            #self._update_brightness()
            self._brightness_last_update = time.time()

        self.backgrounds[self._background_type].update()

        for panel in self.panels:
            if panel == self.active_panel or panel.is_always_update():
                panel.update()

    def _toggle_background_type(self):
        if len(self.backgrounds) == 1:
            return

        self.backgrounds[self._background_type].on_leave()
        self._background_type += 1
        if self._background_type >= len(self.backgrounds):
            self._background_type = 0
        self.backgrounds[self._background_type].on_enter()

    def _draw_background(self, screen):
        background_surface = pygame.Surface((self._screen_width, self._screen_height))
        self.backgrounds[self._background_type].draw(background_surface)
        screen.blit(background_surface.convert(), (0, 0))

    def _apply_brightness(self, screen):
        if self.active_panel is self.camera_panel:
            return

        if 6 < dt.now().hour < 18:
            return

        brightness_surface = pygame.Surface((self._screen_width, self._screen_height))
        brightness_surface.fill((0, 0, 0))
        alpha_factor = min((1 - self._brightness), 0.3)
        brightness_surface.set_alpha(int(alpha_factor * 255))
        screen.blit(brightness_surface.convert(), (0, 0))

    def _update_brightness(self):
        ret, frame = self.camera.read()
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        samples = random.sample(np.ravel(gray), 100)
        samples_avg = sum(samples) / len(samples)
        if samples_avg >= self._brightness_thres:
            self._brightness = 1.0
        else:
            self._brightness = samples_avg / self._brightness_thres

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
            self._draw_screen()
            self.clock.tick(self._frame_rate)

        if self.camera:
            self.camera.release()
