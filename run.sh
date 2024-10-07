# https://stackoverflow.com/questions/18733965/annoying-message-when-opening-windows-from-python-on-os-x-10-8
# ApplePersistenceIgnoreState: Existing state will not be touched. New state will be written...
# defaults write org.python.python ApplePersistenceIgnoreState NO
export PYGAME_HIDE_SUPPORT_PROMPT=1
cd project
# rich -u --rule-char "#"
python3 ./main.py
