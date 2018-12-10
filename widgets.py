#!/usr/bin/python
# -*- coding: utf-8 -*-
import time
import Queue
import re
import glob
import psutil
import polyline
from bs4 import BeautifulSoup
from table import Table
from threads import *
from shapes import *


class Widget:
    __metaclass__ = ABCMeta

    def __init__(self, parent, x, y):
        self.parent = parent
        self.x = x
        self.y = y

        self.colors = {"black": (0, 0, 0),
                       "white": (255, 255, 255),
                       "gray": (100, 100, 100),
                       "lightgray": (75, 75, 75),
                       "green": (0, 255, 0),
                       "red": (255, 0, 0),
                       "blue": (30, 144, 255),
                       "lightblue": (0, 191, 255),
                       "yellow": (255, 255, 0),
                       "orange": (255, 165, 0)}
        self.default_font_name = pygame.font.get_default_font()
        self.default_font = pygame.font.SysFont(self.default_font_name, 25)
        self._screen_width = parent.app.get_width()
        self._screen_height = parent.app.get_height()
        self.is_active = False
        self._shapes = []
        self._subwidgets = []

    def setup(self):
        for widget in self._subwidgets:
            widget.setup()
        self.clear_shapes()
        self._on_setup()

    def update(self):
        for widget in self._subwidgets:
            widget.update()
        self._on_update()

    def draw(self, screen):
        self._draw_background(screen)
        for widget in self._subwidgets:
            widget.draw(screen)
        for shape in self._shapes:
            self._draw_shape(screen, shape)
        self._on_draw(screen)

    @abstractmethod
    def _on_setup(self):
        pass

    @abstractmethod
    def _on_update(self):
        pass

    @abstractmethod
    def _on_draw(self, screen):
        pass

    def _draw_background(self, screen):
        pass

    def _handle_widget_events(self, event):
        pass

    def _on_enter(self):
        pass

    def _on_exit(self):
        pass

    def add_shape(self, shape):
        self._shapes.append(shape)

    def clear_shapes(self):
        self._shapes = []

    def _draw_shape(self, screen, shape):
        if isinstance(shape, Line):
            pygame.draw.line(screen, shape.color, shape.start_pos, shape.end_pos, shape.width)
        elif isinstance(shape, DashLine):
            for line in shape.lines:
                self._draw_shape(screen, line)
        elif isinstance(shape, Lines):
            if shape.anti_alias:
                try:
                    pygame.draw.aalines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
                except ValueError:
                    pygame.draw.lines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
            else:
                pygame.draw.lines(screen, shape.color, shape.closed, shape.pointlist, shape.width)
            for point in shape.pointlist:
                screen.set_at(point, shape.color)
        elif isinstance(shape, Text):
            screen.blit(shape.text_surface, shape.pos)
        elif isinstance(shape, Rectangle):
            pygame.draw.rect(screen, shape.color, shape.to_pygame_rect(), shape.line_width)
        elif isinstance(shape, Polygon):
            pygame.draw.polygon(screen, shape.color, shape.pointlist, shape.width)
        elif isinstance(shape, Circle):
            pygame.draw.circle(screen, shape.color, shape.pos, shape.radius, shape.width)

    def get_pos(self):
        return self.x, self.y

    def set_pos(self, x, y):
        self.x = x
        self.y = y

    def handle_events(self, event):
        for widget in self._subwidgets:
            if widget.is_active:
                if event.type == pygame.KEYDOWN and event.key == pygame.K_ESCAPE:
                    widget.set_active(False)
                    return
                else:
                    widget.handle_events(event)
        self._handle_widget_events(event)

    def set_active(self, status):
        if self.is_active != status:
            self.is_active = status
            if status:
                self._on_enter()
            else:
                self._on_exit()


class News(Widget):
    def __init__(self, parent, x, y):
        super(News, self).__init__(parent, x, y)

        self._news_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._message_font = pygame.font.Font("fonts/FreeSans.ttf", 20)
        self._news_url = "https://newsapi.org/v2/top-headlines"
        self._news_key = "6f19ade7dcd846ef95d927341765f200"
        self._news_payload = {"sources": "google-news-ca", "apiKey": self._news_key}
        self._news_last_update = time.time()
        self._news_index_last_update = time.time()
        self._news_index = 0
        self._news_info_update_interval = 1800
        self._news_line_update_interval = 15
        self._news_info = None
        self._title_max_width = self._screen_width - self.x - 20

    def _get_news(self):
        res = requests.get(self._news_url, params=self._news_payload)
        response = res.json()
        if response.get("status") == "ok":
            self._news_info = response.get("articles")
            self._news_index = 0

        self._news_last_update = time.time()
        log_to_file("News updated")

    def _on_setup(self):
        self._get_news()

    def _on_update(self):
        if time.time() - self._news_last_update > self._news_info_update_interval or self._news_info is None:
            self._get_news()
        elif time.time() - self._news_index_last_update > self._news_line_update_interval and self._news_info:
            self._news_index += 1
            if self._news_index == len(self._news_info):
                self._news_index = 0
            self._news_index_last_update = time.time()

    def _on_draw(self, screen):
        if self._news_info:
            article = self._news_info[self._news_index]
            title = article.get("title")
            title_text = self._news_font.render(title, True, self.colors['white'])
            if title_text.get_width() > self._title_max_width:
                words = title.split(' ')
                brief_title = words[0]
                current_width = self._news_font.render(brief_title, True, self.colors['white']).get_width()
                space_width = self._news_font.render(' ', True, self.colors['white']).get_width()
                dots_width = self._news_font.render('...', True, self.colors['white']).get_width()
                for word in words[1:]:
                    word_width = self._news_font.render(word, True, self.colors['white']).get_width()
                    if current_width + word_width + space_width + dots_width < self._title_max_width:
                        brief_title += ' ' + word
                        current_width += word_width + space_width
                    else:
                        break
                title_text = self._news_font.render(brief_title + "...", True, self.colors['white'])

            screen.blit(title_text, (self.x + 20, self.y))

            percent = (float(time.time()) - self._news_index_last_update) / self._news_line_update_interval
            pygame.draw.arc(screen, self.colors['green'], (self.x + 5, self.y + 5, 10, 10), math.pi * (0.5 - percent * 2), math.pi * 0.5, 2)


class NewsList(News):
    def __init__(self, parent, x, y, max_width=480, max_height=320, title_widget=None):
        super(NewsList, self).__init__(parent, x, y)

        self.max_width = max_width
        self.max_height = max_height
        self.title_widget = title_widget
        self._news_title_font = pygame.font.Font("fonts/FreeSans.ttf", 17)
        self._prefix = "- "
        self._news_image_directory = "news_images"
        self._title_contents = []
        self._display_lines = []
        self._display_count = 0
        self._start_index = 0
        self._active_index = 0
        self._sidebar_width = 5
        self._sidebar_length = int(self.max_height * 0.618)
        self._active_news = False
        self._display_image = False
        self._images = {}

    def _on_exit(self):
        self._active_news = False
        self._display_image = False
        self._parse_news()

    def _get_news(self):
        super(NewsList, self)._get_news()

        self._title_contents = []
        start_x, start_y = self.x, self.y
        for news in self._news_info:
            title = news.get("title")
            title_content = Content(self.parent, start_x, start_y, title,
                                    font=self._news_title_font, max_width=self.max_width,
                                    max_height=self.max_height, prefix=self._prefix)
            title_content.setup()
            start_y += title_content.get_height()
            self._title_contents.append(title_content)

            image_url = news.get("urlToImage")
            news['imageName'] = self._parse_image_name(image_url) if image_url else ""
            if not image_url:
                continue

            if image_url:
                if not os.path.isdir(self._news_image_directory):
                    os.mkdir(self._news_image_directory)
                image_thread = ImageFetchThread(image_url, news, self._news_image_directory)
                image_thread.daemon = True
                image_thread.start()

    def _parse_news(self):
        self.clear_shapes()
        self._display_lines = []
        self._display_count = 0
        total_height = 0
        is_full = False
        for title_ind, content in enumerate(self._title_contents[self._start_index:]):
            for line_ind, content_line in enumerate(content.get_lines()):
                total_height += content_line.get_height()
                if total_height > self.max_height:
                    is_full = True
                    break
                self._display_lines.append(content_line)
                if self._active_news and title_ind + self._start_index == self._active_index:
                    prefix_length = self._news_title_font.render(self._prefix, True, self.colors['white']).get_width()
                    text_length = content_line.get_width()
                    start_pos = (self.x + prefix_length, self.y + total_height)
                    end_pos = (self.x + text_length, self.y + total_height)
                    self.add_shape(Line(self.colors['green'], start_pos, end_pos))
                if line_ind == len(content.get_lines()) - 1:
                    self._display_count += 1
            if is_full:
                break

    def _page_up(self):
        if self._start_index > 0:
            self._start_index -= 1
            self._parse_news()

    def _page_down(self):
        if len(self._display_lines) < sum([len(content.get_lines()) for content in self._title_contents[self._start_index:]]):
            self._start_index += 1
            self._parse_news()

    def _row_up(self):
        if self._active_index > 0:
            self._active_index -= 1
            if self._start_index > self._active_index:
                self._page_up()
            self._parse_news()

    def _row_down(self):
        if self._active_index < len(self._title_contents) - 1:
            self._active_index += 1
            while self._start_index + self._display_count - 1 < self._active_index:
                self._page_down()
            self._parse_news()

    def _active_news(self):
        self._news_status = True

    def _on_setup(self):
        self._get_news()
        self._parse_news()

    def _on_update(self):
        if time.time() - self._news_last_update > self._news_info_update_interval or self._news_info is None:
            self._get_news()
            self._parse_news()

    def _on_draw(self, screen):
        total_height = 0
        for ind, line in enumerate(self._display_lines):
            screen.blit(line, (self.x, self.y + total_height))
            total_height += line.get_height()

        # draw sidebar
        if len(self._display_lines) < sum([len(content.get_lines()) for content in self._title_contents]):
            pre_length = self._start_index * self.max_height / len(self._news_info)
            sidebar_start = (self.x + self.max_width, self.y + pre_length)
            sidebar_end = (self.x + self.max_width, self.y + pre_length + self._sidebar_length)
            if sidebar_end[1] > self.y + self.max_height:
                sidebar_end = (sidebar_end[0], self.y + self.max_height)
            pygame.draw.line(screen, self.colors['white'], sidebar_start, sidebar_end, self._sidebar_width)
            pygame.draw.line(screen, self.colors['white'], (self.x + self.max_width - self._sidebar_width / 2, self.y),
                            (self.x + self.max_width + self._sidebar_width / 2, self.y), 1)
            pygame.draw.line(screen, self.colors['white'], (self.x + self.max_width - self._sidebar_width / 2, self.y + self.max_height),
                            (self.x + self.max_width + self._sidebar_width / 2, self.y + self.max_height), 1)

        # draw image
        if self._display_image:
            if self.title_widget:
                self.title_widget.set_text(self._news_info[self._active_index]['title'])
            pygame.draw.rect(screen, self.colors['blue'], (self.x, self.y, self.max_width, self.max_height), 3)
            image = None
            image_url = self._news_info[self._active_index]['urlToImage']
            if image_url:
                image_name = self._news_info[self._active_index]['imageName']
                image_path = os.path.join("news_images", image_name)
                if self._images.get(image_name) is not None:
                    image = self._images.get(image_name)
                elif os.path.isfile(image_path):
                    try:
                        image = pygame.image.load(image_path)
                    except pygame.error:
                        image = None
                    if image:
                        image = pygame.transform.scale(image, (self.max_width, self.max_height))
                        image = image.convert()
                        self._images[image_name] = image

                if image:
                    screen.blit(image, (self.x, self.y))
                else:
                    self._draw_no_image_message(screen)
            else:
                self._draw_no_image_message(screen)
        elif self.title_widget:
            self.title_widget.set_text("")

    def _draw_no_image_message(self, screen):
        pygame.draw.rect(screen, self.colors['black'], (self.x, self.y, self.max_width, self.max_height), 0)
        message_text = self._message_font.render("No image to show here...", True, self.colors['white'])
        screen.blit(message_text, (self.x + (self.max_width - message_text.get_width()) / 2,
                                             self.y + (self.max_height - message_text.get_height()) / 2))

    def _parse_image_name(self, image_url):
        image_name = image_url.split('/')[-1]
        image_name = '.'.join(image_name.split('.')[-2:])
        image_name = image_name.lower()
        q_ind = image_name.find('?')
        if q_ind != -1:
            image_name = image_name[:q_ind]
        return image_name

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_DOWN:
                if not self._active_news:
                    self._page_down()
                else:
                    self._row_down()
            elif event.key == pygame.K_UP:
                if not self._active_news:
                    self._page_up()
                else:
                    self._row_up()
            elif event.key == pygame.K_RETURN:
                if self._active_news and self._display_image:
                    self._display_image = False
                    if self.title_widget:
                        self.title_widget.set_text("")
                elif self._active_news:
                    self._display_image = True
                elif not self._active_news:
                    self._active_news = True
                    self._active_index = self._start_index
                    self._parse_news()


class Weather(Widget):
    def __init__(self, parent, x, y):
        super(Weather, self).__init__(parent, x, y)

        self.weather_font = pygame.font.Font("fonts/FreeSans.ttf", 50)
        self.forecast_font = pygame.font.Font("fonts/FreeSans.ttf", 25)
        self.desc_font = pygame.font.Font("fonts/FreeSans.ttf", 25)
        self.change_font = pygame.font.Font("fonts/FreeSans.ttf", 16)
        self.last_update_font = pygame.font.Font("fonts/FreeSans.ttf", 10)

        self._weather_last_update = time.time()
        self._current_weather = None
        self._forecast_weather = None
        self._weather_update_interval = 1800

        self._weather_key = "508b76be5129c25115e5e60848b4c20c"
        self._current_url = "http://api.openweathermap.org/data/2.5/weather"
        self._forecase_url = "http://api.openweathermap.org/data/2.5/forecast"
        self._weather_payload = {"q": "Waterloo,ca", "appid": self._weather_key,
                                 "units": "metric"}
        self._waterloo_key = "97a591e399f591e64a5f4536d08d9574"

        self._current_icon_size = 35
        self._change_icon_size = 25
        self._icon_directory = os.path.join("images", "weather_icons")
        self._current_icons = {}
        self._change_icons = {}

    def _get_weather(self):
        current_res = requests.get(self._current_url, params=self._weather_payload)
        self._current_weather = current_res.json()

        forecast_res = requests.get(self._forecase_url, params=self._weather_payload)
        self._forecast_weather = forecast_res.json()

        self._weather_last_update = time.time()

        log_to_file("Weather updated")

    def _load_icons(self):
        for icon_path in glob.glob(os.path.join(self._icon_directory, "*.png")):
            icon_name = icon_path[-7:-4]
            icon = pygame.image.load(icon_path)
            current_icon = pygame.transform.scale(icon, (self._current_icon_size, self._current_icon_size))
            change_icon = pygame.transform.scale(icon, (self._change_icon_size, self._change_icon_size))
            self._current_icons[icon_name] = current_icon.convert_alpha()
            self._change_icons[icon_name] = change_icon.convert_alpha()

    def _on_setup(self):
        self._load_icons()
        self._get_weather()

    def _on_update(self):
        if (time.time() - self._weather_last_update > self._weather_update_interval or
            self._current_weather is None or
            self._forecast_weather is None):
            self._get_weather()

    def _on_draw(self, screen):
        try:
            current_desc = self._current_weather['weather'][0]['main']
            current_temp = int(self._current_weather['main']['temp'])
            current_str = u"{} ℃".format(current_temp)
            current_icon = self._current_icons[self._current_weather['weather'][0]['icon']]
            forecast_temp = [int(pred['main']['temp']) for pred in self._forecast_weather['list'][:8]]
        except KeyError:
            self._current_weather = None
            self._forecast_weather = None
            return

        forecast_min = min(forecast_temp)
        forecast_max = max(forecast_temp)
        forecast_str = u"{} - {} ℃".format(forecast_min, forecast_max)

        desc_text = self.desc_font.render(current_desc, True, self.colors['white'])
        current_text = self.weather_font.render(current_str, True, self.colors['white'])
        forecast_text = self.forecast_font.render(forecast_str, True, self.colors['white'])

        screen.blit(desc_text, (self.x, self.y))
        screen.blit(current_icon, (self.x + desc_text.get_width(), self.y))
        screen.blit(current_text, (self.x, self.y + desc_text.get_height()))
        screen.blit(forecast_text, (self.x, self.y + desc_text.get_height() + current_text.get_height()))

        # draw weather change text
        change_info = []
        change_count = 0
        for pred in self._forecast_weather['list'][:8]:
            if change_count == 3:
                break
            pred_desc = pred['weather'][0]['main']
            icon_id = pred['weather'][0]['icon']
            if (not change_info and pred_desc != current_desc) or \
               (change_info and pred_desc != change_info[-1][0]):
                change_info.append((pred_desc, pred['dt_txt'][11:16], icon_id))
                change_count += 1

        x = self.x
        y = self.y + desc_text.get_height() + current_text.get_height() + forecast_text.get_height() + 5
        for desc, timestamp, icon_id in change_info:
            rendered_change_text = self.change_font.render("{} -> {}".format(timestamp, desc), True, self.colors['white'])
            screen.blit(rendered_change_text, (x, y))
            screen.blit(self._change_icons[icon_id], (x + rendered_change_text.get_width(), y))
            y += rendered_change_text.get_height()

        # draw last update time
        last_update_mins = int(time.time() - self._weather_last_update) / 60
        last_update_text = "Last Update: {} min ago".format(last_update_mins)
        rendered_last_update_text = self.last_update_font.render(last_update_text, True, self.colors['white'])
        screen.blit(rendered_last_update_text, (x, y))


class Calendar(Widget):
    def __init__(self, parent, x, y):
        super(Calendar, self).__init__(parent, x, y)

        self.header_font = pygame.font.Font("fonts/arial.ttf", 18)
        self.content_font = pygame.font.Font("fonts/arial.ttf", 16)

        self._calendar_file = "calendar/calendar.html"
        self._parsed_calendar = []
        self._calendar_status = []
        self._calendar_table = None
        self._calendar_last_update = dt.now().day
        self._calendar_selected_row = 0

    def _on_exit(self):
        self._calendar_selected_row = 0

    def _load_calendar(self):
        current_day = dt.now().day
        with open(self._calendar_file, 'r') as file:
            calendar_text = file.read()
            file.close()

        # parse html file into a BeautifulSoup object
        soup = BeautifulSoup(calendar_text, "html.parser")
        calendar_table = soup.find('table')

        # get table rows
        rows = calendar_table.find_all('tr')
        status_tags = calendar_table.find_all('div', class_="__status__")
        titles = rows[0].find_all('th')
        title_texts = [tag.get_text() for tag in titles]
        content_rows = [row.find_all('td') for row in rows[1:]]

        # add contents to list
        self._parsed_calendar = []
        self._calendar_status = []

        self._parsed_calendar.append([text for text in title_texts])
        for status_tag in status_tags:
            self._calendar_status.append(bool(int(status_tag.get_text())))

        for content_row in content_rows:
            self._parsed_calendar.append([content.get_text() for ind, content in enumerate(content_row)])

        self._parsed_calendar = self._add_days(self._parsed_calendar)

        self._calendar_last_update = current_day
        log_to_file("Calendar updated")

    def _add_days(self, calendar):
        try:
            time_ind = calendar[0].index("Due Date")
        except NameError:
            return calendar

        curr_date = dt.today().replace(hour=0, minute=0, second=0, microsecond=0)
        for ind, row in enumerate(calendar):
            if ind == 0:
                row.append("Days")
                continue

            # convert string to datetime object
            try:
                date = dt.strptime(row[time_ind], "%Y-%m-%d")
                date = date.replace(hour=0, minute=0)
                diff_date = date - curr_date

                row.append(str(diff_date.days))
            except ValueError:
                row.append("")
                continue

            row[time_ind] = row[time_ind]

        return calendar

    def _toggle_calendar_row_status(self, row_index):
        self._calendar_status[row_index] = not self._calendar_status[row_index]

        file = open(self._calendar_file, 'r')
        calendar_text = file.read()
        file.close()

        # parse html file into a BeautifulSoup object
        soup = BeautifulSoup(calendar_text, "html.parser")

        # get table rows
        status_tags = soup.find_all('div', class_="__status__")
        for ind, status in enumerate(self._calendar_status):
            status_tags[ind].string = "1" if self._calendar_status[ind] else "0"

        with open(self._calendar_file, 'w') as file:
            file.write(str(soup))
            file.close()

    def _on_setup(self):
        self._load_calendar()

    def _on_update(self):
        current_day = dt.now().day
        if not self._parsed_calendar or current_day != self._calendar_last_update:
            self._load_calendar()

        self._calendar_table = Table(self._parsed_calendar, header_font=self.header_font,
                                     content_font=self.content_font, x=self.x, y=self.y,
                                     content_centered=[False, False, True], x_padding=2,
                                     selected=self.is_active, selected_row=self._calendar_selected_row,
                                     row_status=self._calendar_status)

    def _on_draw(self, screen):
        if self._calendar_table:
            self._calendar_table.draw(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._calendar_selected_row = max(self._calendar_selected_row - 1, 0)
            elif event.key == pygame.K_DOWN:
                if self._parsed_calendar:
                    self._calendar_selected_row = min(self._calendar_selected_row + 1, len(self._parsed_calendar) - 2)
            elif event.key == pygame.K_RETURN:
                self._toggle_calendar_row_status(self._calendar_selected_row)


class Traffic(Widget):
    def __init__(self, parent, x, y):
        super(Traffic, self).__init__(parent, x, y)

        self.traffic_font = pygame.font.Font("fonts/FreeSans.ttf", 13)
        self.traffic_font_height = self.traffic_font.render(' ', True, self.colors['white']).get_height()

        self._traffic_url = "https://maps.googleapis.com/maps/api/distancematrix/json"
        self._traffic_keys = "AIzaSyDKl1oPieC1EwVdsnUJpg0btJV2Bwg0cd4"
        self._traffic_payload = {"units": "matrics", "key": self._traffic_keys, "origins": "", "destinations": ""}

        self._traffic_icon = None
        self._traffic_icon_path = os.path.join("images", "car.png")
        self._traffic_icon_size = self.traffic_font_height

        self._origin_address = "200 Westfield Pl Waterloo"
        self._dest_address = "SAP Lab Waterloo"

        self._traffic_last_update = time.time()
        self._traffic_update_interval = 1800

    def _load_traffic(self):
        self._traffic_payload['origins'] = '+'.join(self._origin_address.split())
        self._traffic_payload['destinations'] = '+'.join(self._dest_address.split())

        traffic_info_res = requests.get(self._traffic_url, params=self._traffic_payload)
        self._traffic_info = traffic_info_res.json()

        self._traffic_last_update = time.time()
        log_to_file("Traffic updated")

    def _on_setup(self):
        self._load_traffic()

        icon = pygame.image.load(self._traffic_icon_path)
        self._traffic_icon = pygame.transform.scale(icon, (self._traffic_icon_size, self._traffic_icon_size))

    def _on_update(self):
        if (time.time() - self._traffic_last_update > self._traffic_update_interval or
            self._traffic_info is None):
            self._load_traffic()

    def _on_draw(self, screen):
        if not self._traffic_info:
            return

        traffic_distance = self._traffic_info['rows'][0]['elements'][0]['distance']['text']
        traffic_duration = self._traffic_info['rows'][0]['elements'][0]['duration']['text']

        traffic_text = "{} {}".format(traffic_distance, traffic_duration)
        rendered_text = self.traffic_font.render(traffic_text, True, self.colors['white'])

        screen.blit(rendered_text, (self.x, self.y))
        screen.blit(self._traffic_icon, (self.x + rendered_text.get_width() + 5, self.y))


class Stock(Widget):
    def __init__(self, parent, x, y, chart=False, chart_width=100, chart_height=100):
        super(Stock, self).__init__(parent, x, y)

        self.chart = chart
        self.chart_width = chart_width
        self.chart_height = chart_height

        self.stock_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self.stock_font_height = self.stock_font.render(' ', True, self.colors['white']).get_height()
        self.stock_footnote_font = pygame.font.Font("fonts/FreeSans.ttf", 10)
        self.stock_label_font = pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.stock_range_font = pygame.font.Font("fonts/FreeSans.ttf", 13)

        self._stock_url = "https://www.alphavantage.co/query"
        self._stock_keys = ['T9O3IK0TF72YCBP8", "JEIP3D1ZI2UTJZUL", "TI8F72SY4LKSD23L']
        self._stock_symbol = ""
        self._stock_payload = {"1D": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "5min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "5D": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "5min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "1M": {"function": "TIME_SERIES_INTRADAY", "symbol": self._stock_symbol,
                                      "interval": "60min", "outputsize": "full", "apikey": self._stock_keys[0]},
                               "3M": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "6M": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "1Y": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "5Y": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                      "outputsize": "full", "apikey": self._stock_keys[0]},
                               "MAX": {"function": "TIME_SERIES_DAILY", "symbol": self._stock_symbol,
                                       "outputsize": "full", "apikey": self._stock_keys[0]}}
        self._stock_range_ind = 0
        self._stock_range = ["1D", "5D", "1M", "3M", "6M", "1Y", "5Y", "MAX"]
        self._stock_info_queue = Queue.Queue(maxsize=1)
        self._stock_info = {"intraday": None, "hourly": None, "daily": None}
        self._current_price = 0
        self._last_close_price = 0
        self._time_series = []
        self._loading_thread = None

        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._input_widget = Input(self.parent, self.x, self.y, font=self._input_font, width=150,
                                   enter_key_event=self._search, capital_lock=True)
        self._subwidgets.append(self._input_widget)

        self._chart_widget = None
        if self.chart:
            self._chart_widget = Chart(self.parent, self.x, self.y + self.stock_font_height + self._input_widget.get_height() + 10,
                                       label_font=self.stock_label_font, width=self.chart_width, height=self.chart_height)
            self._subwidgets.append(self._chart_widget)

    def _search(self, reset=True):
        if reset:
            self.reset()
            self._stock_symbol = self._input_widget.get_text()
        self._chart_widget.reset()
        self._load_stock()

    def _load_stock(self):
        if not self._stock_symbol:
            return

        if self._stock_info[self._get_range_key()]:
            self._parse_stock_info()
            return

        if not self._loading_thread:
            current_range = self._stock_range[self._stock_range_ind]
            payload = self._stock_payload[current_range]
            payload['symbol'] = self._stock_symbol
            self._loading_thread = RequestThread(self._stock_info_queue, self._stock_url, payload)
            self._loading_thread.start()

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_RETURN:
                self._input_widget.set_active(True)
            elif event.key == pygame.K_UP:
                if self.chart:
                    self._range_up()
            elif event.key == pygame.K_DOWN:
                if self.chart:
                    self._range_down()

    def _range_up(self):
        if self._stock_range_ind > 0:
            self._stock_range_ind -= 1
            self._search(reset=False)

    def _range_down(self):
        if self._stock_range_ind < len(self._stock_range) - 1:
            self._stock_range_ind += 1
            self._search(reset=False)

    def _on_enter(self):
        self._input_widget.set_active(True)

    def _on_exit(self):
        self._input_widget.set_active(False)

    def _on_setup(self):
        self._input_widget.set_active(True)

    def _on_update(self):
        self.clear_shapes()
        self._add_range()

        if not self._stock_info_queue.empty():
            self._stock_info[self._get_range_key()] = self._stock_info_queue.get()
            self._loading_thread = None
            self._parse_stock_info()

    def _get_range_key(self):
        current_range = self._stock_range[self._stock_range_ind]
        if current_range.endswith('D'):
            return "intraday"
        elif current_range == "1M":
            return "hourly"
        else:
            return "daily"

    def _get_time_series(self, time_series_key):
        range_key = self._get_range_key()
        if not self._stock_info[range_key].get(time_series_key):
            return None
        time_series = self._stock_info[range_key].get(time_series_key)
        time_series_list = []
        for key in sorted(time_series, reverse=True):
            time_series[key]['timestamp'] = key
            time_series_list.append(time_series[key])
        return time_series_list

    def _parse_stock_info(self):
        self._time_series = []
        current_range = self._stock_range[self._stock_range_ind]
        range_key = self._get_range_key()

        if self._stock_info[range_key] is None:
            return

        if current_range == "1D":
            time_series_key = "Time Series (5min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            today_str = time_series_list[0]['timestamp'][:10]
            self._time_series = [element for element in time_series_list if element['timestamp'].startswith(today_str)]
            self._current_price = float(self._time_series[0].get('4. close'))
            self._last_close_price = float(time_series_list[len(self._time_series)].get('4. close'))
            self._chart_widget.set_x_range(0, 78)
        elif current_range == "5D":
            time_series_key = "Time Series (5min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            today_str = time_series_list[0]['timestamp'][:10]
            quotes_today = [element for element in time_series_list if element['timestamp'].startswith(today_str)]
            quotes_previous = time_series_list[len(quotes_today):78*5]
            self._time_series = (quotes_today + quotes_previous)[::4]
            self._chart_widget.set_x_range(0, 98)
        elif current_range == "1M":
            time_series_key = "Time Series (60min)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:154:2]
            self._chart_widget.set_x_range(0, 77)
        elif current_range == "3M":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:66]
            self._chart_widget.set_x_range(0, 66)
        elif current_range == "6M":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:132]
            self._chart_widget.set_x_range(0, 132)
        elif current_range == "1Y":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:260:2]
            self._chart_widget.set_x_range(0, 130)
        elif current_range == "5Y":
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            self._time_series = time_series_list[:1304:10]
            self._chart_widget.set_x_range(0, 130)
        else:
            time_series_key = "Time Series (Daily)"
            time_series_list = self._get_time_series(time_series_key)
            if not time_series_list:
                return
            ratio = len(time_series_list) / 100
            self._time_series = time_series_list[::ratio]
            self._chart_widget.set_x_range(0, 100)

        if self.chart and self._time_series:
            price_info = [(float(element['2. high']) + float(element['3. low'])) / 2 for element in self._time_series]
            self._chart_widget.set_info({"price": price_info})
            if current_range == "1D":
                self._chart_widget.set_constants([self._last_close_price])
            else:
                self._chart_widget.set_constants([float(self._time_series[-1].get('1. open'))])
            self._chart_widget.set_y_range(min(price_info) * 0.975, max(price_info) * 1.025)
            change = price_info[0] - self._last_close_price if current_range == "1D" else price_info[0] - price_info[-1]
            if change < 0:
                self._chart_widget.set_info_colors({"price": 'red'})
            else:
                self._chart_widget.set_info_colors({"price": 'green'})

    def _on_draw(self, screen):
        if self._loading_thread and self._loading_thread.is_alive():
            self._display_info(screen, "Loading stock info...")
            return

        range_key = self._get_range_key()
        current_stock_info = self._stock_info[range_key]
        if current_stock_info is None:
            return
        elif current_stock_info.get('Note'):
            self._display_info(screen, "Searching is too frequent!")
            return
        elif current_stock_info.get("Error Message"):
            self._display_info(screen, "Invalid stock symbol!")
            return

        self._draw_quote(screen)

    def _display_info(self, screen, text):
        loading_text = self.stock_font.render(text, True, self.colors['white'])
        screen.blit(loading_text, (self.x, self.y + self._input_widget.get_height() + 5))

    def _draw_quote(self, screen):
        if not self._current_price or not self._last_close_price:
            return

        change = self._current_price - self._last_close_price
        percent = change / self._last_close_price * 100
        if change > 0:
            color = "green"
            arrow = u'▲'
        elif change < 0:
            color = "red"
            arrow = u'▼'
        else:
            color = "white"
            arrow = u'▬'

        symbol_text = self.stock_font.render(self._stock_symbol, True, self.colors['white'])
        price_text = self.stock_font.render('{:.2f}'.format(self._current_price), True, self.colors[color])
        bar_text = self.stock_font.render('  |  ', True, self.colors['white'])
        percent_text = self.stock_font.render(u'{:.2f}% {}'.format(percent, arrow), True, self.colors[color])
        quote_x = self.x
        quote_y = self.y + self._input_widget.get_height() + 5
        screen.blit(symbol_text, (quote_x, quote_y))
        quote_x += symbol_text.get_width() + 10
        for text in [price_text, bar_text, percent_text]:
            screen.blit(text, (quote_x, quote_y))
            quote_x += text.get_width()

    def _add_range(self):
        if not self.chart:
            return

        range_x = self.x + self.chart_width + 10
        range_y = self.y + self.stock_font_height + self._input_widget.get_height() + 10
        range_unit_distance = self.chart_height / (len(self._stock_range) - 1)
        self.add_shape(Line(self.colors['white'], (range_x, range_y), (range_x, range_y + self.chart_height), width=3))
        for ind in range(len(self._stock_range)):
            y = range_y + range_unit_distance * ind if ind < len(self._stock_range) - 1 else range_y + self.chart_height
            if ind == self._stock_range_ind:
                color = self.colors['green']
            else:
                color = self.colors['white']
            rendered_text = self.stock_range_font.render(self._stock_range[ind], True, color)
            self.add_shape(Line(self.colors['white'], (range_x, y), (range_x + 6, y)))
            self.add_shape(Text(rendered_text, (range_x + 10, y - rendered_text.get_height() / 2)))

    def reset(self):
        self._stock_symbol = ""
        self._stock_range_ind = 0
        self._stock_info_queue = Queue.Queue(maxsize=1)
        self._stock_info = {"intraday": None, "hourly": None, "daily": None}
        self._current_price = 0
        self._last_close_price = 0
        self._time_series = []
        self._loading_thread = None

    def clear(self):
        self.reset()
        self._input_widget.reset()
        self._chart_widget.reset()


class SystemInfo(Widget):
    def __init__(self, parent, x, y, font=None, cpu_info=True, memory_info=True, disk_info=True, internet_info=True, percent_bar=True):
        super(SystemInfo, self).__init__(parent, x, y)

        self.font = font if font is not None else pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.cpu_info = cpu_info
        self.memory_info = memory_info
        self.disk_info = disk_info
        self.internet_info = internet_info
        self.percent_bar = percent_bar
        self._info_text_height = self.font.render(' ', True, self.colors['white']).get_height()

        self._cpu_percent = 0.0
        self._memory_percent = 0.0
        self._disk_percent = 0.0
        self._disk_partitions = [partition.mountpoint for partition in psutil.disk_partitions()]
        self._disk_total = 0
        self._last_net_sent_bytes = psutil.net_io_counters().bytes_sent
        self._last_net_recv_bytes = psutil.net_io_counters().bytes_recv
        self._net_sent_speed = 0
        self._net_recv_speed = 0

        self._percent_bar_width = 50 if self.percent_bar else 0
        self._percent_bar_height = int(self._info_text_height * 0.75)

        self._update_interval = 1.0
        self._last_update = time.time()

    def _update_info(self):
        self._memory_percent = psutil.virtual_memory().percent
        self._cpu_percent = psutil.cpu_percent()

        try:
            disk_used = float(sum(psutil.disk_usage(path).used for path in self._disk_partitions))
            if not self._disk_total:
                self._disk_total = float(sum(psutil.disk_usage(path).total for path in self._disk_partitions))
            self._disk_percent = disk_used / self._disk_total * 100
        except WindowsError:
            self._disk_percent = 0.0

        current_sent_bytes = psutil.net_io_counters().bytes_sent
        current_recv_bytes = psutil.net_io_counters().bytes_recv
        self._net_sent_speed = current_sent_bytes - self._last_net_sent_bytes
        self._net_recv_speed = current_recv_bytes - self._last_net_recv_bytes
        self._last_net_sent_bytes = current_sent_bytes
        self._last_net_recv_bytes = current_recv_bytes

    def _add_percent_bar(self, percent, x, y):
        if percent <= 60:
            color = self.colors['green']
        elif percent <= 80:
            color = self.colors['yellow']
        else:
            color = self.colors['red']
        width = int(self._percent_bar_width * percent / 100)
        self.add_shape(Rectangle(self.colors['lightgray'], x, y, self._percent_bar_width, self._percent_bar_height, line_width=0))
        self.add_shape(Rectangle(color, x, y, width, self._percent_bar_height, line_width=0))

    def _on_setup(self):
        self._update_info()

    def _on_update(self):
        current_time = time.time()
        if current_time - self._last_update > self._update_interval:
            self._update_info()
            self._last_update = current_time

    def _on_draw(self, screen):
        self.clear_shapes()
        rendered_cpu_text = self.font.render("CPU: ", True, self.colors['white'])
        rendered_memory_text = self.font.render("Memory: ", True, self.colors['white'])
        rendered_disk_text = self.font.render("Disk: ", True, self.colors['white'])
        percent_bar_x = self.x + max(rendered_cpu_text.get_width(), rendered_memory_text.get_width())
        percent_bar_y = self.y + (self._info_text_height - self._percent_bar_height) / 2
        rendered_cpu_percent_text = self.font.render(" {:.2f}%".format(self._cpu_percent), True, self.colors['white'])
        rendered_memory_percent_text = self.font.render(" {:.2f}%".format(self._memory_percent), True, self.colors['white'])
        rendered_disk_percent_text = self.font.render(" {:.2f}%".format(self._disk_percent), True, self.colors['white'])

        if self.percent_bar:
            self._add_percent_bar(self._cpu_percent, percent_bar_x, percent_bar_y)
            self._add_percent_bar(self._memory_percent, percent_bar_x, percent_bar_y + self._info_text_height)
            self._add_percent_bar(self._disk_percent, percent_bar_x, percent_bar_y + self._info_text_height * 2)

        upload_speed = bytes_to_string(self._net_sent_speed)
        download_speed = bytes_to_string(self._net_recv_speed)
        rendered_net_text = self.font.render(u"Internet: \u2193{}/s \u2191{}/s".format(download_speed, upload_speed), True, self.colors['white'])

        y = self.y
        if self.cpu_info:
            screen.blit(rendered_cpu_text, (self.x, y))
            screen.blit(rendered_cpu_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y += self._info_text_height

        if self.memory_info:
            screen.blit(rendered_memory_text, (self.x, y))
            screen.blit(rendered_memory_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y+= self._info_text_height

        if self.disk_info:
            screen.blit(rendered_disk_text, (self.x, y))
            screen.blit(rendered_disk_percent_text, (percent_bar_x + self._percent_bar_width, y))
            y += self._info_text_height

        if self.internet_info:
            screen.blit(rendered_net_text, (self.x, y))


class Time(Widget):
    def __init__(self, parent):
        super(Time, self).__init__(parent, 0, 0)

        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")

        self.date_font = pygame.font.SysFont(self.default_font_name, 30)
        self.time_font = pygame.font.SysFont(self.default_font_name, 65)

    def _on_setup(self):
        pass

    def _on_update(self):
        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")

    def _on_draw(self, screen):
        date_text = self.date_font.render(self.date_str, True, self.colors['white'])
        time_text = self.time_font.render(self.time_str, True, self.colors['white'])
        screen.blit(date_text, (self._screen_width - date_text.get_width() - 5, 10))
        screen.blit(time_text, (self._screen_width - time_text.get_width() - 5,
                                     date_text.get_height() + 15))

class NightTime(Time):
    def __init__(self, parent):
        super(NightTime, self).__init__(parent)

        self.date_str = dt.now().strftime("%A, %b %d")
        self.time_str = dt.now().strftime("%H:%M")
        self.night_date_font = pygame.font.SysFont(self.default_font_name, 50)
        self.night_time_font = pygame.font.SysFont(self.default_font_name, 150)

    def _on_draw(self, screen):
        time_text = self.night_time_font.render(self.time_str, True, self.colors['gray'])
        date_text = self.night_date_font.render(self.date_str, True, self.colors['gray'])
        time_pos = ((self._screen_width - time_text.get_width()) / 2,
                    (self._screen_height - time_text.get_height()) / 2 - 30)
        date_pos = ((self._screen_width - date_text.get_width()) / 2,
                    time_pos[1] + time_text.get_height() + 10)
        screen.blit(time_text, time_pos)
        screen.blit(date_text, date_pos)


class Content(Widget):
    def __init__(self, parent, x, y, text, font=None, color=(255, 255, 255),
                 max_width=0, max_height=0, prefix=None, borders=[],
                 border_color=(255, 255, 255), border_width=1, margin=(0, 0, 0, 0),
                 underline=False):
        super(Content, self).__init__(parent, x, y)

        self.text = text
        self.font = font
        self.color = color
        self.max_width = max_width
        self.max_height = max_height
        self.prefix = prefix
        self.prefix_text = None
        self.prefix_width = 0
        self.prefix_height = 0
        self.borders = borders
        self.border_color = border_color
        self.border_width = border_width
        self.margin = margin
        self.underline = underline
        if not self.font:
            self.font = self.default_font
        self.content_texts = []

    def _on_setup(self):
        self.content_texts = []
        x, y = self.x, self.y
        if self.prefix:
            self.prefix_text = self.font.render(self.prefix, True, self.color)
            self.content_texts.append((self.prefix, (x, y)))
            self.prefix_width = self.prefix_text.get_width()
            self.prefix_height = self.prefix_text.get_height()
            x += self.prefix_width
            self.max_width -= self.prefix_width

        content_text = self.font.render(self.text, True, self.color)
        if self.max_width <= 0 or content_text.get_width() <= self.max_width:
            self.content_texts.append((self.text, (x, y)))
            return

        words = self.text.split(' ')
        current_width = 0
        line_words = []
        space_width = self.font.render(' ', True, self.color).get_width()
        for word in words:
            word_width = self.font.render(word, True, self.color).get_width()
            if current_width + word_width + space_width > self.max_width:
                line = ' '.join(line_words)
                line_text = self.font.render(line, True, self.color)
                self.content_texts.append((line, (x, y)))
                line_words = []
                current_width = 0
                y += line_text.get_height()
                if self.max_height > 0 and y - self.y > self.max_height:
                    return
            line_words.append(word)
            current_width += word_width + space_width

        if line_words:
            line = ' '.join(line_words)
            self.content_texts.append((line, (x, y)))

        if self.underline:
            for content_text, pos in self.content_texts:
                rendered_text = self.font.render(content_text, True, self.color)
                start_pos = (pos[0], pos[1] + rendered_text.get_height())
                end_pos = (pos[0] + rendered_text.get_width(), pos[1] + rendered_text.get_height())
                self.add_shape(Line(self.color, start_pos, end_pos))

    def _on_update(self):
        if self.text:
            self._add_borders()

    def _on_draw(self, screen):
        for text, pos in self.content_texts:
            rendered_text = self.font.render(text, True, self.color)
            screen.blit(rendered_text, pos)

    def _add_borders(self):
        full_border = "full" in self.borders
        for border in self.borders:
            lt = (self.x - self.margin[0], self.y - self.margin[2])
            lb = (self.x - self.margin[0], self.y + self.margin[3] + self.get_height())
            rt = (self.x + self.margin[1] + self.get_width(), self.y - self.margin[2])
            rb = (self.x + self.margin[1] + self.get_width(), self.y + self.margin[3] + self.get_height())
            if border == "left" or full_border:
                self.add_shape(Line(self.border_color, lt, lb, width=self.border_width))
            elif border == "right" or full_border:
                self.add_shape(Line(self.border_color, rt, rb, width=self.border_width))
            elif border == "top" or full_border:
                self.add_shape(Line(self.border_color, lt, rt, width=self.border_width))
            elif border == "bottom" or full_border:
                self.add_shape(Line(self.border_color, lb, rb, width=self.border_width))

    def get_text(self):
        return self.text

    def set_text(self, text):
        self.text = text
        self.setup()

    def get_width(self):
        if self.prefix:
            return self.prefix_width + self.font.render(self.content_texts[1][0], True, self.color).get_width()
        elif self.content_texts:
            return self.font.render(self.content_texts[0][0], True, self.color).get_width()
        else:
            return 0

    def get_height(self):
        if self.prefix:
            return sum([self.font.render(text, True, self.color).get_height() for text, pos in self.content_texts[1:]])
        elif self.content_texts:
            return sum([self.font.render(text, True, self.color).get_height() for text, pos in self.content_texts])
        else:
            return 0

    def get_lines(self):
        lines = []
        start_index = 1 if self.prefix else 0
        for ind in range(start_index, len(self.content_texts)):
            text, pos = self.content_texts[ind]
            if self.prefix and ind == 1:
                line = self.font.render(self.prefix + text, True, self.color)
            else:
                line = self.font.render(len(self.prefix) * ' ' + text, True, self.color)
            lines.append(line)
        return lines

    def set_underline(self, status):
        self.underline = status


class SearchWidget(Widget):
    def __init__(self, parent, x, y, str_font=None, result_font=None, max_width=0, max_height=0):
        super(SearchWidget, self).__init__(parent, x, y)

        self.str_font = str_font
        self.result_font = result_font
        if not self.str_font:
            self.str_font = self.default_font
        if not self.result_font:
            self.result_font = self.default_font

        self.max_width = max_width
        self.max_height = max_height

        self._page_footnote_font = pygame.font.Font("fonts/FreeSans.ttf", 12)

        self._search_url = "https://www.bestbuy.ca/en-CA/Search/SearchResults.aspx"
        self._search_payload = {"query": ""}
        self._search_str_pos = (self.x + 10, self.y + 10)
        self._search_str_widget = Input(parent, self._search_str_pos[0], self._search_str_pos[1],
                                        font=self.str_font, width=self.max_width, enter_key_event=self._search)

        self._search_result_pos = (self.x + 10, self.y + 45)
        self._search_results = []
        self._search_result_pages = []
        self._page_index = 0
        self._subwidgets = [self._search_str_widget]

    def _on_setup(self):
        self._search_str_widget.set_active(True)

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        self._draw_footnote(screen)

        if self._search_result_pages:
            for search_result in self._search_result_pages[self._page_index]:
                search_result.draw(screen)

    def _on_enter(self):
        self._search_str_widget.set_active(True)

    def _on_exit(self):
        self._search_str_widget.set_active(False)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_UP:
                self._move_page("up")
            elif event.key == pygame.K_DOWN:
                self._move_page("down")
            elif event.key == pygame.K_RETURN:
                self._search_str_widget.set_active(True)

    def _draw_footnote(self, screen):
        # draw page number
        page_text = "page: {}/{}".format(self._page_index + 1, len(self._search_result_pages))
        rendered_page_text = self._page_footnote_font.render(page_text, True, self.colors['white'])
        page_text_pos = (self.x + self.max_width - rendered_page_text.get_width(),
                         self.y + self.max_height)
        if self._search_result_pages:
            screen.blit(rendered_page_text, page_text_pos)

        # draw source string
        source_text = "source: bestbuy.ca"
        rendered_source_text = self._page_footnote_font.render(source_text, True, self.colors['white'])
        source_text_pos = (self.x + self.max_width - rendered_source_text.get_width(),
                           self.y + self.max_height + rendered_page_text.get_height())
        screen.blit(rendered_source_text, source_text_pos)

    def _move_page(self, direction):
        if direction == "up":
            if self._page_index > 0:
                self._page_index -= 1
        else:
            if self._page_index < len(self._search_result_pages) - 1:
                self._page_index += 1

    def _search(self):
        search_str = self._search_str_widget.get_text()
        if not search_str or search_str.isspace():
            return

        self._search_payload['query'] = search_str.replace(' ', '+')
        res = requests.get(self._search_url, params=self._search_payload)
        soup = BeautifulSoup(res.content, 'html.parser')
        with open("search_response.html", 'wb') as f:
            f.write(res.content)
        search_results = soup.find_all('li', class_=re.compile("listing-item"))

        self._page_index = 0
        self._search_result_pages = []
        page_contents = []

        if soup.find('div', class_="search-no-results"):
            title_content = Content(self.parent, self._search_result_pos[0], self._search_result_pos[1],
            "Can't find any results...", font=self.result_font, max_width=self.max_width)
            title_content.setup()
            self._search_result_pages.append([title_content])
            return

        for item in search_results:
            name = item.find('h4', class_="prod-title").get_text()
            price = item.find('span', class_="amount").get_text()
            stars_tag = item.find('div', class_="rating-stars-yellow")
            stars = ""
            if stars_tag:
                stars = stars_tag.get("style")[7:-1]

            x = self._search_result_pos[0]
            y = sum([content.get_height() for content in page_contents]) + self._search_result_pos[1]
            item_text = u'{} - {}'.format(name, price)
            if stars:
                item_text += u' | {}'.format(stars)
            title_content = Content(self.parent, x, y, item_text, font=self.result_font, max_width=self.max_width, prefix="- ")
            title_content.setup()

            if y + title_content.get_height() > self.y + self.max_height:
                title_content.set_pos(x, self._search_result_pos[1])
                title_content.setup()
                self._search_result_pages.append(page_contents)
                page_contents = []

            page_contents.append(title_content)

        if page_contents:
            self._search_result_pages.append(page_contents)

    def reset(self):
        self._search_results = []
        self._search_result_pages = []
        self._page_index = 0
        self._search_str_widget.reset()


class Input(Widget):
    def __init__(self, parent, x, y, font=None, width=100, enter_key_event=None, capital_lock=False):
        super(Input, self).__init__(parent, x, y)

        self.font = font if font is not None else self.default_font
        self.width = width
        self.height = self.font.render(' ', True, self.colors['white']).get_height()
        self.enter_key_event = enter_key_event
        self.capital_lock = capital_lock

        self._background_alpha = 180
        self._cursor_index = 0
        self._cursor_active_time = time.time()
        self._string = ""
        self._content_widget = Content(self.parent, self.x, self.y, self._string, font=self.font, color=self.colors['white'])
        self._subwidgets = [self._content_widget]

    def _draw_cursor(self, screen):
        time_diff = time.time() - self._cursor_active_time
        if time_diff - math.floor(time_diff) > 0.5:
            return

        rendered_text = self.font.render(self._string[:self._cursor_index], True, self.colors['white'])
        start_pos = (self.x + rendered_text.get_width(), self.y)
        end_pos = (self.x + rendered_text.get_width(),
                   self.y + rendered_text.get_height())
        pygame.draw.line(screen, self.colors['white'], start_pos, end_pos)

    def _draw_background(self, screen):
        if not self.is_active:
            return

        background_surface = pygame.Surface((self.width, self.height))
        background_surface.fill(self.colors['lightgray'])
        background_surface.set_alpha(self._background_alpha)
        screen.blit(background_surface, (self.x, self.y))

    def _ctrl_pressed(self):
        pressed = pygame.key.get_pressed()
        return pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

    def _shift_pressed(self):
        pressed = pygame.key.get_pressed()
        return pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]

    def _input(self, s):
        if self._ctrl_pressed():
            return

        if self._shift_pressed() or self.capital_lock:
            s = s.upper()

        self._string = self._string[:self._cursor_index] + s + self._string[self._cursor_index:]
        self._cursor_index += 1
        self._content_widget.set_text(self._string)

    def _backspace(self):
        if self._cursor_index == 0:
            return

        self._string = self._string[:self._cursor_index-1] + self._string[self._cursor_index:]
        self._cursor_index -= 1
        self._content_widget.set_text(self._string)

    def _delete(self):
        if self._cursor_index == len(self._string):
            return

        self._string = self._string[:self._cursor_index] + self._string[self._cursor_index+1:]
        self._content_widget.set_text(self._string)

    def _clear_str(self):
        self._cursor_index = 0
        self._string = ""
        self._content_widget.set_text(self._string)

    def _move_cursor(self, direction):
        self._cursor_active_time = time.time()
        if direction == "left":
            if self._cursor_index > 0:
                self._cursor_index -= 1
        else:
            if self._cursor_index < len(self._string):
                self._cursor_index += 1

    def _on_setup(self):
        pass

    def _on_update(self):
        self.clear_shapes()

        line_start_pos = (self.x, self.y + self._content_widget.get_height())
        line_end_pos = (self.x + self.width, self.y + self._content_widget.get_height())
        self.add_shape(Line(self.colors['white'], line_start_pos, line_end_pos))

    def _on_draw(self, screen):
        if self.is_active:
            self._draw_cursor(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_a:
                self._input('a')
            elif event.key == pygame.K_b:
                self._input('b')
            elif event.key == pygame.K_c:
                self._input('c')
            elif event.key == pygame.K_d:
                self._input('d')
            elif event.key == pygame.K_e:
                self._input('e')
            elif event.key == pygame.K_f:
                self._input('f')
            elif event.key == pygame.K_g:
                self._input('g')
            elif event.key == pygame.K_h:
                self._input('h')
            elif event.key == pygame.K_i:
                self._input('i')
            elif event.key == pygame.K_j:
                self._input('j')
            elif event.key == pygame.K_k:
                self._input('k')
            elif event.key == pygame.K_l:
                self._input('l')
            elif event.key == pygame.K_m:
                self._input('m')
            elif event.key == pygame.K_n:
                self._input('n')
            elif event.key == pygame.K_o:
                self._input('o')
            elif event.key == pygame.K_p:
                self._input('p')
            elif event.key == pygame.K_q:
                self._input('q')
            elif event.key == pygame.K_r:
                self._input('r')
            elif event.key == pygame.K_s:
                self._input('s')
            elif event.key == pygame.K_t:
                self._input('t')
            elif event.key == pygame.K_u:
                self._input('u')
            elif event.key == pygame.K_v:
                self._input('v')
            elif event.key == pygame.K_w:
                self._input('w')
            elif event.key == pygame.K_x:
                self._input('x')
            elif event.key == pygame.K_y:
                self._input('y')
            elif event.key == pygame.K_z:
                self._input('z')
            elif event.key == pygame.K_0 or event.key == pygame.K_KP0:
                self._input('0')
            elif event.key == pygame.K_1 or event.key == pygame.K_KP1:
                self._input('1')
            elif event.key == pygame.K_2 or event.key == pygame.K_KP2:
                self._input('2')
            elif event.key == pygame.K_3 or event.key == pygame.K_KP3:
                self._input('3')
            elif event.key == pygame.K_4 or event.key == pygame.K_KP4:
                self._input('4')
            elif event.key == pygame.K_5 or event.key == pygame.K_KP5:
                self._input('5')
            elif event.key == pygame.K_6 or event.key == pygame.K_KP6:
                self._input('6')
            elif event.key == pygame.K_7 or event.key == pygame.K_KP7:
                self._input('7')
            elif event.key == pygame.K_8 or event.key == pygame.K_KP8:
                self._input('8')
            elif event.key == pygame.K_9 or event.key == pygame.K_KP9:
                self._input('9')
            elif event.key == pygame.K_SPACE:
                self._input(' ')
            elif event.key == pygame.K_BACKSPACE:
                if self._ctrl_pressed():
                    self._clear_str()
                else:
                    self._backspace()
            elif event.key == pygame.K_DELETE:
                if self._ctrl_pressed():
                    self._clear_str()
                else:
                    self._delete()
            elif event.key == pygame.K_RETURN or event.key == pygame.K_KP_ENTER:
                if self.enter_key_event:
                    self.enter_key_event()
            elif event.key == pygame.K_LEFT:
                self._move_cursor("left")
            elif event.key == pygame.K_RIGHT:
                self._move_cursor("right")

    def reset(self):
        self._clear_str()

    def get_text(self):
        return self._string

    def get_height(self):
        return self.font.render(' ', True, self.colors['white']).get_height()


class Chart(Widget):
    def __init__(self, parent, x, y, info=None, label_font=None, constants=[], width=100, height=100,
                 max_x=100, max_y=100, min_x=0, min_y=0, info_colors=None,
                 x_unit=1, y_unit=1,
                 x_label_interval=None, y_label_interval=None,
                 background=False, background_color=(255, 255, 255)):
        super(Chart, self).__init__(parent, x, y)

        self.info = info
        self.label_font = label_font if label_font else pygame.font.Font("fonts/FreeSans.ttf", 12)
        self.constants = constants
        self.width = width
        self.height = height
        self.max_x = max_x
        self.max_y = max_y
        self.min_x = min_x
        self.min_y = min_y
        self.info_colors = info_colors
        self.x_unit = x_unit
        self.y_unit = y_unit
        self.x_label_interval = x_label_interval
        self.y_label_interval = y_label_interval
        self.background = background
        self.background_color = background_color

    def _on_setup(self):
        pass

    def _on_update(self):
        self.clear_shapes()

        self._add_labels()
        self._add_curves()
        self._add_axis()

    def _add_labels(self):
        if self.x_label_interval:
            x = self.x
            y = self.y + self.height
            x_label_interval_distance = self.width / (self.max_x / self.x_label_interval)
            for i in range(self.max_x / self.x_label_interval + 1):
                label_text = str(i * self.x_label_interval)
                rendered_label_text = self.label_font.render(label_text, True, self.colors['white'])
                text_width = rendered_label_text.get_width()
                if i == self.max_x / self.x_label_interval:
                    x = self.x + self.width
                if i > 0:
                    self.add_shape(Line(self.colors['lightgray'], (x, self.y), (x, y)))
                    self.add_shape(Text(rendered_label_text, (x - text_width / 2, y + 2)))
                else:
                    self.add_shape(Text(rendered_label_text, (x, y + 2)))
                x += x_label_interval_distance

        if self.y_label_interval:
            x = self.x
            y = self.y + self.height
            y_label_interval_distance = self.height / (self.max_y / self.y_label_interval)
            for i in range(self.max_y / self.y_label_interval + 1):
                label_text = str(i * self.y_label_interval)
                rendered_label_text = self.label_font.render(label_text, True, self.colors['white'])
                text_height = rendered_label_text.get_height()
                if i == self.max_y / self.y_label_interval:
                    y = self.y
                if i > 0:
                    self.add_shape(Line(self.colors['lightgray'], (x, y), (x + self.width, y)))
                self.add_shape(Text(rendered_label_text, (x - rendered_label_text.get_width() - 3, y - text_height / 2)))
                y -= y_label_interval_distance

    def _add_axis(self):
        self.add_shape(Line(self.colors['white'], (self.x, self.y),
                            (self.x, self.y + self.height), width=2))
        self.add_shape(Line(self.colors['white'], (self.x, self.y + self.height),
                            (self.x + self.width, self.y + self.height), width=2))

    def _add_curves(self):
        if not self.info:
            return

        x_unit_distance = float(self.width) / (self.max_x - self.min_x - 1) * self.x_unit
        y_unit_distance = float(self.height) / (self.max_y - self.min_y) * self.y_unit
        for key, vals in self.info.iteritems():
            if isinstance(vals, Queue.Queue) and vals.qsize() <= 1:
                continue
            elif isinstance(vals, list) and len(vals) <= 1:
                continue

            points = []
            val_list = vals if isinstance(vals, list) else vals.queue
            for ind, val in enumerate(reversed(val_list)):
                pos_x = int(self.x + x_unit_distance * (ind - self.min_x))
                pos_y = int(self.y + self.height - y_unit_distance * (val - self.min_y))
                if pos_x <= self.x + self.width:
                    points.append((pos_x, pos_y))

            color_name = self.info_colors.get(key) if self.info_colors else "white"
            color = self.colors.get(color_name)
            if not color:
                color = self.colors['white']
            curve = Lines(color, False, points, anti_alias=True)
            self.add_shape(curve)

            if self.background:
                background_points = points + [(points[-1][0], self.y + self.height), (points[0][0], self.y + self.height)]
                self.add_shape(Polygon(self.background_color, background_points, width=0))

        for constant in self.constants:
            y = int(self.y + self.height - y_unit_distance * (constant - self.min_y))
            rendered_label_text = self.label_font.render(str(constant), True, self.colors['white'])
            self.add_shape(DashLine(self.colors['white'], (self.x, y), (self.x + self.width, y)))
            self.add_shape(Text(rendered_label_text, (self.x + self.width - rendered_label_text.get_width(),
                                                      y - rendered_label_text.get_height())))

    def _on_draw(self, screen):
        pass

    def reset(self):
        self.info = None
        self.clear_shapes()
        self._add_axis()

    def set_info(self, info):
        self.info = info

    def set_info_colors(self, info_colors):
        self.info_colors = info_colors

    def set_constants(self, constants):
        self.constants = constants

    def set_x_range(self, min_x, max_x):
        self.min_x = min_x
        self.max_x = max_x

    def set_y_range(self, min_y, max_y):
        self.min_y = min_y
        self.max_y = max_y

    def set_background_color(self, color):
        self.background_color = color


class ChartCaption(Widget):
    def __init__(self, parent, x, y, info_colors, font=None, line_length=25):
        super(ChartCaption, self).__init__(parent, x, y)

        self.info_colors = info_colors
        self.font = font if font is not None else self.default_font
        self.line_length = line_length

    def _on_setup(self):
        x, y = self.x, self.y
        content_widgets = []
        for name in self.info_colors:
            content_widget = Content(self.parent, x, y, name, font=self.font)
            content_widget.setup()
            content_widgets.append(content_widget)
            y += content_widget.get_height()
        self._subwidgets.extend(content_widgets)

        line_x = self.x + max([widget.get_width() for widget in content_widgets]) + 5
        for content_widget in content_widgets:
            name = content_widget.get_text()
            line_y = content_widget.get_pos()[1] + content_widget.get_height() / 2
            self.add_shape(Line(self.colors.get(self.info_colors[name]), (line_x, line_y), (line_x + self.line_length, line_y), width=2))

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        pass


class Map(Widget):
    def __init__(self, parent, x, y, map_width=200, map_height=150, map_padding=0.15):
        super(Map, self).__init__(parent, x, y)

        self.map_width = map_width
        self.map_height = map_height
        self.map_padding = map_padding

        self._map_x = self.x + 30
        self._map_y = self.y + 90

        self._direction_info = None
        self._total_distance = 0.0
        self._total_time = 0.0
        self._polyline_points = []

        self._direction_url = "https://maps.googleapis.com/maps/api/directions/json"
        self._direction_key = "AIzaSyDKl1oPieC1EwVdsnUJpg0btJV2Bwg0cd4"
        self._direction_payload = {"units": "metric", "mode": "driving", "key": self._direction_key,
                                   "origin": "", "destination": ""}

        self._caption_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._input_font = pygame.font.Font("fonts/FreeSans.ttf", 15)
        self._result_font = pygame.font.Font("fonts/FreeSans.ttf", 16)

        self._from_text = self._caption_font.render("From: ", True, self.colors['white'])
        self._to_text = self._caption_font.render("To: ", True, self.colors['white'])

        self._input_width = 200
        self._dot_radius = 5
        self._origin_widget = Input(self.parent, self.x + self._from_text.get_width() + 5, self.y,
                                    font=self._input_font, width=self._input_width, enter_key_event=self._search)
        self._dest_widget = Input(self.parent, self.x + self._from_text.get_width() + 5, self.y + 30,
                                  font=self._input_font, width=self._input_width, enter_key_event=self._search)

        self._subwidgets = [self._origin_widget, self._dest_widget]

    def _search(self):
        origin_address = self._origin_widget.get_text()
        dest_address = self._dest_widget.get_text()

        if not origin_address or not dest_address:
            return

        self._direction_payload['origin'] = '+'.join(origin_address.split())
        self._direction_payload['destination'] = '+'.join(dest_address.split())

        direction_res = requests.get(self._direction_url, params=self._direction_payload)
        self._direction_info = direction_res.json()

        self.clear_shapes()
        self._parse_info()

    def _parse_info(self):
        if not self._direction_info:
            return

        self._total_time = sum([step['duration']['value'] for step in self._direction_info['routes'][0]['legs'][0]['steps']])
        self._total_distance = sum([step['distance']['value'] for step in self._direction_info['routes'][0]['legs'][0]['steps']])

        # parse overview polyline
        polyline_width = int(self.map_width * (1 - self.map_padding))
        polyline_height = int(self.map_height * (1 - self.map_padding))
        polyline_x = self._map_x + (self.map_width - polyline_width) / 2
        polyline_y = self._map_y + (self.map_height - polyline_height) / 2

        points = polyline.decode(self._direction_info['routes'][0]['overview_polyline']['points'])
        latitudes = [point[0] for point in points]
        longitudes = [point[1] for point in points]
        min_lat = min(latitudes)
        max_lat = max(latitudes)
        min_long = min(longitudes)
        max_long = max(longitudes)

        coords = [(long - min_long, lat - min_lat) for lat, long in points]
        x_ratio = polyline_width / (max_long - min_long)
        y_ratio = polyline_height / (max_lat - min_lat)
        ratio = min(x_ratio, y_ratio)
        coords = [(int(polyline_x + x * ratio), int(polyline_y + polyline_height - y * ratio)) for x, y in coords]

        coords_x = [coord[0] for coord in coords]
        coords_y = [coord[1] for coord in coords]
        x_offset = polyline_width - (max(coords_x) - min(coords_x))
        y_offset = polyline_height - (max(coords_y) - min(coords_y))
        self._polyline_points = [(x + x_offset / 2, y - y_offset / 2) for x, y in coords]

        self.add_shape(Lines(self.colors['green'], False, self._polyline_points, width=3, anti_alias=False))
        self.add_shape(Circle(self.colors['orange'], self._polyline_points[0], self._dot_radius))
        self.add_shape(Circle(self.colors['lightblue'], self._polyline_points[-1], self._dot_radius))
        self.add_shape(Rectangle(self.colors['white'], self._map_x, self._map_y, self.map_width, self.map_height))

    def _draw_texts(self, screen):
        screen.blit(self._from_text, (self.x, self.y))
        screen.blit(self._to_text, (self.x, self.y + 30))

        if self._direction_info:
            text_height = self._input_font.render(' ', True, self.colors['white']).get_height()
            text_width = max(self._from_text.get_width(), self._to_text.get_width()) + self._input_width
            self.add_shape(Circle(self.colors['orange'], (self.x + text_width + self._dot_radius * 2, self.y + text_height / 2), self._dot_radius))
            self.add_shape(Circle(self.colors['lightblue'], (self.x + text_width + self._dot_radius * 2, self.y + text_height / 2 + 30), self._dot_radius))

    def _draw_result(self, screen):
        if not self._direction_info:
            return

        result_text = "{:.1f} km - {:.1f} min".format(float(self._total_distance) / 1000, float(self._total_time) / 60)
        rendered_result_text = self._result_font.render(result_text, True, self.colors['white'])
        screen.blit(rendered_result_text, (self.x, self.y + 60))

    def _on_enter(self):
        self._origin_widget.set_active(True)

    def _on_exit(self):
        self._origin_widget.set_active(False)
        self._dest_widget.set_active(False)

    def _on_setup(self):
        pass

    def _on_update(self):
        pass

    def _on_draw(self, screen):
        self._draw_texts(screen)
        self._draw_result(screen)

    def _handle_widget_events(self, event):
        if event.type == pygame.KEYDOWN:
            if event.key == pygame.K_TAB:
                self._toggle_input_widget()

    def _toggle_input_widget(self):
        if self._origin_widget.is_active:
            self._origin_widget.set_active(False)
            self._dest_widget.set_active(True)
        else:
            self._dest_widget.set_active(False)
            self._origin_widget.set_active(True)

    def reset(self):
        self.clear_shapes()
        self._origin_widget.reset()
        self._dest_widget.reset()
        self._direction_info = None
        self._total_distance = 0.0
        self._total_time = 0.0
        self._polyline_points = []
