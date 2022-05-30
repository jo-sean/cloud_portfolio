from string import ascii_letters, digits
import random


def state_gen():
    """Creates a 30 character length random string to be used as gen"""
    length = 30
    char_set = ascii_letters + digits

    pwd = ''.join(random.choice(char_set) for i in range(length))

    return pwd
