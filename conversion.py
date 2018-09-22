"""
Conversion - Perform conversion
"""
from asteval import Interpreter
aeval = Interpreter()

def do_conversion1(in_val, expr):
    x = in_val
    # Evaluate Expression
    ret_val = eval(expr)
    return ret_val


def do_conversion(in_val, expr):

    try:
        aeval.symtable['x'] = in_val
        aeval(expr)
        value = aeval.symtable['Value']
    except (KeyError, SyntaxError):
        value = None
    return value

print(do_conversion(1000, "Value=/x*100/2.7"))