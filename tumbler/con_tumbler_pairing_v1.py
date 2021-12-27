
# The prime modulus of the field
from contracts.tumbler.con_pairing_v1 import fqp_div


field_modulus = 21888242871839275222246405745257275088696311157297823662689037894645226208583
# See, it's prime!
assert pow(2, field_modulus, field_modulus) == 2

# The modulus of the polynomial in this representation of FQ12
FQ12_modulus_coeffs = [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0] # Implied + [1]

# Extended euclidean algorithm to find modular inverses for
# integers
def inv(a, n):
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high//low
        nm, new = hm-lm*r, high-low*r
        lm, low, hm, high = nm, new, lm, low
    return lm % n

# A class for field elements in FQ. Wrap a number in this class,
# and it becomes a field element.
class FQ():
    def __init__(self, n):
        if isinstance(n, self.__class__):
            self.n = n.n
        else:
            self.n = n % field_modulus
        assert isinstance(self.n, int)

    def __add__(self, other):
        on = other.n if isinstance(other, FQ) else other
        return FQ((self.n + on) % field_modulus)

    def __mul__(self, other):
        on = other.n if isinstance(other, FQ) else other
        return FQ((self.n * on) % field_modulus)

    def __rmul__(self, other):
        return self * other

    def __radd__(self, other):
        return self + other

    def __rsub__(self, other):
        on = other.n if isinstance(other, FQ) else other
        return FQ((on - self.n) % field_modulus)

    def __sub__(self, other):
        on = other.n if isinstance(other, FQ) else other
        return FQ((self.n - on) % field_modulus)

    def __div__(self, other):
        on = other.n if isinstance(other, FQ) else other
        assert isinstance(on, int)
        return FQ(self.n * inv(on, field_modulus) % field_modulus)

    def __truediv__(self, other):
        return self.__div__(other)

    def __rdiv__(self, other):
        on = other.n if isinstance(other, FQ) else other
        assert isinstance(on, int), on
        return FQ(inv(self.n, field_modulus) * on % field_modulus)

    def __rtruediv__(self, other):
        return self.__rdiv__(other)

    def __pow__(self, other):
        if other == 0:
            return FQ(1)
        elif other == 1:
            return FQ(self.n)
        elif other % 2 == 0:
            return (self * self) ** (other // 2)
        else:
            return ((self * self) ** int(other // 2)) * self

    def __eq__(self, other):
        if isinstance(other, FQ):
            return self.n == other.n
        else:
            return self.n == other

    def __ne__(self, other):
        return not self == other

    def __neg__(self):
        return FQ(-self.n)

    def __repr__(self):
        return repr(self.n)

    @classmethod
    def one(cls):
        return cls(1)

    @classmethod
    def zero(cls):
        return cls(0)

# Utility methods for polynomial math
def deg(p):
    d = len(p) - 1
    while p[d] == 0 and d:
        d -= 1
    return d

def poly_rounded_div(a, b):
    dega = deg(a)
    degb = deg(b)
    temp = [x for x in a]
    o = [0 for x in a]
    for i in range(dega - degb, -1, -1):
        o[i] += temp[degb + i] / b[degb]
        for c in range(degb + 1):
            temp[c + i] -= o[c]
    return o[:deg(o)+1]

# A class for elements in polynomial extension fields
class FQP():
    def __init__(self, coeffs, modulus_coeffs): 
        assert len(coeffs) == len(modulus_coeffs)
        self.coeffs = [FQ(c) for c in coeffs]
        # The coefficients of the modulus, without the leading [1]
        self.modulus_coeffs = modulus_coeffs
        # The degree of the extension field
        self.degree = len(self.modulus_coeffs)

    def __add__(self, other):
        assert isinstance(other, self.__class__)
        return self.__class__([x+y for x,y in zip(self.coeffs, other.coeffs)])

    def __sub__(self, other):
        assert isinstance(other, self.__class__)
        return self.__class__([x-y for x,y in zip(self.coeffs, other.coeffs)])

    def __mul__(self, other):
        if isinstance(other, (FQ, int)):
            return self.__class__([c * other for c in self.coeffs])
        else:
            assert isinstance(other, self.__class__)
            b = [FQ(0) for i in range(self.degree * 2 - 1)]
            for i in range(self.degree):
                for j in range(self.degree):
                    b[i + j] += self.coeffs[i] * other.coeffs[j]
            while len(b) > self.degree:
                exp, top = len(b) - self.degree - 1, b.pop()
                for i in range(self.degree):
                    b[exp + i] -= top * FQ(self.modulus_coeffs[i])
            return self.__class__(b)

    def __rmul__(self, other):
        return self * other

    def __div__(self, other):
        if isinstance(other, (FQ, int)):
            return self.__class__([c / other for c in self.coeffs])
        else:
            assert isinstance(other, self.__class__)
            return self * other.inv()

    def __truediv__(self, other):
        return self.__div__(other)

    def __pow__(self, other):
        if other == 0:
            return self.__class__([1] + [0] * (self.degree - 1))
        elif other == 1:
            return self.__class__(self.coeffs)
        elif other % 2 == 0:
            return (self * self) ** (other // 2)
        else:
            return ((self * self) ** int(other // 2)) * self

    # Extended euclidean algorithm used to find the modular inverse
    def inv(self):
        lm, hm = [1] + [0] * self.degree, [0] * (self.degree + 1)
        low, high = self.coeffs + [0], self.modulus_coeffs + [1]
        while deg(low):
            r = poly_rounded_div(high, low)
            r += [0] * (self.degree + 1 - len(r))
            nm = [x for x in hm]
            new = [x for x in high]
            assert len(lm) == len(hm) == len(low) == len(high) == len(nm) == len(new) == self.degree + 1
            for i in range(self.degree + 1):
                for j in range(self.degree + 1 - i):
                    nm[i+j] -= lm[i] * r[j]
                    new[i+j] -= low[i] * r[j]
            lm, low, hm, high = nm, new, lm, low
        return self.__class__(lm[:self.degree]) / low[0]

    def __repr__(self):
        return repr(self.coeffs)

    def __eq__(self, other):
        assert isinstance(other, self.__class__)
        for c1, c2 in zip(self.coeffs, other.coeffs):
            if c1 != c2:
                return False
        return True

    def __ne__(self, other):
        return not self == other

    def __neg__(self):
        return self.__class__([-c for c in self.coeffs])

    @classmethod
    def one(cls):
        return cls([1] + [0] * (cls.degree - 1))

    @classmethod
    def zero(cls):
        return cls([0] * cls.degree)

# The quadratic extension field
class FQ2(FQP):
    def __init__(self, coeffs):
        self.coeffs = [FQ(c) for c in coeffs]
        self.modulus_coeffs = [1, 0]
        self.degree = 2
        self.__class__.degree = 2

# The 12th-degree extension field
class FQ12(FQP):
    def __init__(self, coeffs):
        self.coeffs = [FQ(c) for c in coeffs]
        self.modulus_coeffs = FQ12_modulus_coeffs
        self.degree = 12
        self.__class__.degree = 12



curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617

# Curve order should be prime
assert pow(2, curve_order, curve_order) == 2
# Curve order should be a factor of field_modulus**12 - 1
assert (field_modulus ** 12 - 1) % curve_order == 0

# Curve is y**2 = x**3 + 3
b = FQ(3)
# Twisted curve over FQ**2
b2 = FQ2([3, 0]) / FQ2([9, 1])
# Extension curve over FQ**12; same b value as over FQ
b12 = FQ12([3] + [0] * 11)

# Generator for curve over FQ
G1 = (FQ(1), FQ(2))
# Generator for twisted curve over FQ2
G2 = (FQ2([10857046999023057135944570762232829481370756359578518086990519993285655852781, 11559732032986387107991004021392285783925812861821192530917403151452391805634]),
      FQ2([8495653923123431417604973247489272438418190587263600148770280649306958101930, 4082367875863433681332203403145435568316851327593401208105741076214120093531]))

# Check if a point is the point at infinity
def is_inf(pt):
    return pt is None

# Check that a point is on the curve defined by y**2 == x**3 + b
def is_on_curve(pt, b):
    if is_inf(pt):
        return True
    x, y = pt
    print(y**2 - x**3)
    print(b)
    return y**2 - x**3 == b

# Elliptic curve doubling
def double(pt):
    x, y = pt
    l = 3 * x**2 / (2 * y)
    newx = l**2 - 2 * x
    newy = -l * newx + l * x - y
    return newx, newy

# Elliptic curve addition
def add(p1, p2):
    if p1 is None or p2 is None:
        return p1 if p2 is None else p2
    x1, y1 = p1
    x2, y2 = p2
    if x2 == x1 and y2 == y1:
        return double(p1)
    elif x2 == x1:
        return None
    else:
        l = (y2 - y1) / (x2 - x1)
    newx = l**2 - x1 - x2
    newy = -l * newx + l * x1 - y1
    assert newy == (-l * newx + l * x2 - y2)
    return (newx, newy)

# Elliptic curve point multiplication
def multiply(pt, n):
    if n == 0:
        return None
    elif n == 1:
        return pt
    elif not n % 2:
        return multiply(double(pt), n // 2)
    else:
        return add(multiply(double(pt), int(n // 2)), pt)

def eq(p1, p2):
    return p1 == p2

# "Twist" a point in E(FQ2) into a point in E(FQ12)
w = FQ12([0, 1] + [0] * 10)

# Convert P => -P
def neg(pt):
    if pt is None:
        return None
    x, y = pt
    return (x, -y)

def twist(pt):
    if pt is None:
        return None
    _x, _y = pt
    # Field isomorphism from Z[p] / x**2 to Z[p] / x**2 - 18*x + 82
    xcoeffs = [_x.coeffs[0] - _x.coeffs[1] * 9, _x.coeffs[1]]
    ycoeffs = [_y.coeffs[0] - _y.coeffs[1] * 9, _y.coeffs[1]]
    # Isomorphism into subfield of Z[p] / w**12 - 18 * w**6 + 82,
    # where w**6 = x
    nx = FQ12([xcoeffs[0]] + [0] * 5 + [xcoeffs[1]] + [0] * 5)
    ny = FQ12([ycoeffs[0]] + [0] * 5 + [ycoeffs[1]] + [0] * 5)
    # Divide x coord by w**2 and y coord by w**3
    return (nx * w **2, ny * w**3)

G12 = twist(G2)
# Check that the twist creates a point that is on the curve
assert is_on_curve(G12, b12)



ate_loop_count = 29793968203157093288
log_ate_loop_count = 63

# Create a function representing the line between P1 and P2,
# and evaluate it at T
def linefunc(P1, P2, T):
    assert P1 and P2 and T # No points-at-infinity allowed, sorry
    x1, y1 = P1
    x2, y2 = P2
    xt, yt = T
    if x1 != x2:
        m = (y2 - y1) / (x2 - x1)
        return m * (xt - x1) - (yt - y1)
    elif y1 == y2:
        m = 3 * x1**2 / (2 * y1)
        return m * (xt - x1) - (yt - y1)
    else:
        return xt - x1

def cast_point_to_fq12(pt):
    if pt is None:
        return None
    x, y = pt
    return (FQ12([x.n] + [0] * 11), FQ12([y.n] + [0] * 11))

# Check consistency of the "line function"
one, two, three = G1, double(G1), multiply(G1, 3)
negone, negtwo, negthree = multiply(G1, curve_order - 1), multiply(G1, curve_order - 2), multiply(G1, curve_order - 3)

assert linefunc(one, two, one) == FQ(0)
assert linefunc(one, two, two) == FQ(0)
assert linefunc(one, two, three) != FQ(0)
assert linefunc(one, two, negthree) == FQ(0)
assert linefunc(one, negone, one) == FQ(0)
assert linefunc(one, negone, negone) == FQ(0)
assert linefunc(one, negone, two) != FQ(0)
assert linefunc(one, one, one) == FQ(0)
assert linefunc(one, one, two) != FQ(0)
assert linefunc(one, one, negtwo) == FQ(0)

# Main miller loop
def miller_loop(Q, P):
    if Q is None or P is None:
        return FQ12.one()
    R = Q
    f = FQ12.one()
    for i in range(log_ate_loop_count, -1, -1):
        f = f * f * linefunc(R, R, P)
        R = double(R)
        if ate_loop_count & (2**i):
            f = f * linefunc(R, Q, P)
            R = add(R, Q)
    # assert R == multiply(Q, ate_loop_count)
    Q1 = (Q[0] ** field_modulus, Q[1] ** field_modulus)
    # assert is_on_curve(Q1, b12)
    nQ2 = (Q1[0] ** field_modulus, -Q1[1] ** field_modulus)
    # assert is_on_curve(nQ2, b12)
    f = f * linefunc(R, Q1, P)
    R = add(R, Q1)
    f = f * linefunc(R, nQ2, P)
    # R = add(R, nQ2) This line is in many specifications but it technically does nothing
    return f ** ((field_modulus ** 12 - 1) // curve_order)

# Pairing computation
@export
def pairing(Q: dict, P: dict) -> int:
    b = FQ(3)
    b2 = fqp_div(FQ2([3, 0]), FQ2([9, 1]))
    assert is_on_curve(Q, b2)
    assert is_on_curve(P, b)
    return miller_loop(twist(Q), cast_point_to_fq12(P))

def final_exponentiate(p):
    return p ** ((field_modulus ** 12 - 1) // curve_order)

