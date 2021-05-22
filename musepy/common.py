relNoteVal = {
    "C": 0,
    "D": 2,
    "E": 4,
    "F": 5,
    "G": 7,
    "A": 9,
    "B": 11
}

class note:
    def __init__(self, name="C", duration="2", pitch_shift=0):
        """
        A note has two basic property: name (C, D, E, F, G, A, B) and duration (whole, half, ...)

        :param name:
        :param duration:
        """
        self.nam = name
        self.dur = duration
        self.val = note.relNoteVal[self.nam] + pitch_shift * 12

    def play(self):
        """
        A basic player for a note

        :return: None
        """
        pass


class score:
    def __init__(self):
        """
        A score is a list of notes
        """
        self.notes = []
        self.time = 0

    def __len__(self):
        return len(self.notes)

    def play(self):
        """
        A basic player for a score

        :return: None
        """
        for note in self.notes:
            note.play()

