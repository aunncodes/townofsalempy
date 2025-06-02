from enum import Enum

class Defense(Enum):
    NONE = 0
    BASIC = 1
    POWERFUL = 2
    INVINCIBLE = 3

class Attack(Enum):
    NONE = 0
    BASIC = 1
    POWERFUL = 2
    UNSTOPPABLE = 3

class Alignment(Enum):
    TOWN = 1
    MAFIA = 2
    NEUTRAL = 3

class Phase(Enum):
    LOBBY = 1
    NIGHT = 2
    DAY = 3
    VOTING = 4

class Action(Enum):
    NONE = 0
    ATTACK = 1
    PROTECT = 2
    INVESTIGATE = 3

if __name__ == '__main__':
    print("This file is not meant to be run directly.")