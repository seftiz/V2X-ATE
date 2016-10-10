ISO_TIME_FMT = '%Y-%m-%dT%H:%M:%S'


import sys
import string
import functools
import types
import threading
import contextlib
import struct

from cStringIO import StringIO as Stream


_context = threading.local()


class MetaType(type):
    def __new__(mcls, name, bases, clsdict):
        cls = type.__new__(mcls, name, bases, clsdict)
        if hasattr(cls, 'static') and cls.static:
            cls._default = cls()
            cls.unpack = cls._unpack_default
            cls.pack = cls._pack_default        
        return cls


class Type(object):
    __metaclass__ = MetaType
    __slots__ = []

    def unpack(self, bytes):
        stream = Stream(bytes)
        value = self.load(stream)
        extra = len(bytes) - stream.tell()
        if extra != 0:
            raise ValueError('Extra %d bytes at the end' % extra)
        return value

    def pack(self, value):
        stream = Stream()
        self.dump(stream, value)
        return stream.getvalue()

    @classmethod
    def _unpack_default(cls, bytes):
        return Type.unpack(cls._default, bytes)

    @classmethod
    def _pack_default(cls, value):
        return Type.pack(cls._default, value)

    def load(self, stream):
        raise NotImplementedError('load')

    def dump(self, stream, value):
        raise NotImplementedError('dump')


class StaticType(Type):
    static = True


class MetaStruct(MetaType):
    def __new__(mcls, name, bases, clsdict):
        if 'layout' not in clsdict:
            raise TypeError('%s must have layout attribute' % name)

        if isinstance(clsdict['layout'], types.FunctionType):
            if 'fields' not in clsdict:
                raise TypeError('%s has a dynamic layout '
                                'and must have fields attribute' % name)
            clsdict['layout'] = property(clsdict['layout'])
        else:
            clsdict['fields'] = [field for _, field in clsdict['layout']]

        if 'extern' not in clsdict:
            clsdict['extern'] = []

        clsdict['names'] = clsdict['extern'] + clsdict['fields']
        clsdict['__slots__'] = clsdict['names']
        cls = type.__new__(mcls, name, bases, clsdict)

        if not clsdict['extern'] and bases != (Type,):
            cls._default = cls()
            cls.load = cls._load_default
            cls.unpack = cls._unpack_default
            cls.dump = cls._dump_default
        else:
            cls.load = cls._load
            cls.dump = cls._dump

        return cls


class Struct(Type):
    __metaclass__ = MetaStruct
    layout = [] # Empty layout needed for metaclass logic
    extern = []

    def __init__(self, **kw):
        for name in self.names:
            setattr(self, name, None)
        for name, value in kw.iteritems():
            setattr(self, name, value)

    def __repr__(self):
        return '%s(%s)' % (
            self.__class__.__name__,
            ', '.join('%s=%r' % (name, getattr(self, name))
                      for name in self.names))

    def __eq__(self, other):
        if type(self) is not type(other):
            return False
        for name in self.names:
            if getattr(self, name) != getattr(other, name):
                return False
        return True

    def __ne__(self, other):
        return not self.__eq__(other)

    def _copy_externs_to(self, other):
        for name in self.extern:
            setattr(other, name, getattr(self, name))

    def _load(self, stream):
        value = self.__class__()
        self._copy_externs_to(value)
        for typeobj, name in value.layout:
            trace('pre_load', stream, self.__class__.__name__, name)
            setattr(value, name, typeobj.load(stream))
        return value

    def _dump(self, stream, value):
        if value is not self:
            self._copy_externs_to(value)
        for typeobj, name in value.layout:
            trace('pre_dump', stream, self.__class__.__name__, name)
            typeobj.dump(stream, getattr(value, name))
            trace('post_dump')
    
    @classmethod
    def _load_default(cls, stream):
        return cls._load(cls._default, stream)

    @classmethod
    def _dump_default(cls, stream, value):
        return cls._dump(cls._default, stream, value)

    @classmethod
    def _unpack_default(cls, bytes):
        return Type.unpack(cls._default, bytes)

    def pack(self):
        return Type.pack(self, self)


# ASCII characters that have visible gliphs
_VISIBLE_CHARS = frozenset(
    string.ascii_letters + string.punctuation + string.digits)

# Maximal number of hexadecimal byte values to display per line
_MAX_HEX_DISPLAY = 32

class _ConsoleTracer(object):
    def __init__(self, output):
        self._output = output
        self._stack = []

    def println(self, line):
        self._output.write(line)
        self._output.write('\n')

    def pre_load(self, stream, container, element):
        offset = stream.tell()
        start = max(offset - _MAX_HEX_DISPLAY / 2, 0)
        try:
            stream.seek(start)
            quote = stream.read(_MAX_HEX_DISPLAY)
        finally:
            stream.seek(offset)

        self.println('Reading %s.%s at [%d], showing [%d:%d]' % (
                container, element, offset,
                start, start + len(quote)))
        self.println(bin2hex(quote))
        self.println('  '.join((q if q in _VISIBLE_CHARS else '.')
                              for q in quote))
        self.println('   ' * (offset - start) + '^^')

    def pre_dump(self, stream, container, element):
        self._stack.append((stream, container, element, stream.tell()))

    def post_dump(self):
        stream, container, element, pre_offset = self._stack.pop()
        post_offset = stream.tell()
        size = post_offset - pre_offset        
        if size <= _MAX_HEX_DISPLAY:
            stream.seek(pre_offset)
            try:
                quote = bin2hex(stream.read(size))
            finally:
                stream.seek(post_offset)
        else:
            quote = '<...>'

        self.println('Wrote %s.%s to [%d:%d]' % (
                container, element, pre_offset, post_offset))
        self.println('  %s' % quote)

    def flush(self):
        while self._stack:
            _, container, element, offset = self._stack.pop()
            self.println('.. writing %s.%s to [%d]' % (
                    container, element, offset))


@contextlib.contextmanager
def tracing(output=None):
    if output is None:
        output = sys.stderr
    _context.tracer = _ConsoleTracer(output)
    try:
        yield
    finally:
        _context.tracer.flush()
        del _context.tracer


def trace(event, *args, **kw):
    if hasattr(_context, 'tracer'):
        getattr(_context.tracer, event)(*args, **kw)


def readn(stream, nbytes):
    bytes = stream.read(nbytes)
    if len(bytes) < nbytes:
        raise ValueError('Got %d bytes, need %d' % (len(bytes), nbytes))
    return bytes


class Integer(Type):
    def __init__(self, format):
        self._struct = struct.Struct(format)
    
    def load(self, stream):
        value, = self._struct.unpack(readn(stream, self._struct.size))
        return value

    def dump(self, stream, value):
        stream.write(self._struct.pack(value))


# Big-endian unsigned
uint8 = Integer('B')
uint16 = Integer('>H')
uint32 = Integer('>L')
uint64 = Integer('>Q')

# Little-endian unsigned
uint16le = Integer('<H')
uint32le = Integer('<L')
uint64le = Integer('<Q')

# Little-endian signed
int32le = Integer('<l')
int16le = Integer('<h')
double64le =  Integer('<d')

# Big-endian signed
sint8 = Integer('b')
sint16 = Integer('>h')
sint32 = Integer('>l')
sint64 = Integer('>q')


class Opaque(Type):
    def __init__(self, length):
        self.length = length

    def load(self, stream):
        return readn(stream, self.length)

    def dump(self, stream, value):
        if len(value) != self.length:
            raise ValueError('Expected length %d, got %d' % (
                    self.length, len(value)))
        stream.write(value)


class Hex(Opaque):
    def load(self, stream):
        raw = super(Hex, self).load(stream)
        return raw.encode('hex')

    def dump(self, stream, value):
        super(Hex, self).dump(stream, value.decode('hex'))


class OpaqueArray(Type):
    def __init__(self, format):
        self._struct = struct.Struct(format)

    def load(self, stream):
        length, = self._struct.unpack(readn(stream, self._struct.size))
        return readn(stream, length)

    def dump(self, stream, value):
        stream.write(self._struct.pack(len(value)))
        stream.write(value)


opaque8 = OpaqueArray('B')
opaque16 = OpaqueArray('!H')
opaque32 = OpaqueArray('!L')


class Enum(Type):
    def __init__(self_, rawtype, name, **kw):
        # We want to allow the use of 'self' as enumerated value
        self_._rawtype = rawtype
        self_._name = name
        self_.values = kw
        self_.numbers = dict((v, k) for k, v in kw.iteritems())
        if len(self_.values) != len(self_.numbers):
            raise ValueError('Enumeration numbers should be unique')

    def load(self, stream):
        number = self._rawtype.load(stream)
        try:
            return self.numbers[number]
        except KeyError:
            raise ValueError('Invalid number %d for %s' % (
                    number, self._name))

    def dump(self, stream, value):
        try:
            number = self.values[value]
        except KeyError:
            raise ValueError('Invalid value %r for %s' % (
                    value, self._name))
        else:
            self._rawtype.dump(stream, number)


def decode_int(byte_str):
    """Decode an arbitrary big-endian integer.
    """
    return int(byte_str.encode('hex'), 16)


def encode_int(number, nbytes):
    """Encode an arbitrary integer as big-endian.
    """
    hexstr = ('%x' % number).rjust(nbytes * 2, '0')
    return hexstr.decode('hex')


def bin2hex(byte_str):
    """Convert binary string to hexadecimal space-separated.

    The string ends with a space to match USDOT certificate distribution
    format exactly.
    """
    return ''.join('%02x ' % ord(b) for b in byte_str)


def hex2bin(hex_str):
    """Convert hexadecimal space-separated string to binary.
    """
    return ''.join(h.decode('hex') for h in hex_str.split())
