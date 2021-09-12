#!/usr/bin/python3

import sys
from socket import socket, AF_INET, SOCK_DGRAM
from struct import pack, unpack
from rsclib.autosuper import autosuper

class Protocol_Element :
    """ A single protocol element to be parsed from binary format or
        serialized to binary format.
    """

    def __init__ (self, value) :
        self.value = value
    # end def __init__

    @classmethod
    def deserialize (cls, bytes, length = 0) :
        raise NotImplementedError ("Needs to be define in sub-class")
    # end def deserialize

    def serialize (self) :
        raise NotImplementedError ("Needs to be define in sub-class")
    # end def serialize

    @property
    def serialization_size (self) :
        raise NotImplementedError ("Needs to be define in sub-class")
    # end def serialization_size

# end class Protocol_Element

class UTF8_String (Protocol_Element) :
    """ An UTF-8 string consisting of a length and the string
        Special case is a null string (different from an empty string)
        which encodes the length as 0xffffffff
    >>> v = UTF8_String.deserialize (b'\\x00\\x00\\x00\\x04abcd')
    >>> v.value
    'abcd'
    >>> v.serialize ()
    b'\\x00\\x00\\x00\\x04abcd'
    >>> s = UTF8_String (None)
    >>> s.serialize ()
    b'\\xff\\xff\\xff\\xff'
    """

    @classmethod
    def deserialize (cls, bytes, length = 0) :
        offset = 4
        length = unpack ('!L', bytes [:offset]) [0]
        # Special case empty (None?) string
        if length == 0xFFFFFFFF :
            value = None
            return cls (value)
        value  = unpack ('%ds' % length, bytes [offset:offset+length]) [0]
        return cls (value.decode ('utf-8'))
    # end def deserialize

    def serialize (self) :
        if self.value is None :
            return pack ('!L', 0xFFFFFFFF)
        length = len (self.value)
        value  = self.value.encode ('utf-8')
        return pack ('!L', length) + pack ('%ds' % length, value)
    # end def serialize

    @property
    def serialization_size (self) :
        if self.value is None :
            return 4
        return 4 + len (self.value.encode ('utf-8'))
    # end def serialization_size

# end class UTF8_String

class Optional_Quint (Protocol_Element) :
    """ A quint which is optional, length in deserialize is used
        We encode a missing value as None
    """

    formats = dict \
        (( (1, '!B')
        ,  (4, '!L')
        ,  (8, '!Q')
        ))

    @classmethod
    def deserialize (cls, bytes, length = 1) :
        if len (bytes) == 0 :
            value = None
        else :
            value = unpack (self.formats [length], bytes) [0]
        object = cls (value)
        object.size = length
        if value is None :
            object.size = 0
        return object
    # end def deserialize

    def serialize (self) :
        if self.value is None :
            return b''
        return pack (self.formats [self.size], self.value)
    # end def serialize

    @property
    def serialization_size (self) :
        if self.value is None :
            return 0
        return self.size
    # end def serialization_size

# end class Optional_Quint

class QDateTime (Protocol_Element) :
    """ A QT DateTime object
        The case with a timezone is not used
    """

    def __init__ (self, date, time, timespec, offset = None) :
        self.date     = date
        self.time     = time
        self.timespec = timespec
        self.offset   = offset
        assert self.offset is None or self.timespec == 2
        if self.timespec == 2 and self.offset is not None :
            raise ValueError ("Offset required when timespec=2")
    # end def __init__

    @classmethod
    def deserialize (cls, bytes, length = 0) :
        date, time, timespec = unpack ('!qLB', bytes [:13])
        offset = None
        if timespec == 2 :
            offset = unpack ('!l', bytes [13:17]) [0]
        return cls (date, time, timespec, offset)
    # end def deserialize

    def serialize (self) :
        r = [pack ('!qLB', self.date, self.time, self.timespec)]
        if self.offset is not None :
            r.append (pack ('!l', self.offset))
        return b''.join (r)
    # end def serialize

    @property
    def serialization_size (self) :
        if self.offset is None :
            return 13
        return 13 + 4
    # end def serialization_size

    @property
    def value (self) :
        return self
    # end def value

    def __str__ (self) :
        s = ( 'QDatTime(date=%(date)s time=%(time)s '
            + 'timespec=%(timespec)s offset=%(offset)s)'
            )
        return s % self.__dict__
    # end def __str__
    __repr__ = __str__

# end class QDateTime

class QColor (Protocol_Element) :
    """ A QT color object
        We support only RGB type or invalid
    """

    fmt          = '!BHHHHH'
    spec_rgb     = 1
    spec_invalid = 0
    cmax         = 0xFFFF
    serialization_size = 11

    def __init__ \
        (self, red = 0, green = 0, blue = 0, alpha = cmax, spec = spec_rgb) :
        self.spec     = spec
        self.red      = red
        self.green    = green
        self.blue     = blue
        self.alpha    = alpha
    # end def __init__

    @classmethod
    def deserialize (cls, bytes, length = 0) :
        b = bytes [:cls.serialization_size]
        spec, alpha, red, green, blue, dummy = unpack (cls.fmt, b)
        return cls (spec, alpha, red, green, blue)
    # end def deserialize

    def serialize (self) :
        return pack \
            ( self.fmt
            , self.spec
            , self.alpha
            , self.red
            , self.green
            , self.blue
            , 0
            )
    # end def serialize

    @property
    def value (self) :
        return self
    # end def value

    def __str__ (self) :
        if self.spec != self.spec_rgb :
            return 'QColor(Invalid)'
        s = ( 'QColor(alpha=%(alpha)s, red=%(red)s, '
            + 'green=%(green)s, blue=%(blue)s)'
            )
        return s % self.__dict__
    # end def __str__
    __repr__ = __str__

# end class QColor
color_red   = QColor (red = QColor.cmax)
color_green = QColor (green = QColor.cmax)
color_blue  = QColor (blue = QColor.cmax)
color_white = QColor (QColor.cmax, QColor.cmax, QColor.cmax)
color_black = QColor ()

# Shortcuts for used data types, also for consistency
quint8     = ('!B', 1)
quint32    = ('!L', 4)
quint64    = ('!Q', 8)
qint32     = ('!l', 4)
qbool      = quint8
qutf8      = (UTF8_String, 0)
qdouble    = ('!d', 8)
opt_quint8 = (Optional_Quint, 1)
qtime      = quint32
qdatetime  = (QDateTime, 0)
qcolor     = (QColor, 0)

statusmsg = b'\xad\xbc\xcb\xda\x00\x00\x00\x02\x00\x00\x00\x01\x00\x00\x00\x14WSJT-X - TS590S-klbg\x00\x00\x00\x00\x00k\xf0\xd0\x00\x00\x00\x03FT8\x00\x00\x00\x06XAMPLE\x00\x00\x00\x02-2\x00\x00\x00\x03FT8\x00\x00\x01\x00\x00\x02\xcb\x00\x00\x04n\x00\x00\x00\x06OE3RSU\x00\x00\x00\x06JN88DG\x00\x00\x00\x04JO21\x00\xff\xff\xff\xff\x00\x00\xff\xff\xff\xff\xff\xff\xff\xff\x00\x00\x00\x0bTS590S-klbg\x00\x00\x00%XAMPLE OE3RSU 73                     '
clearmsg = b'\xad\xbc\xcb\xda\x00\x00\x00\x03\x00\x00\x00\x03\x00\x00\x00\x14WSJT-X - TS590S-klbg'

class WSJTX_Telegram (autosuper) :
    """ Base class of WSJTX Telegram
        Note that we a list of (name, format, len) tuples as the format
        specification. The name is the name of the variable, the format
        is either a struct.pack compatible format specifier or an
        instance of Protocol_Element which knows how to deserialize (or
        serialize) itself. The len is the length to parse from the
        string. If 0 the Protocol_Element will know its serialization
        size.
    >>> WSJTX_Telegram.from_bytes (statusmsg)
    Status dial_frq=7074000 mode=FT8 dx_call=XAMPLE report=-2 tx_mode=FT8 tx_enabled=0 xmitting=0 decoding=1 rx_df=715 tx_df=1134 de_call=OE3RSU de_grid=JN88DG dx_grid=JO21 tx_watchdog=0 sub_mode=None fast_mode=0 special_op=0 frq_tolerance=4294967295 t_r_period=4294967295 config_name=TS590S-klbg tx_message=XAMPLE OE3RSU 73
    >>> WSJTX_Telegram.from_bytes (clearmsg)
    Clear window=None
    """

    schema_version_number = 3
    magic  = 0xadbccbda
    type   = None
    format = \
        ( ('magic',          quint32)
        , ('version_number', quint32)
        , ('type',           quint32)
        , ('id',             qutf8)
        )
    defaults = dict (magic = magic, type = type)

    # Individual telegrams register here:
    type_registry = {}

    def __init__ (self, version_number, id, **kw) :
        params = {}
        params.update (self.defaults)
        params.update (kw)
        assert params ['magic'] == self.magic
        assert self.schema_version_number >= version_number
        self.version_number = version_number
        self.id             = id
        # Thats for sub-classes, they have their own format
        for name, (a, b) in self.format :
            if name in ('version_number', 'id') :
                continue
            setattr (self, name, params [name])
        if self.__class__.type is not None :
            assert self.__class__.type == self.type
        self.__super.__init__ (** kw)
    # end def __init__

    @classmethod
    def from_bytes (cls, bytes) :
        kw   = cls.deserialize (bytes)
        type = kw ['type']
        self = cls (** kw)
        if type in cls.type_registry :
            c = cls.type_registry [type]
            kw.update (c.deserialize (bytes [self.serialization_size:]))
            return c (** kw)
        else :
            return self
    # end def from_bytes

    @classmethod
    def deserialize (cls, bytes) :
        b  = bytes
        kw = {}
        for name, (format, length) in cls.format :
            if isinstance (format, type ('')) :
                kw [name] = unpack (format, b [:length]) [0]
                b = b [length:]
            else :
                value = format.deserialize (b, length)
                b = b [value.serialization_size:]
                kw [name] = value.value
        return kw
    # end def deserialize

    def as_bytes (self) :
        r = []
        fmt = []
        # Get all the format attributes of base classes
        for cls in reversed (self.__class__.mro ()) :
            f = getattr (cls, 'format', None)
            if f :
                fmt.extend (f)
        for name, (format, length) in fmt :
            v = getattr (self, name)
            if isinstance (v, Protocol_Element) :
                r.append (v.serialize ())
            elif isinstance (format, type ('')) :
                r.append (pack (format, v))
            else :
                r.append (format (v).serialize ())
        return b''.join (r)
    # end def as_bytes

    def __str__ (self) :
        r = [self.__class__.__name__.split ('_', 1) [-1]]
        for n, (fmt, length) in self.format :
            r.append ('%s=%s' % (n, getattr (self, n)))
        return ' '.join (r)
    # end def __str__
    __repr__ = __str__

    @property
    def serialization_size (self) :
        return 16 + len (self.id.encode ('utf-8'))
    # end def serialization_size

# end class WSJTX_Telegram

class WSJTX_Heartbeat (WSJTX_Telegram) :

    type   = 0

    format = \
        ( ('max_schema',     quint32)
        , ('version',        qutf8)
        , ('revision',       qutf8)
        )
# end class WSJTX_Heartbeat
WSJTX_Telegram.type_registry [WSJTX_Heartbeat.type] = WSJTX_Heartbeat

class WSJTX_Status (WSJTX_Telegram) :

    type   = 1
    format = \
        ( ('dial_frq',       quint64)
        , ('mode',           qutf8)
        , ('dx_call',        qutf8)
        , ('report',         qutf8)
        , ('tx_mode',        qutf8)
        , ('tx_enabled',     qbool)
        , ('xmitting',       qbool)
        , ('decoding',       qbool)
        , ('rx_df',          quint32)
        , ('tx_df',          quint32)
        , ('de_call',        qutf8)
        , ('de_grid',        qutf8)
        , ('dx_grid',        qutf8)
        , ('tx_watchdog',    qbool)
        , ('sub_mode',       qutf8)
        , ('fast_mode',      qbool)
        , ('special_op',     quint8)
        , ('frq_tolerance',  quint32)
        , ('t_r_period',     quint32)
        , ('config_name',    qutf8)
        , ('tx_message',     qutf8)
        )

# end class WSJTX_Status
WSJTX_Telegram.type_registry [WSJTX_Status.type] = WSJTX_Status

class WSJTX_Decode (WSJTX_Telegram) :

    type   = 2
    format = \
        ( ('is_new',         qbool)
        , ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('delta_f',        quint32)
        , ('mode',           qutf8)
        , ('message',        qutf8)
        , ('low_confidence', qbool)
        , ('off_air',        qbool)
        )

# end class WSJTX_Decode
WSJTX_Telegram.type_registry [WSJTX_Decode.type] = WSJTX_Decode

class WSJTX_Clear (WSJTX_Telegram) :

    type   = 3
    format = \
        ( ('window',         opt_quint8)
        ,
        )
    defaults = dict (WSJTX_Telegram.defaults)
    defaults.update (window = None)

# end class WSJTX_Clear
WSJTX_Telegram.type_registry [WSJTX_Clear.type] = WSJTX_Clear

class WSJTX_Reply (WSJTX_Telegram) :

    type   = 4
    format = \
        ( ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('delta_f',        quint32)
        , ('mode',           qutf8)
        , ('message',        qutf8)
        , ('low_confidence', qbool)
        , ('modifiers',      quint8)
        )

# end class WSJTX_Reply
WSJTX_Telegram.type_registry [WSJTX_Reply.type] = WSJTX_Reply

class WSJTX_QSO_Logged (WSJTX_Telegram) :

    type   = 5
    format = \
        ( ('time_off',       qdatetime)
        , ('dx_call',        qutf8)
        , ('dx_grid',        qutf8)
        , ('tx_frq',         quint64)
        , ('mode',           qutf8)
        , ('report_sent',    qutf8)
        , ('report_recv',    qutf8)
        , ('tx_power',       qutf8)
        , ('comments',       qutf8)
        , ('name',           qutf8)
        , ('time_on',        qdatetime)
        , ('operator_call',  qutf8)
        , ('my_call',        qutf8)
        , ('my_grid',        qutf8)
        , ('exchange_sent',  qutf8)
        , ('exchange_recv',  qutf8)
        , ('adif_propmode',  qutf8)
        )

# end class WSJTX_QSO_Logged
WSJTX_Telegram.type_registry [WSJTX_QSO_Logged.type] = WSJTX_QSO_Logged

class WSJTX_Close (WSJTX_Telegram) :

    type   = 6
    format = ()

# end class WSJTX_Close
WSJTX_Telegram.type_registry [WSJTX_Close.type] = WSJTX_Close

class WSJTX_Replay (WSJTX_Telegram) :

    type   = 7
    format = ()

# end class WSJTX_Replay
WSJTX_Telegram.type_registry [WSJTX_Replay.type] = WSJTX_Replay

class WSJTX_Halt_TX (WSJTX_Telegram) :

    type   = 8
    format = \
        ( ('auto_tx_only',   qbool)
        ,
        )

# end class WSJTX_Halt_TX
WSJTX_Telegram.type_registry [WSJTX_Halt_TX.type] = WSJTX_Halt_TX

class WSJTX_Free_Text (WSJTX_Telegram) :

    type   = 9
    format = \
        ( ('text',   qutf8)
        , ('send',   qbool)
        )
    defaults = dict (WSJTX_Telegram.defaults)
    defaults.update (send = False)

# end class WSJTX_Free_Text
WSJTX_Telegram.type_registry [WSJTX_Free_Text.type] = WSJTX_Free_Text

class WSJTX_WSPR_Decode (WSJTX_Telegram) :

    type   = 10
    format = \
        ( ('is_new',         qbool)
        , ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('frq',            quint64)
        , ('drift',          qint32)
        , ('callsign',       qutf8)
        , ('grid',           qutf8)
        , ('power',          qint32)
        , ('off_air',        qbool)
        )

# end class WSJTX_WSPR_Decode
WSJTX_Telegram.type_registry [WSJTX_WSPR_Decode.type] = WSJTX_WSPR_Decode

class WSJTX_Location (WSJTX_Telegram) :

    type   = 11
    format = \
        ( ('location',   qutf8)
        ,
        )

# end class WSJTX_Location
WSJTX_Telegram.type_registry [WSJTX_Location.type] = WSJTX_Location

class WSJTX_Logged_ADIF (WSJTX_Telegram) :

    type   = 12
    format = \
        ( ('adif_txt',   qutf8)
        ,
        )

# end class WSJTX_Logged_ADIF
WSJTX_Telegram.type_registry [WSJTX_Logged_ADIF.type] = WSJTX_Logged_ADIF

class WSJTX_Highlight_Call (WSJTX_Telegram) :
    """ Highlight a callsign in WSJTX
    >>> kw = dict (id = 'test', version_number = 2)
    >>> whc = WSJTX_Highlight_Call \\
    ...     ( callsign = 'OE3RSU'
    ...     , bg_color = color_white
    ...     , fg_color = color_red
    ...     , highlight_last = 1
    ...     , **kw
    ...     )
    >>> b = whc.as_bytes ()
    >>> WSJTX_Telegram.from_bytes (b)
    Highlight_Call callsign=OE3RSU bg_color=QColor(alpha=65535, red=65535, green=65535, blue=65535) fg_color=QColor(alpha=65535, red=65535, green=0, blue=0) highlight_last=1
    """

    type   = 13
    format = \
        ( ('callsign',       qutf8)
        , ('bg_color',       qcolor)
        , ('fg_color',       qcolor)
        , ('highlight_last', qbool)
        )
    defaults = dict (WSJTX_Telegram.defaults)
    defaults.update (highlight_last = False)

# end class WSJTX_Highlight_Call
WSJTX_Telegram.type_registry [WSJTX_Highlight_Call.type] = WSJTX_Highlight_Call

class WSJTX_Switch_Config (WSJTX_Telegram) :

    type   = 14
    format = \
        ( ('adif_txt',   qutf8)
        ,
        )

# end class WSJTX_Switch_Config
WSJTX_Telegram.type_registry [WSJTX_Switch_Config.type] = WSJTX_Switch_Config

class WSJTX_Configure (WSJTX_Telegram) :

    type   = 15
    format = \
        ( ('mode',           qutf8)
        , ('frq_tolerance',  quint32)
        , ('sub_mode',       qutf8)
        , ('fast_mode',      qbool)
        , ('t_r_period',     quint32)
        , ('rx_df',          quint32)
        , ('dx_call',        qutf8)
        , ('dx_grid',        qutf8)
        , ('gen_messages',   qbool)
        )

# end class WSJTX_Configure
WSJTX_Telegram.type_registry [WSJTX_Configure.type] = WSJTX_Configure

class UDP_Connector :

    def __init__ (self, ip = '127.0.0.1', port = 2237, id = 'wsjt-server') :
        self.socket = socket (AF_INET, SOCK_DGRAM)
        self.ip   = ip
        self.port = port
        self.socket.bind ((self.ip, self.port))
        self.peer = {}
        self.adr  = None
        self.id   = id
    # end def __init__

    def color (self, callsign, fg_color = color_red, bg_color = color_white) :
        kw = dict (id = self.id, version_number = 3)
        tel = WSJTX_Highlight_Call \
            ( callsign = callsign
            , bg_color = bg_color
            , fg_color = fg_color
            , **kw
            )
        self.socket.sendto (tel.as_bytes (), self.adr)
    # end def color

    def heartbeat (self) :
        kw = dict (id = self.id, version_number = 3)
        tel = WSJTX_Heartbeat \
            ( max_schema = 3
            , version    = '4711'
            , revision   = ''
            , **kw
            )
        self.socket.sendto (tel.as_bytes (), self.adr)
    # end def heartbeat

    def receive (self) :
        bytes, address = self.socket.recvfrom (4096)
        tel = WSJTX_Telegram.from_bytes (bytes)
        if tel.id not in self.peer :
            self.peer [tel.id] = address
        if not self.adr :
            self.adr = address
        return tel
    # end def receive

    def set_peer (self, peername) :
        if peername in self.peer :
            self.adr = self.peer [peername]
    # end def set_peer

# end class UDP_Connector

def main () :
    uc = UDP_Connector ()
    n  = 0
    while 1 :
        tel = uc.receive ()
        n -= 1
        if n < 0 :
            n = 20
            uc.heartbeat ()
        if not isinstance (tel, (WSJTX_Decode, WSJTX_Status)):
            print (tel)
        if isinstance (tel, WSJTX_Status) :
            uc.color (sys.argv [1])
# end def main

if __name__ == '__main__' :
    main ()
