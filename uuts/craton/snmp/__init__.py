class MIBError(StandardError):
    pass


def create_manager(address, protocol='snmpv1'):
    if protocol == 'snmpv1':
        from . import snmp
        return snmp.Manager(address)
    else:
        raise ValueError('Unknown protocol %s' % protocol)
