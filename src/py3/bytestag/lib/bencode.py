# The contents of this file are subject to the BitTorrent Open Source License
# Version 1.1 (the License).  You may not copy or use this file, in either
# source code or executable form, except in compliance with the License.  You
# may obtain a copy of the License at http://www.bittorrent.com/license/.
#
# Software distributed under the License is distributed on an AS IS basis,
# WITHOUT WARRANTY OF ANY KIND, either express or implied.  See the License
# for the specific language governing rights and limitations under the
# License.

# Written by Petru Paler
# Python 3 port, UTF-8 support, PEP-8 compliance, implemented commented-
# out test cases, formatting by Christopher Foo :)


class BTFailure(Exception):
    pass


def decode_int(x, f):
    f += 1
    newf = x.index(b'e', f)
    n = int(x[f:newf])

    if x[f] == b'-':
        if x[f + 1] == b'0':
            raise ValueError

    elif x[f] == b'0' and newf != f + 1:
        raise ValueError

    return (n, newf + 1)


def decode_string(x, f):
    colon = x.index(b':', f)
    n = int(x[f:colon])

    if x[f] == b'0' and colon != f + 1:
        raise ValueError

    colon += 1

    return (x[colon:colon + n], colon + n)


def decode_list(x, f):
    r, f = [], f + 1

    while x[f: f + 1] != b'e':
        v, f = decode_func[x[f:f + 1]](x, f)
        r.append(v)

    return (r, f + 1)


def decode_dict(x, f):
    r, f = {}, f + 1

    while x[f: f + 1] != b'e':
        k, f = decode_string(x, f)
        r[k], f = decode_func[x[f:f + 1]](x, f)

    return (r, f + 1)

decode_func = {}
decode_func[b'l'] = decode_list
decode_func[b'd'] = decode_dict
decode_func[b'i'] = decode_int
decode_func[b'0'] = decode_string
decode_func[b'1'] = decode_string
decode_func[b'2'] = decode_string
decode_func[b'3'] = decode_string
decode_func[b'4'] = decode_string
decode_func[b'5'] = decode_string
decode_func[b'6'] = decode_string
decode_func[b'7'] = decode_string
decode_func[b'8'] = decode_string
decode_func[b'9'] = decode_string


def bdecode(x):
    try:
        r, l = decode_func[x[0:1]](x, 0)
    except (IndexError, KeyError, ValueError, TypeError) as e:
#        traceback.print_exc(limit=10)

        raise BTFailure("not a valid bencoded string")

    if l != len(x):
        raise BTFailure("invalid bencoded value (data after valid prefix)")

    return r


class Bencached(object):
    __slots__ = ['bencoded']

    def __init__(self, s):
        self.bencoded = s


def encode_or_raise(v, r):
    if type(v) in encode_func:
        encode_func[type(v)](v, r)
    else:
        raise BTFailure('Cannot encode value of type {}'.format(type(v)))


def encode_bencached(x, r):
    r.append(x.bencoded)


def encode_int(x, r):
    x = str(x).encode()

    r.extend((b'i', x, b'e'))


def encode_bool(x, r):
    if x:
        encode_int(1, r)
    else:
        encode_int(0, r)


def encode_string(x, r):
    r.extend((str(len(x)).encode(), b':', x))


def encode_list(x, r):
    r.append(b'l')

    for i in x:
        encode_or_raise(i, r)

    r.append(b'e')


def encode_dict(x, r):
    r.append(b'd')

    ilist = x.items()

    for k, v in sorted(ilist):
        r.extend((str(len(k)).encode(), b':', k))
        encode_or_raise(v, r)

    r.append(b'e')

encode_func = {}
encode_func[Bencached] = encode_bencached
encode_func[int] = encode_int
encode_func[int] = encode_int
encode_func[bytes] = encode_string
encode_func[list] = encode_list
encode_func[tuple] = encode_list
encode_func[dict] = encode_dict
encode_func[bool] = encode_bool


def bencode(x):
    r = []

    encode_or_raise(x, r)

    return b''.join(r)
