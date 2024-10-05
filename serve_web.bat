@ECHO OFF
call .venv\Scripts\activate.bat

REM blocking (when using sounds)
REM pygbag --ume_block 1 --template utils/default.tmpl --icon project/assets/icon.png --no_opt  project

REM make it available from local network
REM pygbag --ume_block 0 --template utils/default.tmpl --icon project/assets/icon.png --no_opt --bind 0.0.0.0 project

REM non blocking - quicker (no sounds) --no_opt so the pixel art is not distorted with optimisation
python -m pygbag --ume_block 0 --template utils/black.tmpl --icon project/assets/icon.png --no_opt project

REM noctx.tmpl - in order for zengl to work
REM pygbag --ume_block 0 --template noctx.tmpl --icon project/assets/icon.png --no_opt project
