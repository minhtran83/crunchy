'''
security.py

Javascript code is normally executed in a web-browser "sandbox", preventing
access to the user's computer.  Crunchy creates a link between the browser and
a Python backend, enabling the user to execute code on his computer (with full
access to the resources), thereby bypassing the security sandbox of the browser.

This creates a potential security hole.

The purpose of this module is to prevents the automatic execution of Python code
caused by insertion of malicious javascript code within a web page.
'''

import os
import random
from elementtree import ElementTree
import preferences
from crunchyrequest import CrunchyRequestHandler as request
import crunchypages as pages
import urllib
import widget_javascript

# Better safe than sorry: we do not allow the following html tags for the
# following reasons:
# script: because we want to prevent unauthorised code execution
# button, form, input: we only want Crunchy itself to create those
# *frame*: we don't want hidden frames that could be playing tricks with the
#          user (very remote possibility, but still.)
tag_black_list = ["script", 'button', 'form', 'frame', 'frameset', 'input',
                    'iframe']

# The following is not used currently
#attribute_black_list = ["text/javascript"]

# Almost all html tags can make use of these in a sensible way:
common_allowed = ['class', 'dir', 'id', 'lang', 'style', 'title']

# Rather than trying to find which attributes might be problematic (black list),
# we create a database of allowed (safe) attributes which we know will not cause
# any trouble.  This list can always be expanded if required.
# Note that a black list would have included onblur, onload, oninit, etc.,
# with possibly some new attributes introduced by a given browser which we
# would not have foreseen.
specific_allowed = {
    'a': ['charset', 'type', 'name', 'href', 'hreflang', 'rel'],
    'abbr': [],
    'acronym': [],
    'address': [],
    # applet deprecated
    'area': ['name', 'shape', 'coords', 'href', 'alt', 'nohref'],
    'b': [],
    'base': [],
    'bdo': [],
    'big': [],
    'blockquote': ['cite'],
    'body': ['bgcolor'],
    'br' : ['clear'],
    # button not allowed
    'canvas': [],
    'caption': ['align'],
    'center': [],
    'cite': [],
    'code': [],
    'col': ['span', 'width'],
    'colgroup': ['span', 'width'],
    'dd': [],
    'del': ['cite', 'datetime'],
    'dfn': [],
    # dir is deprecated
    'div': ['align'],
    'dl': [],
    'dt': [],
    'em': [],
    'fieldset': ['align'],
    'font': ['size', 'color', 'face'], # deprecated... but still often used!
    # form not allowed; if required, will be inserted by Crunchy itself
    # frame not allowed (don't want stuff possibly hidden)
    # frameset not allowed
    'h1': ['align'],
    'h2': ['align'],
    'h3': ['align'],
    'h4': ['align'],
    'h5': ['align'],
    'h6': ['align'],
    'head': [],
    'hr': ['align', 'noshade', 'size', 'width'], # these attributes are deprecated!
    'html': [],
    'i': [],
    # iframe not allowed
    'img': ['src', 'alt', 'longdesc', 'name', 'height', 'width', 'usemap', 'ismap'],
    # input not allowed
    'ins': ['cite', 'datetime'],
    # isindex deprecated
    'kbd': [],
    'label': ['for'],
    'legend': ['align'],
    'li': ['value'], # value is deprecated... but replaced by what?
    'link': ['charset', 'href', 'hreflang', 'type', 'rel', 'rev', 'media'],
    'map': ['shape', 'coords', 'href', 'nohref', 'alt'],
    # menu deprecated
    'meta': ['name', 'content', 'http-equiv'], # could be stripped safely
    # noframes should not be needed
    'noscript' : [],   # should not be needed
    # object not allowed - preventing unwanted interactions
    'ol': ['start'],  # start is deprecated ... but replaced by ??
    #'optgroup': ['name', 'size', 'multiple'],  # Keep???
    #'option': ['name', 'size', 'multiple'],    # Keep???
    'p': [],
    # param not needed: only for object
    'pre': [],
    'q': ['cite'],
    # s deprecated
    'samp': [],
    # script not allowed!
    # 'select': ['name', 'size', 'multiple'], # Keep???
    'small': [],
    'span': ['align'],
    'strike': [], # deprecated
    'strong': [],
    'style': ['type', 'media'],
    'sub': [],
    'sup': [],
    'table': ['summary', 'align', 'width', 'bgcolor', 'frame', 'rules', 
                'border', 'cellspacing', 'cellpadding'],
    'tbody': ['align', 'char', 'charoff', 'valign'],
    'td': ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'bgcolor',
            'align', 'char', 'charoff', 'valign'],
    # textarea not needed; only included by Crunchy
    'tfoot': ['align', 'char', 'charoff', 'valign'],
    'th': ['abbr', 'axis', 'headers', 'scope', 'rowspan', 'colspan', 'bgcolor',
            'align', 'char', 'charoff', 'valign'],
    'thead': ['align', 'char', 'charoff', 'valign'],
    'u': [], # deprecated ... but still used
    'ul': [],
    'var': []
    }
for key in specific_allowed:
    for item in common_allowed:
        specific_allowed[key].append(item)

commands = {}
js_name = ''

class SecureSession(object):
    
    def __init__(self, root_dir, port):
        global js_name
        self.root_dir = root_dir
        prefs = preferences.UserPreferences()
        self.session_id = str(port)+str(int(random.random()*1000000000))
        self.map_commands()
        # create a unique javascript file to be used within a session
        widget_javascript.set_sessionid(self.session_id)
        
    def map_commands(self):
        commands['/'] = '/'  # safe; no need to add session_id
        request.pagemap[commands['/']] = pages.get_index
        #
        commands['/exit'] = '/exit' # safe; no need to add session_id
        request.pagemap[commands['/exit']] = pages.get_exit
        #
        commands['/dir'] = '/dir' + self.session_id
        request.pagemap[commands['/dir']] = pages.get_dir
        #
        commands['/doc'] = '/doc' + self.session_id
        request.pagemap[commands['/doc']] = pages.get_doc
        #
        commands['/load_local'] = '/load_local' + self.session_id
        request.pagemap[commands['/load_local']] = pages.get_local_page
        #
        commands['/push'] = '/push' + self.session_id
        request.pagemap[commands['/push']] = pages.get_push
        #
        commands['/load_external'] = '/load_external' + self.session_id
        request.pagemap[commands['/load_external']] = pages.get_external_page
        #
        commands['/get_user_js'] = '/get_user_js' + self.session_id
        request.pagemap[commands['/get_user_js']] = pages.get_user_js
        #
        commands['/select_language'] = '/select_language' + self.session_id
        request.pagemap[commands['/select_language']] = pages.get_language
        #
        commands['/doctest'] = '/doctest' + self.session_id
        commands['/execute'] = '/execute' + self.session_id
        commands['/rawio'] = '/rawio' + self.session_id
        commands['/canvas_exec'] = '/canvas_exec' + self.session_id
        commands['/spawn'] = '/spawn' + self.session_id
        commands['/spawn_console'] = '/spawn_console' + self.session_id
        #
        request.pagemap['/js_interp'] = pages.get_interpreter_js
        request.pagemap['/js_common'] = pages.get_common_js
        request.pagemap['/js_editor'] = pages.get_editor_js
        #request.pagemap['/js_output'] = pages.get_output_js
        return   

    def close(self):
        #remove the javascript file created for that session
        os.remove(os.path.join(self.root_dir, js_name))
        
def remove_unwanted(tree):
    '''Removes unwanted tags and or attributes from a "tree" created by
    ElementTree from an html page.'''
    for tag in tag_black_list:
        for element in tree.getiterator(tag):
            element.clear() # removes the text
            element.tag = None  # set up so that cleanup will remove it.
    for tag in specific_allowed:
        for element in tree.getiterator(tag):
            for attr in element.attrib.items():
                if attr[0].lower() not in specific_allowed[tag]:
                    del element.attrib[attr[0]]
                elif attr[0].lower() == 'href':
                    if urllib.unquote_plus(attr[1]).startswith("javascript:"):  
                        del element.attrib[attr[0]]   
    __cleanup(tree.getroot(), lambda e: e.tag)
    return tree

def __cleanup(elem, filter):
    ''' See http://effbot.org/zone/element-bits-and-pieces.htm'''
    out = []
    for e in elem:
        __cleanup(e, filter)
        if not filter(e):
            if e.text:
                if out:
                    out[-1].tail += e.text
                else:
                    elem.text += e.text
            out.extend(e)
            if e.tail:
                if out:
                    out[-1].tail += e.tail
                else:
                    elem.text += e.tail
        else:
            out.append(e)
    elem[:] = out 
    return