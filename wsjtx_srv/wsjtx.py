#!/usr/bin/python3

import sys
import io
import re
import os
import atexit
from socket            import socket, AF_INET, SOCK_DGRAM
from struct            import pack, unpack
from argparse          import ArgumentParser
from rsclib.autosuper  import autosuper
from hamradio.adif     import ADIF
from hamradio.cty      import CTY_DXCC
from hamradio.bandplan import bandplan_austria
from hamradio.dbimport import ADIF_Uploader, urlencode

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
        s, a, r, g, b, dummy = unpack (cls.fmt, b)
        return cls (spec = s, alpha = a, red = r, green = g, blue = b)
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
color_red      = QColor (red = QColor.cmax)
color_green    = QColor (green = QColor.cmax)
color_blue     = QColor (blue = QColor.cmax)
color_white    = QColor (QColor.cmax, QColor.cmax, QColor.cmax)
color_black    = QColor ()
color_cyan     = QColor (0, 0xFFFF, 0xFFFF)
color_cyan1    = QColor (0x9999, 0xFFFF, 0xFFFF)
color_pink     = QColor (0xFFFF, 0, 0xFFFF)
color_pink1    = QColor (0xFFFF, 0xAAAA, 0xFFFF)
color_orange   = QColor (0xFFFF, 0xA0A0, 0x0000)

color_invalid  = QColor (spec = QColor.spec_invalid)
ctuple_invalid = (color_invalid, color_invalid)

# defaults (fg color, bg color)
ctuple_wbf           = ctuple_invalid
ctuple_dxcc          = (color_black,   color_pink)
ctuple_dxcc_band     = (color_black,   color_pink1)
ctuple_new_call      = (color_black,   color_cyan)
ctuple_new_call_band = (color_black,   color_cyan1)
ctuple_highlight     = (color_black,   color_orange)


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
        [ ('magic',          quint32)
        , ('version_number', quint32)
        , ('type',           quint32)
        , ('id',             qutf8)
        ]
    defaults = dict (magic = magic, version_number = 3, id = 'wsjt-server')
    suppress = dict.fromkeys (('magic', 'version_number', 'id', 'type'))

    # Individual telegrams register here:
    type_registry = {}

    def __init__ (self, **kw) :
        params = {}
        params.update (self.defaults)
        params.update (kw)
        if 'type' not in params :
            params ['type'] = self.type
        assert params ['magic'] == self.magic
        assert self.schema_version_number >= params ['version_number']
        # Thats for sub-classes, they have their own format
        for name, (a, b) in self.format :
            setattr (self, name, params [name])
        if self.__class__.type is not None :
            assert self.__class__.type == self.type
        self.__super.__init__ (** params)
    # end def __init__

    @classmethod
    def from_bytes (cls, bytes) :
        kw   = cls.deserialize (bytes)
        type = kw ['type']
        self = cls (** kw)
        if type in cls.type_registry :
            c = cls.type_registry [type]
            kw.update (c.deserialize (bytes))
            return c (** kw)
        else :
            return self
    # end def from_bytes

    @classmethod
    def deserialize (cls, bytes) :
        b  = bytes
        kw = {}
        for name, (format, length) in cls.format :
            # Due to compatibility reasons new message fields are added to
            # the end of the messsage. The buffer is empty when the message
            # is older format and a field is missing.
            if (len(b) == 0):
                kw[name] = None
                continue
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
        for name, (fmt, length) in self.format :
            v = getattr (self, name)
            if isinstance (v, Protocol_Element) :
                r.append (v.serialize ())
            elif isinstance (fmt, type ('')) :
                r.append (pack (fmt, v))
            else :
                r.append (fmt (v).serialize ())
        return b''.join (r)
    # end def as_bytes

    def __str__ (self) :
        r = [self.__class__.__name__.split ('_', 1) [-1]]
        for n, (fmt, length) in self.format :
            if n not in self.suppress :
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

    format = WSJTX_Telegram.format + \
        [ ('max_schema',     quint32)
        , ('version',        qutf8)
        , ('revision',       qutf8)
        ]
    defaults = dict \
        ( max_schema = 3
        , version    = ''
        , revision   = ''
        , ** WSJTX_Telegram.defaults
        )
# end class WSJTX_Heartbeat
WSJTX_Telegram.type_registry [WSJTX_Heartbeat.type] = WSJTX_Heartbeat

class WSJTX_Status (WSJTX_Telegram) :

    type   = 1
    format = WSJTX_Telegram.format + \
        [ ('dial_frq',       quint64)
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
        ]

# end class WSJTX_Status
WSJTX_Telegram.type_registry [WSJTX_Status.type] = WSJTX_Status

class WSJTX_Decode (WSJTX_Telegram) :

    type   = 2
    format = WSJTX_Telegram.format + \
        [ ('is_new',         qbool)
        , ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('delta_f',        quint32)
        , ('mode',           qutf8)
        , ('message',        qutf8)
        , ('low_confidence', qbool)
        , ('off_air',        qbool)
        ]

# end class WSJTX_Decode
WSJTX_Telegram.type_registry [WSJTX_Decode.type] = WSJTX_Decode

class WSJTX_Clear (WSJTX_Telegram) :

    type     = 3
    format   = WSJTX_Telegram.format + [('window', opt_quint8)]
    defaults = dict (window = None, **WSJTX_Telegram.defaults)

# end class WSJTX_Clear
WSJTX_Telegram.type_registry [WSJTX_Clear.type] = WSJTX_Clear

class WSJTX_Reply (WSJTX_Telegram) :

    type   = 4
    format = WSJTX_Telegram.format + \
        [ ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('delta_f',        quint32)
        , ('mode',           qutf8)
        , ('message',        qutf8)
        , ('low_confidence', qbool)
        , ('modifiers',      quint8)
        ]

# end class WSJTX_Reply
WSJTX_Telegram.type_registry [WSJTX_Reply.type] = WSJTX_Reply

class WSJTX_QSO_Logged (WSJTX_Telegram) :

    type   = 5
    format = WSJTX_Telegram.format + \
        [ ('time_off',       qdatetime)
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
        ]

# end class WSJTX_QSO_Logged
WSJTX_Telegram.type_registry [WSJTX_QSO_Logged.type] = WSJTX_QSO_Logged

class WSJTX_Close (WSJTX_Telegram) :

    type   = 6

# end class WSJTX_Close
WSJTX_Telegram.type_registry [WSJTX_Close.type] = WSJTX_Close

class WSJTX_Replay (WSJTX_Telegram) :

    type   = 7

# end class WSJTX_Replay
WSJTX_Telegram.type_registry [WSJTX_Replay.type] = WSJTX_Replay

class WSJTX_Halt_TX (WSJTX_Telegram) :

    type   = 8
    format = WSJTX_Telegram.format + [('auto_tx_only', qbool)]

# end class WSJTX_Halt_TX
WSJTX_Telegram.type_registry [WSJTX_Halt_TX.type] = WSJTX_Halt_TX

class WSJTX_Free_Text (WSJTX_Telegram) :

    type   = 9
    format = WSJTX_Telegram.format + \
        [ ('text',   qutf8)
        , ('send',   qbool)
        ]
    defaults = dict (send = False, **WSJTX_Telegram.defaults)

# end class WSJTX_Free_Text
WSJTX_Telegram.type_registry [WSJTX_Free_Text.type] = WSJTX_Free_Text

class WSJTX_WSPR_Decode (WSJTX_Telegram) :

    type   = 10
    format = WSJTX_Telegram.format + \
        [ ('is_new',         qbool)
        , ('time',           qtime)
        , ('snr',            qint32)
        , ('delta_t',        qdouble)
        , ('frq',            quint64)
        , ('drift',          qint32)
        , ('callsign',       qutf8)
        , ('grid',           qutf8)
        , ('power',          qint32)
        , ('off_air',        qbool)
        ]

# end class WSJTX_WSPR_Decode
WSJTX_Telegram.type_registry [WSJTX_WSPR_Decode.type] = WSJTX_WSPR_Decode

class WSJTX_Location (WSJTX_Telegram) :

    type   = 11
    format = WSJTX_Telegram.format + [('location', qutf8)]

# end class WSJTX_Location
WSJTX_Telegram.type_registry [WSJTX_Location.type] = WSJTX_Location

class WSJTX_Logged_ADIF (WSJTX_Telegram) :

    type   = 12
    format = WSJTX_Telegram.format + [('adif_txt', qutf8)]

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
    format = WSJTX_Telegram.format + \
        [ ('callsign',       qutf8)
        , ('bg_color',       qcolor)
        , ('fg_color',       qcolor)
        , ('highlight_last', qbool)
        ]
    defaults = dict \
        ( fg_color       = color_black
        , bg_color       = color_white
        , highlight_last = False
        , ** WSJTX_Telegram.defaults
        )

# end class WSJTX_Highlight_Call
WSJTX_Telegram.type_registry [WSJTX_Highlight_Call.type] = WSJTX_Highlight_Call

class WSJTX_Switch_Config (WSJTX_Telegram) :

    type   = 14
    format = WSJTX_Telegram.format + [('adif_txt', qutf8)]

# end class WSJTX_Switch_Config
WSJTX_Telegram.type_registry [WSJTX_Switch_Config.type] = WSJTX_Switch_Config

class WSJTX_Configure (WSJTX_Telegram) :

    type   = 15
    format = WSJTX_Telegram.format + \
        [ ('mode',           qutf8)
        , ('frq_tolerance',  quint32)
        , ('sub_mode',       qutf8)
        , ('fast_mode',      qbool)
        , ('t_r_period',     quint32)
        , ('rx_df',          quint32)
        , ('dx_call',        qutf8)
        , ('dx_grid',        qutf8)
        , ('gen_messages',   qbool)
        ]

# end class WSJTX_Configure
WSJTX_Telegram.type_registry [WSJTX_Configure.type] = WSJTX_Configure

class UDP_Connector :

    def __init__ (self, wbf, ip = '127.0.0.1', port = 2237, id = None) :
        self.band    = None
        self.ip      = ip
        self.port    = port
        self.socket  = socket (AF_INET, SOCK_DGRAM)
        self.wbf     = wbf
        self.args    = getattr (wbf, 'args', None)
        self.peer    = {}
        self.adr     = None
        self.id      = id
        self.dx_call = None
        self.socket.bind ((self.ip, self.port))
        if id is None :
            self.id = WSJTX_Telegram.defaults ['id']
        self.heartbeat_seen = False
        self.color_by_call  = {}
        self.pending_color  = {}
        # Register atexit handler for cleanup
        atexit.register (self.cleanup)
    # end def __init__

    def cleanup (self) :
        self.decolor ()
        self.perform_pending_changes ()
    # end def cleanup

    def color (self, callsign, **kw) :
        tel = WSJTX_Highlight_Call (callsign = callsign, **kw)
        self.socket.sendto (tel.as_bytes (), self.adr)
    # end def color

    def decolor (self) :
        """ Remove all coloring
            Needed on band change and when exiting
            Note that this only schedules the changes.
        """
        for call in self.color_by_call :
            # Can save some time not considering uncolored calls
            if self.color_by_call [call] != ctuple_invalid :
                self.pending_color [call] = ctuple_invalid
        self.color_by_call = {}
    # end def decolor

    def handle (self, tel) :
        """ Handle given telegram.
            We send a heartbeat whenever we receive one.
            In addition we parse Decode messages, extract the call sign
            and determine worked-before and coloring.
        """
        if not self.heartbeat_seen or isinstance (tel, WSJTX_Heartbeat) :
            self.heartbeat ()
        if isinstance (tel, WSJTX_Status) :
            self.handle_status (tel)
        if isinstance (tel, WSJTX_Decode) :
            self.handle_decode (tel)
        if isinstance (tel, WSJTX_Logged_ADIF) :
            self.handle_logged (tel)
        if isinstance (tel, WSJTX_Close) :
            self.handle_close (tel)
    # end def handle

    def handle_close (self, tel) :
        """ Just exit when wsjtx exits
        """
        assert self.peer [tel.id] == self.adr
        sys.exit (0)
    # end def handle_close

    def handle_decode (self, tel) :
        if tel.off_air or not tel.is_new :
            return
        call  = self.parse_message (tel) or ''
        call  = call.lstrip ('<').rstrip ('>')
        if not call or call == '...' :
            return
        color = self.wbf.lookup_color (self.band, call)
        if call in self.color_by_call :
            if self.color_by_call [call] != color :
                self.update_color (call, color)
        else :
            self.update_color (call, color)
    # end def handle_decode

    def handle_logged (self, tel) :
        """ Handle a Log event when a QSO is logged.
            We directly receive ADIF from WSJTX
        """
        adif = ADIF (io.StringIO (tel.adif_txt))
        assert len (adif.records) == 1
        rec = adif.records [0]
        self.wbf.add_entry (rec)
    # end def handle_logged

    def handle_status (self, tel) :
        """ Handle pending coloring
        """
        band = bandplan_austria.lookup (tel.dial_frq)
        if self.band != band.name :
            self.band = band.name
            # Invalidate all colors on band change
            self.decolor ()
        if self.dx_call != tel.dx_call :
            self.dx_call = tel.dx_call
            if self.args.set_locator_msg :
                t = '<%s> <%s> 597373 %s' \
                  % (self.dx_call, self.args.callsign, self.args.locator)
                stel = WSJTX_Free_Text (text = t)
                self.socket.sendto (stel.as_bytes (), self.adr)
                print ('Set free text to "%s"' % t)
        if not tel.decoding :
            self.perform_pending_changes ()
    # end def handle_status

    def heartbeat (self, **kw) :
        tel = WSJTX_Heartbeat (version = '4711', **kw)
        self.socket.sendto (tel.as_bytes (), self.adr)
    # end def heartbeat

    # Some regexes for matching
    re_report = re.compile (r'[R]?[-+][0-9]{2}')
    re_loc    = re.compile (r'[A-Z]{2}[0-9]{2}')
    re_call   = re.compile \
        (r'(([A-Z])|([A-Z][A-Z0-9])|([0-9][A-Z]))[0-9][A-Z]{1,3}')

    def is_locator (self, s) :
        """ Check if s is a locator
        >>> u = UDP_Connector (port = 4711, wbf = None)
        >>> u.is_locator ('-2')
        False
        >>> u.is_locator ('JN88')
        True
        >>> u.is_locator ('kk77')
        False
        >>> u.socket.close ()
        """
        return bool (self.re_loc.match (s))
    # end def is_locator

    def is_report (self, s) :
        """ Check if s is a report
        >>> u = UDP_Connector (port = 4711, wbf = None)
        >>> u.is_report ('-2')
        False
        >>> u.is_report ('-02')
        True
        >>> u.is_report ('+20')
        True
        >>> u.is_report ('R+20')
        True
        >>> u.socket.close ()
        """
        return bool (self.re_report.match (s))
    # end def is_locator

    def is_stdcall (self, s) :
        """ Check if s is a standard callsign
        >>> u = UDP_Connector (port = 4711, wbf = None)
        >>> u.is_stdcall ('D1X')
        True
        >>> u.is_stdcall ('JN88')
        False
        >>> u.is_stdcall ('OE3RSU')
        True
        >>> u.socket.close ()
        """
        return bool (self.re_call.match (s))
    # end def is_stdcall

    def parse_message (self, tel) :
        """ Parse the message property of a decode which includes the
            callsign(s). Note that we try to use only the second
            (sender) callsign.
        >>> u = UDP_Connector (port = 4711, wbf = None)
        >>> class t :
        ...     message = None
        >>> t.message = 'JA1XXX YL2XXX R-18'
        >>> u.parse_message (t)
        'YL2XXX'
        >>> t.message = 'UB9XXX OH1XXX KP20'
        >>> u.parse_message (t)
        'OH1XXX'
        >>> t.message = 'RZ6XXX DL9XXX -06'
        >>> u.parse_message (t)
        'DL9XXX'
        >>> t.message = 'IZ7XXX EW4XXX 73'
        >>> u.parse_message (t)
        'EW4XXX'
        >>> t.message = 'CQ II0XXXX'
        >>> u.parse_message (t)
        'II0XXXX'
        >>> t.message = 'CQ PD0XXX JO22'
        >>> u.parse_message (t)
        'PD0XXX'
        >>> t.message = 'CQ NA PD0XXX JO22'
        >>> u.parse_message (t)
        'PD0XXX'
        >>> t.message = 'OK1XXX F4IXXX -07'
        >>> u.parse_message (t)
        'F4IXXX'
        >>> t.message = 'TM50XXX <F6XXX> RR73'
        >>> u.parse_message (t)
        '<F6XXX>'
        >>> t.message = 'CQ E73XXX JN94     a1'
        >>> u.parse_message (t)
        'E73XXX'
        >>> t.message = 'E73XXX 73'
        >>> u.parse_message (t)
        Unknown message: E73XXX 73
        >>> t.message = 'CQ E73XXX OI32     ? a1'
        >>> u.parse_message (t)
        'E73XXX'
        >>> t.message = 'CQ DX IK2XX'
        >>> u.parse_message (t)
        'IK2XX'
        >>> t.message = 'EFHW 50W 73'
        >>> u.parse_message (t)
        Unknown message: EFHW 50W 73
        >>> t.message = 'F1XXX D1X KN87'
        >>> u.parse_message (t)
        'D1X'
        >>> t.message = 'F1XXX D1X R+03'
        >>> u.parse_message (t)
        'D1X'
        >>> t.message = 'F1XXX D1X 73'
        >>> u.parse_message (t)
        'D1X'
        >>> t.message = 'F1XXX D1X RR73'
        >>> u.parse_message (t)
        'D1X'
        >>> t.message = 'OZ1XXX 0'
        >>> u.parse_message (t)
        Unknown message: OZ1XXX 0
        >>> t.message = '9H1XX EA8XX IL18'
        >>> u.parse_message (t)
        'EA8XX'
        >>> u.socket.close ()
        """
        if not tel.message :
            print ("Empty message: %s" % tel)
            return None
        if ';' in tel.message :
            print ("Unknown message: %s" % tel.message)
            return None
        l = tel.message.split ()
        # Strip off marginal decode info
        if l [-1].startswith ('a') :
            l = l [:-1]
        if l [-1] == '?' :
            l = l [:-1]
        if l [0] in ('CQ', 'QRZ') :
            # CQ DX or similar
            if len (l) == 4 and len (l [2]) >= 3 :
                return l [2]
            # CQ DX or something without locator
            if len (l) == 3 and len (l [2]) != 4 and len (l [1]) <= 4 :
                if len (l [2]) >= 3 :
                    return l [2]
            if len (l [1]) >= 3 :
                return l [1]
        if len (l) == 2 and len (l [1]) >= 3 :
            return l [1]
        if len (l) < 2 :
            print ("Unknown message: %s" % tel.message)
            return None
        if len (l) == 4 and l [2] == 'R' and len (l [1]) >= 3 :
            return l [1]
        if len (l) == 3 and len (l [1]) >= 3 :
            if len (l [1]) > 3 or self.is_stdcall (l [1]):
                return l [1]
            if self.is_locator (l [2]) :
                return l [1]
            if self.is_report (l [2]) :
                return l [1]
        print ("Unknown message: %s" % tel.message)
        return None
    # end def parse_message

    def perform_pending_changes (self) :
        for call in self.pending_color :
            fg = self.pending_color [call][0]
            bg = self.pending_color [call][1]
            self.color (call, fg_color = fg, bg_color = bg)
        self.pending_color = {}
    # end def perform_pending_changes

    def receive (self) :
        bytes, address = self.socket.recvfrom (4096)
        tel = WSJTX_Telegram.from_bytes (bytes)
        if tel.id not in self.peer :
            self.peer [tel.id] = address
        if not self.adr :
            self.adr = address
        # Only handle messages from preferred peer for now
        if self.adr == address :
            self.handle (tel)
        return tel
    # end def receive

    def set_peer (self, peername) :
        if peername in self.peer :
            self.adr = self.peer [peername]
    # end def set_peer

    def update_color (self, call, color) :
        self.color_by_call [call] = color
        self.pending_color [call] = color
    # end def update_color

# end class UDP_Connector

class WBF (autosuper) :
    """ Worked before info
    """

    def __init__ (self, band, always_match = False) :
        self.band         = band
        self.wbf          = {}
        self.always_match = always_match
    # end def __init__

    def add_item (self, item, record = 1) :
        self.wbf [item] = record
    # end def add_item

    def lookup (self, item) :
        if self.always_match :
            return None
        return self.wbf.get (item, None)
    # end def lookup

# end class WBF

class Worked_Before (autosuper) :
    """ This parses an ADIF log file and extracts worked-before info
        This can then be used by the UDP_Connector to color calls by
        parsing calls from incoming Decode packets.
        We have a WBF per band and a WBF per known DXCC.
        if we cannot determine the dxcc info for a record (unfortunately
        not provided by wsjtx currently) all records will be colored
        only in the color for "new call" or "new call on band".
        By default we import the DXCC list from ARRL and look up the
        callsign there. This is fuzzy matching and a single call can
        match more than one entity. Only if there is an exact match do
        we use the match for determining worked-before status.
    """
    # Default color tuples
    ctuple_wbf           = ctuple_invalid
    ctuple_dxcc          = ctuple_dxcc
    ctuple_dxcc_band     = ctuple_dxcc_band
    ctuple_new_call      = ctuple_new_call
    ctuple_new_call_band = ctuple_new_call_band
    ctuple_highlight     = ctuple_highlight

    def __init__ (self, adif = None, args = None, **kw) :
        # Color override
        for k in kw :
            if k.startswith ('ctuple_') :
                setattr (self, k, kw [k])
        self.args      = args
        self.cty_dxcc  = CTY_DXCC ()
        self.band_info = {}
        self.dxcc_info = {} # by dxcc number
        self.band_info ['ALL'] = WBF ('ALL')
        self.dxcc_info ['ALL'] = WBF ('ALL')
        if adif :
            with io.open (adif, 'r', encoding = args.encoding) as f :
                adif = ADIF (f)
                for rec in adif :
                    if not rec.band :
                        continue
                    self.add_entry (rec)
    # end def __init__

    def fuzzy_match_dxcc (self, call, use_dxcc = False) :
        lookup = self.cty_dxcc.callsign_lookup
        if use_dxcc :
            lookup = self.cty_dxcc.dxcc.callsign_lookup
        entities = lookup (call)
        return entities
    # end def fuzzy_match_dxcc

    def fuzzy_match_dxcc_code (self, call, only_one = False) :
        """ Use prefix info from dxcc list to fuzzy match the call
        >>> w = Worked_Before ()
        >>> w.fuzzy_match_dxcc_code ('OE3RSU')
        ['206']
        >>> w.fuzzy_match_dxcc_code ('OE3RSU', only_one = True)
        '206'
        >>> w.fuzzy_match_dxcc_code ('RK3LG', only_one = True)
        '054'
        >>> w.fuzzy_match_dxcc_code ('RK3LG')
        ['054']
        """
        entities = self.fuzzy_match_dxcc (call)
        if entities :
            if only_one and len (entities) == 1 :
                return entities [0].code
            elif not only_one :
                return [e.code for e in entities]
    # end def fuzzy_match_dxcc_code

    def add_call_entry (self, rec) :
        if rec.band not in self.band_info :
            self.band_info [rec.band] = WBF (rec.band)
        self.band_info [rec.band].add_item (rec.call, rec)
        self.band_info ['ALL'].   add_item (rec.call, rec)
    # end def add_call_entry

    def add_dxcc_entry (self, rec) :
        """ Match the dxcc for this adif record
            Note that we're using the standard ADIF DXCC entity code in
            the ADIF field DXCC *or* the COUNTRY field (in ASCII) or the
            COUNTRY_INTL field (in utf-8). Since all entity names are in
            english, all the COUNTRY_INTL should be in ASCII (a subset
            of utf-8) anyway. We match country to code and vice-versa
            via the ARRL dxcc list. If all this fails we do a fuzzy
            match on the prefix of the call.

            Note that you may want to code your own dxcc lookup for
            calls: You may want to treat dxcc entities for which you
            worked someone but do not have a QSL (or no LOTW QSL) as not
            worked before. So in that case you can override this
            routine.
        """
        dxcc_code = None
        if getattr (rec, 'dxcc', None) :
            dxcc_code = '%03d' % int (rec.dxcc, 10)
        elif getattr (rec, 'country', None) :
            dxcc = self.cty_dxcc.dxcc.by_name [rec.country]
            dxcc_code = dxcc.code
        elif getattr (rec, 'country_intl', None) :
            dxcc = self.cty_dxcc.dxcc.by_name [rec.country_intl]
            dxcc_code = dxcc.code
        else :
            dxcc_code = self.fuzzy_match_dxcc_code (rec.call, only_one = 1)
        if dxcc_code :
            if rec.band not in self.dxcc_info :
                self.dxcc_info [rec.band] = WBF (rec.band)
            self.dxcc_info [rec.band].add_item (dxcc_code)
            self.dxcc_info ['ALL'].   add_item (dxcc_code)
    # end def add_dxcc_entry

    def add_entry (self, rec) :
        self.add_call_entry (rec)
        self.add_dxcc_entry (rec)
    # end def add_entry

    def lookup_new_call (self, call) :
        """ Look up a call and decide if new on band or global
        >>> w = Worked_Before ()
        >>> w.lookup_new_call ('SX4711TEST')
        'new_call'
        """
        r = self.band_info ['ALL'].lookup (call)
        if r :
            return 'new_call_band'
        return 'new_call'
    # end def lookup_new_call

    def lookup (self, band, call) :
        """ Look up the status for this call for this band
            Involves checking of a new DXCC (on band or globally)
            and the check of a new call (on band or globally)
            The following test looks up RK0 which matches both, European
            Russia and Asiatic Russia.
        >>> w = Worked_Before ()
        >>> w.band_info ['40m'] = WBF ('40m')
        >>> w.band_info ['17m'] = WBF ('40m')
        >>> w.band_info ['10m'] = WBF ('40m')
        >>> w.dxcc_info ['40m'] = WBF ('40m')
        >>> w.dxcc_info ['17m'] = WBF ('17m')
        >>> w.dxcc_info ['10m'] = WBF ('17m')
        >>> w.dxcc_info ['ALL'] = WBF ('ALL')
        >>> for code in ('054', '015', '236', '279') :
        ...     w.dxcc_info ['40m'].add_item (code)
        ...     w.dxcc_info ['ALL'].add_item (code)
        >>> w.lookup ('40m', 'RK0')
        'new_call'
        >>> w.lookup ('40m', 'SX4711TEST')
        'new_call'

        # Worked on 40m, it's in 'ALL' and 40m, should be new on band
        >>> w.lookup ('17m', 'GM0XXX')
        'new_dxcc_band'

        # Nothing worked for this DXCC
        >>> w.lookup ('10m', 'GG7XXX')
        'new_dxcc'
        """
        if band not in self.band_info :
            return 'new_dxcc'
        r = self.band_info [band].lookup (call)
        if r :
            return 'wbf'
        dxccs = self.fuzzy_match_dxcc_code (call)
        if not dxccs :
            return 'new_dxcc'
        r2 = 1
        for dxcc in dxccs :
            if band not in self.dxcc_info:
                self.dxcc_info [band] = WBF (band)
            r2 = r2 and self.dxcc_info [band].lookup (dxcc)
        # Matched for *all* dxccs; not new dxcc on this (and any) band
        if r2 :
            for dxcc in dxccs :
                if dxcc in self.args.highlight_dxcc :
                    return 'highlight'
            return self.lookup_new_call (call)
        r3 = 1
        for dxcc in dxccs :
            r3 = r3 and self.dxcc_info ['ALL'].lookup (dxcc)
        # Matched for *all* dxccs; not new dxcc on this band
        if r3 :
            return 'new_dxcc_band'
        return 'new_dxcc'
    # end def lookup

    color_lookup_table = dict \
        (( ('new_dxcc',      ('New DXCC',         'ctuple_dxcc'))
        ,  ('new_dxcc_band', ('New DXCC on Band', 'ctuple_dxcc_band'))
        ,  ('new_call',      ('New Call',         'ctuple_new_call'))
        ,  ('new_call_band', ('New Call on Band', 'ctuple_new_call_band'))
        ,  ('wbf',           ('Worked before',    'ctuple_wbf'))
        ,  ('highlight',     ('Highlight',        'ctuple_highlight'))
        ))

    def lookup_verbose (self, band, call) :
        """ Look up the verbose description of worked-before status for
            this call for this band
        """
        status = self.lookup (band, call)
        return self.color_lookup_table [status][0]
    # end def lookup_verbose

    def lookup_color (self, band, call) :
        """ Look up the color for this call for this band
            We to a simple lookup and map the result to a color.
            Involves checking of a new DXCC (on band or globally)
            and the check of a new call (on band or globally)
            The following test looks up RK0 which matches both, European
            Russia and Asiatic Russia.
        >>> w = Worked_Before ()
        >>> w.band_info ['40m'] = WBF ('40m')
        >>> w.dxcc_info ['40m'] = WBF ('40m')
        >>> w.dxcc_info ['ALL'] = WBF ('ALL')
        >>> for code in ('054', '015') :
        ...     w.dxcc_info ['40m'].add_item (code)
        ...     w.dxcc_info ['ALL'].add_item (code)
        >>> w.lookup_color ('40m', 'RK0') [1]
        QColor(alpha=65535, red=0, green=65535, blue=65535)
        """
        status = self.lookup (band, call)
        return getattr (self, self.color_lookup_table [status][1])
    # end def lookup_color

# end class Worked_Before

class QSO_Database_Worked_Before (Worked_Before) :
    """ Get DXCC data from QSO database
        This only gets a dxcc if the qso is *confirmed* in LOTW.
    """

    def __init__ \
        ( self, url, username, locator
        , adif = None
        , args = None
        , password = None
        , **kw
        ) :
        d = dict \
            ( url      = url
            , username = username
            , password = password
            , dry_run  = True
            )
        if 'verbose' in kw :
            d.update (verbose = kw ['verbose'])
        self.au = ADIF_Uploader (** d)
        self.__super.__init__ (adif, args, **kw)
        self.locator = locator
        self.add_dxccs ()
    # end def __init__

    def add_dxccs (self) :
        # determine ham_call from locator
        d  = dict (gridsquare = self.locator)
        hc = self.au.get ('ham_call?' + urlencode (d))['data']['collection']
        if len (hc) != 1 :
            raise ValueError \
                ("Ham Call with Loc=%s: Got %d entries"
                % (self.locator, len (hc))
                )
        d = dict (qsl_type = 'LOTW')
        d ['qso.owner'] = hc [0]['id']
        d ['@fields'] = 'qso.dxcc_entity.code,qso.band.name'
        d ['@sort']   = 'qso.band.name'
        qsls = self.au.get ('qsl?' + urlencode (d))['data']['collection']
        for qsl in qsls :
            band = qsl ['qso.band.name']
            dxcc_code = qsl ['qso.dxcc_entity.code']
            if band not in self.dxcc_info :
                self.dxcc_info [band] = WBF (band)
            self.dxcc_info [band]. add_item (dxcc_code)
            self.dxcc_info ['ALL'].add_item (dxcc_code)
    # end def add_dxccs

    def add_dxcc_entry (self, rec) :
        """ Do nothing here: We update the DXCC map in add_dxccs
            and we do *not* mark newly-worked calls in the DXCC map:
            We only want LOTW-confirmed entries.
        """
        return
    # end def add_dxcc_entry

# end class QSO_Database_Worked_Before

def get_defaults () :
    home  = os.environ.get ('HOME', '')
    d     = {}
    d.update (adif_path = os.environ.get 
        ('WBF_PATH', os.path.join (home, '.local/share/WSJTX/wsjtx_log.adi')))
    d.update (call  = os.environ.get ('WBF_CALL',      'OE3RSU'))
    d.update (loc   = os.environ.get ('WBF_LOC',       'JN88dg'))
    d.update (user  = os.environ.get ('WBF_USER',      None))
    d.update (dburl = os.environ.get ('WBF_DBURL',     None))
    hl = [x.strip () for x in os.environ.get ('WBF_HIGHLIGHT', '').split (',')]
    if hl :
        d.update (highlight = hl)
    return d
# end def get_defaults

def default_cmd (defaults = None) :
    if defaults is None :
        defaults = get_defaults ()
    cmd = ArgumentParser ()
    cmd.add_argument \
        ( '-a', '--adif'
        , help    = 'ADIF file to parse, default=%(default)s'
        , default = defaults ['adif_path']
        )
    cmd.add_argument \
        ( "-d", "--highlight-dxcc"
        , help    = 'DXCC to highlight even if only new call on band'
                    ' may be specified multiple times'
        , default = defaults ['highlight']
        , action  = 'append'
        )
    cmd.add_argument \
        ( "-e", "--encoding"
        , help    = 'ADIF file character encoding, default=%(default)s'
        , default = 'utf-8'
        )
    cmd.add_argument \
        ( "-l", "--locator"
        , help    = 'Locator of user of wsjtx, default=%(default)s'
        , default = defaults ['loc']
        )
    cmd.add_argument \
        ( "-p", "--password"
        , help    = "Password, better use .netrc"
        )
    cmd.add_argument \
        ( "-U", "--dburl"
        , help    = 'URL of qso tracker, default=%(default)s'
        , default = defaults ['dburl']
        )
    cmd.add_argument \
        ( "-u", "--dbuser"
        , help    = 'User of qso tracker, default=%(default)s'
        , default = defaults ['user']
        )
    return cmd
# end def default_cmd

def get_wbf (cmd = None, defaults = None) :
    if defaults is None :
        defaults = get_defaults ()
    if cmd is None :
        cmd = default_cmd (defaults)
        cmd.add_argument \
            ( "-c", "--callsign"
            , help    = 'Callsign of user of wsjtx, default=%(default)s'
            , default = defaults ['call']
            )
        cmd.add_argument \
            ( "-L", "--set-locator-msg"
            , help    = 'Set free-text message to locator message with '
                        '<dx-call> <own-call> report locator using EU-VHF '
                        'message'
            , action  = 'store_true'
            )
    args = cmd.parse_args ()
    if args.dburl and args.dbuser :
        wbf = QSO_Database_Worked_Before \
            ( url      = args.dburl
            , username = args.dbuser
            , password = args.password
            , locator  = args.locator
            , adif     = args.adif
            , args     = args
            )
    else :
        wbf = Worked_Before (args = args, adif = args.adif)
    return wbf
# end def get_wbf

def main (get_wbf = get_wbf) :
    wbf  = get_wbf ()
    uc   = UDP_Connector (wbf)
    args = wbf.args
    weedout = \
        ( WSJTX_Decode, WSJTX_Status, WSJTX_Heartbeat, WSJTX_QSO_Logged
        , WSJTX_Logged_ADIF
        )
    while 1 :
        tel = uc.receive ()
        if not isinstance (tel, weedout):
            print (tel)
# end def main

__all__ = [ "main", "QDateTime", "QColor", "color_red", "color_green"
          , "color_blue", "color_white", "color_black"
          , "color_cyan", "color_cyan1", "color_pink", "color_pink1"
          , "ctuple_invalid"
          , "WSJTX_Heartbeat", "WSJTX_Status", "WSJTX_Decode"
          , "WSJTX_Clear", "WSJTX_Reply", "WSJTX_QSO_Logged"
          , "WSJTX_Close", "WSJTX_Replay", "WSJTX_Halt_TX"
          , "WSJTX_Free_Text", "WSJTX_WSPR_Decode", "WSJTX_Location"
          , "WSJTX_Logged_ADIF", "WSJTX_Highlight_Call"
          , "WSJTX_Switch_Config", "WSJTX_Configure", "UDP_Connector"
          , "WBF", "Worked_Before", "get_defaults", "default_cmd"
          , "get_wbf"
          ]

if __name__ == '__main__' :
    main ()
