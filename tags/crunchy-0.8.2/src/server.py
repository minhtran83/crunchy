"""Sublass SimpleHTTPRequestHandler to deal with our specific needs
"""

# Python standard library modules
import os
import sys
import urllib
from SimpleHTTPServer import SimpleHTTPRequestHandler
from urllib2 import urlopen
from urllib import pathname2url
# crunchy modules
import configuration
import crunchyfier
import errors
import interpreters
import security
import translation
prefs = configuration.UserPreferences()
# The following variables are initialised in crunchy.py
repl = None    # read-eval-print-loop: Python interpreter
server = None
active_path = None
active_base = None
not_saved = True
new_path = None

class CrunchyRequestHandler(SimpleHTTPRequestHandler):
    '''handle HTTP requests'''
    pagemap = {}

    def do_GET(self):
        '''handle a GET request, called by methods in SimpleHTTPRequestHandler'''
        path, argmap = self.process_GET_path(self.path)
        if path in self.pagemap:
            data = self.pagemap[path](argmap)
            if type(data) == type(200):
                self.send_error(data)
            else:
                self.send_response(200)
                self.end_headers()
                self.wfile.write(data)
                self.wfile.flush()
                self.wfile.close()
        else:    #OK, we didn't recognise it, assume its in the local filesystem:
            #NOTE: this is undocumented - risky? works with Python 2.4
            #we can't use SimpleHTTPRequestHandler.send_head because it sends an inaccurate "Content-Length" header
            path = self.translate_path(self.path)
            ext = os.path.splitext(path)[1]
            if ext in ['.htm', '.html', ".lore"]:    #treat it as a VLAM page, even if it contains no VLAM, we can still style it
                try:
                    handle = open(path, 'r')
                except IOError, info:
                    self.send_data(errors.IOError_error_dialog(info))
                    return
                try:
                    page = crunchyfier.VLAMPage(handle, 'file://' + path)
                except errors.HTMLTreeBuilderError, e:
                    self.send_data(errors.HTMLTreeBuilder_error_dialog(e))
                    return
                data = page.get()
                self.send_response(200)
                self.end_headers()
                self.wfile.write(data)
                return
            else:
                #its not VLAM, fall back:
                SimpleHTTPRequestHandler.do_GET(self)

    def process_GET_path(self, path):
        """process a path passed in a GET request:
            dplit of the path from the argument segment
            and return the path and a mapping of argument names to values
            - very pythonic :-)
        """
        parts = self.path.split("?")
        path = str(parts[0])
        #extract the arguments,
        # argmap will map from argument names to values as strings
        # values are decoded with urllib.unquote_plus
        argmap = {}
        arg = []
        if len(parts) > 1:
            argstring = str(parts[1])
            arglist = argstring.split('&')
            for i in arglist:
                arg = i.split('=')
                val = ''
                if len(arg) > 1:
                    argmap[arg[0]] = urllib.unquote_plus(arg[1])
        return path, argmap

    def send_data(self, data):
        '''Sends data back to browser, after successfully handling a request.'''
        # Note: It is also used to send a customized javascript error dialog
        # instead of a standard error code, like 404.
        self.send_response(200)
        self.end_headers()
        self.wfile.write(data)
        return

    def do_POST(self):
        '''Handles a POST request, called by methods in SimpleHTTPRequestHandler'''
        if self.path.startswith(security.commands["/push"]):  #interactive interpreter
            args = {}
            args["line"] = self.rfile.read(int(self.headers["Content-Length"]))
            args["name"] = self.path.split('?')[1]
            data = self.pagemap[security.commands["/push"]](args)
            if type(data) == type(200):
                self.send_error(data)
            else:
                self.send_data(data)
        elif self.path.startswith(security.commands["/execute"]):           #code editor
            code = self.rfile.read(int(self.headers["Content-Length"]))
            i = interpreters.CrunchyInterpreter(code, self.path.split('?')[1])
            i.start()
            self.send_response(200)
            self.end_headers()
        elif self.path.startswith(security.commands["/doctest"]):      #doctest
            code = self.rfile.read(int(self.headers["Content-Length"]))
            parts = self.path.split('?')
            self.send_response(200)
            self.end_headers()
            interpreters.run_doctest(code, parts[1])
        elif self.path.startswith(security.commands['/canvas_exec']):
            canvas_id = self.path.split('?')[1]
            try:
                data = interpreters.exec_graphics(canvas_id,
                          self.rfile.read(int(self.headers["Content-Length"])))
                self.send_data(data)
            except errors.ColourNameError, info:
                self.send_error(400, errors.colour_name_dialog(info))
            except Exception, info:
                self.send_error(400, errors.canvas_error_dialog(info))

        elif self.path.startswith(security.commands['/rawio']):
            bufname = self.path.split('?')[1]
            if bufname in interpreters.interpreters:
                i = interpreters.interpreters[bufname]
                #print self.headers
                self.send_response(200)
                self.end_headers()
                data = i.get()
                self.wfile.write(data)
                if not i.isAlive():
                    del interpreters.interpreters[bufname]
            else:
                self.send_error(403)
        elif self.path.startswith(security.commands['/spawn_console']):
            data = self.rfile.read(int(self.headers["Content-Length"]))
            interpreters.exec_external(data, console=True)
        elif self.path.startswith(security.commands['/spawn']):
            data = self.rfile.read(int(self.headers["Content-Length"]))
            interpreters.exec_external(data, console=False)
        elif self.path.startswith(security.commands['/save_python']):
            data = self.rfile.read(int(self.headers["Content-Length"]))
            # We've sent the file (content) and filename (path) in one
            # "document" written as path+"_::EOF::_"+content; the assumption
            # is that "_::EOF::_" would never be part of a filename/path.
            #
            # There could be more robust ways, like sending a string containing
            # the path length separated from the path and the content by
            # a separator where we check to make sure the path recreated
            # is of the correct length - but it probably would be an overkill.
            info = data.split("_::EOF::_")
            path = info[0].decode(translation.current_page_encoding)
            path = path.encode(sys.getdefaultencoding())
            #path = info[0].encode(sys.getdefaultencoding())
            #print "path = ", path
            filename = open(path, 'w')
            # the following is in case "_::EOF::_" appeared in the file content
            content = '_::EOF::_'.join(info[1:])
            filename.write(content)
            filename.close()
        elif self.path.startswith(security.commands['/save_and_run']):
            # combination of /save_python and /span_console as above
            # save file first
            data = self.rfile.read(int(self.headers["Content-Length"]))
            info = data.split("_::EOF::_")
            path = info[0].decode(translation.current_page_encoding)
            path = path.encode(sys.getdefaultencoding())
            #filename = open(path, 'w')
            content = '_::EOF::_'.join(info[1:])
            #filename.write(content)
            #filename.close()
            # then run it
            interpreters.exec_external(content, console=False, path=path)
        else:
            self.send_error(404, self.path)

def get_crunchy_index(dummy):
    '''Default page displayed to user.'''
    return prefs.index#open(prefs.home).read()

def get_exit(dummy):
    """
    set up the flag for the server to quit and present an "exit" page, inviting
    the user to close the window.
    """
    server.still_serving = False
    return open(prefs.exit).read()

def get_push(args):
    '''the push part of the ajax interpreter, uses POST
    '''
    result = interpreters.interps[args['name']].push(args["line"])
    if result is None:
        return 204
    return result

def get_dir(args):
    '''the dir part of the ajax interpreter, uses GET
    '''
    result = interpreters.interps[args['name']].dir(args["line"])
    if result == None:
        return 204
    else:
        #have to convert the list to a string
        result = repr(result)
    return result

def get_doc(args):
    '''the doc part of the ajax interpreter, uses GET
    '''
    result = interpreters.interps[args['name']].doc(args["line"])
    if not result:
        return 204
    return result

def get_external_page(args):
    """load an external page into crunchy"""
    try:
        handle = urlopen(args['path'])
    except:
        return 404
    vlam = crunchyfier.VLAMPage(handle, args['path'], external_flag=True)
    return vlam.get()

def get_local_page(args):
    """load an arbitrary local page into crunchy"""
    # pages are often encoded in a character set (e.g. utf-8) different from
    # the local default; the info received is sometimes in that encoding.
    # If the path contains "weird" characters, such as &eacute; we may
    # need to decode them into the expected local default.
    try:
        path = translation.translate_path(args['path'])
    except:
        path = args['path']
    if path.startswith('file://'):
        path = path.replace('file://', '')
    try:
        handle = open(path)
    except:
        return 404
    if path.endswith('.html') or path.endswith('.htm'):
        base = 'file://'+ os.path.dirname(path)
        vlam = crunchyfier.VLAMPage(handle, base, local_flag=True)
        return vlam.get()
    else:
        return handle.read()

def get_update_page(args):
    '''test function for now '''
    global active_path, active_base, not_saved, new_path
    # save the file with a new name
    if not_saved:
        new_path = active_path.replace(".htm", "_new.htm")
        old = open(active_path)
        new = open(new_path, 'w')
        new.write(old.read())
        new.close()
        not_saved = False
    # now work with the new file
    # first, update it
    handle = open(new_path)
    vlam1 = crunchyfier.HTMLUpdater(handle, active_base, args['changed'])
    saved_changes = open(new_path, 'w')
    saved_changes.write(vlam1.get())
    saved_changes.close()
    # now work with the new file, ready to update it again.
    handle = open(new_path)
    vlam = crunchyfier.VLAMPage(handle, active_base, edit_flag=True,
                local_flag=True)
    return vlam.get()

def get_page_for_editing(args):
    """load an arbitrary local page into chewy"""
    # pages are encoded in utf-8; the info received is sometimes in that encoding.
    # If the path contains "weird" characters, such as &eacute; we may
    # need to decode them into the expected local default.
    global active_path, active_base, not_saved
    try:
        path = translation.translate_path(args['path'])
    except:
        path = args['path']
    if path.startswith('file://'):
        path = path.replace('file://', '')
    try:
        handle = open(path)
    except:
        return 404
    if path.endswith('.html') or path.endswith('.htm'):
        base = 'file://'+ os.path.dirname(path)
        vlam = crunchyfier.VLAMPage(handle, base, edit_flag=True,
                local_flag=True)
        # we save the path and not the handle as we can't read twice
        # from the same handle
        if path != active_path:    # new file
            not_saved = True
            active_path = path
            active_base = base
        return vlam.get()
    else:
        return handle.read()

def get_user_js(args):
    """loads a user-constructed javascript into crunchy"""
    return security.js_memory_file.getvalue()

def get_python_file(args):
    """loads a local Python file; intended target should be
       an EditArea.
    """
    # For reasons that puzzle me, this one does not need to be decoded
    # from the current html page encoding and encoded in the
    # default system encoding to work.
    path = pathname2url(args['path'])
    try:
        handle = urlopen('file://' + path)
    except:
        return 404
    return handle.read()

def get_language(args):
    '''Present the user with a page that give a choice of language
       to use for menus and dialogs.
    '''
    prefs = configuration.UserPreferences()
    prefs.language = args['language']
    handle = open(prefs.options)
    vlam = crunchyfier.VLAMPage(handle, prefs.options)
    return vlam.get()

def get_style(args):
    '''Present the user with a page that give a choice of page style.
    '''
    prefs = configuration.UserPreferences()
    prefs.style = args['style']
    handle = open(prefs.options)
    vlam = crunchyfier.VLAMPage(handle, prefs.options)
    return vlam.get()