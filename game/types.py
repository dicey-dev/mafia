from enum import Enum


class Role(str, Enum):
    MAFIA = "mafia"
    VILLAGER = "villager"
    HEALER = "healer"
    DETECTIVE = "detective"
    ALL = "all"
