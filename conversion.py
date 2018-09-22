"""
Conversion - Perform conversion
"""
from asteval import Interpreter


def do_conversion(in_val, expr):
    aeval = Interpreter()
    try:
        aeval.symtable['x'] = in_val
        aeval(expr)
        value = aeval.symtable['Value']
    except (KeyError, SyntaxError):
        value = None
    return value
