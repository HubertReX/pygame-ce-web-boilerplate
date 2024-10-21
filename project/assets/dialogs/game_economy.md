# Game economy

## player goals / behavior tree

- stay alive
  - keep [health](#health) above `0`
  - keep [stamina](#stamina) above `0`

- keep [health](#health) above `0`
  - buy [potion](#item) from [merchant](#npc) `or` gather [potion](#item)
  - eat [potion](#item)

- keep [stamina](#stamina) above `0`
  - [resting](#resting) (`?`)

- earn [money](#money)
  - sell [items](#item) to [merchant](#npc)
  - complete [quests](#quest)

- get stronger
  - get better [items](#item)

- get better [items](#item)
  - earn [money](#money)
  - buy [items](#item) from [merchant](#npc)

- sell [items](#item)
  - gather [items](#item)
  - kill [enemy](#npc)

- gather [items](#item)
  - explore deeper [maze](#place)

## players stats

### health

- `-` loose from [enemy](#npc) hit
- `-` loose by eating [poison](#item) (`?`)
- `+` regain a bit after [resting](#resting) (`?`)
- `+` regain a bit after eating [food](#item)
- `+` regain a lot after drinking health [potion](#item)

### stamina

- `-` loose tiny amount while walking
- `-` loose small amount while running
- `-` loose while hitting [enemy](#npc)
- `-` loose while hitting destructibles (`?`)
- `+` regain while [resting](#resting)
- `+` regain a lot after drinking stamina [potion](#item) (`?`)

### load-limit

max total weight of all [items](#item) carried by player

## items-slots

number of slots for [items](#item) carried by player

### money

- `-` buying [items](#item)
- `-` pay to rest in [tavern](#place) (`?`)
- `+` gather [money](#item)
- `+` sell [items](#item) to [merchant](#npc)
- `+` complete a [quest](#quest) for a [friendly player](#npc)

### experience

Experience points is a number greater than `0`. If experience raises above particular threshold limits, players level increases by `1`.

can be gained by:

- completing [quest](#quest)
- going one level deeper into [maze](#place)

can improve stats:

- max [health](#health)
- max [stamina](#stamina)
- max [load-limit](#load-limit)
- [items-slots](#items-slots)

### item

Item features:

- **value** - in [money](#money)
- **amount**
- **weight** - in kg

Types of items:

- **weapon** - can deal different amount of [damage](#health)
- **potion** - can [heal](#health)
- **poison** - can [hurt](#health)
- **coin** - visual representation of [money](#money), can be gathered on map
- **food** - can restore [health](#health)
- **gems** - can be found in [maze](#place) and sold to [merchant](#npc) to get [money](#money)

Items can be:

- found in [maze](#place)
- be dropped by killed [enemies](#npc)
- sold to [merchant](#npc)
- bought from [merchant](#npc)

## Entities

### chest

TODO

### NPC

NPCs can be of kind:

- **friendly** - neutral character, can give [quest](#quest) to the player
- **merchant** - can buy and sell [items](#item) from/to the player
- **enemy** - can fight and deal [damage](#health) to the player

## Other

### resting

player can rest by:

- spending time at [campfire](#place)
- sleeping in [house](#place)
- paying to sleep in [tavern](#place)

## place

- **maze** - multilevel, have [items](#item) and [enemies](#npc)
- **campfire** - only on surface
- **house** - only one
- **tavern** - place where you can pay [money](#money) to [rest](#resting)

### quest

it's a task from [friendly-player](#npc) to find (or buy), and give a rare [item](#item)
