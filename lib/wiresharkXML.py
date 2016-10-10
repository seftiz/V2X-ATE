"""
Routines for reading PDML produced from TShark.

Copyright (c) 2003, 2013 by Gilbert Ramirez <gram@alumni.rice.edu>

This program is free software; you can redistribute it and/or
modify it under the terms of the GNU General Public License
as published by the Free Software Foundation; either version 2
of the License, or (at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU General Public License for more details.

You should have received a copy of the GNU General Public License
along with this program; if not, write to the Free Software
Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA 02110-1301 USA.
"""

import sys
import xml.sax
from xml.sax.saxutils import quoteattr
import cStringIO as StringIO
import cPickle
# from picklingtools import xmlloader

class CaptureFile:
    pass

class FoundItException(Exception):
    """Used internally for exiting a tree search"""
    pass

class PacketList:
    """Holds Packet objects, and has methods for finding
    items within it."""

    def __init__(self, children=None):
        if children == None:
            self.children = []
        else:
            self.children = children

    def __getitem__(self, index):
        """We act like a list."""
        return self.children[index]

    def __len__(self):
        return len(self.children)

    def item_exists(self, name):
        """Does an item with name 'name' exist in this
        PacketList? Returns True or False."""
        for child in self.children:
            if child.name == name:
                return True

        try:
            for child in self.children:
                child._item_exists(name)

        except FoundItException:
            return True

        return False

    def _item_exists(self, name):
        for child in self.children:
            if child.name == name:
                raise FoundItException
            child._item_exists(name)

    def build_packet(self, proto, obj):
        for child in proto:
            field_name = child.name
            if len(field_name.split('.')) > 1:
                field_name = field_name.split('.')[-1]

            if len(child.children) > 0:
                setattr( obj, field_name, obj.__class__() )
                #print "CLASS : sub class object {} type {}".format( child.name, obj.__class__.__name__)
                child.build_packet(child, getattr(obj, field_name) )
            else:
                setattr( obj, field_name, [child.get_value() , child.get_show()] )
                #print "FIELD : var {}: value {}, show_value {}".format( child.name, child.value, child.get_show())

            
        #print "OK"


    def get_all_items(self):
        items = []
        for child in self.children:
            items.append(child)

        return items


    def get_items(self, name, items=None):
        """Return all items that match the name 'name'.
        They are returned in order of a depth-first-search."""
        if items == None:
            top_level = 1
            items = []
        else:
            top_level = 0

        for child in self.children:
            if child.name == name:
                items.append(child)
            child.get_items(name, items)

        if top_level:
            return PacketList(items)

    def get_items_before(self, name, before_item, items=None):
        """Return all items that match the name 'name' that
        exist before the before_item. The before_item is an object.
        They results are returned in order of a depth-first-search.
        This function allows you to find fields from protocols that occur
        before other protocols. For example, if you have an HTTP
        protocol, you can find all tcp.dstport fields *before* that HTTP
        protocol. This helps analyze in the presence of tunneled protocols."""
        if items == None:
            top_level = 1
            items = []
        else:
            top_level = 0

        for child in self.children:
            if top_level == 1 and child == before_item:
                break
            if child.name == name:
                items.append(child)
            # Call get_items because the 'before_item' applies
            # only to the top level search.
            child.get_items(name, items)

        if top_level:
            return PacketList(items)

class ProtoTreeItem(PacketList):
    def __init__(self, xmlattrs):
        PacketList.__init__(self)

        self.name = xmlattrs.get("name", "")
        self.showname = xmlattrs.get("showname", "")
        self.pos = xmlattrs.get("pos", "")
        self.size = xmlattrs.get("size", "")
        self.value = xmlattrs.get("value", "")
        self.show = xmlattrs.get("show", "")
        self.hide = xmlattrs.get("hide", "")

    def add_child(self, child):
        self.children.append(child)

    def get_name(self):
        return self.name

    def get_showname(self):
        return self.showname

    def get_pos(self):
        return self.pos

    def get_size(self):
        return self.size

    def get_value(self):
        return self.value

    def get_show(self):
        return self.show

    def get_hide(self):
        return self.hide

    def dump(self, fh=sys.stdout):
        if self.name:
            print >> fh, " name=%s" % (quoteattr(self.name),),

        if self.showname:
            print >> fh, "showname=%s" % (quoteattr(self.showname),),

        if self.pos:
            print >> fh, "pos=%s" % (quoteattr(self.pos),),

        if self.size:
            print >> fh, "size=%s" % (quoteattr(self.size),),

        if self.value:
            print >> fh, "value=%s" % (quoteattr(self.value),),

        if self.show:
            print >> fh, "show=%s" % (quoteattr(self.show),),

        if self.hide:
            print >> fh, "hide=%s" % (quoteattr(self.hide),),

class Packet(ProtoTreeItem, PacketList):
    def dump(self, fh=sys.stdout, indent=0):
        print >> fh, "  " * indent, "<packet>"
        indent += 1
        for child in self.children:
            child.dump(fh, indent)
        print >> fh, "  " * indent, "</packet>"

    def __getitem__(self,key):
        try:
            return self.get_items(key)[-1].get_show()
        except:
            return None


class Protocol(ProtoTreeItem):

    def dump(self, fh=sys.stdout, indent=0):
        print >> fh, "%s<proto " %  ("  " * indent,),
       
        ProtoTreeItem.dump(self, fh)

        print >> fh, '>'

        indent += 1
        for child in self.children:
            child.dump(fh, indent)
        print >> fh, "  " * indent, "</proto>"

class Field(ProtoTreeItem):

    def dump(self, fh=sys.stdout, indent=0):
        print >> fh, "%s<field " % ("  " * indent,),

        ProtoTreeItem.dump(self, fh)

        if self.children:
            print >> fh, ">"
            indent += 1
            for child in self.children:
                child.dump(fh, indent)
            print >> fh, "  " * indent, "</field>"

        else:
            print >> fh, "/>"

class ParseXML(xml.sax.handler.ContentHandler):

    ELEMENT_FILE        = "pdml"
    ELEMENT_FRAME       = "packet"
    ELEMENT_PROTOCOL    = "proto"
    ELEMENT_FIELD       = "field"

    def __init__(self, cb):
        self.cb = cb
        self.chars = ""
        self.element_stack = []

    def startElement(self, name, xmlattrs):
        self.chars = ""

        if name == self.ELEMENT_FILE:
            # Eventually, we should check version number of pdml here
            elem = CaptureFile()

        elif name == self.ELEMENT_FRAME:
            elem = Packet(xmlattrs)

        elif name == self.ELEMENT_PROTOCOL:
            elem = Protocol(xmlattrs)

        elif name == self.ELEMENT_FIELD:
            elem = Field(xmlattrs)

        else:
            sys.exit("Unknown element: %s" % (name,))

        self.element_stack.append(elem)


    def endElement(self, name):
        elem = self.element_stack.pop()

#        if isinstance(elem, Field):
#            if elem.get_name() == "frame.number":
#                print >> sys.stderr, "Packet:", elem.get_show()

        # Add element as child to previous element as long
        # as there is more than 1 element in the stack. Only
        # one element in the stack means that the the element in
        # the stack is the single CaptureFile element, and we don't
        # want to add this element to that, as we only want one
        # Packet element in memory at a time.
        if len(self.element_stack) > 1:
            parent_elem = self.element_stack[-1]
            parent_elem.add_child(elem)
        
        self.chars = ""

        # If we just finished a Packet element, hand it to the
        # user's callback.
        if isinstance(elem, Packet):
            self.cb(elem)

    def characters(self, chars):
        self.chars = self.chars + chars

def _create_parser(cb):
    """Internal function for setting up the SAX parser."""

    # Create a parser
    parser = xml.sax.make_parser()

    # Create the handler
    handler = ParseXML(cb)

    # Tell the parser to use our handler
    parser.setContentHandler(handler)

    # Don't fetch the DTD, in case it is listed
    parser.setFeature(xml.sax.handler.feature_external_ges, False)

    return parser

def parse_fh(fh, cb):
    """Parse a PDML file, given filehandle, and call the callback function (cb),
    once for each Packet object."""

    parser = _create_parser(cb)

    # Parse the file
    parser.parse(fh)

    # Close the parser ; this is erroring out, but I'm not sure why.
    #parser.close()

def parse_pdml_file( file_name , callback_handler ):

    # filename = sys.argv[1]
    #filename = "I:\\pdml_result.xml"
    
    fh = open(filename, "r")
    
    my_pos = 0
    data = fh.readline()
    while data != '<?xml version="1.0"?>\n':
        my_pos = fh.tell()
        data = fh.readline()

    parse_fh(fh, callback_handler)



def parse_string(text, cb):
    """Parse the PDML contained in a string."""
    stream = StringIO.StringIO(text)
    parse_fh(stream, cb)

class wildcard(object):
    def __eq__(self, other):
        return True
 
    def __ne__(self, other):
        return False

class Template(object):
    """ This class is used as base class for converting xml to python classs
        It contain the base for comparison of class comare using TTCN style.
    """
    def __init__(self):
        self._frozen = False
        self._fields = []        
 
    def __setattr__(self, name, value):
        if name in ('_fields', '_frozen'):
            object.__setattr__(self, name, value)
            return
        if self._frozen:
            raise RuntimeError("Cannot set attribute value on a frozen template")
        if name not in self._fields:
            self._fields.append(name)
        object.__setattr__(self, name, value)
 
    def __eq__(self, other):
        if len(self._fields)!=len(other._fields):
            return False
        else:
            for f_self, f_other in zip(self._fields, other._fields):
                val_self  = getattr(self, f_self)
                val_other = getattr(self, f_other)
                if val_self != val_other:
                    return False
            return True
 
    def __ne__(self, other):
        return not self.__eq__(other)
 
    def freeze(self):
        self._frozen = True
    
    def save_to_file(self, file_name):
        with open(file_name, "wb") as output:
            cPickle.dump(self, output, cPickle.HIGHEST_PROTOCOL)
        output.close()

    def clone(self):
        T = Template()
        T._fields = self._fields[:]
        for field in T._fields:
            setattr(T, field, getattr(self, field))
        return T

def load_template_from_file(obj, file_name):
    with open(file_name, "rb") as input:
        obj = cPickle.load(input) # protocol version is auto detected
    input.close()


def _test():
    import sys
    

    def test_cb(packet):

        print "Proccessing frame %s with protocols %s"  % (packet.get_items("frame.number")[-1].get_show(), packet.get_items("frame.protocols")[-1].get_show())
        if packet.item_exists("wsmp"):
            print packet.get_items("wsmp.version")[-1].get_show()
            print packet.get_items("wsmp.txpower")[-1].get_show()



        

    # filename = sys.argv[1]
    filename = "I:\\pdml_result.xml"
    fh = open(filename, "r")
    
    my_pos = 0
    data = fh.readline()
    while data != '<?xml version="1.0"?>\n':
        print "line : %s, pos = %d" % (data , my_pos)
        my_pos = fh.tell()
        data = fh.readline()



    parse_fh(fh, test_cb)

if __name__ == '__main__':
    _test()