from dataclasses import dataclass, field
import json
from os import PathLike
from pathlib import Path
from enum import Enum, IntEnum, StrEnum, auto
from typing import Annotated, Any, Dict, List, Literal, Tuple
from pydantic import BaseModel, PositiveInt, Field, ValidationError

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

# https://docs.python.org/3/library/enum.html#enum.Enum
# class ToolEnum(IntEnum):
#     spanner = 1
#     wrench = 2

##################################################################################################################
# MARK: Character


class Character(BaseModel):
    name: str   = Field(min_length=3, rozen=True, description="Unique character name")
    sprite: str = Field(
        min_length=3,
        description="Must be valid asset folder name (assets/[ASSET_PACK]/characters/[sprite])",
        repr=False
    )
    race:         Annotated[RaceEnum,     Field(description="Base character race (e.g. humanoid, animal)")]
    attitude:     Annotated[AttitudeEnum, Field(description="Attitude towards the player", repr=False)]
    health:       Annotated[int,          Field(30, ge=0, description="initial health value", repr=False)]
    max_health:   Annotated[int,          Field(30, ge=0, description="maximal health value", repr=False)]
    max_carry_weight: Annotated[float,    Field(15.0, ge=0, description="maximal carrying weight in kg", repr=False)]
    money:        Annotated[int,          Field(0,  ge=0, description="initial amount of possessed money", repr=False)]
    damage:       Annotated[int,          Field(10, ge=0, description="amount of damage delt to others", repr=False)]

##################################################################################################################
# MARK: Item


class Item(BaseModel):
    name: str   = Field(
        min_length=3, rozen=True, description="Unique item name")
    type:          Annotated[ItemTypeEnum, Field(
        description="Item type (e.g. weapon, tool, consumable)")]
    value:         Annotated[int,          Field(
        50, ge=0, description="Monetary value", repr=False)]
    health_impact: Annotated[int,          Field(
        0, ge=0,
        description="The impact on health when consumed (e.g. apple => +30, poison => -10)",
        repr=False)]
    in_use:        Annotated[bool,         Field(
        False,
        description="Whether the item is currently in use", repr=False)]
    count:         Annotated[int,          Field(
        1, ge=1, description="Number of items in the stack", repr=False)]
    weight:        Annotated[float,        Field(
        1.0, ge=0, description="Weight of single item in the stack in kg", repr=False)]
    damage:        Annotated[int,          Field(
        10, ge=0,
        description="The amount of damage delt (weapon only)", repr=False)]
    cooldown_time: Annotated[float,        Field(
        1.0, ge=0.0,
        description="The amount of time in seconds it takes to use the weapon again",
        repr=False)]
# dataclass version


# @dataclass
# class Character():
#     name: str
#     sprite: str = field(repr=False)
#     race:         RaceEnum
#     attitude:     AttitudeEnum
#     health:       Annotated[int,          field(repr=False)]
#     max_health:   Annotated[int,          field(repr=False)]
#     money:        Annotated[int,          field(repr=False)]
#     damage:       Annotated[int,          field(repr=False)]

#     @classmethod
#     def from_dict(cls, data):
#         return cls(
#             name = data.get('name'),
#             sprite = data.get('sprite'),
#             race = data.get('race'),
#             attitude = data.get('attitude'),
#             health = data.get('health', 30),
#             max_health = data.get('max_health', 30),
#             money = data.get('money', 0),
#             damage = data.get('damage', 10),
#         )

###################################################################################################################
# MARK: Config

class Config(BaseModel):
    characters: Dict[str, Character]
    items: Dict[str, Item]

# dataclass version


# @dataclass
# class Config():
#     characters: Dict[str, Character]

#     @classmethod
#     def build(cls, data):
#         chars = {}
#         for name, chr in data["characters"].items():
#             # print(name, chr)
#             character = Character.from_dict(chr)
#             chars[name] = character

#         return cls(chars)
###################################################################################################################


def test():
    # try:
    #     main_conf = Config(**conf)
    # except ValidationError as e:
    #     print(e.errors())

    save_config_schema(Config, Path("config_schema.json"))

    # c = load_config(Path("config.json"))

    # print(len(c.characters.keys()))

###################################################################################################################
# MARK: Helper functions


def generate_config_schema(model: BaseModel) -> dict[str, Any]:
    return model.model_json_schema()


def save_config_schema(model: BaseModel, file_name: PathLike) -> None:
    schema = generate_config_schema(model)
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=4)

###################################################################################################################


def save_config(model: BaseModel, file_name: PathLike) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(model.model_dump_json(), f, ensure_ascii=False, indent=4)


###################################################################################################################
def load_config(file_name: PathLike) -> "Config":
    with open(file_name, "r") as f:
        config_json = json.load(f)

    # del config_json["$schema"]
    # config = Config.build(config_json)
    try:
        config = Config(**config_json)
    # except ValidationError as e:
    except Exception as e:
        print(e.errors())
    # finally:
    #     print(config.characters)
    return config


###################################################################################################################
if __name__ == "__main__":
    test()
