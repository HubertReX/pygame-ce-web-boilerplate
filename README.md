# Introduction <!-- omit in toc -->

![Static Badge](https://img.shields.io/badge/content-Top_down_RPG_game-purple)

![GitHub last commit](https://img.shields.io/github/last-commit/hubertrex/pygame-ce-web-boilerplate)
[![License: MIT](https://img.shields.io/badge/License-MIT-green.svg)](https://opensource.org/licenses/MIT)

This is a template for a game using [Pygame-CE](https://pyga.me/) that can run both on **desktop** and int the **Web** browser

![screenshot](./screenshots/screenshot_20240919_223615.png)

You can play it online:

- [![GitHub Pages](https://img.shields.io/badge/github_pages-%23121011.svg?style=for-the-badge&logo=github&logoColor=white)](https://hubertrex.github.io/pygame-ce-web-boilerplate/NinjaAdventure)

- [![Itch.io](https://img.shields.io/badge/Itch-%23FF0B34.svg?style=for-the-badge&logo=Itch.io&logoColor=white)](https://hubertnafalski.itch.io/misadventures-of-malachi)

Build using:
![Pygame-ce](https://raw.githubusercontent.com/pygame/pygame/main/docs/reST/_static/pygame_logo.svg)

## Table of contents <!-- omit in toc -->

- [Features](#features)
- [Known bugs](#known-bugs)
- [Ideas for future](#ideas-for-future)
  - [Core features](#core-features)
  - [Tools and experiments](#tools-and-experiments)
- [Run](#run)
- [Deploying](#deploying)
  - [To itch.io](#to-itchio)
  - [To GitHub pages](#to-github-pages)
- [Contribution](#contribution)
- [Footnotes](#footnotes)

## Features

- runs both on **desktop** and in the **web browser** ([itch.io] and [GitHub Pages](https://pages.github.com/)) thanks to [pygbag](https://pygame-web.github.io/)
- implemented **finite state machine** (states: _Menu_, _Scene_, _Splash screen_ and NPCs animations)
- usage of menus `pygame-menu`[^1] (patched - `gfxdraw` was not working in **WEB**)
- **keyboard** (_arrows_, _WSAD_), **mouse** and **gamepad** support (player control and in menus)
- a custom **mouse** cursor loaded from **PNG** file
- **maps** can be created using `Tiled`[^2] - loaded using `pytmx`[^3]
- maps **live reloading**, **scrolling**, and **zooming** - using `pyscroll`[^4]
- configurable **transition** between maps (custom properties in `Tiled`[^2] maps)
- map with **layers** (walls, markers for spawning points and map entry/exits)
- obstacles on map can be destroyed
- procedurally generated **mazes** with randomly placed **decors**
- semi-transparent panels and text with background (alpha blending)
- custom UI interface with rich text formatting and animated emojis/icons (using the mix of [Thorpy] and [SFText])
- notifications system with UI
- preliminary screen for dialog with NPCs
- full-screen **color filtering** (alpha blending, e.g.: warm sunny light, dark blue at night) - turned off because of performance issues
- postprocessing OpenGL/WebGL **shaders** (`zengl`[^5]): _saturated_, _black&white_, _retro CRT monitor_ - turned off because of performance issues
- **day** and **night** cycle (implemented using shaders for better performance)
- functionality that allows **animate** any numerical value of the game like camera position, time of day allowing to create custom **cutscenes**
  - non-numerical values and any other game function can be scheduled for execution at given time (_chain_, _delay_)
  - complete workflow to create `json` with **cutscene** definition and automatic execution - separation from core game logic
  - different kinds of **transitions** between changed values (_linear_, _quad_, _sin_, _anticipation_, _overshoot_  with '_in_', '_out_', '_in&out_' and more)
  - **PoC** of exemplary game **intro** can be tested by pressing **F4**
  - based on `Bitcraft's`[^6] genius `animation`[^7] module
- particle system (_falling leaves_, _rain_, more to come)
- game manual and auto **pause** (if the game window is out of focus)
- pixel style **monospace font**
- **animated sprites** with static mockup shadows, and health bar - NPCs animations can be customized for new asset pack, by changing `SPRITE_SHEET_DEFINITION` in [settings.py](./project/settings.py#L165)
- **NPCs** states (_Idle_, _Bored_, _Walk_, _Run_, _Jump_, _Fly_, _Stunned_)
- **NPCs** **path finding** `A*`[^8] with different step cost depending on surface type (road speeds up, water slows down)
- **NPCs** follow individual lists of waypoints defined inside `Tiled`[^2] map or automatically moving towards set target (e.g. **Player**) or random walk
- simple inventory system
- global game **config** thanks to `Pydantic`[^9]
  - **config** is stored in `json` file and validated on load using `json schema` (**schema** autogenerated using **pydantic**)
  - [config.json](project/config_model/config.json) can be directly edited in **VS Code**, no dedicated editor yet, but thanks to **schema** it can be validated and autocompleted in the editor
  - **NPCs'** and **Player's** **traits** kept in **config** - easy to change, clean separation of logic and settings
  - in code, config is used as if it was **dataclass** - type hinting, properties names autocompletion (and not just a `dict[str, Any]`)
  - in future, **quests**, **dialogs** and other game definitions will go here
- separation of controller **key bindings** from **actions** - easy to customize in one file
- scene **transitions** (_fade in/out_, _circle shutter close/open_)
- build-in **screenshots** saving (in both **desktop** and **Web** modes)
- build-in gameplay **recordings** saving (*.mp4) thanks to `ffmpeg-python`[^10] - only in **desktop** mode
- automatic **build** and **deploy** from selected branch to `GitHub Pages`[^11] and `itch.io`[^12] using **GitHub action**

## Known bugs

- ✅ ~~screenshot of menu not working (showing only part of menu)~~ - `done`
- ✅ ~~some key events are lost (action is repeated even key is not pressed in menus)~~ - `done`
- ✅ ~~after transition between game **Scenes**, game state is not preserved~~ - `done`
- ✅ ~~low performance of **A**_function - delaying of **A**_ calls (no need to do it every frame)~~ - `done`
- ✅ ~~very low performance of **color filtering** (alpha blending) on **Windows** (heavy on **CPU**), although works well on **MacBook** - to be moved into **shader**~~ - `done`
- ✅ ~~**pydantic** not imported properly in **WEB** (problem with **pygbag**)~~ - as workaround **WEB** version uses static dataclasses - `done`
- **camera** randomly stops **following** the **Player**
- game not loading on **Firefox**
- Player shouldn't move after **colliding** with **map exit**
- ✅ ~~**leafs** particles are moving in screen coordinates, but should move according to game world coordinates~~ - `done`
- ✅ ~~gameplay recording flickering when night shader is applied~~ - switched to **ffmpeg-python** lib - `done`

## Ideas for future

### Core features

- ✅ ~~list key bindings~~ - `done`
- ✅ ~~create global **config** `json` with `schema`~~ -  `done`
- ✅ ~~add UI (**health bar**, player stats)~~ -  `done`
- ⏳ ~~add **particles** system~~ ✅ (~~leafs~~ ✅, ~~wind~~ ✅, _rain_ ✅, _footsteps_, _smoke_) - `WIP`
- ✅ ~~add **day/night** cycle~~ - `done`
- add **weather** conditions changing over time (e.g.: _rain_)
- add **fog of war** and/or **line of sight** - try [this](https://www.redblobgames.com/grids/circle-drawing/)
- ⏳ add **light** sources (~~_around NPCs_~~ ✅, _camp fire_, _torch_, _houses_ ✅) - `WIP`
- ✅ ~~add NPC, enemies with movements (add shadows)~~ - `done`
- ⏳ add more sophisticated NPC AI like `Behaviour Tree` or `GOAP` - `WIP`
- ✅ ~~add **animals**~~ - `done`
- add NPC and Player the ability to move on different **ground levels** (_hills_, _valley_, _bridge_ over lower level)
- add separate `walls` layer used for collision detection when **Player** is **airborn** (e.g.: _jump_, _flying_)
- add **movable** objects
- ✅ ~~add object **destruction**~~ - `done`
- ✅ ~~add item **drop/pickup** and **inventory** system~~ - `done`
- add **items spawning** on the map
- ✅ ~~separate **Scene** state from currently loaded **map**~~ - `done`
- 💡 add procedurally generated, natural looking **animations**/**movements** (using **Second Order Dynamics**) - `POC`
- ⏳ add **fighting** system - `WIP`
- ✅ ~~add **gamepad** controller mapping~~ - `done` - not so easy on **SteamDeck**
- add option to play using **touchscreen** - use [this](https://forums.raspberrypi.com/viewtopic.php?t=354101) - first check performance on **mobile** devices
- ⏳ add **dialog** system - `WIP`
- add **quest** system
- add **merchants**
- ✅ ~~add **cutscenes**~~ - `done`
- add game **save/load** system
- add game **highscore** table
- add game **achievements**
- add **music** and **sfx**
- ⏳ add better **menus**, **UI/HUD** - `WIP`
- ✅ ~~add **dungeons** (generated procedurally)~~ - `done`
- ✅ ~~add **path finding** algorithm~~ - `done`
- make more **maps**
- ⏳ optimize performance (e.g. using [Austin], [Austin-TUI], [Austin VS Code Plugin]) - `WIP`

### Tools and experiments

- add **animated gif** with gameplay for promotion (use ezGif or [DaVinci Resolve] or simply **ffmpeg** from CLI)
- test **pixel editors**:
  - [Pyxel Edit] - `$9`
  - [Piskel] - `free`, online
  - [Pixilart] - `free`, online
  - [Photopea] - `free`, online
  - ✅ [aseprite] - `$20` or build own for [MacOs] or [Win] `free` copy = `done`
    - [PixelLab] - `free` tier, plugin for Aseprite to generate pixel art, rendered in cloud
    - [RetroDiffusion] - `$60` plugins for Aseprite to generate pixel art using Stable Diffusion
  - [PixelVive] - `free` online asset generator
  - [OpenPoseAI] - use **OpenPoseAI** with SD to get best pose - see [video]
- create **workflow** to quickly create **new assets** (_characters_, _animations_, _tiles_):
  - use **Stable Diffusion**
  - find pixelation filter and apply to images found on net (eg.: for different types of trees)
- test how hard it is to switch to new **assets pack** - at current game state is still doable
  - customize sprite animation config `SPRITE_SHEET_DEFINITION` in [settings.py] to new layout, add missing options (mirror, copy default)
  - create new copy of maze template [MazeTileset_clean.tmx] maze map using new tile sheets
  - change tiles IDs in [maze_utils.py]
- ⏳ add [game page] on itch.io and customize `CSS` (see [CSS video]) - `WIP`
- ✅ ~~add **GitHub action** to automatically deploy to [itch.io] - use [itch-io-publish] and [Publish video]~~ - `done`
- 💡 smooth and natural looking animation/movement (e.g. **anticipation** and **overshoot**)
  - with the use of `Second Order Dynamics` (**SOD**) - see [game.py] - `POC`
  - with the use of `AnimationTransition` - see [characters.py] - `POC`
- ✅ ~~live **recording** of animation generated by **OpenGL** directly to **mp4** file (see side script [ffmpeg_recorder.py]) using: **zengl**, **pil**, **numpy**, **ffmpeg**~~ - `done`
- **build** and **distribute** standalone **executables** for 3 major platforms using [NW.js] - see [Steam video] - might be useful when releasing on **Steam**
- try out the `Level Designer toolkit` [LDtk] as supplement or substitution of `Tiled`[^2]
- ✅ try out the [Thorpy] for **UI/HUD** - as full replacement of current **menus** or at least the **heterogeneous texts** for mixed text and formatting (see [heterogeneous_texts]) - can be useful in **dialogs** - `done`
- try out the [Pixel Composer] for `$10` - create and animate sprites, including IK based character animation 🤯
- try [Smack Studio] for sprite animation using skeletons
- ⏳ test other ways of porting **Python** to the **Web** (see [pygame for web]) - `WIP`
- add ability to upload files to the **Web** browser (see [test_upload.py]) - useful for uploading game **saves** (downloading already works - see [save_screenshot])
- use [MoviePy] and **cutscene** functionality to create game **trailer**
- use [ezGif] - converting video to gif, cutting video
- try [Mode7] - for fun?

[Pyxel Edit]: https://pyxeledit.com/get.php
[DaVinci Resolve]: https://www.blackmagicdesign.com/products/davinciresolve/
[Piskel]: https://www.piskelapp.com/
[Pixilart]: https://www.pixilart.com/
[Photopea]: https://www.photopea.com/
[aseprite]: https://www.aseprite.org/
[MacOs]: https://github.com/Chasnah7/aseprite-build-script-mac
[Win]: https://github.com/Intrivus/Aseductor
[PixelLab]: https://www.pixellab.ai/
[RetroDiffusion]: https://astropulse.itch.io/retrodiffusion
[PixelVive]: https://beta.pixelvibe.com/
[OpenPoseAI]: https://openposeai.com/
[video]: https://www.youtube.com/watch?v=849xBkgpF3E&list=PLEAS_zp3JXpuYxEsXiazPGSMa260ahuYP&ab_channel=Mickmumpitz
[game page]: https://hubertnafalski.itch.io/top-down-rpg
[settings.py]: ./project/settings.py#L165
[MazeTileset_clean.tmx]: ./project/assets/MazeTileset/MazeTileset_clean.tmx
[maze_utils.py]: ./project/maze_generator/maze_utils.py
[CSS video]: https://www.youtube.com/watch?v=VM3cnMU4A-M&list=WL&index=11&pp=gAQBiAQB
[itch.io]: https://itch.io
[itch-io-publish]: https://github.com/marketplace/actions/itch-io-publish
[Publish video]: https://www.youtube.com/watch?v=TXROTe0ASeM
[game.py]: ./project/game.py#L69
[characters.py]: ./project/characters.py#L677
[NW.js]: https://github.com/nwjs/nw.js
[Steam video]: https://dev.to/jacklehamster/releasing-a-web-game-onto-steam-47cd
[LDtk]: https://ldtk.io/
[Thorpy]: https://www.thorpy.org/doc.html
[SFText]: https://https//github.com/LukeMS/sftext/
[heterogeneous_texts]: https://www.thorpy.org/examples/heterogeneous_texts.html
[Pixel Composer]: https://makham.itch.io/pixel-composer
[Smack Studio]: https://smackstudio.com/
[pygame for web]: https://github.com/pygame-community/pygame-ce/issues/540
[test_upload.py]: https://github.com/pygame-web/showroom/blob/main/src/test_upload.py
[save_screenshot]: ./project/game.py#L371
[MoviePy]: https://github.com/Zulko/moviepy
[ezGif]: https://ezgif.com/
[Mode7]: https://github.com/bitcraft/mode7
[ffmpeg_recorder.py]: utils/ffmpeg_recorder.py
[Austin]: https://github.com/P403n1x87/austin
[Austin-TUI]: https://github.com/P403n1x87/austin-tui
[Austin VS Code Plugin]: https://marketplace.visualstudio.com/items?itemName=p403n1x87.austin-vscode

```bash
# create venv
python3 -m venv .venv
# activate it
# on Linux/MacOS
source .venv/bin/activate
# on Windows
.venv\Scripts\activate

# install packages
pip install -r requirements.txt

# install packages for development
pip install -r requirements-dev.txt
```

## Run

Desktop mode:

```bash
./run.sh
```

***

Browser mode:

```bash
./serve_web.sh
```

open [http://localhost:8000/](http://localhost:8000/) in browser

use [http://localhost:8000#debug](http://localhost:8000/debug) to show Python repl terminal in browser - useful for troubleshooting

## Deploying

### To [itch.io]

full instruction [here](https://pygame-web.github.io/wiki/pygbag/itch.io/)

in short:

```bash
./build_itchio.sh
```

upload `'build/web.zip'` to [itch.io] or any other hosting service.

***

### To GitHub pages

Manually run [pygbag_build](https://github.com/HubertReX/pygame-ce-web-boilerplate/actions/workflows/pygbag.yml) GitHub action on selected branch.

Full instruction how to setup is [here](https://pygame-web.github.io/wiki/pygbag/github.io/).

## Contribution

This project is based on Matt Owen's tutorial:

[Pygame ARPG Tutorial Series](https://www.youtube.com/watch?v=a1NIscbsmKo&list=PLLdd2IQ6qKU7OAOpVdaK304D_BGSOw3iW&pp=iAQB)

Ninja Sprite is from the same author:

[Monochrome ninja](https://mowen88.itch.io/monochrome-ninja)

Cursor by:

Precision icons created by [redempticon - Flaticon](https://www.flaticon.com/free-icons/precision)

***

[back to top](#introduction-)

## Footnotes

[^1]: [pygame_menu](<https://github.com/ppizarror/pygame-menu>)
[^2]: [Tiled](<https://www.mapeditor.org/>)
[^3]: [pytmx](https://github.com/bitcraft/pytmx)
[^4]: [pyscroll](https://github.com/bitcraft/pyscroll)
[^5]: [zengl](https://github.com/szabolcsdombi/zengl)
[^6]: [Bitcraft](https://github.com/bitcraft)
[^7]: [animation](https://github.com/bitcraft/animation)
[^8]: [A*](https://panda-man.medium.com/a-pathfinding-algorithm-efficiently-navigating-the-maze-of-possibilities-8bb16f9cecbd)
[^9]: [Pydantic](https://github.com/pydantic/pydantic)
[^10]: [ffmpeg-python](https://github.com/kkroening/ffmpeg-python)
[^11]: [GitHub-Pages](.github/workflows/pygbag.yml)
[^12]: [itch_io.yml](.github/workflows/itch_io.yml)
