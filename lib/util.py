import math
import pygame
import random
from datetime import datetime as dt


__PYGAME_KEYS = {
    'A': [{'key': pygame.K_a}],
    'B': [{'key': pygame.K_b}],
    'C': [{'key': pygame.K_c}],
    'D': [{'key': pygame.K_d}],
    'E': [{'key': pygame.K_e}],
    'F': [{'key': pygame.K_f}],
    'G': [{'key': pygame.K_g}],
    'H': [{'key': pygame.K_h}],
    'I': [{'key': pygame.K_i}],
    'J': [{'key': pygame.K_j}],
    'K': [{'key': pygame.K_k}],
    'L': [{'key': pygame.K_l}],
    'M': [{'key': pygame.K_m}],
    'N': [{'key': pygame.K_n}],
    'O': [{'key': pygame.K_o}],
    'P': [{'key': pygame.K_p}],
    'Q': [{'key': pygame.K_q}],
    'R': [{'key': pygame.K_r}],
    'S': [{'key': pygame.K_s}],
    'T': [{'key': pygame.K_t}],
    'U': [{'key': pygame.K_u}],
    'V': [{'key': pygame.K_v}],
    'W': [{'key': pygame.K_w}],
    'X': [{'key': pygame.K_x}],
    'Y': [{'key': pygame.K_y}],
    'Z': [{'key': pygame.K_z}],
    '1': [{'key': pygame.K_1, 'shift': False}, {'key': pygame.K_KP1, 'shift': False}],
    '2': [{'key': pygame.K_2, 'shift': False}, {'key': pygame.K_KP2, 'shift': False}],
    '3': [{'key': pygame.K_3, 'shift': False}, {'key': pygame.K_KP3, 'shift': False}],
    '4': [{'key': pygame.K_4, 'shift': False}, {'key': pygame.K_KP4, 'shift': False}],
    '5': [{'key': pygame.K_5, 'shift': False}, {'key': pygame.K_KP5, 'shift': False}],
    '6': [{'key': pygame.K_6, 'shift': False}, {'key': pygame.K_KP6, 'shift': False}],
    '7': [{'key': pygame.K_7, 'shift': False}, {'key': pygame.K_KP7, 'shift': False}],
    '8': [{'key': pygame.K_8, 'shift': False}, {'key': pygame.K_KP8, 'shift': False}],
    '9': [{'key': pygame.K_9, 'shift': False}, {'key': pygame.K_KP9, 'shift': False}],
    '0': [{'key': pygame.K_0, 'shift': False}, {'key': pygame.K_KP0, 'shift': False}],
    ' ': [{'key': pygame.K_SPACE}],
    '!': [{'key': pygame.K_1, 'shift': True}],
    '@': [{'key': pygame.K_2, 'shift': True}],
    '#': [{'key': pygame.K_3, 'shift': True}],
    '$': [{'key': pygame.K_4, 'shift': True}],
    '%': [{'key': pygame.K_5, 'shift': True}],
    '^': [{'key': pygame.K_6, 'shift': True}],
    '&': [{'key': pygame.K_7, 'shift': True}],
    '*': [{'key': pygame.K_8, 'shift': True}, {'key': pygame.K_KP_MULTIPLY}],
    '(': [{'key': pygame.K_9, 'shift': True}],
    ')': [{'key': pygame.K_0, 'shift': True}],
    '-': [{'key': pygame.K_MINUS}, {'key': pygame.K_KP_MINUS}],
    '_': [{'key': pygame.K_MINUS, 'shift': True}],
    '=': [{'key': pygame.K_EQUALS}, {'key': pygame.K_KP_EQUALS}],
    '+': [{'key': pygame.K_EQUALS, 'shift': True}, {'key': pygame.K_KP_PLUS}],
    '/': [{'key': pygame.K_SLASH}, {'key': pygame.K_KP_DIVIDE}],
    '?': [{'key': pygame.K_SLASH, 'shift': True}],
    '[': [{'key': pygame.K_LEFTBRACKET}],
    '{': [{'key': pygame.K_LEFTBRACKET, 'shift': True}],
    ']': [{'key': pygame.K_RIGHTBRACKET}],
    '}': [{'key': pygame.K_RIGHTBRACKET, 'shift': True}],
    '\\': [{'key': pygame.K_BACKSLASH}],
    '|': [{'key': pygame.K_BACKSLASH, 'shift': True}],
    '`': [{'key': pygame.K_BACKQUOTE}],
    '~': [{'key': pygame.K_BACKQUOTE, 'shift': True}],
    ';': [{'key': pygame.K_SEMICOLON}],
    ':': [{'key': pygame.K_SEMICOLON, 'shift': True}],
    '\'': [{'key': pygame.K_QUOTE}],
    '\"': [{'key': pygame.K_QUOTE, 'shift': True}],
    ',': [{'key': pygame.K_COMMA}],
    '<': [{'key': pygame.K_COMMA, 'shift': True}],
    '.': [{'key': pygame.K_PERIOD}],
    '>': [{'key': pygame.K_PERIOD, 'shift': True}],
    '←': [{'key': pygame.K_BACKSPACE}]
}


def in_sorted(target, sorted_list):
    """Check if target is in the given sorted list"""
    for ind in range(len(sorted_list)):
        if target == sorted_list[ind]:
            return True
        elif target > ind:
            continue
        else:
            return False
    return False


def split_list(a, n):
    """Split the given list into n parts and return a list of parts"""
    part_len = int(len(a) / n)
    parts = []
    for i in range(n):
        start_ind = i * part_len
        end_ind = (i + 1) * part_len
        if i == n - 1:
            parts.append(a[start_ind:])
        else:
            parts.append(a[start_ind:end_ind])
    return parts


def distance(a, b):
    """Calculate the distance between point a and b"""
    return math.sqrt((a[0] - b[0]) ** 2 + (a[1] - b[1]) ** 2)


def get_timestr():
    """Return the current time"""
    return str(dt.now())[:19]


def bytes_to_string(n):
    """Convert bytes to human-readable units"""
    if n < 1000:
        return "{}B".format(n)

    n /= 1000
    if n < 1000:
        return "{:.2f}K".format(n)

    n /= 1000
    if n < 1000:
        return "{:.2f}M".format(n)

    n /= 1000
    return "{:.2f}G".format(n)


def log_to_file(content):
    """Output log information"""
    print("[{}] {}".format(get_timestr(), content))


def ctrl_pressed():
    pressed = pygame.key.get_pressed()
    return bool(pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL])


def shift_pressed():
    pressed = pygame.key.get_pressed()
    return bool(pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT])


def cap_lock_on():
    return bool(pygame.key.get_mods() & pygame.KMOD_CAPS)


def is_key_active(des):
    if des is None or ctrl_pressed():
        return False

    shift = shift_pressed()
    caps = cap_lock_on()
    pressed = pygame.key.get_pressed()

    des_shift = des.get('shift')
    des_caps = des.get('caps')
    return pressed[des['key']] and \
        (shift == des_shift or des_shift is None) and \
        (caps == des_caps or des_caps is None)


def char_to_pygame_key(c):
    """Convert character to pygame key"""
    global __PYGAME_KEYS
    ret = __PYGAME_KEYS.get(c)
    if ret is not None:
        return ret[0]


def pygame_key_to_char(key):
    """Convert pygame key to character"""
    global __PYGAME_KEYS
    shift = shift_pressed()
    caps = cap_lock_on()
    for c in __PYGAME_KEYS:
        for des in __PYGAME_KEYS[c]:
            des_shift = des.get('shift')
            des_caps = des.get('caps')
            if des['key'] == key and \
               (shift == des_shift or des_shift is None) and \
               (caps == des_caps or des_caps is None):
                if 'A' <= c <= 'Z' and not shift ^ caps:
                    return c.lower()
                return c


def choices(l, k=1):
    """Randomly choose k items from l"""
    length = len(l)
    if length <= k:
        return l

    result = []
    selected = [False for _ in range(length)]
    while len(result) < k:
        ind = random.choice(range(length))
        if not selected[ind]:
            result.append(l[ind])
            selected[ind] = True
    
    return result
