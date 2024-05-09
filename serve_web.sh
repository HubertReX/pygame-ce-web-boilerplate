# blocking (when using sounds)
# pygbag --ume_block 1 --template utils/default.tmpl --icon project/assets/icon.png --no_opt  project

# make it available from local network
# pygbag --ume_block 0 --template utils/default.tmpl --icon project/assets/icon.png --no_opt --bind 0.0.0.0 project

# non blocking - quicker (no sounds) --no_opt so the pixel art is not distorted with optimisation
pygbag --ume_block 0 --template utils/black.tmpl --icon project/assets/icon.png --no_opt project

# noctx.tmpl - in order for zengl to work
# pygbag --ume_block 0 --template noctx.tmpl --icon project/assets/icon.png --no_opt project
