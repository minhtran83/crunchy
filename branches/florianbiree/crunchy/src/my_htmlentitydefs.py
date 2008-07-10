"""HTML character entity references.

This is a modification of the module in the standard library
so that Crunchy can work properly using Python 3.0"""

from htmlentitydefs import name2codepoint

# maps the Unicode codepoint to the HTML entity name
codepoint2name = {}

# maps the HTML entity name to the character
# (or a character reference if the character is outside the Latin-1 range)
entitydefs = {}

for (name, codepoint) in name2codepoint.items():
    codepoint2name[codepoint] = name
    entitydefs[name] = chr(codepoint)  # valid for Py3k

del name, codepoint