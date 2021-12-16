# con_otp_v1
random.seed()


def encrypt_int(message: int, otp: int, safe: bool = True) -> int:
    assert message >= 0, "Only non-negative numbers are supported"
    assert not safe or message <= otp, "The message %i is too long" % (message)
    return message ^ otp


def bit_size(num: int) -> int:
    assert isinstance(num, int), "bit_size(num) only supports integers, not %r" % type(num)
    return num.bit_length()


def byte_size(number: int) -> int:
    if number == 0:
        return 1
    return div_ceil(bit_size(number), 8)


def int2bytes(number: int, fill_size: int = 0) -> bytes:
    assert number >= 0, "Number must be an unsigned integer: %d" % number
    bytes_required = max(1, div_ceil(number.bit_length(), 8))
    if fill_size > 0:
        return number.to_bytes(fill_size, "big")
    return number.to_bytes(bytes_required, "big")


def bytes2int(raw_bytes: bytes) -> int:
    return int.from_bytes(raw_bytes, "big", signed=False)


def div_ceil(a: int, b: int) -> int:
    return a//b + bool(a%b)


@export
def encrypt(message_str: str, otp: int, safe: bool = True) -> str:
    message_bytes = message_str.encode()
    message_int = bytes2int(message_bytes)
    key_length = max(byte_size(otp), len(message_bytes))
    encrypted_int = encrypt_int(message_int, otp, safe=safe)
    encrypted_bytes = int2bytes(encrypted_int, key_length)
    return encrypted_bytes.hex()

@export
def encrypt_hex(message_str: str, otp: int, safe: bool = True) -> str:
    message_bytes = bytes.fromhex(message_str)
    message_int = bytes2int(message_bytes)
    key_length = max(byte_size(otp), len(message_bytes))
    encrypted_int = encrypt_int(message_int, otp, safe=safe)
    encrypted_bytes = int2bytes(encrypted_int, key_length)
    return encrypted_bytes.hex()

@export
def decrypt(encrypted_str: str, otp: int, safe: bool = True) -> str:
    encrypted_bytes = bytes.fromhex(encrypted_str)
    encrypted_int = bytes2int(encrypted_bytes)
    key_length = max(byte_size(otp), len(encrypted_bytes))
    decrypted_int = encrypt_int(otp, encrypted_int, safe=safe)
    decrypted_bytes = int2bytes(decrypted_int, key_length)
    return decrypted_bytes.lstrip(b'\x00').decode()

@export
def decrypt_hex(encrypted_str: str, otp: int, safe: bool = True) -> str:
    encrypted_bytes = bytes.fromhex(encrypted_str)
    encrypted_int = bytes2int(encrypted_bytes)
    key_length = max(byte_size(otp), len(encrypted_bytes))
    decrypted_int = encrypt_int(otp, encrypted_int, safe=safe)
    decrypted_bytes = int2bytes(decrypted_int, key_length)
    return decrypted_bytes.hex()

@export
def generate_otp(n_bits: int) -> int:
    return random.getrandbits(n_bits)


@construct
def seed():
    pass    