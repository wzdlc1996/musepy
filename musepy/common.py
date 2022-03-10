from __future__ import annotations
from copy import deepcopy
from gettext import find
from operator import ne
from typing import Tuple, List
from re import fullmatch, findall


relNoteVal = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11
}
revNoteVal = {x: y for y, x in relNoteVal.items()}

wholeNoteLen = 256
quartNoteLen = int(wholeNoteLen / 4)


octave_len = 12


_plList = ["C", "D", "E", "F", "G", "A", "B"]
_plIndx = {_plList[i]: i for i in range(len(_plList))}


def _note_next(nt: str):
    next = _plList[(_plIndx[nt] + 1) % len(_plList)]
    return next, (relNoteVal[next] - relNoteVal[nt]) % octave_len


def _note_last(nt: str):
    next = _plList[(_plIndx[nt] - 1) % len(_plList)]
    return next, ((relNoteVal[next] - relNoteVal[nt]) % octave_len - octave_len)


class note:
    def __init__(self, name: str = "C", duration: int = quartNoteLen, octave_group: int = 4):
        """
        A note has two basic property: name (C, D, E, F, G, A, B) and duration (whole, half, ...)

        It returns a quarter note middle C

        :param name: str, is the name of note, default "C"
        :param duration: int, is the duration (relative), default quarNoteLen is the duration of quater note
        :param octave_group: The shift by octave, default 4
        """
        self.nam = name
        self.dur = duration

        self.rel_val = relNoteVal[name]
        self.octave_group = octave_group

        self.val = self.rel_val + octave_group * octave_len
        self.semi_shift = 0

    def sharp(self, n_semi: int = 1) -> note:
        """
        Sharpen the note by n_semi. Note recommended for n_semi > 2

        :param n_semi:
        """
        if n_semi == 1:
            self._valAdd(1)
            if self.semi_shift == 1:
                nex, add = _note_next(self.nam)
                self.nam = nex
                self.semi_shift -= add - n_semi
            else:
                self.semi_shift += n_semi

        else:
            for _ in range(n_semi):
                self = self.sharp(1)

        return self

    def flat(self, n_semi: int = 1) -> note:
        if n_semi == 1:
            self._valAdd(-1)
            if self.semi_shift == -1:
                nex, add = _note_last(self.nam)
                self.nam = nex
                self.semi_shift -= add + n_semi
            else:
                self.semi_shift -= n_semi
        else:
            for _ in range(n_semi):
                self = self.flat(1)
        return self

    def normal(self) -> Tuple[note, bool]:
        """
        Try to normalize the note into natural tone
        """
        if self.semi_shift == 0:
            return self, True
        else:
            if self.semi_shift == 1:
                next_func = _note_next
            else:
                next_func = _note_last

            nex, add = next_func(self.nam)
            if add == self.semi_shift:
                self.nam = nex
                self.semi_shift = 0
                return self, True
            else:
                return self, False

    def _valAdd(self, n: int):
        self.val += n
        self.rel_val = (self.rel_val + n) % octave_len
        self.octave_group = int((self.val - self.rel_val) / octave_len)

    def play(self):
        """
        A basic player for a note

        :return: None
        """
        pass

    def __str__(self):
        base = f"{self.nam}_{calculateOctaveGroup(self.val - self.semi_shift)}"
        if self.semi_shift == 1:
            base += "#"
        elif self.semi_shift == -1:
            base += "b"
        else:
            base += " "
        return base


class score:
    def __init__(self):
        """
        A score is a list of notes
        """
        self.notes: List[note] = []
        self.time = 0

    def __len__(self):
        return len(self.notes)

    def __getitem__(self, k):
        return self.notes[k]

    def append(self, note: note):
        self.notes.append(note)
        self.time += note.dur

    def normalizable(self) -> Tuple[score, bool]:
        selfcopy = deepcopy(self)
        for i in range(octave_len):
            isnorm = True
            for x in self:
                _, yes = x.normal()
                isnorm = isnorm and yes
            
            if isnorm:
                return self, True

            for x in self:
                x.sharp()
        self = selfcopy
        return self, False

    def __str__(self):
        return ", ".join([str(x) for x in self.notes])

    def play(self):
        """
        A basic player for a score

        :return: None
        """
        for note in self.notes:
            note.play()


def parseNote(notes: str, dur: str) -> note:
    """
    parse the note symbol into note object

    :param note: (str), like 'C4#', 'C3', 'A2b'
    :param dur: (str), duration of the note, like '1/4', '1/16', '1'
    """
    if '/' in dur:
        denm = findall(r'1/(\d+)', dur)[0]
        dur = calculateNoteDuration(1/denm)
    else:
        dur = calculateNoteDuration(dur)

    name, group, shift = findall(r'([A-Z])(\d+)(.*)', notes)[0]
    nt = note(name, dur, group)

    if shift == "#":
        nt.sharp()
    elif shift == "b":
        nt.flat()
    
    return nt


def calculateNoteDuration(relToWhole: float) -> int:
    """
    calculate the duration with relToWhole as the relative lenth to whole note, return int

    :param relToWhole:
    """
    return int(relToWhole * wholeNoteLen)


def calculateOctaveGroup(val: int) -> int:
    return int(val / octave_len)