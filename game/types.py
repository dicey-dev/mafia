from enum import Enum


class Role(str, Enum):
    MAFIA = "mafia"
    VILLAGER = "villager"
    HEALER = "healer"
    DETECTIVE = "detective"
    ALL = "all"


class Phase(str, Enum):
    NIGHT = "night"
    DAY = "day"
    VOTING = "voting"


PlayerName = str
