import math
import pygame
from datetime import datetime as dt


__PYGAME_KEYS = {
    'a': [{'key': pygame.K_a}, {'key': pygame.K_a, 'shift': True, 'caps': True}],
    'b': [{'key': pygame.K_b}, {'key': pygame.K_b, 'shift': True, 'caps': True}],
    'c': [{'key': pygame.K_c}, {'key': pygame.K_c, 'shift': True, 'caps': True}],
    'd': [{'key': pygame.K_d}, {'key': pygame.K_d, 'shift': True, 'caps': True}],
    'e': [{'key': pygame.K_e}, {'key': pygame.K_e, 'shift': True, 'caps': True}],
    'f': [{'key': pygame.K_f}, {'key': pygame.K_f, 'shift': True, 'caps': True}],
    'g': [{'key': pygame.K_g}, {'key': pygame.K_g, 'shift': True, 'caps': True}],
    'h': [{'key': pygame.K_h}, {'key': pygame.K_h, 'shift': True, 'caps': True}],
    'i': [{'key': pygame.K_i}, {'key': pygame.K_i, 'shift': True, 'caps': True}],
    'j': [{'key': pygame.K_j}, {'key': pygame.K_j, 'shift': True, 'caps': True}],
    'k': [{'key': pygame.K_k}, {'key': pygame.K_k, 'shift': True, 'caps': True}],
    'l': [{'key': pygame.K_l}, {'key': pygame.K_l, 'shift': True, 'caps': True}],
    'm': [{'key': pygame.K_m}, {'key': pygame.K_m, 'shift': True, 'caps': True}],
    'n': [{'key': pygame.K_n}, {'key': pygame.K_n, 'shift': True, 'caps': True}],
    'o': [{'key': pygame.K_o}, {'key': pygame.K_o, 'shift': True, 'caps': True}],
    'p': [{'key': pygame.K_p}, {'key': pygame.K_p, 'shift': True, 'caps': True}],
    'q': [{'key': pygame.K_q}, {'key': pygame.K_q, 'shift': True, 'caps': True}],
    'r': [{'key': pygame.K_r}, {'key': pygame.K_r, 'shift': True, 'caps': True}],
    's': [{'key': pygame.K_s}, {'key': pygame.K_s, 'shift': True, 'caps': True}],
    't': [{'key': pygame.K_t}, {'key': pygame.K_t, 'shift': True, 'caps': True}],
    'u': [{'key': pygame.K_u}, {'key': pygame.K_u, 'shift': True, 'caps': True}],
    'v': [{'key': pygame.K_v}, {'key': pygame.K_v, 'shift': True, 'caps': True}],
    'w': [{'key': pygame.K_w}, {'key': pygame.K_w, 'shift': True, 'caps': True}],
    'x': [{'key': pygame.K_x}, {'key': pygame.K_x, 'shift': True, 'caps': True}],
    'y': [{'key': pygame.K_y}, {'key': pygame.K_y, 'shift': True, 'caps': True}],
    'z': [{'key': pygame.K_z}, {'key': pygame.K_z, 'shift': True, 'caps': True}],
    'A': [{'key': pygame.K_a, 'shift': True}, {'key': pygame.K_a, 'caps': True}],
    'B': [{'key': pygame.K_b, 'shift': True}, {'key': pygame.K_b, 'caps': True}],
    'C': [{'key': pygame.K_c, 'shift': True}, {'key': pygame.K_c, 'caps': True}],
    'D': [{'key': pygame.K_d, 'shift': True}, {'key': pygame.K_d, 'caps': True}],
    'E': [{'key': pygame.K_e, 'shift': True}, {'key': pygame.K_e, 'caps': True}],
    'F': [{'key': pygame.K_f, 'shift': True}, {'key': pygame.K_f, 'caps': True}],
    'G': [{'key': pygame.K_g, 'shift': True}, {'key': pygame.K_g, 'caps': True}],
    'H': [{'key': pygame.K_h, 'shift': True}, {'key': pygame.K_h, 'caps': True}],
    'I': [{'key': pygame.K_i, 'shift': True}, {'key': pygame.K_i, 'caps': True}],
    'J': [{'key': pygame.K_j, 'shift': True}, {'key': pygame.K_j, 'caps': True}],
    'K': [{'key': pygame.K_k, 'shift': True}, {'key': pygame.K_k, 'caps': True}],
    'L': [{'key': pygame.K_l, 'shift': True}, {'key': pygame.K_l, 'caps': True}],
    'M': [{'key': pygame.K_m, 'shift': True}, {'key': pygame.K_m, 'caps': True}],
    'N': [{'key': pygame.K_n, 'shift': True}, {'key': pygame.K_n, 'caps': True}],
    'O': [{'key': pygame.K_o, 'shift': True}, {'key': pygame.K_o, 'caps': True}],
    'P': [{'key': pygame.K_p, 'shift': True}, {'key': pygame.K_p, 'caps': True}],
    'Q': [{'key': pygame.K_q, 'shift': True}, {'key': pygame.K_q, 'caps': True}],
    'R': [{'key': pygame.K_r, 'shift': True}, {'key': pygame.K_r, 'caps': True}],
    'S': [{'key': pygame.K_s, 'shift': True}, {'key': pygame.K_s, 'caps': True}],
    'T': [{'key': pygame.K_t, 'shift': True}, {'key': pygame.K_t, 'caps': True}],
    'U': [{'key': pygame.K_u, 'shift': True}, {'key': pygame.K_u, 'caps': True}],
    'V': [{'key': pygame.K_v, 'shift': True}, {'key': pygame.K_v, 'caps': True}],
    'W': [{'key': pygame.K_w, 'shift': True}, {'key': pygame.K_w, 'caps': True}],
    'X': [{'key': pygame.K_x, 'shift': True}, {'key': pygame.K_x, 'caps': True}],
    'Y': [{'key': pygame.K_y, 'shift': True}, {'key': pygame.K_y, 'caps': True}],
    'Z': [{'key': pygame.K_z, 'shift': True}, {'key': pygame.K_z, 'caps': True}],
    '1': [{'key': pygame.K_1}, {'key': pygame.K_KP1}],
    '2': [{'key': pygame.K_2}, {'key': pygame.K_KP2}],
    '3': [{'key': pygame.K_3}, {'key': pygame.K_KP3}],
    '4': [{'key': pygame.K_4}, {'key': pygame.K_KP4}],
    '5': [{'key': pygame.K_5}, {'key': pygame.K_KP5}],
    '6': [{'key': pygame.K_6}, {'key': pygame.K_KP6}],
    '7': [{'key': pygame.K_7}, {'key': pygame.K_KP7}],
    '8': [{'key': pygame.K_8}, {'key': pygame.K_KP8}],
    '9': [{'key': pygame.K_9}, {'key': pygame.K_KP9}],
    '0': [{'key': pygame.K_0}, {'key': pygame.K_KP0}],
    ' ': [{'key': pygame.K_SPACE}, {'key': pygame.K_SPACE, 'shift': True}],
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
    '>': [{'key': pygame.K_PERIOD, 'shift': True}]
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

    n /= 1000.0
    if n < 1000:
        return "{:.2f}K".format(n)

    n /= 1000.0
    if n < 1000:
        return "{:.2f}M".format(n)

    n /= 1000.0
    return "{:.2f}G".format(n)

def log_to_file(content):
    """Output log information"""
    print("[{}] {}".format(get_timestr(), content))

def ctrl_pressed():
    pressed = pygame.key.get_pressed()
    return pressed[pygame.K_LCTRL] or pressed[pygame.K_RCTRL]

def shift_pressed():
    pressed = pygame.key.get_pressed()
    return pressed[pygame.K_LSHIFT] or pressed[pygame.K_RSHIFT]

def cap_lock_on():
    return pygame.key.get_mods() & pygame.KMOD_CAPS

def is_key_active(des):
    if des is None or ctrl_pressed():
        return False

    shift = shift_pressed()
    caps = cap_lock_on()
    pressed = pygame.key.get_pressed()

    des_shift = bool(des.get('shift'))
    des_caps = bool(des.get('caps'))
    return pressed[des['key']] and shift == des_shift and caps == des_caps

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
            des_shift = bool(des.get('shift'))
            des_caps = bool(des.get('caps'))
            if des['key'] == key and shift == des_shift and caps == des_caps:
                return c
