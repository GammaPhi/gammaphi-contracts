p = 21888242871839275222246405745257275088696311157297823662689037894645226208583
p2s = [0x3c208c16d87cfd47, 0x97816a916871ca8d, 0xb85045b68181585d, 0x30644e72e131a029]

def convert(p2s: list) -> int:
    x = 0
    for i in range(4):
        x += p2s[3-i]
        if i < 3:
            x <<= 64
    return x


assert convert(p2s) == p, 'Invalid'



# p2 is p, represented as little-endian 64-bit words.
p2 = [0x3c208c16d87cfd47, 0x97816a916871ca8d, 0xb85045b68181585d, 0x30644e72e131a029]

# np is the negative inverse of p, mod 2^256.
np = [0x87d20782e4866389, 0x9ede7d651eca6ac9, 0xd8afcbd01833da80, 0xf57a22b791888c6b]

# rN1 is R^-1 where R = 2^256 mod p.
rN1 = [0xed84884a014afa37, 0xeb2022850278edf8, 0xcf63e9cfb74492d9, 0x2e67157159e5c639]

# r2 is R^2 where R = 2^256 mod p.
r2 = [0xf32cfc5b538afa89, 0xb5e71911d44501fb, 0x47ab1eff0a417ff6, 0x06d89f71cab8351f]

# r3 is R^3 where R = 2^256 mod p.
r3 = [0xb1cd6dafda1530df, 0x62f210e6a7283db6, 0xef7f0b0c0ada0afb, 0x20fd6e902d592544]

# xiToPMinus1Over6 is ξ^((p-1)/6) where ξ = i+9.
xiToPMinus1Over6 = [[0xa222ae234c492d72, 0xd00f02a4565de15b, 0xdc2ff3a253dfc926, 0x10a75716b3899551], [0xaf9ba69633144907, 0xca6b1d7387afb78a, 0x11bded5ef08a2087, 0x02f34d751a1f3a7c]]

# xiToPMinus1Over3 is ξ^((p-1)/3) where ξ = i+9.
xiToPMinus1Over3 = [[0x6e849f1ea0aa4757, 0xaa1c7b6d89f89141, 0xb6e713cdfae0ca3a, 0x26694fbb4e82ebc3], [0xb5773b104563ab30, 0x347f91c8a9aa6454, 0x7a007127242e0991, 0x1956bcd8118214ec]]

# xiToPMinus1Over2 is ξ^((p-1)/2) where ξ = i+9.
xiToPMinus1Over2 = [[0xa1d77ce45ffe77c7, 0x07affd117826d1db, 0x6d16bd27bb7edc6b, 0x2c87200285defecc], [0xe4bbdd0c2936b629, 0xbb30f162e133bacb, 0x31a9d1b6f9645366, 0x253570bea500f8dd]]

# xiToPSquaredMinus1Over3 is ξ^((p²-1)/3) where ξ = i+9.
xiToPSquaredMinus1Over3 = [0x3350c88e13e80b9c, 0x7dce557cdb5e56b9, 0x6001b4b8b615564a, 0x2682e617020217e0]

# xiTo2PSquaredMinus2Over3 is ξ^((2p²-2)/3) where ξ = i+9 (a cubic root of unity, mod p).
xiTo2PSquaredMinus2Over3 = [0x71930c11d782e155, 0xa6bb947cffbe3323, 0xaa303344d4741444, 0x2c3b3f0d26594943]

# xiToPSquaredMinus1Over6 is ξ^((1p²-1)/6) where ξ = i+9 (a cubic root of -1, mod p).
xiToPSquaredMinus1Over6 = [0xca8d800500fa1bf2, 0xf0c5d61468b39769, 0x0e201271ad0d4418, 0x04290f65bad856e6]

# xiTo2PMinus2Over3 is ξ^((2p-2)/3) where ξ = i+9.
xiTo2PMinus2Over3 = [[0x5dddfd154bd8c949, 0x62cb29a5a4445b60, 0x37bc870a0c7dd2b9, 0x24830a9d3171f0fd], [0x7361d77f843abe92, 0xa5bb2bd3273411fb, 0x9c941f314b3e2399, 0x15df9cddbb9fd3ec]]


np = convert(np)
print(f'np = {np}')

rN1 = convert(rN1)
print(f'rN1 = {rN1}')

r2 = convert(r2)
print(f'r2 = {r2}')

r3 = convert(r3)
print(f'r3 = {r3}')

xiToPSquaredMinus1Over3 = convert(xiToPSquaredMinus1Over3)
print(f'xiToPSquaredMinus1Over3 = {xiToPSquaredMinus1Over3}')

xiTo2PSquaredMinus2Over3 = convert(xiTo2PSquaredMinus2Over3)
print(f'xiTo2PSquaredMinus2Over3 = {xiTo2PSquaredMinus2Over3}')

xiToPSquaredMinus1Over6 = convert(xiToPSquaredMinus1Over6)
print(f'xiToPSquaredMinus1Over6 = {xiToPSquaredMinus1Over6}')

xiToPMinus1Over6 = [convert(y) for y in xiToPMinus1Over6]
print(f'xiToPMinus1Over6 = {xiToPMinus1Over6}')

xiToPMinus1Over3 = [convert(y) for y in xiToPMinus1Over3]
print(f'xiToPMinus1Over3 = {xiToPMinus1Over3}')

xiToPMinus1Over2 = [convert(y) for y in xiToPMinus1Over2]
print(f'xiToPMinus1Over2 = {xiToPMinus1Over2}')

xiTo2PMinus2Over3 = [convert(y) for y in xiTo2PMinus2Over3]
print(f'xiTo2PMinus2Over3 = {xiTo2PMinus2Over3}')


twistB = [
	[0x38e7ecccd1dcff67, 0x65f0b37d93ce0d3e, 0xd749d0dd22ac00aa, 0x0141b9ce4a688d4d],
	[0x3bf938e377b802a8, 0x020b1b273633535d, 0x26b7edf049755260, 0x2514c6324384a86d],
]

twistB = [convert(y) for y in twistB]
print(f'twistB = {twistB}')


# twistGen is the generator of group G₂.
twistGen = [
	[
		[0xafb4737da84c6140, 0x6043dd5a5802d8c4, 0x09e950fc52a02f86, 0x14fef0833aea7b6b],
		[0x8e83b5d102bc2026, 0xdceb1935497b0172, 0xfbb8264797811adf, 0x19573841af96503b],
    ],
	[
		[0x64095b56c71856ee, 0xdc57f922327d3cbb, 0x55f935be33351076, 0x0da4a0e693fd6482],
		[0x619dfa9d886be9f6, 0xfe7fd297f59e9b78, 0xff9e1a62231b7dfe, 0x28fd7eebae9e4206],
    ],
	[0, 1],
	[0, 1],
]

twistGen[0] = [convert(y) for y in twistGen[0]]
twistGen[1] = [convert(y) for y in twistGen[1]]
print(f'twistGen = {twistGen}')
