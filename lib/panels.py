#!/usr/bin/python3
# -*- coding: utf-8 -*-
import os
import time
import glob
import queue
import psutil
import pygame
from abc import ABCMeta
from datetime import datetime as dt
from lib.buttons import Button
from lib.games import GameSnake, GameTetris, GameFlip
from lib.widgets import News, NewsList, Weather, Calendar, Traffic, Stock, \
    SystemInfo, Time, NightTime, Content, Search, Chart, ChartCaption, Map, \
    List, Calculator, Camera, QRCode, StatusBar
from lib.popups import InfoPopup, ConfirmPopup, InputPopup


class Panel:
    __metaclass__ = ABCMeta

    def __init__(self, app):
        super(Panel, self).__init__()

        self.app = app
        self.args = app.args
        self.always_update = False
        self.invert_screen = self.args.invert if self.args else False
        self.screen_width = app.get_width()
        self.screen_height = app.get_height()

        self.widgets = []
        self.buttons = []
        self.popup = None
        self.default_font_name = pygame.font.get_default_font()
        self.active_widget = None
        if self.widgets:
            self.active_widget = self.widgets[0]

    def set_active_widget(self, widget):
        if self.active_widget is not widget:
            if self.active_widget is not None:
                self.active_widget.set_active(False)
            self.active_widget = widget
            if widget is not None:
                widget.set_active(True)

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass

    def _on_enter(self):
        pass

    def _on_exit(self):
        pass

    def is_always_update(self):
        return self.always_update

    def enter(self):
        for button in self.buttons:
            button.set_active(True)

        self._on_enter()

    def exit(self):
        for button in self.buttons:
            button.set_active(False)

        self._on_exit()

    def setup(self):
        for widget in self.widgets:
            widget.setup()

    def update(self):
        self._on_update()
        for widget in self.widgets:
            widget.update()

        if self.popup:
            self.popup.update()
            if not self.popup.is_active:
                self.popup = None

    def draw(self, screen):
        self._on_draw(screen)
        for widget in self.widgets:
            widget.draw(screen)
        for button in self.buttons:
            button.draw(screen)

        if self.popup:
            self.popup.draw(screen)

    def handle_events(self, event):
        if self.popup:
            self.popup.handle_events(event)
            return True

        handled = False
        if event.type == pygame.MOUSEBUTTONDOWN:
            clicked = False
            for button in self.buttons:
                if button.is_focused():
                    button.click()
                    clicked = True
                    handled = True
            if not clicked:
                self.handle_panel_events(event)

        if self.active_widget:
            self.active_widget.handle_events(event)
            if not self.active_widget.is_active:
                self.active_widget = None
            else:
                handled = True
        else:
            if event.type == pygame.KEYDOWN:
                if event.key == pygame.K_ESCAPE:
                    self.app.set_active_panel(self.app.main_panel)
                else:
                    self.handle_panel_events(event)

        return handled

    def get_screen_size(self):
        return self.screen_width, self.screen_height

    def get_setting(self, name, default=None):
        return self.app.get_setting(name, default=default)

    def set_setting(self, name, value):
        return self.app.set_setting(name, value)

    def handle_panel_events(self, event):
        pass

    def create_popup(self, category, *args, **kwargs):
        if self.popup is not None:
            return

        if category == 'info':
            new_popup = InfoPopup(*args, **kwargs)
        elif category == 'confirm':
            new_popup = ConfirmPopup(*args, **kwargs)
        elif category == 'input':
            new_popup = InputPopup(*args, **kwargs)
        else:
            return

        self.popup = new_popup
        self.popup.setup()
        self.popup.set_active(True)
        self.popup.set_align('center')


class MainPanel(Panel):
    def __init__(self, app):
        super(MainPanel, self).__init__(app)

        self.news_widget = News(self, 30, 300)
        self.weather_widget = Weather(self, 10, 75)
        self.time_widget = Time(self)
        self.calendar_widget = Calendar(self, 215, 90, max_rows=9, max_past_days=2,
                                        timeout=30, align="right", max_name_length=17)
        self.stock_widget = Stock(self, 5, 5)
        self.systeminfo_widget = SystemInfo(self, 10, 10, ip_info=False)
        self.traffic_widget = Traffic(self, 180, 10)
        self.statusbar_widget = StatusBar(self, 0, 10, centered=True)
        self.widgets = [self.news_widget, self.weather_widget, self.time_widget,
                        self.calendar_widget, self.systeminfo_widget, self.traffic_widget,
                        self.statusbar_widget]

        self._night_icon_path = os.path.join("images", "icon", "night.gif")
        self._night_icon_size = 25
        self._night_icon = pygame.transform.scale(pygame.image.load(self._night_icon_path),
                                                  (self._night_icon_size, ) * 2)
        self.night_button = Button(self, -1, self.screen_height - self._night_icon_size + 1,
                                   image=self._night_icon, on_click=self.enter_night_mode)

        self._settings_icon_path = os.path.join("images", "icon", "settings.png")
        self._settings_icon_size = 24
        self._settings_icon = pygame.transform.scale(pygame.image.load(self._settings_icon_path),
                                                     (self._settings_icon_size, ) * 2)
        self._settings_button = Button(self, self.screen_width - self._settings_icon_size, 
                                       self.screen_height - self._settings_icon_size,
                                       image=self._settings_icon, on_click=self.settings_popup,
                                       background_color=(0, 0, 0), background_alpha=80)

        self.buttons = [self.night_button, self._settings_button]

    def _on_update(self):
        now = dt.now()
        if now.hour == 0 and now.minute == 0 and now.second == 0:
            self.enter_night_mode()

    def _set_brightness(self):
        data = self.popup.get_input()
        main_brightness = int(data["Main Brightness (0-9)"])
        night_brightness = int(data["Night Brightness (0-9)"])
        self.app.set_brightness(main_brightness, night_brightness)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_c:
                self.set_active_widget(self.calendar_widget)
            elif event.key == pygame.K_t:
                self.traffic_widget.set_locations()
            elif event.key == pygame.K_l:
                self.weather_widget.get_location_from_popup()
            elif event.key == pygame.K_u:
                self.settings_popup()

    def enter_night_mode(self):
        self.app.set_active_panel(self.app.night_panel)

    def settings_popup(self):
        main_brightness, night_brightness = self.app.get_brightness()
        self.create_popup('input', self, 300, 200, input_width=50,
                          entries=["Main Brightness (0-9)", "Night Brightness (0-9)"],
                          required=[r'^[0-9]$', r'^[0-9]$'],
                          values=[str(main_brightness), str(night_brightness)],
                          close_action=self._set_brightness)
        self.popup.set_title('Settings')


class NightPanel(Panel):
    def __init__(self, app):
        super(NightPanel, self).__init__(app)

        self.time_widget = NightTime(self)
        self.widgets = [self.time_widget]

        self._curr_hour = dt.now().hour
        self._curr_minute = dt.now().minute

    def _on_update(self):
        now = dt.now()
        self.curr_hour = now.hour
        self.curr_minute = now.minute
        self.curr_sec = now.second
        self._auto_set_night()

    def _auto_set_night(self):
        if self.curr_hour == 6 and self.curr_minute == 0 and self.curr_sec == 0:
            self.app.set_active_panel(self.app.main_panel)

    def handle_panel_events(self, event):
        if event.type == pygame.MOUSEBUTTONDOWN:
            self.app.set_active_panel(self.app.main_panel)


class NewsPanel(Panel):
    def __init__(self, app):
        super(NewsPanel, self).__init__(app)

        self._news_main_font = pygame.font.SysFont(self.default_font_name, 35)
        self._news_title_font = pygame.font.SysFont(self.default_font_name, 20)
        self.news_widget = Content(self, 10, 10, "News", font=self._news_main_font)
        self.title_widget = Content(self, 90, 10, "", font=self._news_title_font,
                                    max_width=self.screen_width - 100, max_height=30,
                                    borders=['left'], margin=(10, 0, 0, 0))
        self.newslist_widget = NewsList(self, 10, 45, max_width=self.screen_width - 20,
                                        max_height=self.screen_height - 60,
                                        title_widget=self.title_widget)
        self.widgets = [self.news_widget, self.title_widget, self.newslist_widget]

        self.set_active_widget(self.newslist_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            self.set_active_widget(self.newslist_widget)
            self.active_widget.handle_events(event)

    def _on_enter(self):
        self.set_active_widget(self.newslist_widget)


class SearchPanel(Panel):
    def __init__(self, app):
        super(SearchPanel, self).__init__(app)

        self._search_str_font = pygame.font.Font("fonts/FreeSans.ttf", 18)
        self._search_result_font = pygame.font.Font("fonts/FreeSans.ttf", 16)
        self.search_widget = Search(self, 10, 10, str_font=self._search_str_font,
                                    result_font=self._search_result_font,
                                    max_width=self.screen_width - 40,
                                    max_height=self.screen_height - 45)
        self.widgets = [self.search_widget]

        self.set_active_widget(self.search_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.search_widget)

    def _on_enter(self):
        self.set_active_widget(self.search_widget)

    def _on_exit(self):
        self.search_widget.reset()


class SystemInfoPanel(Panel):
    def __init__(self, app):
        super(SystemInfoPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)
        self._caption_font = pygame.font.Font("fonts/FreeSans.ttf", 13)
        self._info_font = pygame.font.Font("fonts/FreeSans.ttf", 13)

        self._max_size = 120
        self._update_interval = 0.5
        self._cpu_info = queue.Queue(maxsize=self._max_size)
        self._last_cpu_info = 0
        self._memory_info = queue.Queue(maxsize=self._max_size)
        self._cputemp_info = queue.Queue(maxsize=self._max_size)
        self._system_info = {"CPU": self._cpu_info, "Memory": self._memory_info,
                             "CPU Temp": self._cputemp_info}
        self._info_colors = {"CPU": "green", "Memory": "yellow", "CPU Temp": "orange"}

        self.title_widget = Content(self, 10, 10, "System Info", font=self._title_font)
        self.chart_widget = Chart(self, 30, 70, info=self._system_info,
                                  width=self.screen_width - 50, height=self.screen_height - 100,
                                  max_x=int(self._max_size * self._update_interval),
                                  info_colors=self._info_colors, line_width=2,
                                  x_unit=self._update_interval, y_unit=1,
                                  x_label_interval=10, y_label_interval=20,
                                  background=True, background_color=(75, 75, 75),
                                  background_alpha=180)
        self._info_widget = SystemInfo(self, 160, 10, font=self._info_font,
                                       cpu_info=False, memory_info=False,
                                       disk_info=False, percent_bar=False,
                                       ip_info=True)
        self.caption_widget = ChartCaption(self, 357, 10, self._info_colors,
                                           font=self._caption_font)
        self.statusbar_widget = StatusBar(self, 15, 40)
        self.widgets = [self.title_widget, self.chart_widget, self._info_widget, self.caption_widget, self.statusbar_widget]

        self._last_update = time.time()

    def _on_update(self):
        current_time = time.time()
        if self._max_size <= 0 or current_time - self._last_update < self._update_interval:
            return
        if self._cpu_info.full():
            self._cpu_info.get_nowait()
        if self._memory_info.full():
            self._memory_info.get_nowait()
        if self._cputemp_info.full():
            self._cputemp_info.get_nowait()

        cpu_info = psutil.cpu_percent()
        if cpu_info == 0:
            cpu_info = self._last_cpu_info
        else:
            self._last_cpu_info = cpu_info
        self._cpu_info.put(cpu_info)
        self._memory_info.put(psutil.virtual_memory().percent)

        try:
            temperatures = psutil.sensors_temperatures()
        except AttributeError:
            temperatures = []
        for sensor_name in temperatures:
            if sensor_name.find('cpu') != -1:
                cpu_temps = temperatures[sensor_name]
                if len(cpu_temps) > 0:
                    cpu_temp = cpu_temps[0].current
                    self._cputemp_info.put(cpu_temp)

        self._last_update = current_time


class StockPanel(Panel):
    def __init__(self, app):
        super(StockPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)

        self.title_widget = Content(self, 10, 10, "Stock", font=self._title_font)
        self.stock_widget = Stock(self, 25, 40, chart=True, chart_width=self.screen_width - 80,
                                  chart_height=self.screen_height - 120)
        self.widgets = [self.title_widget, self.stock_widget]

    def _on_enter(self):
        self.set_active_widget(self.stock_widget)

    def _on_exit(self):
        self.stock_widget.clear()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.stock_widget)


class MapPanel(Panel):
    def __init__(self, app):
        super(MapPanel, self).__init__(app)

        self._title_font = pygame.font.SysFont(self.default_font_name, 35)

        self.title_widget = Content(self, 10, 10, "Map", font=self._title_font)
        self.map_widget = Map(self, 10, 45, map_width=400, map_height=170,
                              map_padding=0.075, background_alpha=100)
        self.widgets = [self.title_widget, self.map_widget]

    def _on_enter(self):
        self.set_active_widget(self.map_widget)

    def _on_exit(self):
        self.map_widget.reset()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.map_widget)


class CameraPanel(Panel):
    def __init__(self, app):
        super(CameraPanel, self).__init__(app)

        self.camera_widget = Camera(self, 0, 0)
        self.widgets = [self.camera_widget]

    def _on_enter(self):
        self.set_active_widget(self.camera_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.camera_widget)


class GamePanel(Panel):
    def __init__(self, app):
        super(GamePanel, self).__init__(app)

        self.title_font = pygame.font.SysFont(self.default_font_name, 35)
        self.title_widget = Content(self, 10, 10, "Game", font=self.title_font)

        self.game_names = []
        self.menu_widget = List(self, 10, 45, items=self.game_names,
                                max_width=400, max_height=260, selectable=True,
                                select_event=self.select_game, reset_on_exit=False)
        self.widgets = [self.title_widget, self.menu_widget]

        self.games = {}
        self._add_game("Snake", GameSnake(self, self.exit_game, total_rows=16, total_cols=16))
        self._add_game("Tetris", GameTetris(self, self.exit_game, total_rows=16, total_cols=10))
        self._add_game("Flip", GameFlip(self, self.exit_game, board_size=10, border_width=1))

    def _add_game(self, name, game):
        self.game_names.append(name)
        self.games[name] = game
        self.widgets.append(game)

    def select_game(self):
        selected_game = self.games.get(self.game_names[self.menu_widget.get_selected()])
        self.set_active_widget(selected_game)

    def exit_game(self):
        self.set_active_widget(self.menu_widget)

    def _on_enter(self):
        self.set_active_widget(self.menu_widget)

    def _on_exit(self):
        self.menu_widget.reset()

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.menu_widget)


class CalculatorPanel(Panel):
    def __init__(self, app):
        super(CalculatorPanel, self).__init__(app)

        self.calculator_widget = Calculator(self, 10, 10, width=450, height=300, key_padding=3)

        self.widgets = [self.calculator_widget]

    def _on_enter(self):
        self.set_active_widget(self.calculator_widget)

    def _on_exit(self):
        self.calculator_widget.reset()


class QRCodePanel(Panel):
    def __init__(self, app):
        super(QRCodePanel, self).__init__(app)

        self.qr_widget = QRCode(self, 10, 10, width=430, height=260)
        self.widgets = [self.qr_widget]

        self.set_active_widget(self.qr_widget)

    def handle_panel_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self.set_active_widget(self.qr_widget)

    def _on_enter(self):
        self.set_active_widget(self.qr_widget)

    def _on_exit(self):
        self.qr_widget.reset()
