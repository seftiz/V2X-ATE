import os
import re

from pysnmp.entity.rfc3413.oneliner import cmdgen
from pysnmp.smi import builder
from pyasn1.type.univ import Integer, OctetString


from . import *
from lib import globals

#MIBError


AGENT_NAME = 'test-agent'

# Note MIB attribute prefix could be one that's *not* trivially
# derived from MIB module name, so don't assume it.
MIBS = {
    'wlan': 'AUTOTALKS-WLAN-MIB',
    'vca': 'AUTOTALKS-VCA-MIB',
    'nav': 'AUTOTALKS-NAV-MIB',
    'if': 'IF-MIB', 
    'sys': 'SNMPv2-MIB'
}

_MIB_PREFIX_RE = re.compile('(%s)' % '|'.join(MIBS.keys()))


def _find_pysnmp_dir(mibs_dirs = None):
    
    
    private_mibs = "_pysnmp" if mibs_dirs == None else "_pysnmp_" + mibs_dirs
    #pysnmp_dir = os.path.join(os.path.dirname(__file__), '_pysnmp')
    pysnmp_dir = os.path.join(os.path.dirname(__file__), private_mibs)
    if not os.path.isdir(pysnmp_dir):
        # Check on def lib
        raise RuntimeError('%s not found, please run `make\'' % pysnmp_dir)

    #    from atlk.ut import root_path
    #    pysnmp_dir = os.path.join(root_path, 'output', 'python', '_pysnmp')
    #    if not os.path.isdir(pysnmp_dir):
    #        raise RuntimeError('%s not found, please run `make\'' % pysnmp_dir)
    return pysnmp_dir

_dir_mib_source = builder.DirMibSource(_find_pysnmp_dir())
_community_public = cmdgen.CommunityData(AGENT_NAME, 'public', 0)
_community_private = cmdgen.CommunityData(AGENT_NAME, 'private', 0)


class SNMPError(MIBError):
    pass


def _load_pysnmp_modules(cmd_gen, mibs_directory = None):
    
    mib_builder = cmd_gen.snmpEngine.msgAndPduDsp.mibInstrumController.mibBuilder

    unit_mib_path = _dir_mib_source if mibs_directory == None else mibs_directory
    
    # override default _pysnmp Library
    unit_mib_source = builder.DirMibSource(_find_pysnmp_dir(unit_mib_path))

    # mib_sources = mib_builder.getMibSources() + (_dir_mib_source,)
    mib_sources = mib_builder.getMibSources() + (unit_mib_source,)
    mib_builder.setMibSources(*mib_sources)
    mib_builder.loadModules(*MIBS.values())


def _process_result(result):
    errorIndication, errorStatus, errorIndex, varBinds = result
    if errorIndication:
        raise SNMPError(errorIndication)
    elif errorStatus:
        raise SNMPError('%s at %s' % (
                errorStatus.prettyPrint(),
                errorIndex and varBinds[int(errorIndex) - 1] or '?'))
    else:
        # Assertion below holds until WALK is supported
        assert len(varBinds) == 1
        _, value = varBinds[0]
        return _pyasn1_to_native(value)


def _key_to_pysnmp(key):
    """Convert our attribute key notation to PySNMP notation.
    """
    if isinstance(key, basestring):
        return ((_detect_mib(key), key), 0)

    try:
        column, row = key
    except:
        raise MIBError('Key %r is neither a string '
                        'nor a sequence of length 2' % key)

    if not isinstance(column, basestring):
        raise MIBError('Column name %r is not a string' % column)

    try:
        row = int(row)
    except:
        raise MIBError('Row index %r couldn\'t be converted to int' % row)

    return ((_detect_mib(column), column), row)


def _detect_mib(attr):
    """Detect MIB module name by MIB attribute prefix (this assumes
    that each MIB module uses a unique prefix for its attributes).
    """
    m = _MIB_PREFIX_RE.match(attr)
    if m is None:
        raise MIBError('Unrecognized MIB attribute name %r' % attr)

    # This lookup must succeed because of the way _MIB_PREFIX_RE is
    # constructed from MIBS.keys()
    return MIBS[m.group(1)]


def _pyasn1_to_native(value):
    if isinstance(value, Integer):
        return int(value)
    elif isinstance(value, OctetString):
        return str(value)
    raise NotImplementedError(
        '%s objects not supported yet' % type(value))


class Manager(object):
    """PySNMP child-proof wrapper; currently supports get and set only.
    """
    def __init__(self, address, mibs_directory = None):
        self._transport = cmdgen.UdpTransportTarget((address, 161))
        self._set_cmd_gen = cmdgen.CommandGenerator()
        self._get_cmd_gen = cmdgen.CommandGenerator()
        _load_pysnmp_modules(self._set_cmd_gen, mibs_directory)
        _load_pysnmp_modules(self._get_cmd_gen, mibs_directory)

    def get(self, key):
        """Get value MIB of attribute referred by `key`.

        `key` is of the form:
        - 'scalarName' if the attribute is scalar.
        - ('columnName', row_index) if the attribute is a cell in a table.
        """
        result = self._get_cmd_gen.getCmd(
            _community_public, self._transport, _key_to_pysnmp(key))
        return _process_result(result)

    def set(self, key, value):
        """Set value of MIB attribute referred by `key`.

        `key` syntax is identical to that accepted by `get` method.
        """
        result = self._set_cmd_gen.setCmd(
            _community_private, self._transport, (_key_to_pysnmp(key), value))
        return _process_result(result)

    def close(self):
        pass
