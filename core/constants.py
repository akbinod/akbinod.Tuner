from enum import Enum, auto, Flag
import cv2

# statics

# HIGHLIGHT_COLOR = (173,255,47)
HIGHLIGHT_THICKNESS_LIGHT = 1
HIGHLIGHT_THICKNESS_HEAVY = 2
PUT_TEXT_FONT = cv2.FONT_HERSHEY_PLAIN
PUT_TEXT_SMALL = 0.7
PUT_TEXT_NORMAL = 1.0
PUT_TEXT_HEAVY = 2.0
# HIGHLIGHT_BLUE = (255,153,51)
# HIGHLIGHT_GREEN = (153,255,51)
# HIGHLIGHT_RED = (51,51,255)
class Highlight(Enum):
    highlight = (173,255,47)
    blue = (255,153,51)
    green = (153,255,51)
    red = (51,51,255)
    white = (255,255,255)
    gray = (153,153,153)
    black = (0,0,0)
class Tags(Enum):
    '''
    These are keycodes (macOS). The following are available for users to map.
    Just change this Enum - the rest is automatic.
    F1 - 122,   in use by Tuner, cannot be remapped
    F2          in use by Tuner, cannot be remapped
    F3          in use by Tuner, cannot be remapped
    F4 - 118    available
    F5 - 96     available
    F7 - 98     available
    F6 -        not available - trapped by cv
    F8 - 100    in use by Tuner, but can be remapped
    F9 - 101    in use by Tuner, but can be remapped
    F10 - 109   in use by Tuner, but can be remapped
    '''
    avoid   = 109 # F10
    exact   = 101 # F9
    close   = 100 # F8

class SaveStyle(Flag):
    '''
    Change the TunerConfig.save_style static if the current scheme does not work for you.
    '''
    all = auto()
    tagged = auto()
    newfile = auto()
    overwrite = auto()

class FrameGenStyle(Flag):
    yield_1 = auto()
    yield_2 = auto()
    yield_all_new = auto()
    yield_last_one_sticks = auto()
    convert_grayscale = auto()
    convert_normalize = auto()
