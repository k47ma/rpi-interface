#!/usr/bin/python3
# -*- coding: utf-8 -*-
import pygame
import colors
from shapes import Line, Text, DashLine


class Chart:
    def __init__(self, caption=None, width=300, height=250, margin=10, pos=(0, 0)):
        self.caption = caption
        self.width = width
        self.height = height
        self.margin = margin
        self.pos = pos

        self.curves = []
        self.constants = []
        self.shapes = []

        self.axis_color = colors.WHITE
        self.text_color = colors.WHITE
        self.point_color = colors.WHITE
        self.label_font = pygame.font.SysFont(pygame.font.get_default_font(), 16)
        self.digit_font = pygame.font.SysFont(pygame.font.get_default_font(), 15)
        self.caption_font = pygame.font.SysFont(pygame.font.get_default_font(), 23)

        self.x_range = None
        self.y_range = None

    def _add_offset(self, shapes):
        x_offset, y_offset = self.pos
        for shape in shapes:
            shape.add_offset(x_offset, y_offset)

    def get_shapes(self):
        return self.shapes

    def add_constant(self, constant, label=None, color=colors.WHITE):
        self.constants.append({"value": constant, "label": label, "color": color})
        self.shapes = self.calculate_shapes()

    def add_constants(self, constants, labels=None, colors=None):
        for ind, constant in enumerate(constants):
            if labels:
                label = labels[ind]
            else:
                label = None
            if colors:
                color = colors[ind]
            else:
                color = colors.WHITE
            self.constants.append({"value": constant, "label": label, "color": color})
        self.shapes = self.calculate_shapes()

    def add_curve(self, x, y, label=None, color=colors.WHITE):
        self.curves.append({"x": x, "y": y, "label": label, "color": color})
        self.shapes = self.calculate_shapes()

    def calculate_shapes(self):
        """returns a list of shapes for plotting"""
        shapes = []

        # calculate the range of x, y
        if self.curves:
            x_max = max([max(curve['x']) for curve in self.curves])
            x_min = min([min(curve['x']) for curve in self.curves])
            y_max = max([max(curve['y']) for curve in self.curves])
            y_min = min([min(curve['y']) for curve in self.curves])
            self.x_range = (x_min, x_max)
            self.y_range = (y_min, y_max)

        # calculate axis
        y_axis_start = (self.margin + 10, self.margin)
        y_axis_end = (y_axis_start[0], y_axis_start[1] + self.height - 2 * self.margin)
        y_axis = Line(self.axis_color, y_axis_start, y_axis_end)
        shapes.append(y_axis)

        x_axis_start = y_axis_end
        x_axis_end = (x_axis_start[0] + self.width - 2 * self.margin, x_axis_start[1])
        x_axis = Line(self.axis_color, x_axis_start, x_axis_end)
        shapes.append(x_axis)

        # values on the axis
        anchor_length = 2
        anchors = 5
        anchor_distance = int((y_axis_end[1] - y_axis_start[1]) / 5)
        mid_point = (0, 0)
        for i in range(anchors):
            start_pos = (y_axis_start[0], y_axis_start[1] + anchor_distance * (i + 1))
            end_pos = (start_pos[0] - anchor_length, start_pos[1])
            anchor_shape = Line(self.axis_color, start_pos, end_pos)
            shapes.append(anchor_shape)

            if i == 0:
                mid_point = start_pos

            # add value text for the anchor
            if self.y_range[1] - self.y_range[0]:
                anchor_value = int(self.y_range[1] * 0.25 * (anchors - 1 - i))

                rendered_text = self.digit_font.render(str(anchor_value), True, self.text_color)
                anchor_text = Text(rendered_text, (end_pos[0] - 17, end_pos[1] - 3))
                shapes.append(anchor_text)
            elif i == 0:
                anchor_value = int(self.y_range[1])

                rendered_text = self.digit_font.render(str(anchor_value), True, self.text_color)
                anchor_text = Text(rendered_text, (end_pos[0] - 17, end_pos[1] - 3))
                shapes.append(anchor_text)

        # add points and constants
        last_x, last_y = (0, 0)
        for curve in self.curves:
            x_values = curve['x']
            y_values = curve['y']
            for i in range(len(x_values)):
                if not self.x_range[1] - self.x_range[0]:
                    x, y = mid_point
                else:
                    try:
                        x = int(x_axis_start[0] + (x_axis_end[0] - x_axis_start[0] - 20) / (self.x_range[1] - 1) * (x_values[i] - 1))
                    except ZeroDivisionError:
                        x = mid_point[0]
                    try:
                        y = int(y_axis_end[1] - anchor_distance * (anchors - 1) / self.y_range[1] * y_values[i])
                    except ZeroDivisionError:
                        y = mid_point[1]

                # connect points with line
                if i:
                    line = Line(curve['color'], (last_x, last_y), (x, y))
                    shapes.append(line)

                last_x, last_y = x, y

            # add label to curve
            if curve['label']:
                label_text = self.label_font.render(curve['label'], True, curve['color'])
                label = Text(label_text, (last_x + 5, last_y - 3))
                shapes.append(label)

        if self.constants:
            for constant in self.constants:
                start_x = x_axis_start[0]
                end_x = x_axis_end[0] - 20
                if self.y_range[1] - self.y_range[0] and constant['value'] - self.y_range[0]:
                    y = int(y_axis_end[1] - anchor_distance * (anchors - 1) / self.y_range[1] * constant['value'])
                else:
                    y = mid_point[1]
                line = DashLine(constant['color'], (start_x, y), (end_x, y), dash_length=5)
                shapes.append(line)

                # add label to constant
                if constant['label']:
                    constant_text = self.label_font.render(constant['label'], True, constant['color'])
                    constant = Text(constant_text, (end_x + 5, y - 3))
                    shapes.append(constant)

        # add caption
        if self.caption:
            rendered_text = self.caption_font.render(self.caption, True, self.text_color)
            caption_text = Text(rendered_text, (self.margin + 40, 0))
            shapes.append(caption_text)

        self._add_offset(shapes)

        return shapes
