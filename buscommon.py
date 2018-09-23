"""
ReadResponse - Return object for Channel Read
"""


class ReadResponse:
    def __init__(self):
        self.result = 0
        self.response = None
        self.exception = None

def getSignedNumber(number, bitLength):
    mask = (2 ** bitLength) - 1
    if number & (1 << (bitLength - 1)):
        return number | ~mask
    else:
        return number & mask
