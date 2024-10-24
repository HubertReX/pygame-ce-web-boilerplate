from enum import StrEnum, auto


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


class NotificationTypeEnum(StrEnum):
    debug = auto()
    info = auto()
    warning = auto()
    error = auto()
    success = auto()
    failure = auto()
