from enum import Enum, auto, Flag

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
    exact   = 109 # F10
    debug   = 101 # F9
    close   = 100 # F8

class SaveStyle(Flag):
    '''
    Change the Tuner.save_style static if the current scheme does not work for you.
    '''
    all = auto()
    tagged = auto()
    newfile = auto()
    overwrite = auto()
