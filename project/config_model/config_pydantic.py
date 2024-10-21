import json
from dataclasses import dataclass, field
from enum import Enum, IntEnum, StrEnum, auto
from os import PathLike
from pathlib import Path
from typing import Annotated, Any
from rich import print
from pydantic import BaseModel, ConfigDict, Field, PositiveInt, ValidationError

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


class MazeLevelProperties(BaseModel):
    model_config = ConfigDict(extra="forbid")

    monsters_list:  Annotated[list[str],    Field(
        description="List of regular monster NPC models names", repr=False, default_factory=list)]

    boss_monster:   str                   = Field(min_length=3, description="Boss monster NPC model name")
    monsters_count: Annotated[int,          Field(4, description="Number of regular monster per level (without boss)",
                                                  ge=0, repr=False)]
    chest_count: Annotated[int,             Field(1, description="Number of chest on the map",
                                                  ge=0, repr=False)]
    maze_cols: Annotated[int,              Field(10, description="Number of columns in map grid",
                                                 ge=0, repr=False)]
    maze_rows: Annotated[int,              Field(7, description="Number of rows in map grid",
                                                 ge=0, repr=False)]


class Character(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str   = Field(min_length=3, frozen=True, description="Unique character name")
    sprite: str = Field(
        min_length=3,
        description="Must be valid asset folder name (assets/[ASSET_PACK]/characters/[sprite])",
        repr=False
    )
    race:          Annotated[RaceEnum,     Field(description="Base character race (e.g. humanoid, animal)")]
    attitude:      Annotated[AttitudeEnum, Field(description="Attitude towards the player", repr=False)]
    allowed_zones: Annotated[list[str],    Field(
        description="Zones where the character is allowed to move", repr=False, default_factory = list)]
    health:        Annotated[int,          Field(30, ge=0, description="initial health value", repr=False)]
    max_health:    Annotated[int,          Field(30, ge=0, description="maximal health value", repr=False)]
    # items:        Annotated[list["Item"], Field(description="list of character's items", default_factory = list)]
    items:         Annotated[list[str],    Field(description="list of character's items", default_factory = list)]
    max_carry_weight: Annotated[float,     Field(15.0, ge=0, description="maximal carrying weight in kg", repr=False)]
    money:         Annotated[int,          Field(0,  ge=0, description="initial amount of possessed money", repr=False)]
    damage:        Annotated[int,          Field(10, ge=0, description="amount of damage delt to others", repr=False)]
    speed_walk:    Annotated[int,          Field(30, gr=0, description="walking speed", repr=False)]
    speed_run:     Annotated[int,          Field(40, gr=0, description="walking speed", repr=False)]


##################################################################################################################
# MARK: Item


class Item(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # id: str   = Field(
    #     min_length=3, frozen=True, description="Unique string identifier")
    name: str   = Field(
        min_length=3, frozen=True, description="Item display name")
    type:          Annotated[ItemTypeEnum, Field(description="Item type (e.g. weapon, tool, consumable)")]
    value:         Annotated[int,          Field(50, ge=0, description="Monetary value", repr=False)]
    health_impact: Annotated[int,          Field(
        0, ge=0,
        description="The impact on health when consumed (e.g. apple => +30, poison => -10)",
        repr=False)]
    in_use:        Annotated[bool,         Field(False, description="Whether the item is currently in use", repr=False)]
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


###################################################################################################################
class Chest(BaseModel):
    model_config = ConfigDict(extra="forbid")

    # id: str   = Field(
    #     min_length=3, frozen=True, description="Unique string identifier")
    name: str = Field(min_length=3, frozen=True, description="Chest display name")
    is_small:   Annotated[bool,      Field(True, description="Is it small or big", repr=False)]
    is_closed:  Annotated[bool,      Field(True, description="Is it closed or open", repr=False)]
    items:      Annotated[list[str], Field(description="list of items in the chest", default_factory = list)]

###################################################################################################################
# MARK: Config


class Config(BaseModel):
    # this class is used only for crating instances of the config class
    characters: dict[str, Character]
    items: dict[str, Item]
    chests: dict[str, Chest]
    maze_configs: dict[int, MazeLevelProperties]


class ConfigForSchemaGen(Config):
    # this class is used only for generating the config schema
    # we can't use the same class since $schema won't validate
    # json_schema_extra={'$schema': "./config_schema.json"}
    model_config = ConfigDict(extra="forbid")


###################################################################################################################


def test() -> None:
    # try:
    #     main_conf = Config(**conf)
    # except ValidationError as e:
    #     print(e.errors())

    save_config_schema(ConfigForSchemaGen, Path("config_schema.json"))

    # c = load_config(Path("config.json"))

    # print(len(c.characters.keys()))

###################################################################################################################
# MARK: Helper functions


def generate_config_schema(model: type[Config]) -> dict[str, Any]:
    return model.model_json_schema()


def save_config_schema(model: type[Config], file_name: PathLike) -> None:
    schema = generate_config_schema(model)
    # hack allows to add additional property that $schema name
    schema["properties"]["$schema"] = f"./{file_name}"
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(schema, f, ensure_ascii=False, indent=4)
    print(f"\n[light_green]INFO[/] Config schema regenerated and saved to '{file_name}'\n")

###################################################################################################################


def save_config(model: Config, file_name: PathLike) -> None:
    with open(file_name, "w", encoding="utf-8") as f:
        json.dump(model.model_dump_json(), f, ensure_ascii=False, indent=4)


###################################################################################################################
def load_config(file_name: PathLike) -> "Config":
    config: Config | None = None
    with open(file_name, "r") as f:
        config_json = json.load(f)

    # del config_json["$schema"]
    # config = Config.build(config_json)
    try:
        config = Config(**config_json)
    # except ValidationError as e:
    except Exception as e:
        print("[red]Error![/] Unable to create config - validation failed.")
        print(e)
        exit(1)
    # finally:
    #     print(config.characters)
    return config


###################################################################################################################
if __name__ == "__main__":
    save_config_schema(ConfigForSchemaGen, Path("config_schema.json"))
