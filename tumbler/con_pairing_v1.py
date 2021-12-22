# The prime modulus of the field
field_modulus = 21888242871839275222246405745257275088696311157297823662689037894645226208583

# The modulus of the polynomial in this representation of FQ12
FQ12_modulus_coeffs = [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0] # Implied + [1]

ate_loop_count = 29793968203157093288
log_ate_loop_count = 63

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


@export
def FQP(coeffs: list, modulus_coeffs: list) -> dict:
    assert len(coeffs) == len(modulus_coeffs)
    coeffs = [FQ(c) for c in coeffs]
    # The coefficients of the modulus, without the leading [1]
    modulus_coeffs = modulus_coeffs
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
    coeffs = self['coeffs']
    if other == 0:
        return FQP([1] + [0] * (degree - 1), modulus_coeffs)
    elif other == 1:
        return FQP(coeffs, modulus_coeffs)
    elif other % 2 == 0:
        return fqp_pow(fqp_mul(self, self), (other // 2))
    else:
        return fqp_mul(fqp_pow(fqp_mul(self, self), (other // 2)), self)

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
    assert len(coeffs) == 2
    return FQP(coeffs, [1, 0])

# The 12th-degree extension field
@export
def FQ12(coeffs: list) -> dict:
    assert len(coeffs) == 12
    return FQP(coeffs, FQ12_modulus_coeffs)

def fq2_one() -> dict:
    return FQ2([1, 0])

def fq2_zero() -> dict:
    return FQ2([0, 0])

def fq12_one() -> dict:
    return FQ12([1] + [0] * len(FQ12_modulus_coeffs) - 1)

def fq12_zero() -> dict:
    return FQ12([0] * len(FQ12_modulus_coeffs))

# Check if a point is the point at infinity
def is_inf(pt: Any) -> bool:
    return pt is None

# Check that a point is on the curve defined by y**2 == x**3 + b
def is_on_curve(pt: Any, b: Any) -> bool:
    if is_inf(pt):
        return True
    x, y = tuple(pt)
    if isinstance(x, int):
        return fq_eq(fq_sub(fq_pow(y,2), fq_pow(x, 3)), b)
    else:
        a = fqp_sub(fqp_pow(y,2), fqp_pow(x, 3))
        #print(f'A: {a}')
        #print(f'B: {b}')
        return fqp_eq(a, b)

# Elliptic curve doubling
@export
def double(pt: Any) -> Any:
    x, y = tuple(pt)
    if isinstance(x, int):
        l = fq_div(fq_mul(3, fq_pow(x,2)), fq_mul(2, y))
        newx = fq_sub(fq_pow(l, 2), fq_mul(2, x))
        newy = fq_sub(fq_add(fq_mul(fq_neg(l), newx), fq_mul(l, x)), y)
    else:
        l = fqp_div(fqp_mul(3, fqp_pow(x,2)), fqp_mul(2, y))
        newx = fqp_sub(fqp_pow(l, 2), fqp_mul(2, x))
        newy = fqp_sub(fqp_add(fqp_mul(fqp_neg(l), newx), fqp_mul(l, x)), y)
    return newx, newy


# Elliptic curve addition
@export
def add(p1: Any, p2: Any) -> Any:
    if p1 is None or p2 is None:
        return p1 if p2 is None else p2
    x1, y1 = tuple(p1)
    x2, y2 = tuple(p2)
    if x2 == x1 and y2 == y1:
        return double(p1)
    elif x2 == x1:
        return None
    if isinstance(x1, int):
        l = fq_div(fq_sub(y2, y1), fq_sub(x2, x1))
        newx = fq_sub(fq_sub(fq_pow(l, 2), x1), x2)
        newy = fq_sub(fq_add(fq_mul(fq_neg(l), newx), fq_mul(l, x1)), y1)
        assert fq_eq(newy, fq_sub(fq_add(fq_mul(fq_neg(l), newx), fq_mul(l, x2)), y2))
    else:
        l = fqp_div(fqp_sub(y2, y1), fqp_sub(x2, x1))
        newx = fqp_sub(fqp_sub(fqp_pow(l, 2), x1), x2)
        newy = fqp_sub(fqp_add(fqp_mul(fqp_neg(l), newx), fqp_mul(l, x1)), y1)
        assert fqp_eq(newy, fqp_sub(fqp_add(fqp_mul(fqp_neg(l), newx), fqp_mul(l, x2)), y2))
    return (newx, newy)


# Elliptic curve point multiplication
@export
def multiply(pt: Any, n: Any) -> Any:
    if n == 0:
        return None
    elif n == 1:
        return pt
    elif not n % 2:
        return multiply(double(pt), n // 2)
    else:
        return add(multiply(double(pt), int(n // 2)), pt)


@export
def eq(p1: Any, p2: Any) -> Any:
    x1, y1 = tuple(p1)
    x2, y2 = tuple(p2)
    if isinstance(x1, int) and isinstance(x2, int):        
        return fq_eq(x1, x2) and fq_eq(y1, y2)
    else:
        return fqp_eq(x1, x2) and fqp_eq(y1, y2)

# "Twist" a point in E(FQ2) into a point in E(FQ12)
w = FQ12([0, 1] + [0] * 10)

# Convert P => -P
@export
def neg(pt: Any) -> Any:
    if pt is None:
        return None
    x, y = tuple(pt)
    if isinstance(x, int):
        return (x, fq_neg(y))
    else:
        return (x, fqp_neg(y))

@export
def twist(pt: Any) -> Any:
    if pt is None:
        return None
    x, y = tuple(pt)
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 18*x + 82
    xcoeffs = [fq_sub(x['coeffs'][0], fq_mul(x['coeffs'][1], 9)), x['coeffs'][1]]
    ycoeffs = [fq_sub(y['coeffs'][0], fq_mul(y['coeffs'][1], 9)), y['coeffs'][1]]
    # Isomorphism into subfield of Z[p] / w**12 - 18 * w**6 + 82,
    # where w**6 = x
    nx = FQ12([xcoeffs[0]] + [0] * 5 + [xcoeffs[1]] + [0] * 5)
    ny = FQ12([ycoeffs[0]] + [0] * 5 + [ycoeffs[1]] + [0] * 5)
    # Divide x coord by w**2 and y coord by w**3
    return (fqp_mul(nx, fqp_pow(w, 2)), fqp_mul(ny, fqp_pow(w, 3)))

# Create a function representing the line between P1 and P2,
# and evaluate it at T
@export
def linefunc(P1: Any, P2: Any, T: Any) -> Any:
    assert P1 and P2 and T # No points-at-infinity allowed, sorry
    x1, y1 = tuple(P1)
    x2, y2 = tuple(P2)
    xt, yt = tuple(T)
    if isinstance(x1, int):
        if fq_ne(x1, x2):
            m = fq_div(fq_sub(y2, y1), fq_sub(x2, x1))
            return fq_sub(fq_mul(m, fq_sub(xt, x1)), fq_sub(yt, y1))
        elif fq_eq(y1, y2):
            m = fq_div(fq_mul(fq_pow(x1,2), 3), fq_mul(y1, 2))
            return fq_sub(fq_mul(m, fq_sub(xt, x1)), fq_sub(yt, y1))
        else:
            return fq_sub(xt, x1)
    else:
        if fqp_ne(x1, x2):
            m = fqp_div(fqp_sub(y2, y1), fqp_sub(x2, x1))
            return fqp_sub(fqp_mul(m, fqp_sub(xt, x1)), fqp_sub(yt, y1))
        elif fqp_eq(y1, y2):
            m = fqp_div(fqp_mul(fqp_pow(x1,2), 3), fqp_mul(y1, 2))
            return fqp_sub(fqp_mul(m, fqp_sub(xt, x1)), fqp_sub(yt, y1))
        else:
            return fqp_sub(xt, x1)

def cast_point_to_fq12(pt: Any) -> Any:
    if pt is None:
        return None
    x, y = tuple(pt)
    return (FQ12([x] + [0] * 11), FQ12([y] + [0] * 11))


# Main miller loop
def miller_loop(Q: Any, P: Any) -> Any:
    if Q is None or P is None:
        return fq12_one()
    R = Q
    f = fq12_one()    
    for i in range(log_ate_loop_count, -1, -1):
        f = fqp_mul(fqp_mul(f, f), linefunc(R, R, P))
        R = double(R)
        if ate_loop_count & (2**i):
            f = fqp_mul(f, linefunc(R, Q, P))
            R = add(R, Q)
    # assert R == multiply(Q, ate_loop_count)
    Q1 = (Q[0] ** field_modulus, Q[1] ** field_modulus)
    # assert is_on_curve(Q1, b12)
    nQ2 = (Q1[0] ** field_modulus, -Q1[1] ** field_modulus)
    # assert is_on_curve(nQ2, b12)
    f = fqp_mul(f, linefunc(R, Q1, P))
    R = add(R, Q1)
    f = fqp_mul(f, linefunc(R, nQ2, P))
    # R = add(R, nQ2) This line is in many specifications but it technically does nothing
    return final_exponentiate(f)

# Pairing computation
@export
def pairing(Q: Any, P: Any) -> Any:
    assert is_on_curve(Q, b2)
    assert is_on_curve(P, b)
    return miller_loop(twist(Q), cast_point_to_fq12(P))

@export
def final_exponentiate(p: Any) -> Any:
    return fqp_pow(p, ((field_modulus ** 12 - 1) // curve_order))
