import json
from dataclasses import dataclass, field
from os import PathLike
from pathlib import Path
from typing import Annotated, Any, Dict, List, Literal, Tuple

from enums import AttitudeEnum, ItemTypeEnum, RaceEnum


# https://docs.python.org/3/library/enum.html#enum.Enum
# class ToolEnum(IntEnum):
#     spanner = 1
#     wrench = 2

###################################################################################################################
# MARK: Character

# class Character(BaseModel):
#     name: str   = Field(min_length=3, rozen=True, description="Unique character name")
#     sprite: str = Field(min_length=3,
#                       description=f"Must be valid asset folder name (assets/[ASSET_PACK]/characters/[sprite])" ,
#                       repr=False)
#     race:         Annotated[RaceEnum,     Field(description="Base character race (e.g. humanoid, animal)")]
#     attitude:     Annotated[AttitudeEnum, Field(description="Attitude towards the player", repr=False)]
#     health:       Annotated[int,          Field(30, ge=0, description="initial health value", repr=False)]
#     max_health:   Annotated[int,          Field(30, ge=0, description="maximal health value", repr=False)]
#     money:        Annotated[int,          Field(0,  ge=0, description="initial amount of possessed money",
#                                               repr=False)]
#     damage:       Annotated[int,          Field(10, ge=0, description="amount of damage delt to others", repr=False)]

# dataclass version


@dataclass(slots=True)
class MazeLevelProperties():
    monsters_list:        Annotated[list[str], field(repr=False)]
    boss_monster:         str =                field(repr=False)
    monsters_count:       Annotated[int,       field(repr=False)]
    small_chest_count:    Annotated[int,       field(repr=False)]
    small_chest_template: Annotated[str,       field(repr=False)]
    big_chest_template:   Annotated[str,       field(repr=False)]
    maze_cols:            Annotated[int,       field(repr=False)]
    maze_rows:            Annotated[int,       field(repr=False)]

    @classmethod
    def from_dict(cls: type["MazeLevelProperties"], data: dict[str, Any]) -> "MazeLevelProperties":
        return cls(
            monsters_list        = data.get("monsters_list",        []),
            boss_monster         = data.get("boss_monster",         ""),
            monsters_count       = data.get("monsters_count",       4),
            small_chest_count    = data.get("chest_count",          1),
            small_chest_template = data.get("small_chest_template", ""),
            big_chest_template   = data.get("big_chest_template",   ""),
            maze_cols            = data.get("maze_cols",            10),
            maze_rows            = data.get("maze_rows",            7)
        )


@dataclass(slots=True)
class Character():
    name: str
    sprite:          str = field(repr=False)
    race:             RaceEnum
    attitude:         AttitudeEnum
    allowed_zones:    Annotated[list[str], field(repr=False)]
    health:           Annotated[int,       field(repr=False)]
    max_health:       Annotated[int,       field(repr=False)]
    items:            Annotated[list[str], field(repr=False)]
    max_carry_weight: Annotated[float,     field(repr=False)]
    money:            Annotated[int,       field(repr=False)]
    damage:           Annotated[int,       field(repr=False)]
    speed_walk:       Annotated[int,       field(repr=False)]
    speed_run:        Annotated[int,       field(repr=False)]

    @classmethod
    def from_dict(cls: type["Character"], data: dict[str, Any]) -> "Character":
        return cls(
            name = data.get("name", ""),
            sprite = data.get("sprite", ""),
            race = RaceEnum(data.get("race", "")),
            attitude = AttitudeEnum(data.get("attitude", "")),
            allowed_zones = data.get("allowed_zones", []),
            health = data.get("health", 30),
            max_health = data.get("max_health", 30),
            items = data.get("items", []),
            max_carry_weight = data.get("max_carry_weight", 15.0),
            money = data.get("money", 0),
            damage = data.get("damage", 10),
            speed_walk = data.get("speed_walk", 30),
            speed_run = data.get("speed_run", 40),
        )


@dataclass(slots=True)
class Item():
    # id:            Annotated[str,          field(repr=False)]
    name:          str
    type:          ItemTypeEnum
    value:         Annotated[int,   field(repr=False)]
    health_impact: Annotated[int,   field(repr=False)]
    in_use:        Annotated[bool,  field(repr=False)]
    damage:        Annotated[int,   field(repr=False)]
    count:         Annotated[int,   field(repr=False)]
    weight:        Annotated[float, field(repr=False)]
    cooldown_time: Annotated[float, field(repr=False)]

    @classmethod
    def from_dict(cls, data: dict[str, Any]) -> "Item":
        return cls(
            # id            = data.get("id", ""),
            name          = data.get("name", ""),
            type          = ItemTypeEnum(data.get("type", "")),
            value         = data.get("value", 50),
            health_impact = data.get("health_impact", 0),
            in_use        = data.get("in_use", False),
            damage        = data.get("damage", 10),
            count         = data.get("count", 1),
            weight        = data.get("weight", 1.0),
            cooldown_time = data.get("cooldown_time", 1.0),
        )


@dataclass(slots=True)
class Chest():
    name:               str
    is_small:           Annotated[bool,      field(repr=False)]
    is_closed:          Annotated[bool,      field(repr=False)]
    items:              Annotated[list[str], field(repr=False)]
    total_items_count:  Annotated[int,       field(repr=False)]
    random_items:       Annotated[list[str], field(repr=False)]

    @classmethod
    def from_dict(cls: type["Chest"], data: dict[str, Any]) -> "Chest":
        return cls(
            name      =          data.get("name", ""),
            is_small  =          data.get("is_small", True),
            is_closed =          data.get("is_closed", True),
            items     =          data.get("items", []),
            total_items_count =  data.get("random_items_count", 0),
            random_items      =  data.get("random_items", []),
        )


###################################################################################################################
# MARK: Config

# class Config(BaseModel):
#     characters: Dict[str, Character]

# dataclass version


@dataclass
class Config():
    characters:   dict[str, Character]
    items:        dict[str, Item]
    chests:       dict[str, Chest]
    maze_configs: dict[int, MazeLevelProperties]

    @classmethod
    def build(cls, data: dict[str, Any]) -> "Config":
        chars = {}
        for name, character_dict in data["characters"].items():
            character = Character.from_dict(character_dict)
            chars[name] = character

        items = {}
        for name, item_dict in data["items"].items():
            item = Item.from_dict(item_dict)
            items[name] = item

        chests = {}
        for name, chest_dict in data["chests"].items():
            chest = Chest.from_dict(chest_dict)
            chests[name] = chest

        maze_configs = {}
        for name, maze_config_dict in data["maze_configs"].items():
            maze_config = MazeLevelProperties.from_dict(maze_config_dict)
            maze_configs[int(name)] = maze_config

        return cls(chars, items, chests, maze_configs)
###################################################################################################################


def test() -> None:
    # try:
    #     main_conf = Config(**conf)
    # except ValidationError as e:
    #     print(e.errors())

    # save_config_schema(Config, Path("config_schema.json"))

    c = load_config(Path("config.json"))

    print(len(c.characters.keys()))

###################################################################################################################
# MARK: Helper functions
# def generate_config_schema(model: BaseModel) -> dict[str, Any]:
#     return model.model_json_schema()


# def save_config_schema(model: BaseModel, file_name: PathLike) -> None:
#     schema = generate_config_schema(model)
#     with open(file_name, "w", encoding="utf-8") as f:
#         json.dump(schema, f, ensure_ascii=False, indent=4)

###################################################################################################################
# def save_config(model: BaseModel, file_name: PathLike) -> None:
#     with open(file_name, "w", encoding="utf-8") as f:
#         json.dump(model.model_dump_json(), f, ensure_ascii=False, indent=4)


def load_config(file_name: PathLike) -> "Config":
    with open(file_name, "r") as f:
        config_json = json.load(f)

    del config_json["$schema"]
    config = Config.build(config_json)
    # try:
    #     config = Config(**config_json)
    # # except ValidationError as e:
    # except Exception as e:
    #     print(e.errors())
    # finally:
    # print(config.characters)
    return config


###################################################################################################################
if __name__ == "__main__":
    test()
