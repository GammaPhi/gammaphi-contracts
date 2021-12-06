random.seed()


@construct
def seed():
    pass


def assert_int(var: int, name: str) -> None:
    assert isinstance(var, int), "%s should be an integer, not %s" % (name, type(var))


def encrypt_int(message: int, ekey: int, n: int) -> int:
    """Encrypts a message using encryption key 'ekey', working modulo n"""

    assert_int(message, "message")
    assert_int(ekey, "ekey")
    assert_int(n, "n")

    assert message >= 0, "Only non-negative numbers are supported"

    assert message <= n, "The message %i is too long for n=%i" % (message, n)

    return pow(message, ekey, n)


def bytes2int(raw_bytes: bytes) -> int:
    r"""Converts a list of bytes or an 8-bit string to an integer.
    When using unicode strings, encode it to some encoding like UTF8 first.
    >>> (((128 * 256) + 64) * 256) + 15
    8405007
    >>> bytes2int(b'\x80@\x0f')
    8405007
    """
    return int.from_bytes(raw_bytes, "big", signed=False)


def div_ceil(a: int, b: int) -> int:
    return a//b + bool(a%b)


def int2bytes(number: int, fill_size: int = 0) -> bytes:
    """
    Convert an unsigned integer to bytes (big-endian)::
    Does not preserve leading zeros if you don't specify a fill size.
    :param number:
        Integer value
    :param fill_size:
        If the optional fill size is given the length of the resulting
        byte string is expected to be the fill size and will be padded
        with prefix zero bytes to satisfy that length.
    :returns:
        Raw bytes (base-256 representation).
    :raises:
        ``OverflowError`` when fill_size is given and the number takes up more
        bytes than fit into the block. This requires the ``overflow``
        argument to this function to be set to ``False`` otherwise, no
        error will be raised.
    """

    assert number >= 0, "Number must be an unsigned integer: %d" % number

    bytes_required = max(1, div_ceil(number.bit_length(), 8))

    if fill_size > 0:
        return number.to_bytes(fill_size, "big")

    return number.to_bytes(bytes_required, "big")


def bit_size(num: int) -> int:
    """
    Number of bits needed to represent a integer excluding any prefix
    0 bits.
    Usage::
        >>> bit_size(1023)
        10
        >>> bit_size(1024)
        11
        >>> bit_size(1025)
        11
    :param num:
        Integer value. If num is 0, returns 0. Only the absolute value of the
        number is considered. Therefore, signed integers will be abs(num)
        before the number's bit length is determined.
    :returns:
        Returns the number of bits in the integer.
    """

    assert isinstance(num, int), "bit_size(num) only supports integers, not %r" % type(num)
    return num.bit_length()


def byte_size(number: int) -> int:
    """
    Returns the number of bytes required to hold a specific long number.
    The number of bytes is rounded up.
    Usage::
        >>> byte_size(1 << 1023)
        128
        >>> byte_size((1 << 1024) - 1)
        128
        >>> byte_size(1 << 1024)
        129
    :param number:
        An unsigned integer
    :returns:
        The number of bytes required to hold a specific long number.
    """
    if number == 0:
        return 1
    return div_ceil(bit_size(number), 8)


def pad_for_encryption(message: bytes, target_length: int) -> bytes:
    r"""Pads the message for encryption, returning the padded message.
    :return: 00 02 RANDOM_DATA 00 MESSAGE
    >>> block = pad_for_encryption(b'hello', 16)
    >>> len(block)
    16
    >>> block[0:2]
    b'\x00\x02'
    >>> block[-6:]
    b'\x00hello'
    """

    max_msglength = target_length - 11
    msglength = len(message)

    assert msglength <= max_msglength, "%i bytes needed for message, but there is only space for %i" % (msglength, max_msglength)
    
    # Get random padding
    padding = b""
    padding_length = target_length - msglength - 3

    # We remove 0-bytes, so we'll end up with less padding than we've asked for,
    # so keep adding data until we're at the correct length.
    while len(padding) < padding_length:
        needed_bytes = padding_length - len(padding)

        # Always read at least 8 bytes more than we need, and trim off the rest
        # after removing the 0-bytes. This increases the chance of getting
        # enough bytes, especially when needed_bytes is small
        random_bits = random.getrandbits((needed_bytes + 5) * 8)
        new_padding = int2bytes(random_bits, fill_size=needed_bytes+5)
        new_padding = new_padding.replace(b"\x00", b"")
        padding = padding + new_padding[:needed_bytes]

    assert len(padding) == padding_length, "Invalid padding length: %i != %i" % (len(padding), padding_length)

    return b"".join([b"\x00\x02", padding, b"\x00", message])


@export
def encrypt(message_str: str, n: int, e: int) -> str:
    """Encrypts the given message using PKCS#1 v1.5
    :param message: the message to encrypt. Must be a byte string no longer than
        ``k-11`` bytes, where ``k`` is the number of bytes needed to encode
        the ``n`` component of the public key.
    :param pub_key: the :py:class:`rsa.PublicKey` to encrypt with.
    :raise OverflowError: when the message is too large to fit in the padded
        block.
    >>> from rsa import key, common
    >>> (pub_key, priv_key) = key.newkeys(256)
    >>> message = b'hello'
    >>> crypto = encrypt(message, pub_key)
    The crypto text should be just as long as the public key 'n' component:
    >>> len(crypto) == common.byte_size(pub_key.n)
    True
    """

    message = message_str.encode()

    keylength = byte_size(n)
    padded = pad_for_encryption(message, keylength)

    payload = bytes2int(padded)
    encrypted = encrypt_int(payload, e, n)
    block = int2bytes(encrypted, keylength)

    return block.hex()
