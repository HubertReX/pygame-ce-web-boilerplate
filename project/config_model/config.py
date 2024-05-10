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

# https://docs.python.org/3/library/enum.html#enum.Enum  
# class ToolEnum(IntEnum):
#     spanner = 1
#     wrench = 2

###################################################################################################################
#MARK: Character
class Character(BaseModel):
    name: str   = Field(min_length=3, rozen=True, description="Unique character name")
    sprite: str = Field(min_length=3, description=f"Must be valid asset folder name (assets/[ASSET_PACK]/characters/[sprite])" , repr=False)
    race:         Annotated[RaceEnum,     Field(description="Base character race (e.g. humanoid, animal)")]
    attitude:     Annotated[AttitudeEnum, Field(description="Attitude towards the player", repr=False)]
    health:       Annotated[int,          Field(30, ge=0, description="initial health value", repr=False)]
    max_health:   Annotated[int,          Field(30, ge=0, description="maximal health value", repr=False)]
    money:        Annotated[int,          Field(0,  ge=0, description="initial amount of possessed money", repr=False)]
    damage:       Annotated[int,          Field(10, ge=0, description="amount of damage delt to others", repr=False)]

###################################################################################################################
#MARK: Config
class Config(BaseModel):
    characters: Dict[str, Character]


###################################################################################################################

def test():
    # try:
    #     main_conf = Config(**conf)
    # except ValidationError as e:
    #     print(e.errors())
    
    save_config_schema(Config, Path("config_schema.json"))

    c = load_config(Path("config.json"))
    
    print(len(c.characters.keys()))
    
###################################################################################################################
#MARK: Helper functions
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
    
    
def load_config(file_name: PathLike) -> Config:
    with open(file_name, "r") as f:
        config_json = json.load(f)

    try:
        config = Config(**config_json)
    except ValidationError as e:
        print(e.errors())
    finally:
        return config
    
###################################################################################################################
if __name__ == "__main__":
    test()
    