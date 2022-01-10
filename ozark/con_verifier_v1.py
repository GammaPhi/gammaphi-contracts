# con_verifier_v1
# The prime modulus of the field
field_modulus = 21888242871839275222246405745257275088696311157297823662689037894645226208583

# The modulus of the polynomial in this representation of FQ12
FQ12_modulus_coeffs = [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0] # Implied + [1]
pseudo_binary_encoding = [0, 0, 0, 1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 0, 1, 0,
                          0, 1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1, 1,
                          1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 1,
                          1, 0, 0, -1, 0, 0, 0, 1, 1, 0, -1, 0, 0, 1, 0, 1, 1]


# Extended euclidean algorithm to find modular inverses for integers
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


def fq_one(n: int = None) -> int:
    return FQ(1)


def fq_zero(n: int = None) -> int:
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


def fqp_add(self: list, other: list) -> list:
    assert isinstance(other, list)
    other_coeffs = other
    return [fq_add(x, y) for x,y in zip(self, other_coeffs)]


def fqp_sub(self: list, other: list) -> list:
    assert isinstance(other, list)
    other_coeffs = other
    return [fq_sub(x, y) for x,y in zip(self, other_coeffs)]


def modulus_coeffs_for_degree(degree: int):
    if degree == 2:
        return [1, 0]
    elif degree == 12:
        return FQ12_modulus_coeffs
    else:
        assert False, f'Attempting to get modulus coeffs for degree {degree}'


def fqp_mul(self: list, other: Any) -> list:
    assert not isinstance(self, int), f'Called fqp_mul with an integer: {self}'
    if isinstance(other, int):
        return [fq_mul(c, other) for c in self]
    else:
        assert isinstance(other, list)
        degree = len(self)
        coeffs = self
        modulus_coeffs = modulus_coeffs_for_degree(degree)
        other_coeffs = other
        b = [0 for i in range(degree * 2 - 1)]
        for i in range(degree):
            for j in range(degree):
                b[i + j] = fq_add(b[i + j], fq_mul(coeffs[i], other_coeffs[j]))
        while len(b) > degree:
            exp, top = len(b) - degree - 1, b.pop()
            for i in range(degree):
                b[exp + i] = fq_sub(b[exp + i], fq_mul(top, FQ(modulus_coeffs[i])))
        return b


def fqp_div(self: list, other: Any) -> list:
    if isinstance(other, int):
        return [fq_div(c, other) for c in self]
    else:
        assert isinstance(other, list)
        return fqp_mul(self, fqp_inv(other))


def fqp_pow(self: list, other: int) -> list:
    #print(f'Calling fq_pow with: {self}, {other}')
    degree = len(self)
    o = [1] + [0] * (degree - 1)
    t = self
    while other > 0:
        if other & 1:
            o = fqp_mul(o, t)
        other >>= 1
        t = fqp_mul(t, t)
    return o


# Extended euclidean algorithm used to find the modular inverse
def fqp_inv(self: list) -> list:
    degree = len(self)
    modulus_coeffs = modulus_coeffs_for_degree(degree)
    coeffs = self
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
    return fqp_div(lm[:degree], low[0])


def fqp_eq(self: list, other: list) -> bool:
    assert isinstance(other, list)
    coeffs = self
    other_coeffs = other
    for c1, c2 in zip(coeffs, other_coeffs):
        if fq_ne(c1, c2):
            return False
    return True


def fqp_ne(self: list, other: list) -> bool:
    return not fqp_eq(self, other)


def fqp_neg(self: list) -> list:
    coeffs = self
    return [-c for c in coeffs]


# The quadratic extension field
def FQ2(coeffs: list) -> list:
    assert len(coeffs) == 2, f'FQ2 must have 2 coefficients but had {len(coeffs)}'
    return coeffs


# The 12th-degree extension field
def FQ12(coeffs: list) -> list:
    assert len(coeffs) == 12
    return coeffs


def fq2_one(n: int = 0) -> list:
    return [1, 0]


def fq2_zero(n: int = 0) -> list:
    return [0, 0]


def fq12_one(n: int = 0) -> list:
    return [1] + [0] * 11


def fq12_zero(n: int = 0) -> list:
    return [0] * 12


# Check if a point is the point at infinity
def is_inf(pt: Any) -> bool:
    x, y, z = pt
    if isinstance(x, int):
        return fq_eq(z, 0)
    else:
        zero = [0] * len(z)
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
def double(pt: Any) -> Any:
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
    return (newx, newy, newz)


# Elliptic curve addition
def add(p1: Any, p2: Any) -> Any:
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
        degree = len(x1)        
        one = [1] + [0] * (degree-1)
        zero = [0] * degree
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
        degree = len(x1)
        one = [1] + [0] * (degree-1)
        zero = [0] * degree
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


def normalize(pt: Any) -> Any:
    x, y, z = pt
    if isinstance(x, int):
        return (fq_div(x, z), fq_div(y, z))
    else:
        return (fqp_div(x, z), fqp_div(y, z))


def normalize1(pt: Any) -> Any:
    x, y = normalize(pt)
    if isinstance(x, int):
        one = 1
    else:
        degree = len(x)
        one = [1] + [0] * (degree-1)
    return (x, y, one)


def twist(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z = tuple(pt)
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 18*x + 82
    xcoeffs = [fq_sub(x[0], fq_mul(x[1], 9)), x[1]]
    ycoeffs = [fq_sub(y[0], fq_mul(y[1], 9)), y[1]]
    zcoeffs = [fq_sub(z[0], fq_mul(z[1], 9)), z[1]]
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
def linefunc(P1: Any, P2: Any, T: Any) -> Any:
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
        degree = len(x1)
        zero = [0] * degree
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
        n, d = linefunc(R, R, P)
        f_num = fqp_mul(fqp_mul(f_num, f_num), n)
        f_den = fqp_mul(fqp_mul(f_den, f_den), d)
        R = double(R)
        if b == 1:
            n, d = linefunc(R, Q, P)
            f_num = fqp_mul(f_num, n)
            f_den = fqp_mul(f_den, d)
            R = add(R, Q)
        elif b == -1:
            nQ = neg(Q)
            n, d = linefunc(R, nQ, P)
            f_num = fqp_mul(f_num, n)
            f_den = fqp_mul(f_den, d)
            R = add(R, nQ)
    Q1 = (fqp_pow(Q[0], field_modulus), fqp_pow(Q[1], field_modulus), fqp_pow(Q[2], field_modulus))
    nQ2 = (fqp_pow(Q1[0], field_modulus), fqp_pow(fqp_neg(Q1[1]), field_modulus), fqp_pow(Q1[2], field_modulus))
    n1, d1 = linefunc(R, Q1, P)
    R = add(R, Q1)
    n2, d2 = linefunc(R, nQ2, P)
    f = fqp_mul(fqp_mul(f_num, n1), fqp_div(n2, fqp_mul(fqp_mul(f_den, d1), d2)))
    # R = add(R, nQ2) This line is in many specifications but it technically does nothing
    return f


# Pairing computation
def pairing(Q: Any, P: Any) -> Any:
    b = FQ(3)
    # Twisted curve over FQ**2
    b2 = fqp_div(FQ2([3, 0]), FQ2([9, 1]))
    assert is_on_curve(P, b), f'P is not on the curve.'
    assert is_on_curve(Q, b2), f'Q is not on the curve.'
    if fq_eq(P[-1], fq_zero()) or fqp_eq(Q[-1], fq2_zero()):
        return fq12_one()
    r = miller_loop(twist(Q), cast_point_to_fq12(P))
    return r


def final_exponentiate(p: Any) -> Any:
    return fqp_pow(p, ((field_modulus ** 12 - 1) // 21888242871839275222246405745257275088548364400416034343698204186575808495617))


vk = {
    "IC": [
        [
            16225148364316337376768119297456868908427925829817748684139175309620217098814,
            5167268689450204162046084442581051565997733233062478317813755636162413164690,
            1
        ],
        [
            12882377842072682264979317445365303375159828272423495088911985689463022094260,
            19488215856665173565526758360510125932214252767275816329232454875804474844786,
            1
        ],
        [
            13083492661683431044045992285476184182144099829507350352128615182516530014777,
            602051281796153692392523702676782023472744522032670801091617246498551238913,
            1
        ],
        [
            9732465972180335629969421513785602934706096902316483580882842789662669212890,
            2776526698606888434074200384264824461688198384989521091253289776235602495678,
            1
        ],
        [
            8586364274534577154894611080234048648883781955345622578531233113180532234842,
            21276134929883121123323359450658320820075698490666870487450985603988214349407,
            1
        ],
        [
            4910628533171597675018724709631788948355422829499855033965018665300386637884,
            20532468890024084510431799098097081600480376127870299142189696620752500664302,
            1
        ],
        [
            15335858102289947642505450692012116222827233918185150176888641903531542034017,
            5311597067667671581646709998171703828965875677637292315055030353779531404812,
            1
        ]
    ],
    "vk_alfa_1": [
        20692898189092739278193869274495556617788530808486270118371701516666252877969,
        11713062878292653967971378194351968039596396853904572879488166084231740557279,
        1
    ],
    "vk_beta_2": [
        [
            281120578337195720357474965979947690431622127986816839208576358024608803542,
            12168528810181263706895252315640534818222943348193302139358377162645029937006
        ],
        [
            9011703453772030375124466642203641636825223906145908770308724549646909480510,
            16129176515713072042442734839012966563817890688785805090011011570989315559913
        ],
        [
            1,
            0
        ]
    ],
    "vk_gamma_2": [
        [
            10857046999023057135944570762232829481370756359578518086990519993285655852781,
            11559732032986387107991004021392285783925812861821192530917403151452391805634
        ],
        [
            8495653923123431417604973247489272438418190587263600148770280649306958101930,
            4082367875863433681332203403145435568316851327593401208105741076214120093531
        ],
        [
            1,
            0
        ]
    ],
    "vk_delta_2": [
        [
            150879136433974552800030963899771162647715069685890547489132178314736470662,
            21280594949518992153305586783242820682644996932183186320680800072133486887432
        ],
        [
            11434086686358152335540554643130007307617078324975981257823476472104616196090,
            1081836006956609894549771334721413187913047383331561601606260283167615953295
        ],
        [
            1,
            0
        ]
    ],
}


def verify(
    inputs: list, 
    proof: dict) -> int:
    snark_scalar_field = 21888242871839275222246405745257275088548364400416034343698204186575808495617
    IC = vk['IC']
    assert len(inputs) + 1 == len(IC), "verifier-bad-input"
    # Compute the linear combination vk_x
    vk_x = IC[0]
    for i in range(len(inputs)):
        assert inputs[i] < snark_scalar_field, "verifier-gte-snark-scalar-field"
        vk_x = add(vk_x, multiply(IC[i+1], inputs[i]))


    p1 = [
        neg(proof['A']),
        vk['vk_alfa_1'],
        vk_x,
        proof['C']
    ]
    p2 = [
        (proof['B'][0], proof['B'][1], proof['B'][2]),
        vk['vk_beta_2'],
        vk['vk_gamma_2'],
        vk['vk_delta_2']
    ]
    x = fq12_one()
    for i in range(len(p1)):
        if is_inf(p2[i]) or is_inf(p1[i]):
            continue
        y = pairing(p2[i], p1[i])
        x = fqp_mul(x, y)

    x = final_exponentiate(x)    

    if fqp_ne(x, fq12_one()):
        return 1
    return 0


@export
def verify_proof(
    a: list,
    b: list,
    c: list,
    inputs: list
) -> bool:
    proof = {}
    proof['A'] = (int(a[0]), int(a[1]), int(a[2]))
    proof['B'] = (
        FQ2([int(b[0][0]), int(b[0][1])]), 
        FQ2([int(b[1][0]), int(b[1][1])]),
        FQ2([int(b[2][0]), int(b[2][1])])
    )
    proof['C'] = (int(c[0]), int(c[1]), int(c[2]))
    inputs = [int(i) for i in inputs]
    if verify(inputs, proof) == 0:
        return True
    else:
        return False