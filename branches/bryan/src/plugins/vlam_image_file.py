"""  Crunchy image file plugin.

plugin used to display an image generated by some Python code.

This file is heavily commented in case someone needs some detailed
example as to how to write a plugin.
"""

import os

# All plugins should import the crunchy plugin API
import src.CrunchyPlugin as CrunchyPlugin
from src.configuration import defaults

# The set of "widgets/services" provided by this plugin
provides = set(["image_file_widget"])
# The set of other "widgets/services" required from other plugins
requires = set(["io_widget", "/exec", "style_pycode",  "editor_widget"])

def register():
    """The register() function is required for all plugins.
       In this case, we need to register only one type of action:
          a custom 'vlam handler' designed to tell Crunchy how to
          interpret the special Crunchy markup.
       """
    # 'image_file' only appears inside <pre> elements, using the notation
    # <pre title='image_file ...'>
    CrunchyPlugin.register_tag_handler("pre", "title", "image_file",
                                            insert_image_file)

def insert_image_file(page, elem, uid):
    """handles the insert image file widget"""
    vlam = elem.attrib["title"]
    # We add html markup, extracting the Python
    # code to be executed in the process
    code, markup = CrunchyPlugin.services.style_pycode(page, elem)

    # reset the original element to use it as a container.  For those
    # familiar with dealing with ElementTree Elements, in other context,
    # note that the style_pycode() method extracted all of the existing
    # text, removing any original markup (and other elements), so that we
    # do not need to save either the "text" attribute or the "tail" one
    # before resetting the element.
    elem.clear()
    elem.tag = "div"
    elem.attrib["id"] = "div_" + uid
    # extracting the image file name
    stripped_vlam = vlam.strip()
    args = stripped_vlam.split()
    if len(args) >1:
        img_fname = args[1]  # assume name is first argument
    else:
        # The user hasn't supplied the filename in the VLAM.
        elem.insert(0, markup)
        message = CrunchyPlugin.SubElement(elem, "p")
        message.text = """
        The above code was supposed to be used to generate an image.
        However, Crunchy could not find a file name to save the image, so
        only code styling has been performed.
        """
        return

    # determine where the code should appear; we can't have both
    # no-pre and no-copy at the same time; both are optional.
    if not "no-pre" in vlam:
        elem.insert(0, markup)
    elif "no-copy" in vlam:
        code = "\n"
    CrunchyPlugin.services.insert_editor_subwidget(page, elem, uid, code)
    # some spacing:
    CrunchyPlugin.SubElement(elem, "br")

    # The actual file name to be used is "mangled" by adding a prefix
    # that will be extracted later by Crunchy upon a GET call.  This is
    # required as the directory where the file is saved will not
    # typically be reachable from the server root.

    image_fname = "/CrunchyTempDir" + img_fname

    # the actual button used for code execution:
    btn = CrunchyPlugin.SubElement(elem, "button")
    btn.attrib["onclick"] = "image_exec_code('%s', '%s')" % (uid, image_fname)
    btn.text = "Generate image"  # This will eventually need to be translated
    CrunchyPlugin.SubElement(elem, "br")
    # an output subwidget:
    CrunchyPlugin.services.insert_io_subwidget(page, elem, uid)

    # Extension of the file; used for determining the filetype
    ext = img_fname.split('.')[-1]
    CrunchyPlugin.SubElement(elem, "br")
    if ext in ['svg', 'svgz']:  # currently untested
        img = CrunchyPlugin.SubElement(elem, "iframe")
    else:
        img = CrunchyPlugin.SubElement(elem, "img")
    img.attrib['id'] = 'img_' + uid
    img.attrib['src'] = ''
    img.attrib['alt'] = 'The code above should create a file named ' +\
                        img_fname + '.'
    CrunchyPlugin.SubElement(elem, "br")
    # we need some unique javascript in the page; note how the
    # "/exec" referred to above as a required service appears here
    # with a random session id appended for security reasons.
    #
    # Also note that the string representing the javascript code
    # has some parameters that need to be defined; this is done below.

    image_jscode = """
function image_exec_code(uid, image_path){
    // execute the code
    code=editAreaLoader.getValue('code_'+uid);
    var j = new XMLHttpRequest();
    j.open("POST", "/run_external%(session_id)s?uid="+uid, false);
    j.send(code)
    // now load newly created image; we append a random string as a
    // parameter (after a ?) to prevent the browser from loading a
    // previously cached image.
    var now = new Date();
    img_path = image_path + '?' + now.getTime();
    img = document.getElementById('img_'+uid);
    img.src = img_path;
    img.alt = 'Image file saved as ' + image_path + '.';
    img.alt = img.alt + '%(error_message)s';
    // We then reload the new image
     j.open('GET', img_path, false);
     j.send(null);
};
"""

    # Now replacing the parameter in the javascript code as mentioned above
    # and adding it to the page for each image, unlike many other plugins
    # where we only need to add the code once per page.
    image_jscode = image_jscode%{
    "session_id": CrunchyPlugin.session_random_id,
    "error_message": """
    If you see this message, then the image was
    not created or loaded properly. This sometimes happens when creating
    a figure for the first time. Try generating the image again.
    """.replace('\n', '\\n')
}

    # We clean up the directory before the first use
    # to remove all old images; this is not strictly needed, but will
    # help to prevent cluttering.
    if not page.includes("image_included"):
        page.add_include("image_included")
        page.add_js_code(image_jscode)
        old_files = [x for x in os.listdir(defaults.temp_dir)]
        for x in old_files:
            print "removing file %s"%(x)
            try:
                os.remove(os.path.join(defaults.temp_dir, x))
            except:  # if it fails, it is not a major problem
                print "could not remove file %s"%(x)