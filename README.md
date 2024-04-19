# Introduction

This is a template for a game using Pygame-ce that can run in both desktop and browser.

![screenshot](./screenshots/screenshot_gameplay.png)

This project is based on Matt Owen's tutorial:

[Pygame ARPG Tutorial Series](https://www.youtube.com/watch?v=a1NIscbsmKo&list=PLLdd2IQ6qKU7OAOpVdaK304D_BGSOw3iW&pp=iAQB)

Ninja sprite is from the same author:

[Monochrome ninja](https://mowen88.itch.io/monochrome-ninjaa)

Cursor by:

Precision icons created by [redempticon - Flaticon](https://www.flaticon.com/free-icons/precision)

## TOC

* [Features](#features)
* [Ideas for future](#ideas-for-future)
* [Installation](#installation)
* [Run](#run)
* [Deploying](#deploying)

## Features

* runs in web (itch.io and GitHub Pages) thanks to [pygbag](https://pygame-web.github.io/)
* implemented fine state machin
* usage of menus [pygame-menu](https://github.com/ppizarror/pygame-menu) (patched - gfxdraw not working in WEB)
* partial mouse support (in menus)
* [Tiled](https://www.mapeditor.org/) map loading [pytmx](https://github.com/bitcraft/pytmx)
* Map reloading, scrolling and zooming [pyscroll](https://github.com/bitcraft/pyscroll)
* map with layers (occlusion and collision)
* custom mouse cursor
* animated sprites
* separation keys from actions
* scene transitions
* automatic screenshots

## Ideas for future

* ~~list key bindings~~ ✅
* add enemies
* add fog of war and/or line of sight
* add particles system
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
