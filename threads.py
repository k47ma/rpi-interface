import os
import requests
import random
import pygame
from threading import Thread

class RequestThread(Thread):
    def __init__(self, queue, url, payload):
        super(RequestThread, self).__init__()

        self.queue = queue
        self.url = url
        self.payload = payload
        self.daemon = True

    def run(self):
        res = requests.get(self.url, params=self.payload)
        self.queue.put(res.json())


class ImageFetchThread(Thread):
    def __init__(self, url, news, directory):
        super(ImageFetchThread, self).__init__()

        self.url = url
        self.news = news
        self.directory = directory
        self.daemon = True

    def run(self):
        if not self.news['imageName']:
            return

        image_path = os.path.join(self.directory, self.news['imageName'])
        if os.path.isfile(image_path):
            prefix = str(random.randint(100000, 1000000)) + "-"
            new_image_name = prefix + self.news['imageName']
            image_path = os.path.join(self.directory, new_image_name)
            self.news['imageName'] = new_image_name

        with open(image_path, 'wb') as f:
            f.write(requests.get(self.url).content)


class ImageRotateThread(Thread):
    def __init__(self, image, center, queue):
        super(ImageRotateThread, self).__init__()

        self.image = image
        self.center = center
        self.queue = queue
        self.daemon = True

    def run(self):
        image_set = []
        for ind in range(1080):
            rotate_image = pygame.transform.rotate(self.image, ind * 0.333)
            rotate_rect = rotate_image.get_rect(center=self.center)
            image_set.append((rotate_image, rotate_rect))
        self.queue.put(image_set)
