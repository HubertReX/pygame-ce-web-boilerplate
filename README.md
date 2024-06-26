# Introduction

This is a template for a game using [Pygame-CE](https://pyga.me/) that can run on both desktop and browser.

![screenshot](./screenshots/screenshot_gameplay.png)

You can play an online demo [here](https://hubertrex.github.io/pygame-ce-web-boilerplate/NinjaAdventure).

## TOC

* [Features](#features)
* [Ideas for future](#ideas-for-future)
* [Installation](#installation)
* [Run](#run)
* [Deploying](#deploying)
* [Contribution](#contribution)

## Features

* runs on the web browser (itch.io and GitHub Pages) thanks to [pygbag](https://pygame-web.github.io/)
* implemented finite state machine
* usage of menus [pygame-menu](https://github.com/ppizarror/pygame-menu) (patched - gfxdraw not working in WEB)
* mouse support (player control and in menus)
* [Tiled](https://www.mapeditor.org/) map loading [pytmx](https://github.com/bitcraft/pytmx)
* map live reloading, scrolling, and zooming [pyscroll](https://github.com/bitcraft/pyscroll)
* configurable transition between maps (custom properties in Tiled maps)
* map with layers (walls, markers for start and exits)
* procedurally generated mazes with randomly places decors
* semi-transparent panels and text with background (alpha blending)
* full-screen color filter (alpha blending, e.g.: warm sunny light, dark blue at night)
* particle system (falling leaves, more to come)
* postprocessing OpenGL/WebGL shaders ([zengl](https://github.com/szabolcsdombi/zengl)): saturated, black&white, retro CRT monitor
* game auto pause (if the game window is out of focus)
* pixel style monospace font
* a custom mouse cursor
* animated sprites with shadows and different
* NPCs states (Idle, Bored, Walk, Run, Jump, Fly)
* NPCs path finding with different step cost depending on surface type (road speeds up, water slows down)
* NPCs follow individual lists of waypoints or moving target (e.g. Player)
* separation of key bindings from actions
* scene transitions (fade in/out, round shutter)
* automatic screenshots saving


## Ideas for future

Features:

* ~~list key bindings~~ - ✅ done
* create global config json with schema - ⏳ WIP
* add UI (~~health bar~~ ✅, stats)
* ~~add particles system~~ ✅ (~~leafs~~ ✅, ~~wind~~ ✅, rain, footsteps, smoke) - ⏳ WIP
* add day/night cycle and weather (rain)
* add fog of war and/or line of sight
* add light sources (camp fire, torch, houses)
* ~~add NPC, enemies and animals with movements (add shadows)~~ ✅
* add movable objects
* add object destruction
* add item drop/pickup and inventory system
* add procedurally generated animations/movements (using Second Order Dynamics) - ⏳ WIP
* add fighting system - ⏳ WIP
* add dialog system
* add merchants
* add cutscenes
* add game save/load system
* add game highscore table
* add game achievements
* add music and sfx
* add better menus
* ~~add dungeons (generated procedurally)~~ - ✅ done
* ~~add path finding algorithm~~ - ✅ done
* make more maps

Bugs:

* ~~screenshot of menu not working (showing only part of menu)~~ ✅
* ~~some key events are lost (action is repeated even key is not pressed in menus)~~ ✅
* continuing game after exiting menu causes loosing player's position on small map (works on grassland though)
* should new map be a new game state?

## Installation

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
```

## Run

Desktop mode:

```bash
cd project
python main.py
```

***

Browser mode:

```bash
# from top level folder
pygbag --ume_block 0 project
```

open [http://localhost:8000/](http://localhost:8000/) in browser

use [http://localhost:8000#debug](http://localhost:8000/debug) to show Python repl terminal in browser - useful for troubleshooting

## Deploying

### To [itch.io](https://itch.io/)

full instruction [here](https://pygame-web.github.io/wiki/pygbag/itch.io/)

in short:

```bash
pygbag --ume_block 0 --archive project
```

upload `'build/web.zip'` to [itch.io](https://itch.io/) or any other hosted site.

***

### To GitHub pages

full instruction [here](https://pygame-web.github.io/wiki/pygbag/github.io/)


## Contribution

This project is based on Matt Owen's tutorial:

[Pygame ARPG Tutorial Series](https://www.youtube.com/watch?v=a1NIscbsmKo&list=PLLdd2IQ6qKU7OAOpVdaK304D_BGSOw3iW&pp=iAQB)

Ninja Sprite is from the same author:

[Monochrome ninja](https://mowen88.itch.io/monochrome-ninja)

Cursor by:

Precision icons created by [redempticon - Flaticon](https://www.flaticon.com/free-icons/precision)
