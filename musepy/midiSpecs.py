from typing import Tuple, Dict


def _defmsg(status: int, type: str, value_names: tuple, length: int) -> dict:
    return {
        "status": status,
        "type": type,
        "value_names": value_names,
        "attr_names": set(value_names) | {"type", "time"},
        "length": length
    }



_channelled_msg = set(range(0x80, 0xf0))


_specs = [
    _defmsg(0x80, 'note_off', ('channel', 'note', 'velocity'), 3),
    _defmsg(0x90, 'note_on', ('channel', 'note', 'velocity'), 3),
    _defmsg(0xa0, 'polytouch', ('channel', 'note', 'value'), 3),
    _defmsg(0xb0, 'control_change', ('channel', 'control', 'value'), 3),
    _defmsg(0xc0, 'program_change', ('channel', 'program',), 2),
    _defmsg(0xd0, 'aftertouch', ('channel', 'value',), 2),
    _defmsg(0xe0, 'pitchwheel', ('channel', 'pitch',), 3),

    # System common messages.
    # 0xf4 and 0xf5 are undefined.
    _defmsg(0xf0, 'sysex', ('data',), float('inf')),
    _defmsg(0xf1, 'quarter_frame', ('frame_type', 'frame_value'), 2),
    _defmsg(0xf2, 'songpos', ('pos',), 3),
    _defmsg(0xf3, 'song_select', ('song',), 2),
    _defmsg(0xf6, 'tune_request', (), 1),

    # System real time messages.
    # 0xf9 and 0xfd are undefined.
    _defmsg(0xf8, 'clock', (), 1),
    _defmsg(0xfa, 'start', (), 1),
    _defmsg(0xfb, 'continue', (), 1),
    _defmsg(0xfc, 'stop', (), 1),
    _defmsg(0xfe, 'active_sensing', (), 1),
    _defmsg(0xff, 'reset', (), 1),
]


def initSpecByStatus() -> Dict[int, dict]:
    res = {}
    for spec in _specs:
        type = spec["type"]
        status = spec["status"]

        if status in _channelled_msg:
            for channel in range(16):
                res[status | channel] = spec
        else:
            res[status] = spec
    
    return res


SpecByStatus = initSpecByStatus()


NoteMap = {}