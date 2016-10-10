import struct
import hashlib
import time

from ecdsa import ecdsa
from .. import ISO_TIME_FMT
from . import (
    Type, StaticType, Struct, Enum, Hex, Opaque, Stream,
    uint8, uint16, uint32, uint64, wsmp,
    encode_int, decode_int, readn, hex2bin, bin2hex)

# Which draft of IEEE 1609.2 we implement
# Note: Should reflect firmware build configuration flags with the same names
CONFIG_1609DOT2_D9_3 = True
CONFIG_1609DOT2_D17 = False

#
# 1609.2 over-the-air encoding utilities
#
class Flags(Type):
    def __init__(self, name, **kw):
        if max(kw.values()) > 27:
            raise TypeError('Maximal flag value is 27')
        self.name = name
        self.flags = kw.items()
        self._flag_set = set(kw.keys())
    
    def load(self, stream):
        first = uint8.load(stream)
        length = wsmp.PSID_LENGTHS[first >> 4]
        if length is None:
            raise ValueError('Invalid first octet 0x%x for %s' % (
                    first, self.name))

        number = first & ((1 << (8 - length)) - 1)
        for i in xrange(length - 1):
            number <<= 8
            number |= uint8.load(stream)

        value = set()
        for flag, i in self.flags:
            if number & (1 << i):
                value.add(flag)
        return value
    
    def dump(self, stream, value):
        unknown = value - set(self._flag_set)
        if unknown:
            raise ValueError('Invalid %s: %r' % (self.name, unknown))

        number = 0
        last = 0
        for flag, i in self.flags:
            if flag in value:
                number |= (1 << i)
                last = i
        
        length = (last // 7) + 1
        number |= wsmp.PSID_LENGTHS.index(length) << ((length * 8) - 4)
        for i in xrange(length):
            shift = (length - 1 - i) * 8
            stream.write(chr((number >> shift) & 0xff))


def _load_objects(stream, typeobj, length):
    start = stream.tell()
    consumed = 0
    objects = []        
    while consumed < length:
        objects.append(typeobj.load(stream))
        consumed = stream.tell() - start
    if consumed > length:
        raise ValueError('Array length %d invalid, %d was consumed' % (
                length, consumed))
    return objects


class Array(Type):
    def __init__(self, format, typeobj):
        self._struct = struct.Struct(format)
        self._typeobj = typeobj

    def load(self, stream):
        length, = self._struct.unpack(readn(stream, self._struct.size))
        return _load_objects(stream, self._typeobj, length)

    def dump(self, stream, value):
        stream.write(self._struct.pack(0))
        start = stream.tell()
        for obj in value:
            self._typeobj.dump(stream, obj)
        finish = stream.tell()
        stream.seek(start - self._struct.size)
        stream.write(self._struct.pack(finish - start))
        stream.seek(finish)


# As of 1609.2/D9.3 only used in ToBeEncryptedCertificateResponse
def array64(typeobj):
    return Array('!Q', typeobj)


class VarLength(StaticType):
    @classmethod
    def load(cls, stream):
        first = uint8.load(stream)
        if first & 0x80 == 0:
            return first
        elif first & 0xc0 == 0x80:
            second = uint8.load(stream)
            return ((first & 0x7f) << 8) | second
        else:
            raise NotImplementedError(
                '<var> arrays longer than 2^14-1 not supported yet')

    @classmethod
    def dump(cls, stream, value):
        if value < 0x80:
            uint8.dump(stream, value)
        elif value < 0x4000:
            uint16.dump(stream, value | 0x8000)
        else:
            raise NotImplementedError(
                '<var> arrays longer than 2^14-1 not supported yet')


class VarArray(Type):
    def __init__(self, typeobj):
        self._typeobj = typeobj

    def load(self, stream):
        length = VarLength.load(stream)
        return _load_objects(stream, self._typeobj, length)
    
    def dump(self, stream, value):
        obj_stream = Stream()
        for obj in value:
            self._typeobj.dump(obj_stream, obj)
        obj_data = obj_stream.getvalue()
        VarLength.dump(stream, len(obj_data))
        stream.write(obj_data)


class OpaqueVarArray(StaticType):
    @classmethod
    def load(cls, stream):
        return readn(stream, VarLength.load(stream))
    
    @classmethod
    def dump(cls, stream, value):
        VarLength.dump(stream, len(value))
        stream.write(value)

#
# 1609.2 over-the-air encoding implementation
#
Time32 = uint32
Time64 = uint64
CrlSeries = uint32
CERTID8_LEN = 8
CertId8 = Hex(CERTID8_LEN)


class Data(Struct):
    fields = ['protocol_version',
              'type',
              'signed_data']

    def layout(self):
        if self.protocol_version is None:
            self.protocol_version = 2
        yield uint8, 'protocol_version'
        if self.protocol_version != 2:
            raise ValueError('Expected protocol_version 2, got %d' %
                             self.protocol_version)

        yield ContentType, 'type'
        if self.type == 'signed':
            yield SignedData(type=self.type), 'signed_data'
        else:
            raise NotImplementedError('ContentType %r' % self.type)


ContentType = Enum(
    uint8, 'ContentType',
    unsecured=0, signed=1, encrypted=2,
    certificate_request=3, certificate_response=4,
    anonymous_certificate_response=5,
    certificate_request_error=6, crl_request=7,
    crl=8,
    signed_partial_payload=9,
    signed_external_payload=10,
    signed_wsa=11,
    certificate_response_acknowledgment=12)


class SignedData(Struct):
    extern = ['type']
    fields = ['signer',
              'unsigned_data',
              'signature']

    def algorithm(self):
        if self.signer.type in CERTIFICATE_DIGEST_TYPES:
            return CERTIFICATE_DIGEST_TYPE_TO_PKALGORITHM[self.signer.type]
        elif self.signer.type == 'certificate':
            return self.signer.certificate.verification_algorithm
        else:
            assert False, 'Unknown signer.type %s' % self.signer.type

    def layout(self):
        yield SignerIdentifier, 'signer'
        yield ToBeSignedData(type=self.type), 'unsigned_data'       
        yield Signature(algorithm=self.algorithm()), 'signature'

    def verify(self, public_key):        
        """Return whether verification using `public_key` succeeds.
        """
        signature = ecdsa.Signature(
            decode_int(self.signature.ecdsa_signature.R.x),
            decode_int(self.signature.ecdsa_signature.s))
        
        if self.algorithm() == 'ecdsa_nistp224_with_sha224':
            return public_key.verifies(
                int(self.unsigned_data.sha224(), 16), signature)
        else:
            return public_key.verifies(
                int(self.unsigned_data.sha256(), 16), signature)

class SignerIdentifier(Struct):
    fields = ['type',
              'certificate',
              'digest']

    def layout(self):
        yield SignerIdentifierType, 'type'
        if self.type == 'certificate':
            yield Certificate, 'certificate'
        elif self.type in CERTIFICATE_DIGEST_TYPES:
            yield CertId8, 'digest'
        else:
            raise NotImplementedError('SignerIdentifierType %r' % self.type)


SignerIdentifierType = Enum(
    uint8, 'SignerIdentifierType',
    self=0, certificate_digest_with_ecdsap224=1,
    certificate_digest_with_ecdsap256=2,
    certificate=3,
    certificate_chain=4,
    certificate_digest_with_other_algorithm=5)


CERTIFICATE_DIGEST_TYPE_TO_PKALGORITHM = dict(
    certificate_digest_with_ecdsap224='ecdsa_nistp224_with_sha224',
    certificate_digest_with_ecdsap256='ecdsa_nistp256_with_sha256')


CERTIFICATE_DIGEST_TYPES = CERTIFICATE_DIGEST_TYPE_TO_PKALGORITHM.keys()


class ToBeSignedData(Struct):
    extern = ['type']
    fields = ['tf',
              'psid',
              'data',
              'generation_time']

    def layout(self):
        yield TbsDataFlags, 'tf'        
        if self.type == 'signed':
            yield wsmp.Psid, 'psid'
            yield OpaqueVarArray, 'data'
        else:
            raise NotImplementedError('ContentType %r' % self.type)

        if 'use_generation_time' in self.tf:
            yield Time64WithStandardDeviation, 'generation_time'

        if self.tf - set(['use_generation_time']):
            raise NotImplementedError('TbsDataFlags %r' % self.tf)

    def unsigned_data(self):
        if CONFIG_1609DOT2_D9_3:
            return self.pack()
        elif CONFIG_1609DOT2_D17:
            return ContentType.pack(self.type) + self.pack()
        else:
            assert False, 'Unknown IEEE P1609.2 version'

    def sha224(self):
        return hashlib.sha224(self.unsigned_data()).hexdigest()

    def sha256(self):
        return hashlib.sha256(self.unsigned_data()).hexdigest()

    def signature(self, private_key, ephemeral_key, algorithm):
        """Returns Signature object that contains an ECDSA signature
        with fast verification support in point-compressed format.
        """
        
        if algorithm == 'ecdsa_nistp224_with_sha224':
            signature = private_key.sign(int(self.sha224(), 16), ephemeral_key)
            field_size = 28
        elif algorithm == 'ecdsa_nistp256_with_sha256':
            signature = private_key.sign(int(self.sha256(), 16), ephemeral_key)
            field_size = 32
        else:
            raise ValueError('Unknown algorithm %s' % algorithm)
        
        key_type = ('compressed_lsb_y_0',
                    'compressed_lsb_y_1')[signature.r_y % 2]
        return Signature(
            algorithm=algorithm,
            ecdsa_signature=EcdsaSignature(
                R=EccPublicKey(
                    type=key_type,
                    x=encode_int(signature.r, field_size)),
                s=encode_int(signature.s, field_size)))

if CONFIG_1609DOT2_D9_3:
    TbsDataFlags = Flags('TbsDataFlags',
                         fragment=0,
                         use_generation_time=1,
                         expires=2,
                         use_location=3,
                         extensions=4)
elif CONFIG_1609DOT2_D17:
    TbsDataFlags = Flags('TbsDataFlags',
                         use_generation_time=0,
                         expires=1,
                         use_location=2,
                         extensions=3)
else:
    assert False, 'Unknown IEEE P1609.2 version'

class Time64WithStandardDeviation(Struct):
    layout = [
        (Time64, 'time'),
        (uint8, 'log_std_dev')]


class Signature(Struct):
    extern = ['algorithm']
    fields = ['ecdsa_signature']

    def layout(self):
        if self.algorithm == 'ecdsa_nistp224_with_sha224':
            yield EcdsaSignature(field_size=28), 'ecdsa_signature'
        elif self.algorithm == 'ecdsa_nistp256_with_sha256':
            yield EcdsaSignature(field_size=32), 'ecdsa_signature'
        else:
            raise ValueError('%r is not a known algorithm' % self.algorithm)


PKAlgorithm = Enum(
    uint8, 'PKAlgorithm',
    ecdsa_nistp224_with_sha224=0,
    ecdsa_nistp256_with_sha256=1,
    ecies_nistp256=2)


class EcdsaSignature(Struct):
    extern = ['field_size']
    fields = ['R', 's']

    def layout(self):
        yield EccPublicKey(field_size=self.field_size), 'R'
        yield Opaque(self.field_size), 's'


class EccPublicKey(Struct):
    extern = ['field_size']
    fields = ['type', 'x', 'y']

    def layout(self):
        yield EccPublicKeyType, 'type'
        yield Opaque(self.field_size), 'x'
        if self.type == 'uncompressed':
            yield Opaque(self.field_size), 'y'


EccPublicKeyType = Enum(
    uint8, 'EccPublicKeyType',
    x_coordinate_only=0, compressed_lsb_y_0=2,
    compressed_lsb_y_1=3, uncompressed=4)


class Certificate(Struct):
    fields = ['version_and_type',
              'unsigned_certificate',
              'reconstruction_value',
              'signature']

    @property
    def verification_algorithm(self):
        if self.version_and_type == 2:
            return self.unsigned_certificate.verification_key.algorithm
        elif self.version_and_type == 3:
            return self.unsigned_certificate.signature_alg
        else:
            raise NotImplementedError(
                'Certificate.version_and_type %d' % self.version_and_type)

    def layout(self):
        yield uint8, 'version_and_type'
        yield ToBeSignedCertificate(
            version_and_type=self.version_and_type), 'unsigned_certificate'

        if self.version_and_type == 2:
            yield Signature(algorithm='ecdsa_nistp256_with_sha256'), 'signature'
        elif self.version_and_type == 3:
            signature_alg = self.verification_algorithm
            if signature_alg != 'ecdsa_nistp256_with_sha256':
                raise ValueError(
                    'Invalid signature algorithm %r' % signature_alg)
            yield EccPublicKey(field_size=32), 'reconstruction_value'
        else:
            raise NotImplementedError(
                'Certificate.version_and_type %d' % self.version_and_type)

    def certid8(self):
        return hashlib.sha256(self.pack()).hexdigest()[-16:]


class ToBeSignedCertificate(Struct):
    extern = ['version_and_type']
    fields = ['holder_type',
              'cf',
              'signer_id',
              'signature_alg',
              'scope',
              'start_validity',
              'lifetime',
              'expiration',
              'crl_series',
              'verification_key',
              'encryption_key']

    def layout(self):
        yield HolderType, 'holder_type'
        yield CertificateContentFlags, 'cf'

        if self.holder_type != 'root_ca':
            yield CertId8, 'signer_id'
            yield PKAlgorithm, 'signature_alg'

        yield CertSpecificData(holder_type=self.holder_type), 'scope'
        yield Time32, 'expiration'

        if 'use_start_validity' in self.cf:
            if 'lifetime_is_duration' in self.cf:
                yield CertificateDuration, 'lifetime'
            else:
                yield Time32, 'start_validity'

        yield CrlSeries, 'crl_series'
        if self.crl_series == 0 and self.expiration == 0:
            raise ValueError('Either crl_series or expiration must be nonzero')

        if self.version_and_type == 2:
            yield PublicKey, 'verification_key'
        # if version_and_type == 3 then do nothing
        elif self.version_and_type != 3:
            raise NotImplementedError(
                'version_and_type %s' % self.version_and_type)

        if 'encryption_key' in self.cf:
            yield PublicKey, 'encryption_key'


HolderType = Enum(
    uint8, 'HolderType',
    sde_anonymous=0,
    sde_identified_not_localized=1,
    sde_identified_localized=2,
    sde_csr=3,
    wsa=4,
    wsa_csr=5,
    sde_ca=6, wsa_ca=7, crl_signer=8,
    root_ca=255)


CertificateContentFlags = Flags(
    'CertificateContentFlags',
    use_start_validity=0, lifetime_is_duration=1,
    encryption_key=2)


class CertificateDuration(StaticType):
    units = ['seconds', 'minutes', 'hours', '60hours', 'years']
    _magnitude_bits = 13
    _magnitude_max = (1 << _magnitude_bits) - 1

    @classmethod
    def load(cls, stream):
        number = uint16.load(stream)
        magnitude = number & cls._magnitude_max
        units = cls.units[number >> cls._magnitude_bits]
        return magnitude, units

    @classmethod
    def dump(cls, stream, value):
        magnitude, units = value
        if magnitude > cls._magnitude_max:
            raise ValueError('CertificateDuration '
                             'magnitude %d too big' % magnitude)
        units = cls.units.index(units)
        number = (units << cls._magnitude_bits) | magnitude
        uint16.dump(stream, number)


class PsidSsp(Struct):
    layout = [
        (wsmp.Psid, 'psid'),
        (OpaqueVarArray, 'service_specific_permissions')]


class PsidSspArray(Struct):
    fields = ['type', 'permissions_list']

    def layout(self):
        yield ArrayType, 'type'
        if self.type == 'specified':
            yield VarArray(PsidSsp), 'permissions_list'


class IdentifiedNotLocalizedScope(Struct):
    layout = [
        (OpaqueVarArray, 'subject_name'),
        (PsidSspArray, 'permissions')]


RegionType = Enum(
    uint8, 'RegionType',
    from_issuer=0, circle=1, rectangle=2, polygon=3, none=4)


class GeographicRegion(Struct):
    fields = ['region_type']

    def layout(self):
        yield RegionType, 'region_type'
        if self.region_type not in ('none', 'from_issuer'):
            raise NotImplementedError('RegionType %r' % self.region_type)


class AnonymousScope(Struct):
    layout = [
        (OpaqueVarArray, 'additional_data'),
        (PsidSspArray, 'permissions'),
        (GeographicRegion, 'region')
        ]


class CertSpecificData(Struct):
    extern = ['holder_type']
    scopes = dict(
        sde_identified_not_localized=(
            IdentifiedNotLocalizedScope, 'idnonloc_scope'),
        sde_anonymous=(
            AnonymousScope, 'anonymous_scope'))
    fields = [name for _, name in scopes.values()]

    def layout(self):
        try:
            scope = self.scopes[self.holder_type]
        except KeyError:
            raise NotImplementedError('HolderType %r' % self.holder_type)
        else:
            yield scope


ArrayType = Enum(
    uint8, 'ArrayType',
    from_issuer=0, specified=1)


class PublicKey(Struct):
    fields = ['algorithm',
              'public_key',
              'supported_symm_alg']

    def layout(self):
        yield PKAlgorithm, 'algorithm'
        if self.algorithm == 'ecdsa_nistp224_with_sha224':
            yield EccPublicKey(field_size=28), 'public_key'
        elif self.algorithm == 'ecdsa_nistp256_with_sha256':
            yield EccPublicKey(field_size=32), 'public_key'
        else:
            raise NotImplementedError('PKAlgorithm %r' % self.algorithm)


#
# Utilities
#
NBITS_TO_GENERATOR = {
    224: ecdsa.generator_224,
    256: ecdsa.generator_256}
GENERATOR_TO_NBITS = dict((v, k) for k, v in NBITS_TO_GENERATOR.iteritems())


NONLEAP_SECONDS_FROM_1970JAN1_TO_2004JAN1 = 1072915200
TIME64_PER_TIME32 = 1000000
SECONDS_PER_YEAR = 31556925

# TODO: temp solution, valid until 2013-12-31T23:59:59Z (AT-1233)
LEAP_SECONDS_FROM_2004JAN1_TO_2013JAN1 = 3


def make_private_key(secret, p_number):
    """Make a private ECDSA key from an integer secret.
    """
    try:
        generator = NBITS_TO_GENERATOR[p_number]
    except KeyError:
        raise ValueError('Only P-224 or P-256 supported, got P-%d' % p_number)

    return ecdsa.Private_key(generator, secret)


def derive_public_key(private_key):
    """Make a public ECDSA key from a private key.

    @param private_key ecdsa.Private_key object
    """
    product = private_key.generator * private_key.secret_multiplier
    return ecdsa.Public_key(private_key.generator, product)


def export_key_cert_pair(prefix, key, cert_packed):
    with open('%s.key' % prefix, 'wb') as keyfile:
        nbytes = GENERATOR_TO_NBITS[key.generator] / 8
        keyfile.write(bin2hex(encode_int(key.secret_multiplier, nbytes)))

    with open('%s.cert' % prefix, 'wb') as certfile:
        certfile.write(bin2hex(cert_packed))


def time32(t=None):
    """Convert Unix time `t` to Time32.

    If `t` is None, convert current time to Time32.
    """
    if t is None:
        t = time.time()
    return int(round(t)) - NONLEAP_SECONDS_FROM_1970JAN1_TO_2004JAN1 + \
            LEAP_SECONDS_FROM_2004JAN1_TO_2013JAN1


def time32_to_tuple(t32):
    """Convert Time32 to GMT time tuple (cf. time.gmtime).
    """
    return time.gmtime(t32 + NONLEAP_SECONDS_FROM_1970JAN1_TO_2004JAN1 - \
            LEAP_SECONDS_FROM_2004JAN1_TO_2013JAN1)


def time32_to_str(t32):
    """Convert Time32 to GMT time string.
    """
    return time.strftime(ISO_TIME_FMT, time32_to_tuple(t32))


def time64_to_str(t64):
    """Convert Time64 to GMT time string.
    """
    t32 = t64 // TIME64_PER_TIME32
    return '%s.%06d' % (time32_to_str(t32), t64 % TIME64_PER_TIME32)


def time64_to_ts(t64):
    """Convert Time64 to Unix timestamp.
    """
    return (1e-6 * t64) + NONLEAP_SECONDS_FROM_1970JAN1_TO_2004JAN1 - \
            LEAP_SECONDS_FROM_2004JAN1_TO_2013JAN1


def ts_to_time64(ts):
    """Convert Unix timestamp to Time64.
    """
    return int(1e6 * (ts - NONLEAP_SECONDS_FROM_1970JAN1_TO_2004JAN1 + \
            LEAP_SECONDS_FROM_2004JAN1_TO_2013JAN1))

FAKE_PUBLIC_KEY_P224 = PublicKey(
    algorithm='ecdsa_nistp224_with_sha224',
    public_key=EccPublicKey(
        type='compressed_lsb_y_0',
        x='K' * 28))

FAKE_PUBLIC_KEY_P256 = PublicKey(
    algorithm='ecdsa_nistp256_with_sha256',
    public_key=EccPublicKey(
        type='compressed_lsb_y_0',
        x='K' * 32))

FAKE_CERTID8 = 'FAKE_ID8'.encode('hex')

FAKE_CERT_SIGNATURE = Signature(
    algorithm='ecdsa_nistp256_with_sha256',
    ecdsa_signature=EcdsaSignature(
        R=EccPublicKey(
            type='x_coordinate_only',
            x='R' * 32),
        s='S' * 32))


TEST_PRIVATE_KEY_224 = make_private_key(int('cafe' * 14, 16), 224)
TEST_PRIVATE_KEY_256 = make_private_key(int('cafe' * 16, 16), 256)

TEST_PRIVATE_KEYS = dict(
    p224=TEST_PRIVATE_KEY_224,
    p256=TEST_PRIVATE_KEY_256
    )

def make_simple_cert(name, validity=None, bits=256):
    """Make a simple fake certificate.

    @param name: string to be embedded in the certificate
    @param validity: Examples:
      * (None, None): Valid from Time32 0 until Time32 2^32-1
      * (None, 50): Valid from Time32 0, expires on Time32 50
      * (70, None): Valid from Time32 70 until Time32 2^32-1
      * (70, 100): Valid from Time32 70, expires on Time32 100
    """
    
    if bits == 224:
        key = FAKE_PUBLIC_KEY_P224
    else:
        key = FAKE_PUBLIC_KEY_P256
    
    cert = ToBeSignedCertificate(
        holder_type='sde_identified_not_localized',
        cf=set(),
        signer_id=FAKE_CERTID8,
        signature_alg='ecdsa_nistp256_with_sha256',
        scope=CertSpecificData(
            idnonloc_scope=IdentifiedNotLocalizedScope(
                subject_name=name,
                permissions=PsidSspArray(type='from_issuer'))),
        crl_series=1,
        verification_key=key)

    if validity is None:
        start, end = None, None
    else:
        start, end = validity

    if end is None:
        # Non-expiring certificate
        cert.expiration = 0
    else:
        if end <= start:
            raise ValueError('Validity interval %r is empty' % validity)
        cert.expiration = end

    if start is not None:
        cert.cf.add('use_start_validity')
        cert.start_validity = start

    return Certificate(
        version_and_type=2,
        unsigned_certificate=cert,
        signature=FAKE_CERT_SIGNATURE)


# Anonymous OBU message certificate #1 from USDOT VAD project
USDOT_CERT_ANON_HEX = """
03 00 03 2a 48 0a f3 5d bb 43 5a 01 12 aa aa aa aa bb bb bb bb cc cc cc cc cc cc
cc cc cc cc 01 02 20 00 04 0e bb d4 a8 01 4a 00 00 00 01 03 8f 32 c8 58 03 30 2c
2d 3d b7 33 44 9d 0b fa ba a2 3f 7f 4c a0 3f ec e3 4e e5 46 a1 aa a6 d2 d5
"""

# Expiration time of above certificate
USDOT_CERT_ANON_EXPIRATION = 247190696
