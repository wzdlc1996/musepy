"""
Read MIDI Files

Refererence:

mido.midifiles:
    https://github.com/mido/mido/blob/stable/mido/midifiles/midifiles.py

https://www.jianshu.com/p/31d02765e1ec
https://www.cs.cmu.edu/~music/cmsip/readings/MIDI%20tutorial%20for%20programmers.html
http://midi.teragonaudio.com/tech/midispec/run.htm


TODO: Complete the code.
"""


from multiprocessing.sharedctypes import Value
from struct import unpack
from typing import BinaryIO, Tuple, List, Any

from musepy.midiSpecs import SpecByStatus


_maxMsgLen = 1000


def ReadMIDIFile(filename: str) -> tuple:
    """
    Simple interface to read a midi file
    """
    with open(filename, "rb") as f:
        tp, num_tracks, ticks_per_beat = readHeader(f)
        trk = []
        for i in range(num_tracks):
            trk.append(readTrack(f))
    
    return (tp, num_tracks, ticks_per_beat), trk



def readChunckHeader(file: BinaryIO) -> Tuple[bytes, int]:
    """
    Read the 8-byte size header from the file

    :param file: (BinaryIO), open a file with mode 'rb'
    :return a: (bytes)
    :return b: (int)
    """
    header = file.read(8)  # Read to the end if there is less than 8 bytes
    if len(header) < 8:
        raise EOFError

    """
    Return the header as a tuple of (bytes, int)
    The format '>4sL' means big-endian, 4-len char[], and an unsigned long. 
        's' format is different with others, the count is interpreted as the length of the bytes
    """
    a, b = unpack('>4sL', header)  # return the header as tuple of (bytes, int), 
    return a, b


def readHeader(file: BinaryIO) -> Tuple[int, int, int]:
    """
    Read the header (should be 14-byte) of a MIDI file
    The header of a MIDI file is
        -  name: 4-byte, should be 'MThd'
        -  size: 4-byte, is the size of header, fixed as `00 00 00 06`
        -  data: 6-byte, is made up with three integers
            1.  2-byte, denotes the type of MIDI file:
                -  `00 00` means there is only one track
                -  `00 01` means there are multiple syncronized tracks
                -  `00 10` means there are multiple asyncronized tracks
            2.  2-byte, is the number of tracks
            3.  2-byte, is the time unit of the MIDI file. 
                -  The highest bit denotes the method to use
                   -  0: means by ticks
                   -  1: means by SMPET format
                -  The rest denotes the time unit. 
                   For ticks format, it is the number of ticks of the duration of quarter note

    :param file: (BinaryIO), open a file with mode 'rb'
    :return: (int) is the type of MIDI file
    :return: (int) is the number of tracks
    :return: (int) is the number of ticks per quarter note
    """
    name, size = readChunckHeader(file)

    if name != b'MThd':
        raise IOError("MThd not found. Probably not a MIDI file")
    
    data = file.read(size)
    if len(data) < 6:
        raise EOFError
    
    """
    Return the information as a tupe of (int, int, int)
    The format '>3h' means big-endian, 3 repeats of short
    """
    return unpack('>3h', data[:6])
    

def readTrack(file: BinaryIO) -> List[tuple]:
    """
    Read the track of a MIDI file
        A track is one 8-byte header and sequence of event defined by MIDI
        In the header:
            -  name: 4-byte, should be 'MTrk'
            -  size: 4-byte, should be an integer
        In each event, there are two entries:
            -  delta time: by dynamic byte, is the number of ticks
            -  MIDI message: is made up with a 1-byte status and data of multiple bytes.

    :param file: (BinaryIO), open a file with mode 'rb'
    """
    track = []
    name, size = readChunckHeader(file)

    if name != b'MTrk':
        raise IOError("MTrk not found. Probably not a MIDI file")
    
    start = file.tell()  # store the current position of reader pointer

    while True:
        if file.tell() - start == size:
            break  # break if all events read

        delta = readDynamicBytes(file)  # read in a delta time

        status = readByte(file)  # read in the status of MIDI message
        last_s = None  # store the last status

        """
        It is strange that most tutorials say status should has highest bit `1`
        This is a check for `running status` referred in mido.midifile
        """
        if status < 0x80:
            if last_s is None:
                raise IOError("running status without last status")
            
            peek_data = [status]
            status = last_s
        else:
            if status != 0xff:  # meta-message
                last_s = status
            peek_data = []
        
        if status == 0xff:
            msg = readMetaMessage(file, delta)
        elif status in [0xf0, 0xf7]:
            msg = readSysex(file, delta)
        else:
            msg = readMessage(file, status, peek_data, delta)
        
        
        msg = messageWrap(msg)
        if msg is not None:
            track.append(msg)

    return track


def messageWrap(msg: Any) -> Any:
    """
    Only ouput the note_on and note_off message. 

    :return: (bool), Ture for note_on, False for note_off
    :return: (int), time
    :return: (int), note number
    """
    if msg is None:
        return None
    status, databytes, delta = msg
    if SpecByStatus[status]["type"] == "note_on":
        note_on = True
    elif SpecByStatus[status]["type"] == "note_off":
        note_on = False
    else:
        return None
    
    note = databytes[0]
    return note_on, note, delta



def readMetaMessage(file: BinaryIO, delta: int, *args) -> Any:
    meta_type = readByte(file)
    length = readDynamicBytes(file)
    data = readBytes(file, length)
    return None


def readSysex(file, *args):
    length = readDynamicBytes(file)
    _ = readBytes(file, length)
    return None


def readMessage(file: BinaryIO, status: int, peek_data: List[int], delta: int) -> Tuple[int, list, int]:
    try:
        spec = SpecByStatus[status]
    except LookupError:
        raise IOError("undefined status 0x{:02x}".format(status))

    # Subtract 1 for status byte.
    size = spec["length"] - 1 - len(peek_data)
    databytes = peek_data + readBytes(file, size)
    for data in databytes:
        if data > 127:
            raise IOError("data byte must be in range 0..127")
    
    return status, databytes, delta


def readDynamicBytes(file: BinaryIO) -> int:
    """
    Read a integer represented by dynamic bytes from file

    The algorithm is (big-endian):
        1.  read a byte
        2.  If the highest is 0, it should end.
        3.  Else, the number should left-shift 7 bits and waiting for lower bits (big-endian)
        4.  `byte & 0x7f` is `byte & 0111,1111`, omit the highest position and add as lower bits.
        5.  goto 1 repeat
    
    For example, represent `0000,0001,1111,0100` as dynamic bytes with big-endian:
        The number should be splitted as `11` and `1110100`
        1.  lower bits: `0111,0100`, the highest bit is `0` denoting it is the end
        2.  higher bits: `1000,0011`, the highest bit is `1` denoting it is the end
        Follow this algorithm
            1.  read in one byte: `1000,0011` 
            2.  make the left-shift and mask: `0000,0000 | 0000,0011` -> `0000,0011`
            3.  read in one byte: `0111,0100`
            4.  make the left-shift and mask: `1,100,0000 | 0,0111,0100` -> `1,1111,0100`
            5.  check the current byte `0100,0100` is less than `0x7f == 0111,1111`
            6.  return the number `1,1111,0100`
    
    :param file: (BinaryIO), open a file with mode 'rb'  
    :return: (int)
    """
    delta = 0
    while True:
        byte = readByte(file)
        delta = (delta << 7) | (byte & 0x7f)
        if byte < 0x80:
            return delta


def readBytes(file: BinaryIO, size: int) -> List[int]:
    if size > _maxMsgLen:
        raise IOError(f"Message length {size} exceeds maximum length {_maxMsgLen}")
    return [readByte(file) for _ in range(size)]
    


def readByte(file: BinaryIO) -> int:
    byte = file.read(1)
    if byte == b'':
        raise EOFError
    return ord(byte)
