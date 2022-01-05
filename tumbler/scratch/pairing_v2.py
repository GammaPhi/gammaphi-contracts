from typing import Any

# The prime modulus of the field
field_modulus = 21888242871839275222246405745257275088696311157297823662689037894645226208583

# The modulus of the polynomial in this representation of FQ12
FQ12_modulus_coeffs = [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0] # Implied + [1]

ate_loop_count = 29793968203157093288
log_ate_loop_count = 63
pseudo_binary_encoding = [0, 0, 0, 1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 0, 1, 0,
                          0, 1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1, 1,
                          1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 1,
                          1, 0, 0, -1, 0, 0, 0, 1, 1, 0, -1, 0, 0, 1, 0, 1, 1]

assert sum([e * 2**i for i, e in enumerate(pseudo_binary_encoding)]) == ate_loop_count

curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Extended euclidean algorithm to find modular inverses for
# integers

def inv(a: int, n: int) -> int:
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high//low
        nm, new = hm-lm*r, high-low*r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def FQ(n: int) -> int:
    return n % field_modulus


def fq_add(self: int, other: int) -> int:
    return (self + other) % field_modulus


def fq_mul(self: int, other: int) -> int:
    return (self * other) % field_modulus


def fq_sub(self: int, other: int) -> int:
    return (self - other) % field_modulus


def fq_div(self: int, other: int) -> int:
    assert isinstance(other, int), 'Invalid other. Should be an int.'
    return fq_mul(self, inv(other, field_modulus)) % field_modulus


def fq_pow(self: int, other: int) -> int:
    #print(f'Calling fq_pow with: {self}, {other}')
    if other == 0:
        return 1
    elif other == 1:
        return self
    elif other % 2 == 0:
        return fq_pow(fq_mul(self, self), other // 2)
    else:
        return fq_mul(fq_pow(fq_mul(self, self), other // 2), self)


def fq_eq(self: int, other: int) -> bool:
    return self == other


def fq_ne(self: int, other: int) -> int:
    return not fq_eq(self, other)


def fq_neg(self: int) -> int:
    return -self


def fq_one() -> int:
    return FQ(1)

def fq_zero() -> int:
    return FQ(0)

# Utility methods for polynomial math
def deg(p: list) -> int:
    d = len(p) - 1
    while p[d] == 0 and d:
        d -= 1
    return d

def poly_rounded_div(a: list, b: list) -> list:
    dega = deg(a)
    degb = deg(b)
    temp = [x for x in a]
    o = [0 for x in a]
    for i in range(dega - degb, -1, -1):
        o[i] = fq_add(o[i], fq_div(temp[degb + i], b[degb]))
        for c in range(degb + 1):
            temp[c + i] = fq_sub(temp[c + i], o[c])
    return o[:deg(o)+1]



def FQP(coeffs: list, modulus_coeffs: list) -> dict:
    assert len(coeffs) == len(modulus_coeffs)
    coeffs = [FQ(c) for c in coeffs]
    # The degree of the extension field
    degree = len(modulus_coeffs)
    return {
        'coeffs': coeffs,
        'modulus_coeffs': modulus_coeffs,
        'degree': degree
    }



def fqp_add(self: dict, other: dict) -> dict:
    assert isinstance(other, (dict, list))
    other_coeffs = other if isinstance(other, list) else other['coeffs']
    return FQP([fq_add(x, y) for x,y in zip(self['coeffs'], other_coeffs)], self['modulus_coeffs'])


def fqp_sub(self: dict, other: dict) -> dict:
    assert isinstance(other, (dict, list))
    other_coeffs = other if isinstance(other, list) else other['coeffs']
    return FQP([fq_sub(x, y) for x,y in zip(self['coeffs'], other_coeffs)], self['modulus_coeffs'])


def fqp_mul(self: dict, other: Any) -> dict:
    assert not isinstance(self, int), f'Called fqp_mul with an integer: {self}'
    if isinstance(other, int):
        return FQP([fq_mul(c, other) for c in self['coeffs']], self['modulus_coeffs'])
    else:
        assert isinstance(other, dict)
        degree = self['degree']
        coeffs = self['coeffs']
        modulus_coeffs = self['modulus_coeffs']
        other_coeffs = other['coeffs']
        b = [FQ(0) for i in range(degree * 2 - 1)]
        for i in range(degree):
            for j in range(degree):
                b[i + j] = fq_add(b[i + j], fq_mul(coeffs[i], other_coeffs[j]))
        while len(b) > degree:
            exp, top = len(b) - degree - 1, b.pop()
            for i in range(degree):
                b[exp + i] = fq_sub(b[exp + i], fq_mul(top, FQ(modulus_coeffs[i])))
        return FQP(b, modulus_coeffs)


def fqp_div(self: dict, other: Any) -> dict:
    if isinstance(other, int):
        return FQP([fq_div(c, other) for c in self['coeffs']], self['modulus_coeffs'])
    else:
        assert isinstance(other, dict)
        return fqp_mul(self, fqp_inv(other))


def fqp_pow(self: dict, other: int) -> dict:
    #print(f'Calling fq_pow with: {self}, {other}')
    degree = self['degree']
    modulus_coeffs = self['modulus_coeffs']
    o = FQP([1] + [0] * (degree - 1), modulus_coeffs)
    t = self
    while other > 0:
        if other & 1:
            o = fqp_mul(o, t)
        other >>= 1
        t = fqp_mul(t, t)
    return o


# Extended euclidean algorithm used to find the modular inverse
def fqp_inv(self: dict) -> dict:
    degree = self['degree']
    modulus_coeffs = self['modulus_coeffs']
    coeffs = self['coeffs']
    lm, hm = [1] + [0] * degree, [0] * (degree + 1)
    low, high = coeffs + [0], modulus_coeffs + [1]
    while deg(low):
        r = poly_rounded_div(high, low)
        r.extend([0] * (degree + 1 - len(r)))
        nm = [x for x in hm]
        new = [x for x in high]
        assert len(lm) == len(hm) == len(low) == len(high) == len(nm) == len(new) == degree + 1
        for i in range(degree + 1):
            for j in range(degree + 1 - i):
                nm[i+j] = fq_sub(nm[i+j], fq_mul(lm[i], r[j]))
                new[i+j] = fq_sub(new[i+j], fq_mul(low[i], r[j]))
        lm, low, hm, high = nm, new, lm, low
    return fqp_div(FQP(lm[:degree], modulus_coeffs), low[0])


def fqp_eq(self: dict, other: dict) -> bool:
    assert isinstance(other, dict)
    coeffs = self['coeffs']
    other_coeffs = other['coeffs']
    for c1, c2 in zip(coeffs, other_coeffs):
        if fq_ne(c1, c2):
            return False
    return True


def fqp_ne(self: dict, other: dict) -> bool:
    return not fqp_eq(self, other)


def fqp_neg(self: dict) -> dict:
    modulus_coeffs = self['modulus_coeffs']
    coeffs = self['coeffs']
    return FQP([-c for c in coeffs], modulus_coeffs)

# The quadratic extension field
def FQ2(coeffs: list) -> dict:
    assert len(coeffs) == 2, f'FQ2 must have 2 coefficients but had {len(coeffs)}'
    return FQP(coeffs, [1, 0])

# The 12th-degree extension field
def FQ12(coeffs: list) -> dict:
    assert len(coeffs) == 12
    return FQP(coeffs, FQ12_modulus_coeffs)

def fq2_one() -> dict:
    return FQ2([1, 0])

def fq2_zero() -> dict:
    return FQ2([0, 0])

def fq12_one() -> dict:
    return FQ12([1] + [0] * (len(FQ12_modulus_coeffs) - 1))

def fq12_zero() -> dict:
    return FQ12([0] * len(FQ12_modulus_coeffs))

# Check if a point is the point at infinity
def is_inf(pt: Any) -> bool:
    x, y, z = pt
    if isinstance(x, int):
        return fq_eq(z, 0)
    else:
        zero = FQP([0] * z['degree'], modulus_coeffs=z['modulus_coeffs'])
        return fqp_eq(z, zero)


# Check that a point is on the curve defined by y**2 == x**3 + b
def is_on_curve(pt: Any, b: Any) -> bool:
    if is_inf(pt):
        return True
    x, y, z = tuple(pt)
    if isinstance(x, int):
        a = fq_sub(fq_mul(fq_pow(y,2), z), fq_pow(x, 3))
        return fq_eq(a, fq_mul(b, fq_pow(z, 3)))
    else:
        a = fqp_sub(fqp_mul(fqp_pow(y,2), z), fqp_pow(x, 3))
        return fqp_eq(a, fqp_mul(b, fqp_pow(z, 3)))

# Elliptic curve doubling
def double(pt):
    x, y, z = pt
    if isinstance(x, int):
        W = fq_mul(x, fq_mul(x, 3))
        S = fq_mul(y, z)
        B = fq_mul(x, fq_mul(y, S))
        H = fq_sub(fq_mul(W, W), fq_mul(B, 8))
        S_squared = fq_mul(S, S)
        newx = fq_mul(H, fq_mul(S, 2))
        newy = fq_sub(fq_mul(W, fq_sub(fq_mul(B, 4), H)), fq_mul(y, fq_mul(y, fq_mul(S_squared, 8))))
        newz = fq_mul(S_squared, fq_mul(S, 8))
    else:
        W = fqp_mul(x, fqp_mul(x, 3))
        S = fqp_mul(y, z)
        B = fqp_mul(x, fqp_mul(y, S))
        H = fqp_sub(fqp_mul(W, W), fqp_mul(B, 8))
        S_squared = fqp_mul(S, S)
        newx = fqp_mul(H, fqp_mul(S, 2))
        newy = fqp_sub(fqp_mul(W, fqp_sub(fqp_mul(B, 4), H)), fqp_mul(y, fqp_mul(y, fqp_mul(S_squared, 8))))
        newz = fqp_mul(S_squared, fqp_mul(S, 8))
    return normalize1((newx, newy, newz))


# Elliptic curve addition
def add(p1, p2):
    x1, y1, z1 = p1
    x2, y2, z2 = p2
    if isinstance(x1, int):
        one = 1
        zero = 0
        if fq_eq(p1[2], zero) or fq_eq(p2[2], zero):
            return p1 if fq_eq(p2[2], zero) else p2
        U1 = fq_mul(y2, z1)
        U2 = fq_mul(y1, z2)
        V1 = fq_mul(x2, z1)
        V2 = fq_mul(x1, z2)
        if fq_eq(V1, V2) and fq_eq(U1, U2):
            return double(p1)
        elif fq_eq(V1, V2):
            return (one, one, zero)
        U = fq_sub(U1, U2)
        V = fq_sub(V1, V2)
        V_squared = fq_mul(V, V)
        V_squared_times_V2 = fq_mul(V_squared, V2)
        V_cubed = fq_mul(V_squared, V)
        W = fq_mul(z1, z2)
        A = fq_sub(fq_sub(fq_mul(fq_mul(U, U), W), V_cubed), fq_mul(V_squared_times_V2, 2))
        newx = fq_mul(V, A)
        newy = fq_sub(fq_mul(U, fq_sub(V_squared_times_V2, A)), fq_mul(V_cubed, U2))
        newz = fq_mul(V_cubed, W)
    else:
        degree = x1['degree']
        modulus_coeffs = x1['modulus_coeffs']
        one = FQP([1] + [0] * (degree-1), modulus_coeffs)
        zero = FQP([0] * degree, modulus_coeffs)
        if fqp_eq(p1[2], zero) or fqp_eq(p2[2], zero):
            return p1 if fqp_eq(p2[2], zero) else p2
        U1 = fqp_mul(y2, z1)
        U2 = fqp_mul(y1, z2)
        V1 = fqp_mul(x2, z1)
        V2 = fqp_mul(x1, z2)
        if fqp_eq(V1, V2) and fqp_eq(U1, U2):
            return double(p1)
        elif fqp_eq(V1, V2):
            return (one, one, zero)
        U = fqp_sub(U1, U2)
        V = fqp_sub(V1, V2)
        V_squared = fqp_mul(V, V)
        V_squared_times_V2 = fqp_mul(V_squared, V2)
        V_cubed = fqp_mul(V_squared, V)
        W = fqp_mul(z1, z2)
        A = fqp_sub(fqp_sub(fqp_mul(fqp_mul(U, U), W), V_cubed), fqp_mul(V_squared_times_V2, 2))
        newx = fqp_mul(V, A)
        newy = fqp_sub(fqp_mul(U, fqp_sub(V_squared_times_V2, A)), fqp_mul(V_cubed, U2))
        newz = fqp_mul(V_cubed, W)
    return normalize1((newx, newy, newz))


# Elliptic curve point multiplication
def multiply(pt: Any, n: Any) -> Any:
    x1, y1, z1 = tuple(pt)
    if isinstance(x1, int):
        one = 1
        zero = 0
    else:
        degree = x1['degree']
        modulus_coeffs = x1['modulus_coeffs']
        one = FQP([1] + [0] * (degree-1), modulus_coeffs)
        zero = FQP([0] * degree, modulus_coeffs)
    if n == 0:
        return (one, one, zero)
    elif n == 1:
        return pt
    elif not n % 2:
        return multiply(double(pt), n // 2)
    else:
        return add(multiply(double(pt), int(n // 2)), pt)



def eq(p1: Any, p2: Any) -> Any:
    x1, y1, z1 = tuple(p1)
    x2, y2, z2 = tuple(p2)
    if isinstance(x1, int) and isinstance(x2, int):        
        return fq_eq(fq_mul(x1, z2), fq_mul(x2, z1)) and fq_eq(fq_mul(y1, z2), fq_mul(y2, z1))
    else:
        return fqp_eq(fqp_mul(x1, z2), fqp_mul(x2, z1)) and fqp_eq(fqp_mul(y1, z2), fqp_mul(y2, z1))


# "Twist" a point in E(FQ2) into a point in E(FQ12)
w = FQ12([0, 1] + [0] * 10)

# Convert P => -P
def neg(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z = tuple(pt)
    if isinstance(x, int):
        return (x, fq_neg(y), z)
    else:
        return (x, fqp_neg(y), z)


def normalize(pt):
    x, y, z = pt
    if isinstance(x, int):
        return (fq_div(x, z), fq_div(y, z))
    else:
        return (fqp_div(x, z), fqp_div(y, z))

def normalize1(pt):
    x, y = normalize(pt)
    if isinstance(x, int):
        one = 1
    else:
        degree = x['degree']
        modulus_coeffs = x['modulus_coeffs']
        one = FQP([1] + [0] * (degree-1), modulus_coeffs)
    return (x, y, one)

def twist(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z = tuple(pt)
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 18*x + 82
    xcoeffs = [fq_sub(x['coeffs'][0], fq_mul(x['coeffs'][1], 9)), x['coeffs'][1]]
    ycoeffs = [fq_sub(y['coeffs'][0], fq_mul(y['coeffs'][1], 9)), y['coeffs'][1]]
    zcoeffs = [fq_sub(z['coeffs'][0], fq_mul(z['coeffs'][1], 9)), z['coeffs'][1]]
    # Isomorphism into subfield of Z[p] / w**12 - 18 * w**6 + 82,
    # where w**6 = x
    nx = FQ12([xcoeffs[0]] + [0] * 5 + [xcoeffs[1]] + [0] * 5)
    ny = FQ12([ycoeffs[0]] + [0] * 5 + [ycoeffs[1]] + [0] * 5)
    nz = FQ12([zcoeffs[0]] + [0] * 5 + [zcoeffs[1]] + [0] * 5)
    # Divide x coord by w**2 and y coord by w**3
    return (fqp_mul(nx, fqp_pow(w, 2)), fqp_mul(ny, fqp_pow(w, 3)), nz)


def cast_point_to_fq12(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z  = tuple(pt)
    return (FQ12([x] + [0] * 11), FQ12([y] + [0] * 11), FQ12([z] + [0] * 11))


# Create a function representing the line between P1 and P2,
# and evaluate it at T
def linefunc(P1, P2, T):
    x1, y1, z1 = P1
    x2, y2, z2 = P2
    xt, yt, zt = T
    # points in projective coords: (x / z, y / z)
    # hence, m = (y2/z2 - y1/z1) / (x2/z2 - x1/z1)
    # multiply numerator and denominator by z1z2 to get values below
    if isinstance(x1, int):
        zero = FQ(0)
        m_numerator = fq_sub(fq_mul(y2, z1), fq_mul(y1, z2))
        m_denominator = fq_sub(fq_mul(x2, z1), fq_mul(x1, z2))
        if fq_ne(m_denominator, zero):
            # m * ((xt/zt) - (x1/z1)) - ((yt/zt) - (y1/z1))
            return fq_sub(fq_mul(m_numerator, fq_sub(fq_mul(xt, z1), fq_mul(x1, zt))), fq_mul(m_denominator, fq_sub(fq_mul(yt, z1), fq_mul(y1, zt)))), \
                fq_mul(fq_mul(m_denominator, zt), z1)
        elif fq_eq(m_numerator, zero):
            # m = 3(x/z)^2 / 2(y/z), multiply num and den by z**2
            m_numerator = fq_mul(fq_mul(x1, x1), 3)
            m_denominator = fq_mul(fq_mul(z1, y1), 2)
            return fq_sub(fq_mul(m_numerator, fq_sub(fq_mul(xt, z1), fq_mul(x1, zt))), fq_mul(m_denominator, fq_sub(fq_mul(yt, z1), fq_mul(y1, zt)))), \
                fq_mul(fq_mul(m_denominator, zt), z1)
        else:
            return fq_sub(fq_mul(xt, z1), fq_mul(x1, zt)), fq_mul(z1, zt)
    else:
        degree = x1['degree']
        modulus_coeffs = x1['modulus_coeffs']
        zero = FQP([0] * degree, modulus_coeffs)
        m_numerator = fqp_sub(fqp_mul(y2, z1), fqp_mul(y1, z2))
        m_denominator = fqp_sub(fqp_mul(x2, z1), fqp_mul(x1, z2))
        if fqp_ne(m_denominator, zero):
            # m * ((xt/zt) - (x1/z1)) - ((yt/zt) - (y1/z1))
            return fqp_sub(fqp_mul(m_numerator, fqp_sub(fqp_mul(xt, z1), fqp_mul(x1, zt))), fqp_mul(m_denominator, fqp_sub(fqp_mul(yt, z1), fqp_mul(y1, zt)))), \
                fqp_mul(fqp_mul(m_denominator, zt), z1)
        elif fqp_eq(m_numerator, zero):
            # m = 3(x/z)^2 / 2(y/z), multiply num and den by z**2
            m_numerator = fqp_mul(fqp_mul(x1, x1), 3)
            m_denominator = fqp_mul(fqp_mul(z1, y1), 2)
            return fqp_sub(fqp_mul(m_numerator, fqp_sub(fqp_mul(xt, z1), fqp_mul(x1, zt))), fqp_mul(m_denominator, fqp_sub(fqp_mul(yt, z1), fqp_mul(y1, zt)))), \
                fqp_mul(fqp_mul(m_denominator, zt), z1)
        else:
            return fqp_sub(fqp_mul(xt, z1), fqp_mul(x1, zt)), fqp_mul(z1, zt)


def miller_loop(Q: Any, P: Any) -> Any:
    if Q is None or P is None:
        return fq12_one()
    Q = normalize1(Q)
    P = normalize1(P)
    Q = (Q[0], Q[1], fq12_one())
    P = (P[0], P[1], fq12_one())
    R = Q
    f_num, f_den = fq12_one(), fq12_one()
    for b in pseudo_binary_encoding[63::-1]:
        _n, _d = linefunc(R, R, P)
        f_num = fqp_mul(fqp_mul(f_num, f_num), _n)
        f_den = fqp_mul(fqp_mul(f_den, f_den), _d)
        R = double(R)
        if b == 1:
            _n, _d = linefunc(R, Q, P)
            f_num = fqp_mul(f_num, _n)
            f_den = fqp_mul(f_den, _d)
            R = add(R, Q)
        elif b == -1:
            nQ = neg(Q)
            _n, _d = linefunc(R, nQ, P)
            f_num = fqp_mul(f_num, _n)
            f_den = fqp_mul(f_den, _d)
            R = add(R, nQ)
    assert R == multiply(Q, ate_loop_count)
    Q1 = (fqp_pow(Q[0], field_modulus), fqp_pow(Q[1], field_modulus), fqp_pow(Q[2], field_modulus))
    assert is_on_curve(Q1, b12)
    nQ2 = (fqp_pow(Q1[0], field_modulus), fqp_pow(fqp_neg(Q1[1]), field_modulus), fqp_pow(Q1[2], field_modulus))
    assert is_on_curve(nQ2, b12)
    _n1, _d1 = linefunc(R, Q1, P)
    R = add(R, Q1)
    _n2, _d2 = linefunc(R, nQ2, P)
    f = fqp_mul(fqp_mul(f_num, _n1), fqp_div(_n2, fqp_mul(fqp_mul(f_den, _d1), _d2)))
    # R = add(R, nQ2) This line is in many specifications but it technically does nothing
    return f

# Pairing computation
# Curve is y**2 = x**3 + 3
b = FQ(3)
# Twisted curve over FQ**2
b2 = fqp_div(FQ2([3, 0]), FQ2([9, 1]))
# Extension curve over FQ**12; same b value as over FQ
b12 = FQ12([3] + [0] * 11)


def pairing(Q: Any, P: Any, final_exp: bool = True) -> Any:
    assert is_on_curve(P, b), f'P is not on the curve. \n{P}'
    assert is_on_curve(Q, b2), f'Q is not on the curve. \n{Q}'
    if fq_eq(P[-1], fq_zero()) or fqp_eq(Q[-1], fq2_zero()):
        return fq12_one()
    r = miller_loop(twist(Q), cast_point_to_fq12(P))
    if final_exp:
        r = final_exponentiate(r)
    return r


def final_exponentiate(p: Any) -> Any:
    return fqp_pow(p, ((field_modulus ** 12 - 1) // curve_order))


# Generator for curve over FQ
G1 = (FQ(1), FQ(2), FQ(1))
# Generator for twisted curve over FQ2
G2 = (FQ2([10857046999023057135944570762232829481370756359578518086990519993285655852781, 11559732032986387107991004021392285783925812861821192530917403151452391805634]),
      FQ2([8495653923123431417604973247489272438418190587263600148770280649306958101930, 4082367875863433681332203403145435568316851327593401208105741076214120093531]),
      fq2_one()
    )

# Check that the twist creates a point that is on the curve
G12 = twist(G2)
assert is_on_curve(G12, b12)