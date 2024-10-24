from enum import Enum, StrEnum, auto


###################################################################################################################


class RaceEnum(StrEnum):
    humanoid = auto()
    animal = auto()
    monster = auto()

###################################################################################################################


class AttitudeEnum(StrEnum):
    friendly = auto()
    afraid = auto()
    enemy = auto()

###################################################################################################################


class ItemTypeEnum(StrEnum):
    weapon = auto()
    key = auto()
    consumable = auto()
    money = auto()
    gem = auto()

#################################################################################################################


class NPCEventActionEnum(Enum):
    stunned: int  = auto()
    pushed: int   = auto()
    standard: int = auto()
    resting: int   = auto()
    attacking: int = auto()
    switching_weapon: int = auto()


#################################################################################################################


class NotificationTypeEnum(StrEnum):
    debug = auto()
    info = auto()
    warning = auto()
    error = auto()
    success = auto()
    failure = auto()
