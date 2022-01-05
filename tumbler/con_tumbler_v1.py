# con_pairing_v1

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
curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Extended euclidean algorithm to find modular inverses for
# integers

@export
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


@export
def FQ(n: int) -> int:
    return n % field_modulus


@export
def fq_add(self: int, other: int) -> int:
    return (self + other) % field_modulus


@export
def fq_mul(self: int, other: int) -> int:
    return (self * other) % field_modulus


@export
def fq_sub(self: int, other: int) -> int:
    return (self - other) % field_modulus


@export
def fq_div(self: int, other: int) -> int:
    assert isinstance(other, int), 'Invalid other. Should be an int.'
    return fq_mul(self, inv(other, field_modulus)) % field_modulus


@export
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

@export
def fq_eq(self: int, other: int) -> bool:
    return self == other


@export
def fq_ne(self: int, other: int) -> int:
    return not fq_eq(self, other)


@export
def fq_neg(self: int) -> int:
    return -self


@export
def fq_one(n: int = None) -> int:
    return FQ(1)

@export
def fq_zero(n: int = None) -> int:
    return FQ(0)

# Utility methods for polynomial math
@export
def deg(p: list) -> int:
    d = len(p) - 1
    while p[d] == 0 and d:
        d -= 1
    return d

@export
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



@export
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



@export
def fqp_add(self: dict, other: dict) -> dict:
    assert isinstance(other, (dict, list))
    other_coeffs = other if isinstance(other, list) else other['coeffs']
    return FQP([fq_add(x, y) for x,y in zip(self['coeffs'], other_coeffs)], self['modulus_coeffs'])


@export
def fqp_sub(self: dict, other: dict) -> dict:
    assert isinstance(other, (dict, list))
    other_coeffs = other if isinstance(other, list) else other['coeffs']
    return FQP([fq_sub(x, y) for x,y in zip(self['coeffs'], other_coeffs)], self['modulus_coeffs'])


@export
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


@export
def fqp_div(self: dict, other: Any) -> dict:
    if isinstance(other, int):
        return FQP([fq_div(c, other) for c in self['coeffs']], self['modulus_coeffs'])
    else:
        assert isinstance(other, dict)
        return fqp_mul(self, fqp_inv(other))


@export
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
@export
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


@export
def fqp_eq(self: dict, other: dict) -> bool:
    assert isinstance(other, dict)
    coeffs = self['coeffs']
    other_coeffs = other['coeffs']
    for c1, c2 in zip(coeffs, other_coeffs):
        if fq_ne(c1, c2):
            return False
    return True


@export
def fqp_ne(self: dict, other: dict) -> bool:
    return not fqp_eq(self, other)


@export
def fqp_neg(self: dict) -> dict:
    modulus_coeffs = self['modulus_coeffs']
    coeffs = self['coeffs']
    return FQP([-c for c in coeffs], modulus_coeffs)

# The quadratic extension field
@export
def FQ2(coeffs: list) -> dict:
    assert len(coeffs) == 2, f'FQ2 must have 2 coefficients but had {len(coeffs)}'
    return FQP(coeffs, [1, 0])

# The 12th-degree extension field
@export
def FQ12(coeffs: list) -> dict:
    assert len(coeffs) == 12
    return FQP(coeffs, FQ12_modulus_coeffs)

@export
def fq2_one(n: int = 0) -> dict:
    return FQ2([1, 0])

@export
def fq2_zero(n: int = 0) -> dict:
    return FQ2([0, 0])

@export
def fq12_one(n: int = 0) -> dict:
    return FQ12([1] + [0] * (len(FQ12_modulus_coeffs) - 1))

@export
def fq12_zero(n: int = 0) -> dict:
    return FQ12([0] * len(FQ12_modulus_coeffs))

# Check if a point is the point at infinity
@export
def is_inf(pt: Any) -> bool:
    x, y, z = pt
    if isinstance(x, int):
        return fq_eq(z, 0)
    else:
        zero = FQP([0] * z['degree'], modulus_coeffs=z['modulus_coeffs'])
        return fqp_eq(z, zero)


# Check that a point is on the curve defined by y**2 == x**3 + b
@export
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
@export
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
    return normalize1((newx, newy, newz))


# Elliptic curve addition
@export
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
@export
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



@export
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
@export
def neg(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z = tuple(pt)
    if isinstance(x, int):
        return (x, fq_neg(y), z)
    else:
        return (x, fqp_neg(y), z)


@export
def normalize(pt: Any) -> Any:
    x, y, z = pt
    if isinstance(x, int):
        return (fq_div(x, z), fq_div(y, z))
    else:
        return (fqp_div(x, z), fqp_div(y, z))

@export
def normalize1(pt: Any) -> Any:
    x, y = normalize(pt)
    if isinstance(x, int):
        one = 1
    else:
        degree = x['degree']
        modulus_coeffs = x['modulus_coeffs']
        one = FQP([1] + [0] * (degree-1), modulus_coeffs)
    return (x, y, one)

@export
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


@export
def cast_point_to_fq12(pt: Any) -> Any:
    if pt is None:
        return None
    x, y, z  = tuple(pt)
    return (FQ12([x] + [0] * 11), FQ12([y] + [0] * 11), FQ12([z] + [0] * 11))


# Create a function representing the line between P1 and P2,
# and evaluate it at T
@export
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


@export
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
    assert R == multiply(Q, ate_loop_count)
    Q1 = (fqp_pow(Q[0], field_modulus), fqp_pow(Q[1], field_modulus), fqp_pow(Q[2], field_modulus))
    assert is_on_curve(Q1, b12)
    nQ2 = (fqp_pow(Q1[0], field_modulus), fqp_pow(fqp_neg(Q1[1]), field_modulus), fqp_pow(Q1[2], field_modulus))
    assert is_on_curve(nQ2, b12)
    n1, d1 = linefunc(R, Q1, P)
    R = add(R, Q1)
    n2, d2 = linefunc(R, nQ2, P)
    f = fqp_mul(fqp_mul(f_num, n1), fqp_div(n2, fqp_mul(fqp_mul(f_den, d1), d2)))
    # R = add(R, nQ2) This line is in many specifications but it technically does nothing
    return f

# Pairing computation
# Curve is y**2 = x**3 + 3
b = FQ(3)
# Twisted curve over FQ**2
b2 = fqp_div(FQ2([3, 0]), FQ2([9, 1]))
# Extension curve over FQ**12; same b value as over FQ
b12 = FQ12([3] + [0] * 11)


@export
def pairing(Q: Any, P: Any, final_exp: bool = True) -> Any:
    assert is_on_curve(P, b), f'P is not on the curve. \n{P}'
    assert is_on_curve(Q, b2), f'Q is not on the curve. \n{Q}'
    if fq_eq(P[-1], fq_zero()) or fqp_eq(Q[-1], fq2_zero()):
        return fq12_one()
    r = miller_loop(twist(Q), cast_point_to_fq12(P))
    if final_exp:
        r = final_exponentiate(r)
    return r


@export
def final_exponentiate(p: Any) -> Any:
    return fqp_pow(p, ((field_modulus ** 12 - 1) // curve_order))

# con_mimc_sponge_v1

SEED = "mimcsponge"
NROUNDS = 220


curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
cts = [0, 7120861356467848435263064379192047478074060781135320967663101236819528304084, 5024705281721889198577876690145313457398658950011302225525409148828000436681, 17980351014018068290387269214713820287804403312720763401943303895585469787384, 19886576439381707240399940949310933992335779767309383709787331470398675714258, 1213715278223786725806155661738676903520350859678319590331207960381534602599, 18162138253399958831050545255414688239130588254891200470934232514682584734511, 7667462281466170157858259197976388676420847047604921256361474169980037581876, 7207551498477838452286210989212982851118089401128156132319807392460388436957, 9864183311657946807255900203841777810810224615118629957816193727554621093838, 4798196928559910300796064665904583125427459076060519468052008159779219347957, 17387238494588145257484818061490088963673275521250153686214197573695921400950, 10005334761930299057035055370088813230849810566234116771751925093634136574742, 11897542014760736209670863723231849628230383119798486487899539017466261308762, 16771780563523793011283273687253985566177232886900511371656074413362142152543, 749264854018824809464168489785113337925400687349357088413132714480582918506, 3683645737503705042628598550438395339383572464204988015434959428676652575331, 7556750851783822914673316211129907782679509728346361368978891584375551186255, 20391289379084797414557439284689954098721219201171527383291525676334308303023, 18146517657445423462330854383025300323335289319277199154920964274562014376193, 8080173465267536232534446836148661251987053305394647905212781979099916615292, 10796443006899450245502071131975731672911747129805343722228413358507805531141, 5404287610364961067658660283245291234008692303120470305032076412056764726509, 4623894483395123520243967718315330178025957095502546813929290333264120223168, 16845753148201777192406958674202574751725237939980634861948953189320362207797, 4622170486584704769521001011395820886029808520586507873417553166762370293671, 16688277490485052681847773549197928630624828392248424077804829676011512392564, 11878652861183667748838188993669912629573713271883125458838494308957689090959, 2436445725746972287496138382764643208791713986676129260589667864467010129482, 1888098689545151571063267806606510032698677328923740058080630641742325067877, 148924106504065664829055598316821983869409581623245780505601526786791681102, 18875020877782404439294079398043479420415331640996249745272087358069018086569, 15189693413320228845990326214136820307649565437237093707846682797649429515840, 19669450123472657781282985229369348220906547335081730205028099210442632534079, 5521922218264623411380547905210139511350706092570900075727555783240701821773, 4144769320246558352780591737261172907511489963810975650573703217887429086546, 10097732913112662248360143041019433907849917041759137293018029019134392559350, 1720059427972723034107765345743336447947522473310069975142483982753181038321, 6302388219880227251325608388535181451187131054211388356563634768253301290116, 6745410632962119604799318394592010194450845483518862700079921360015766217097, 10858157235265583624235850660462324469799552996870780238992046963007491306222, 20241898894740093733047052816576694435372877719072347814065227797906130857593, 10165780782761211520836029617746977303303335603838343292431760011576528327409, 2832093654883670345969792724123161241696170611611744759675180839473215203706, 153011722355526826233082383360057587249818749719433916258246100068258954737, 20196970640587451358539129330170636295243141659030208529338914906436009086943, 3180973917010545328313139835982464870638521890385603025657430208141494469656, 17198004293191777441573635123110935015228014028618868252989374962722329283022, 7642160509228669138628515458941659189680509753651629476399516332224325757132, 19346204940546791021518535594447257347218878114049998691060016493806845179755, 11501810868606870391127866188394535330696206817602260610801897042898616817272, 3113973447392053821824427670386252797811804954746053461397972968381571297505, 6545064306297957002139416752334741502722251869537551068239642131448768236585, 5203908808704813498389265425172875593837960384349653691918590736979872578408, 2246692432011290582160062129070762007374502637007107318105405626910313810224, 11760570435432189127645691249600821064883781677693087773459065574359292849137, 5543749482491340532547407723464609328207990784853381797689466144924198391839, 8837549193990558762776520822018694066937602576881497343584903902880277769302, 12855514863299373699594410385788943772765811961581749194183533625311486462501, 5363660674689121676875069134269386492382220935599781121306637800261912519729, 13162342403579303950549728848130828093497701266240457479693991108217307949435, 916941639326869583414469202910306428966657806899788970948781207501251816730, 15618589556584434434009868216186115416835494805174158488636000580759692174228, 8959562060028569701043973060670353733575345393653685776974948916988033453971, 16390754464333401712265575949874369157699293840516802426621216808905079127650, 168282396747788514908709091757591226095443902501365500003618183905496160435, 8327443473179334761744301768309008451162322941906921742120510244986704677004, 17213012626801210615058753489149961717422101711567228037597150941152495100640, 10394369641533736715250242399198097296122982486516256408681925424076248952280, 17784386835392322654196171115293700800825771210400152504776806618892170162248, 16533189939837087893364000390641148516479148564190420358849587959161226782982, 18725396114211370207078434315900726338547621160475533496863298091023511945076, 7132325028834551397904855671244375895110341505383911719294705267624034122405, 148317947440800089795933930720822493695520852448386394775371401743494965187, 19001050671757720352890779127693793630251266879994702723636759889378387053056, 18824274411769830274877839365728651108434404855803844568234862945613766611460, 12771414330193951156383998390424063470766226667986423961689712557338777174205, 11332046574800279729678603488745295198038913503395629790213378101166488244657, 9607550223176946388146938069307456967842408600269548190739947540821716354749, 8756385288462344550200229174435953103162307705310807828651304665320046782583, 176061952957067086877570020242717222844908281373122372938833890096257042779, 12200212977482648306758992405065921724409841940671166017620928947866825250857, 10868453624107875516866146499877130701929063632959660262366632833504750028858, 2016095394399807253596787752134573207202567875457560571095586743878953450738, 21815578223768330433802113452339488275704145896544481092014911825656390567514, 4923772847693564777744725640710197015181591950368494148029046443433103381621, 1813584943682214789802230765734821149202472893379265320098816901270224589984, 10810123816265612772922113403831964815724109728287572256602010709288980656498, 1153669123397255702524721206511185557982017410156956216465120456256288427021, 5007518659266430200134478928344522649876467369278722765097865662497773767152, 2511432546938591792036639990606464315121646668029252285288323664350666551637, 32883284540320451295484135704808083452381176816565850047310272290579727564, 10484856914279112612610993418405543310546746652738541161791501150994088679557, 2026733759645519472558796412979210009170379159866522399881566309631434814953, 14731806221235869882801331463708736361296174006732553130708107037190460654379, 14740327483193277147065845135561988641238516852487657117813536909482068950652, 18787428285295558781869865751953016580493190547148386433580291216673009884554, 3804047064713122820157099453648459188816376755739202017447862327783289895072, 16709604795697901641948603019242067672006293290826991671766611326262532802914, 11061717085931490100602849654034280576915102867237101935487893025907907250695, 2821730726367472966906149684046356272806484545281639696873240305052362149654, 17467794879902895769410571945152708684493991588672014763135370927880883292655, 1571520786233540988201616650622796363168031165456869481368085474420849243232, 10041051776251223165849354194892664881051125330236567356945669006147134614302, 3981753758468103976812813304477670033098707002886030847251581853700311567551, 4365864398105436789177703571412645548020537580493599380018290523813331678900, 2391801327305361293476178683853802679507598622000359948432171562543560193350, 214219368547551689972421167733597094823289857206402800635962137077096090722, 18192064100315141084242006659317257023098826945893371479835220462302399655674, 15487549757142039139328911515400805508248576685795694919457041092150651939253, 10142447197759703415402259672441315777933858467700579946665223821199077641122, 11246573086260753259993971254725613211193686683988426513880826148090811891866, 6574066859860991369704567902211886840188702386542112593710271426704432301235, 11311085442652291634822798307831431035776248927202286895207125867542470350078, 20977948360215259915441258687649465618185769343138135384346964466965010873779, 792781492853909872425531014397300057232399608769451037135936617996830018501, 5027602491523497423798779154966735896562099398367163998686335127580757861872, 14595204575654316237672764823862241845410365278802914304953002937313300553572, 13973538843621261113924259058427434053808430378163734641175100160836376897004, 16395063164993626722686882727042150241125309409717445381854913964674649318585, 8465768840047024550750516678171433288207841931251654898809033371655109266663, 21345603324471810861925019445720576814602636473739003852898308205213912255830, 21171984405852590343970239018692870799717057961108910523876770029017785940991, 10761027113757988230637066281488532903174559953630210849190212601991063767647, 6678298831065390834922566306988418588227382406175769592902974103663687992230, 4993662582188632374202316265508850988596880036291765531885657575099537176757, 18364168158495573675698600238443218434246806358811328083953887470513967121206, 3506345610354615013737144848471391553141006285964325596214723571988011984829, 248732676202643792226973868626360612151424823368345645514532870586234380100, 10090204501612803176317709245679152331057882187411777688746797044706063410969, 21297149835078365363970699581821844234354988617890041296044775371855432973500, 16729368143229828574342820060716366330476985824952922184463387490091156065099, 4467191506765339364971058668792642195242197133011672559453028147641428433293, 8677548159358013363291014307402600830078662555833653517843708051504582990832, 1022951765127126818581466247360193856197472064872288389992480993218645055345, 1888195070251580606973417065636430294417895423429240431595054184472931224452, 4221265384902749246920810956363310125115516771964522748896154428740238579824, 2825393571154632139467378429077438870179957021959813965940638905853993971879, 19171031072692942278056619599721228021635671304612437350119663236604712493093, 10780807212297131186617505517708903709488273075252405602261683478333331220733, 18230936781133176044598070768084230333433368654744509969087239465125979720995, 16901065971871379877929280081392692752968612240624985552337779093292740763381, 146494141603558321291767829522948454429758543710648402457451799015963102253, 2492729278659146790410698334997955258248120870028541691998279257260289595548, 2204224910006646535594933495262085193210692406133533679934843341237521233504, 16062117410185840274616925297332331018523844434907012275592638570193234893570, 5894928453677122829055071981254202951712129328678534592916926069506935491729, 4947482739415078212217504789923078546034438919537985740403824517728200332286, 16143265650645676880461646123844627780378251900510645261875867423498913438066, 397690828254561723549349897112473766901585444153303054845160673059519614409, 11272653598912269895509621181205395118899451234151664604248382803490621227687, 15566927854306879444693061574322104423426072650522411176731130806720753591030, 14222898219492484180162096141564251903058269177856173968147960855133048449557, 16690275395485630428127725067513114066329712673106153451801968992299636791385, 3667030990325966886479548860429670833692690972701471494757671819017808678584, 21280039024501430842616328642522421302481259067470872421086939673482530783142, 15895485136902450169492923978042129726601461603404514670348703312850236146328, 7733050956302327984762132317027414325566202380840692458138724610131603812560, 438123800976401478772659663183448617575635636575786782566035096946820525816, 814913922521637742587885320797606426167962526342166512693085292151314976633, 12368712287081330853637674140264759478736012797026621876924395982504369598764, 2494806857395134874309386694756263421445039103814920780777601708371037591569, 16101132301514338989512946061786320637179843435886825102406248183507106312877, 6252650284989960032925831409804233477770646333900692286731621844532438095656, 9277135875276787021836189566799935097400042171346561246305113339462708861695, 10493603554686607050979497281838644324893776154179810893893660722522945589063, 8673089750662709235894359384294076697329948991010184356091130382437645649279, 9558393272910366944245875920138649617479779893610128634419086981339060613250, 19012287860122586147374214541764572282814469237161122489573881644994964647218, 9783723818270121678386992630754842961728702994964214799008457449989291229500, 15550788416669474113213749561488122552422887538676036667630838378023479382689, 15016165746156232864069722572047169071786333815661109750860165034341572904221, 6506225705710197163670556961299945987488979904603689017479840649664564978574, 10796631184889302076168355684722130903785890709107732067446714470783437829037, 19871836214837460419845806980869387567383718044439891735114283113359312279540, 20871081766843466343749609089986071784031203517506781251203251608363835140622, 5100105771517691442278432864090229416166996183792075307747582375962855820797, 8777887112076272395250620301071581171386440850451972412060638225741125310886, 5300440870136391278944213332144327695659161151625757537632832724102670898756, 1205448543652932944633962232545707633928124666868453915721030884663332604536, 5542499997310181530432302492142574333860449305424174466698068685590909336771, 11028094245762332275225364962905938096659249161369092798505554939952525894293, 19187314764836593118404597958543112407224947638377479622725713735224279297009, 17047263688548829001253658727764731047114098556534482052135734487985276987385, 19914849528178967155534624144358541535306360577227460456855821557421213606310, 2929658084700714257515872921366736697080475676508114973627124569375444665664, 15092262360719700162343163278648422751610766427236295023221516498310468956361, 21578580340755653236050830649990190843552802306886938815497471545814130084980, 1258781501221760320019859066036073675029057285507345332959539295621677296991, 3819598418157732134449049289585680301176983019643974929528867686268702720163, 8653175945487997845203439345797943132543211416447757110963967501177317426221, 6614652990340435611114076169697104582524566019034036680161902142028967568142, 19212515502973904821995111796203064175854996071497099383090983975618035391558, 18664315914479294273286016871365663486061896605232511201418576829062292269769, 11498264615058604317482574216318586415670903094838791165247179252175768794889, 10814026414212439999107945133852431304483604215416531759535467355316227331774, 17566185590731088197064706533119299946752127014428399631467913813769853431107, 14016139747289624978792446847000951708158212463304817001882956166752906714332, 8242601581342441750402731523736202888792436665415852106196418942315563860366, 9244680976345080074252591214216060854998619670381671198295645618515047080988, 12216779172735125538689875667307129262237123728082657485828359100719208190116, 10702811721859145441471328511968332847175733707711670171718794132331147396634, 6479667912792222539919362076122453947926362746906450079329453150607427372979, 15117544653571553820496948522381772148324367479772362833334593000535648316185, 6842203153996907264167856337497139692895299874139131328642472698663046726780, 12732823292801537626009139514048596316076834307941224506504666470961250728055, 6936272626871035740815028148058841877090860312517423346335878088297448888663, 17297554111853491139852678417579991271009602631577069694853813331124433680030, 16641596134749940573104316021365063031319260205559553673368334842484345864859, 7400481189785154329569470986896455371037813715804007747228648863919991399081, 2273205422216987330510475127669563545720586464429614439716564154166712854048, 15162538063742142685306302282127534305212832649282186184583465569986719234456, 5628039096440332922248578319648483863204530861778160259559031331287721255522, 16085392195894691829567913404182676871326863890140775376809129785155092531260, 14227467863135365427954093998621993651369686288941275436795622973781503444257, 18224457394066545825553407391290108485121649197258948320896164404518684305122, 274945154732293792784580363548970818611304339008964723447672490026510689427, 11050822248291117548220126630860474473945266276626263036056336623671308219529, 2119542016932434047340813757208803962484943912710204325088879681995922344971, 0]


def mimc_hash(xL_in: str, xR_in: str, k: str) -> tuple:
    xL = int(xL_in)
    xR = int(xR_in)
    k = int(k)
    
    for i in range(NROUNDS):
        c = cts[i]
        t = mimc_add(xL, k) if i == 0 else mimc_add(mimc_add(xL, k), c)
        xR_tmp = int(xR)
        if i < NROUNDS - 1:
            xR = xL
            xL = mimc_add(xR_tmp, mimc_exp(t, 5))
        else:
            xR = mimc_add(xR_tmp, mimc_exp(t, 5))
    
    return mimc_affine(xL), mimc_affine(xR)


def mimc_multi_hash(arr: list, key: str = None, num_outputs: int = 1):
    key = int(key or 0)
    r = 0
    c = 0
    for i in range(len(arr)):
        r = mimc_add(r, int(arr[i]))
        r, c = mimc_hash(r, c, key)
    outputs = [mimc_affine(r)]
    for i in range(1, num_outputs):
        r, c = mimc_hash(r, c, key)
        outputs.append(mimc_affine(r))
    return outputs


@export
def hash_left_right(left: str, right: str) -> str:
    assert int(left) < curve_order, 'left should be inside the field'
    assert int(right) < curve_order, 'right should be inside the field'
    return str(mimc_multi_hash([left, right])[0])


def mimc_add(self: int, other: int) -> int:
    return (self + other) % curve_order

def mimc_mul(self: int, other: int) -> int:
    return (self * other) % curve_order

def mimc_square(self: int) -> int:
    return mimc_mul(self, self)

def mimc_shr(self: int, b: int) -> int:
    return self >> b
    
def mimc_exp(base: int, e: int) -> int:
    res = 1
    rem = int(e)
    ex = base
    while rem != 0:
        if rem % 2 == 1:
            res = mimc_mul(res, ex)
        ex = mimc_square(ex)
        rem = mimc_shr(rem, 1)
    return res

def mimc_affine(self: int) -> int:
    aux = self
    nq = -curve_order
    if aux < 0:
        if aux <= nq:
            aux = aux % curve_order
        if aux < 0:
            aux = aux + curve_order
    else:
        if aux >= curve_order:
            aux = aux % curve_order
    return aux

# con_merkle_tree_v1

current_root_index = Variable()
next_index = Variable()
levels = Variable()
roots_var = Variable()
filled_subtrees_var = Variable()

ROOT_HISTORY_SIZE = 30
FIELD_SIZE = 21888242871839275222246405745257275088548364400416034343698204186575808495617
ZERO_VALUE = 21663839004416932945382355908790599225266501822907911457504978515578255421292


nullifier_hashes = Hash(default_value=None)
commitments = Hash(default_value=None)
denomination = Variable()
total_deposit_balance = Variable()
token_contract = Variable()
I = importlib


@construct
def init(tree_levels: int = 20):
    assert tree_levels > 0, 'tree_levels should be greater than zero'
    assert tree_levels < 32, 'tree_levels should be less than 32'
    filled_subtrees = []
    roots = [None] * ROOT_HISTORY_SIZE

    for i in range(tree_levels):
        filled_subtrees.append(zeros(i))

    roots[0] = zeros(tree_levels-1)

    # Set variables
    current_root_index.set(0)
    next_index.set(0)
    levels.set(tree_levels)
    roots_var.set(roots)
    filled_subtrees_var.set(filled_subtrees)

    token_contract.set('con_phi_lst001')
    total_deposit_balance.set(0)
    denomination.set(1000)


@export
def insert(leaf: str) -> int:
    current_index = next_index.get()
    tree_levels = levels.get()
    assert current_index != 2**tree_levels, 'Merkle tree is full. No more leaves can be added.'

    filled_subtrees = filled_subtrees_var.get()
    roots = roots_var.get()

    current_level_hash = str(leaf)

    for i in range(tree_levels):
        if current_index % 2 == 0:
            left = current_level_hash
            right = zeros(i)
            filled_subtrees[i] = current_level_hash
        else:
            left = filled_subtrees[i]
            right = current_level_hash

        current_level_hash = hash_left_right(left, right)

        current_index /= 2

    root_index = current_root_index.get()
    next_root_index = int((root_index + 1) % ROOT_HISTORY_SIZE)
    roots[next_root_index] = current_level_hash

    next_index.set(int(current_index + 1))
    current_root_index.set(next_root_index)
    roots_var.set(roots)
    filled_subtrees_var.set(filled_subtrees)
    return current_index


@export
def is_known_root(root: str) -> bool:
    if root is None or len(root) == 0 or int(root) == 0:
        return False

    i = current_root_index.get()
    current_index = i

    roots = roots_var.get()

    first_loop = True

    while first_loop or i != current_index:
        first_loop = False
        if root == roots[i]:
            return True
        if i == 0:
            i = ROOT_HISTORY_SIZE
        i -= 1
    return False

@export
def get_last_root(i: str = None) -> str:
    return roots_var.get()[current_root_index.get()]


def zeros(i: int) -> int:
    if i == 0:
        return int('0x2fe54c60d3acabf3343a35b6eba15db4821b340f76e741e2249685ed4899af6c', 16)
    elif i == 1:
        return int('0x256a6135777eee2fd26f54b8b7037a25439d5235caee224154186d2b8a52e31d', 16)
    elif i == 2:
        return int('0x1151949895e82ab19924de92c40a3d6f7bcb60d92b00504b8199613683f0c200', 16)
    elif i == 3:
        return int('0x20121ee811489ff8d61f09fb89e313f14959a0f28bb428a20dba6b0b068b3bdb', 16)
    elif i == 4:
        return int('0x0a89ca6ffa14cc462cfedb842c30ed221a50a3d6bf022a6a57dc82ab24c157c9', 16)
    elif i == 5:
        return int('0x24ca05c2b5cd42e890d6be94c68d0689f4f21c9cec9c0f13fe41d566dfb54959', 16)
    elif i == 6:
        return int('0x1ccb97c932565a92c60156bdba2d08f3bf1377464e025cee765679e604a7315c', 16)
    elif i == 7:
        return int('0x19156fbd7d1a8bf5cba8909367de1b624534ebab4f0f79e003bccdd1b182bdb4', 16)
    elif i == 8:
        return int('0x261af8c1f0912e465744641409f622d466c3920ac6e5ff37e36604cb11dfff80', 16)
    elif i == 9:
        return int('0x0058459724ff6ca5a1652fcbc3e82b93895cf08e975b19beab3f54c217d1c007', 16)
    elif i == 10:
        return int('0x1f04ef20dee48d39984d8eabe768a70eafa6310ad20849d4573c3c40c2ad1e30', 16)
    elif i == 11:
        return int('0x1bea3dec5dab51567ce7e200a30f7ba6d4276aeaa53e2686f962a46c66d511e5', 16)
    elif i == 12:
        return int('0x0ee0f941e2da4b9e31c3ca97a40d8fa9ce68d97c084177071b3cb46cd3372f0f', 16)
    elif i == 13:
        return int('0x1ca9503e8935884501bbaf20be14eb4c46b89772c97b96e3b2ebf3a36a948bbd', 16)
    elif i == 14:
        return int('0x133a80e30697cd55d8f7d4b0965b7be24057ba5dc3da898ee2187232446cb108', 16)
    elif i == 15:
        return int('0x13e6d8fc88839ed76e182c2a779af5b2c0da9dd18c90427a644f7e148a6253b6', 16)
    elif i == 16:
        return int('0x1eb16b057a477f4bc8f572ea6bee39561098f78f15bfb3699dcbb7bd8db61854', 16)
    elif i == 17:
        return int('0x0da2cb16a1ceaabf1c16b838f7a9e3f2a3a3088d9e0a6debaa748114620696ea', 16)
    elif i == 18:
        return int('0x24a3b3d822420b14b5d8cb6c28a574f01e98ea9e940551d2ebd75cee12649f9d', 16)
    elif i == 19:
        return int('0x198622acbd783d1b0d9064105b1fc8e4d8889de95c4c519b3f635809fe6afc05', 16)
    elif i == 20:
        return int('0x29d7ed391256ccc3ea596c86e933b89ff339d25ea8ddced975ae2fe30b5296d4', 16)
    elif i == 21:
        return int('0x19be59f2f0413ce78c0c3703a3a5451b1d7f39629fa33abd11548a76065b2967', 16)
    elif i == 22:
        return int('0x1ff3f61797e538b70e619310d33f2a063e7eb59104e112e95738da1254dc3453', 16)
    elif i == 23:
        return int('0x10c16ae9959cf8358980d9dd9616e48228737310a10e2b6b731c1a548f036c48', 16)
    elif i == 24:
        return int('0x0ba433a63174a90ac20992e75e3095496812b652685b5e1a2eae0b1bf4e8fcd1', 16)
    elif i == 25:
        return int('0x019ddb9df2bc98d987d0dfeca9d2b643deafab8f7036562e627c3667266a044c', 16)
    elif i == 26:
        return int('0x2d3c88b23175c5a5565db928414c66d1912b11acf974b2e644caaac04739ce99', 16)
    elif i == 27:
        return int('0x2eab55f6ae4e66e32c5189eed5c470840863445760f5ed7e7b69b2a62600f354', 16)
    elif i == 28:
        return int('0x002df37a2642621802383cf952bf4dd1f32e05433beeb1fd41031fb7eace979d', 16)
    elif i == 29:
        return int('0x104aeb41435db66c3e62feccc1d6f5d98d0a0ed75d1374db457cf462e3a1f427', 16)
    elif i == 30:
        return int('0x1f3c6fd858e9a7d4b0d1f38e256a09d81d5a5e3c963987e2d4b814cfab7c6ebb', 16)
    elif i == 31:
        return int('0x2c7a07d20dff79d01fecedc1134284a8d08436606c93693b67e333f671bf69cc', 16)
    else:
         assert False, "Index out of bounds"


'''
Tornado
'''

@export
def deposit(commitment: str, encrypted_note: str):
    assert commitments[commitment] is None, 'The commitment has been submitted.'
    inserted_index = insert(commitment)
    commitments[commitment] = True
    process_deposit(ctx.caller)    


def process_deposit(caller: str):
    amount = denomination.get()
    I.import_module(token_contract.get()).transfer_from(
        to=ctx.this,
        amount=amount,
        main_account=caller
    )
    total_deposit_balance.set(total_deposit_balance.get() + amount)


@export
def withdraw(a: list, b: list, c: list, root: str, nullifier_hash: str, recipient: str, relayer: str = '0', fee: str = '0', refund: str = '0'):
    assert int(fee) < denomination.get(), 'Fee exceeds transfer value.'
    assert nullifier_hashes[nullifier_hash] is None, 'The note has already been spent.'
    assert is_known_root(root), 'Cannot find your merkle root.'
    assert verify_proof(
        a=a, b=b, c=c,
        inputs=[
            int(root, 10), 
            int(nullifier_hash, 10),
            int(recipient, 10),
            int(relayer, 10),
            int(fee, 10),
            int(refund, 10),
        ],
    ), 'Invalid withdraw proof.'

    nullifier_hashes[nullifier_hash] = True

    process_withdraw(recipient, relayer, int(fee, 10), int(refund, 10))


def process_withdraw(recipient: str, relayer: str, fee: int, refund: int):
    assert refund == 0, 'Refund not supported.'

    amount = denomination.get() - fee
    assert amount > 0, 'Nothing to withdraw.'

    token = I.import_module(token_contract.get())

    token.transfer(
        to=recipient,
        amount=amount
    )

    if fee > 0:
        token.transfer(
            to=relayer,
            amount = fee
        )

    total_deposit_balance.set(total_deposit_balance.get() - (amount + fee))


@export
def is_spent(nullifier_hash: str) -> bool:
    return nullifier_hashes[nullifier_hash] is not None

@export
def is_spent_array(nullifier_hash_array: list) -> list:
    spent = []
    for nullifier_hash in nullifier_hash_array:
        spent.append(is_spent(nullifier_hash))
    return spent


vk = {}
vk_tmp = {
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

vk['alfa1'] = tuple(vk_tmp['vk_alfa_1'])
vk['beta2'] = (FQ2(vk_tmp['vk_beta_2'][0]), FQ2(vk_tmp['vk_beta_2'][1]), FQ2(vk_tmp['vk_beta_2'][2]))
vk['gamma2'] = (FQ2(vk_tmp['vk_gamma_2'][0]), FQ2(vk_tmp['vk_gamma_2'][1]), FQ2(vk_tmp['vk_gamma_2'][2]))
vk['delta2'] = (FQ2(vk_tmp['vk_delta_2'][0]), FQ2(vk_tmp['vk_delta_2'][1]), FQ2(vk_tmp['vk_delta_2'][2]))
vk['IC'] = [tuple(x) for x in vk_tmp['IC']]

@export
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
        vk['alfa1'],
        vk_x,
        proof['C']
    ]
    p2 = [
        (proof['B'][0], proof['B'][1], proof['B'][2]),
        vk['beta2'],
        vk['gamma2'],
        vk['delta2']
    ]

    # Testing
    #p1 = [neg(G1), G1, ]
    #p2 = [G2, G2]
    
    x = fq12_one()
    for i in range(len(p1)):
        if is_inf(p2[i]) or is_inf(p1[i]):
            continue
        y = pairing(p2[i], p1[i], False)
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