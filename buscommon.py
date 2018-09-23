"""
ReadResponse - Return object for Channel Read
"""


class ReadResponse:
    def __init__(self):
        self.result = 0
        self.response = None
        self.exception = None

def get_signed_number(number, bitLength):
    mask = (2 ** bitLength) - 1 # All Bits to 1 of bit length
    if number & (1 << (bitLength - 1)):
        # Sign Bit is Set
        return number | ~mask
    else:
        # Unsigned
        return number & mask
