"""This plugin handles loading all pages not loaded by other plugins"""

from imp import find_module
from os.path import normpath, join, isdir, dirname
from dircache import listdir, annotate

from CrunchyPlugin import *

requires = set(["translation"])

_ = None

def register():
    global _
    register_http_handler(None, handler)
    _ = services._
    
def path_to_filedata(path, root):
    """
    Given a path, finds the matching file and returns a read-only reference
    to it. If the path specifies a directory and does not have a trailing slash
    (ie. /example instead of /example/) this function will return none, the
    browser should then be redirected to the same path with a trailing /.
    Root is the fully qualified path to server root.
    Paths containing .. will return an error message.
    POSIX version, should work in Windows.
    """
    if path.find("/../") != -1:
        return error_page(path)
    npath = normpath(join(root, normpath(path[1:])))
    if isdir(npath):
        if path[-1] != "/":
            return None
        else:
            return get_directory(npath)
    else:
        try:
            if npath.endswith(".html") or npath.endswith(".htm"):
                return create_vlam_page(open(npath), path).read()
            # we need binary mode because otherwise the file doesn't get read properly on windows
            fhandle = open(npath, mode="rb")
            data = fhandle.read()
            return data
        except IOError:
            print "can not open path = ", npath
            return error_page(path)

def handler(request):
    """the actual handler"""
    data = path_to_filedata(request.path, root_path)
    if data == None:
        request.send_response(301)
        request.send_header("Location", request.path + "/")
        request.end_headers()
    else:
        request.send_response(200)
        request.end_headers()
        request.wfile.write(data)

def get_directory(npath):
    childs = listdir(npath)
    childs = childs[:]
    annotate(npath, childs)
    for i in default_pages:
        if i in childs:
            return path_to_filedata("/"+i, npath)
    tstring = ""
    for child in childs:
        tstring += '<li><a href="%s">%s</a></li>' % (child, child)
    return dir_list_page % (_("Directory Listing"), tstring)

# the root of the server is in a separate directory:
root_path = join(dirname(find_module("crunchy")[1]), "server_root/")

print "Root path is %s" % root_path

default_pages = ["index.htm", "index.html"]

illegal_paths_page = """
<html>
<head>
<title>
%s <!--Illegal path, page not found. -->
</title>
</head>
<body>
<h1>%s<!--Illegal path, page not found. --></h1>
<p>%s <!--Crunchy could not open the page you requested. This could be for one of anumber of reasons, including: --></p>
<ul>
<li>%s <!--The page doesn't exist. --></li>
<li>%s<!--The path you requested was illegal, examples of illegal paths include those containg the .. path modifier.-->
</li>
</ul>
<p>%s <!--The path you requested was:--> <b>%s<!--path--></b></p>
</body>
</html>
"""

dir_list_page = """
<html>
<head>
<title>
%s
</title>
</head>
<body>
<ul>
<li><a href="../">..</a></li>
%s
</ul>
</body>
</html>
""" 

def error_page(path):
    return illegal_paths_page % (_("Illegal path, page not found."), _("Illegal path, page not found."),
                                 _("Crunchy could not open the page you requested. This could be for one of anumber of reasons, including:"),
                                 _("The page doesn't exist."),
                                 _("The path you requested was illegal, examples of illegal paths include those containing the .. path modifier."),
                                 _("The path you requested was: "),
                                 path)



