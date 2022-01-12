# con_verifier_opt_pairing

pseudo_binary_encoding = [0, 0, 0, 1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 0, 1, 0,
                          0, 1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1, 1,
                          1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 1,
                          1, 0, 0, -1, 0, 0, 0, 1, 1, 0, -1, 0, 0, 1, 0, 1, 1]
curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
p2 = 21888242871839275222246405745257275088696311157297823662689037894645226208583
u = 4965661367192848881
xiToPMinus1Over6 = [16469823323077808223889137241176536799009286646108169935659301613961712198316,
                    8376118865763821496583973867626364092589906065868298776909617916018768340080]
xiToPMinus1Over3 = [10307601595873709700152284273816112264069230130616436755625194854815875713954,
                    21575463638280843010398324269430826099269044274347216827212613867836435027261]
xiToPMinus1Over2 = [3505843767911556378687030309984248845540243509899259641013678093033130930403,
                    2821565182194536844548159561693502659359617185244120367078079554186484126554]
xiToPSquaredMinus1Over3 = 21888242871839275220042445260109153167277707414472061641714758635765020556616
xiTo2PSquaredMinus2Over3 = 2203960485148121921418603742825762020974279258880205651966
xiToPSquaredMinus1Over6 = 21888242871839275220042445260109153167277707414472061641714758635765020556617
xiTo2PMinus2Over3 = [19937756971775647987995932169929341994314640652964949448313374472400716661030,
                     2581911344467009335267311115468803099551665605076196740867805258568234346338]
twistB = [266929791119991161246907387137283842545076965332900288569378510910307636690,
          19485874751759354771024239261021720505790618469301721065564631296452457478373]
curveB = 3


def FQ(n: int) -> int:
    n = n % p2
    if n < 0:
        n += p2
    return n


def fq_inv(a: int, n: int = p2) -> int:
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high // low
        nm, new = hm - lm * r, high - low * r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def fa(self: int, other: int) -> int:
    return FQ(self + other)


def fm(self: int, other: int) -> int:
    return FQ(self * other)


def fs(self: int, other: int) -> int:
    return FQ(self - other)


def fq_eq(self: int, other: int) -> bool:
    return self == other


def fq_neg(self: int) -> int:
    self = -self
    if self < 0:
        self += p2
    return self


def bits_of(k):
    return [int(c) for c in "{0:b}".format(k)]


def FQ2(coeffs: list) -> list:
    assert len(coeffs) == 2, f'FQ2 must have 2 coefficients but had {len(coeffs)}'
    return coeffs


def FQ6(coeffs: list) -> list:
    assert len(coeffs) == 3 and len(coeffs[0]) == 2, 'FQ6 must have 3 FQ2s'
    return coeffs


def FQ12(coeffs: list) -> list:
    assert len(coeffs) == 2 and len(coeffs[0]) == 3, 'FQ12 must have 2 FQ6s'
    return coeffs


def fq2_one(n: int = 0) -> list:
    return [0, 1]


def fq2_zero(n: int = 0) -> list:
    return [0, 0]


def fq2_is_one(self: list) -> bool:
    return self[0] == 0 and self[1] == 1


def fq2_is_zero(self: list) -> bool:
    return self[0] == 0 and self[1] == 0


def fq2_conjugate(self: list) -> list:
    return [fq_neg(self[0]), self[1]]


def fq2_neg(self: list) -> list:
    return [fq_neg(self[0]), fq_neg(self[1])]


def f2a(self: list, other: list) -> list:
    return [fa(self[0], other[0]), fa(self[1], other[1])]


def f2s(self: list, other: list) -> list:
    return [fs(self[0], other[0]), fs(self[1], other[1])]


def f2m(self: list, other: list) -> list:
    tx = fm(self[0], other[1])
    t = fm(other[0], self[1])
    tx = fa(tx, t)

    ty = fm(self[1], other[1])
    t = fm(self[0], other[0])
    ty = fs(ty, t)
    return [tx, ty]


def f2m_scalar(self: list, other: int) -> list:
    x = fm(self[0], other)
    y = fm(self[1], other)
    return [x, y]


def f2m_xi(self: list) -> list:
    tx = fa(self[0], self[0])
    tx = fa(tx, tx)
    tx = fa(tx, tx)
    tx = fa(tx, self[0])
    tx = fa(tx, self[1])

    ty = fa(self[1], self[1])
    ty = fa(ty, ty)
    ty = fa(ty, ty)
    ty = fa(ty, self[1])
    ty = fs(ty, self[0])
    return [tx, ty]


def fq2_eq(self: list, other: list) -> bool:
    return self[0] == other[0] and self[1] == other[1]


def fq2_square(self: list) -> list:
    tx = fs(self[1], self[0])
    ty = fa(self[0], self[1])
    ty = fm(tx, ty)

    tx = fm(self[0], self[1])
    tx = fa(tx, tx)
    return [tx, ty]


def fq2_invert(self: list) -> list:
    t1 = fm(self[0], self[0])
    t2 = fm(self[1], self[1])
    t1 = fa(t1, t2)
    inv = fq_inv(t1)
    t1 = fq_neg(self[0])
    x = fm(t1, inv)
    y = fm(self[1], inv)
    return [x, y]


def fq6_one(n: int = 0) -> list:
    return [fq2_zero(), fq2_zero(), fq2_one()]


def fq6_zero(n: int = 0) -> list:
    return [fq2_zero(), fq2_zero(), fq2_zero()]


def fq6_is_zero(self: list) -> bool:
    return fq2_is_zero(self[0]) and fq2_is_zero(self[1]) and fq2_is_zero(self[2])


def fq6_is_one(self: list) -> bool:
    return fq2_is_zero(self[0]) and fq2_is_zero(self[1]) and fq2_is_one(self[2])


def fq6_neg(self: list) -> list:
    return [fq2_neg(self[0]), fq2_neg(self[1]), fq2_neg(self[2])]


def fq6_frobenius(self: list) -> list:
    x = fq2_conjugate(self[0])
    y = fq2_conjugate(self[1])
    z = fq2_conjugate(self[2])
    x = f2m(x, xiTo2PMinus2Over3)
    y = f2m(y, xiToPMinus1Over3)
    return [x, y, z]


def fq6_frobenius_p2(self: list) -> list:
    x = f2m_scalar(self[0], xiTo2PSquaredMinus2Over3)
    y = f2m_scalar(self[1], xiToPSquaredMinus1Over3)
    return [x, y, self[2]]


def f6a(self: list, other: list) -> list:
    return [f2a(self[0], other[0]), f2a(self[1], other[1]), f2a(self[2], other[2])]


def f6s(self: list, other: list) -> list:
    return [f2s(self[0], other[0]), f2s(self[1], other[1]), f2s(self[2], other[2])]


def f6m(self: list, other: list) -> list:
    v0 = f2m(self[2], other[2])
    v1 = f2m(self[1], other[1])
    v2 = f2m(self[0], other[0])
    t0 = f2a(self[0], self[1])
    t1 = f2a(other[0], other[1])
    tz = f2m(t0, t1)
    tz = f2s(tz, v1)
    tz = f2s(tz, v2)
    tz = f2m_xi(tz)
    tz = f2a(tz, v0)

    t0 = f2a(self[1], self[2])
    t1 = f2a(other[1], other[2])
    ty = f2m(t0, t1)
    t0 = f2m_xi(v2)
    ty = f2s(ty, v0)
    ty = f2s(ty, v1)
    ty = f2a(ty, t0)

    t0 = f2a(self[0], self[2])
    t1 = f2a(other[0], other[2])
    tx = f2m(t0, t1)
    tx = f2s(tx, v0)
    tx = f2a(tx, v1)
    tx = f2s(tx, v2)
    return [tx, ty, tz]


def f6m_scalar(self: list, other: list) -> list:
    return [f2m(self[0], other), f2m(self[1], other), f2m(self[2], other)]


def f6m_gfp(self: list, other: int) -> list:
    return [f2m_scalar(self[0], other), f2m_scalar(self[1], other), f2m_scalar(self[2], other)]


def f6m_tau(self: list) -> list:
    tz = f2m_xi(self[0])
    ty = self[1]
    return [ty, self[2], tz]


def fq6_square(self: list) -> list:
    v0 = fq2_square(self[2])
    v1 = fq2_square(self[1])
    v2 = fq2_square(self[0])

    c0 = f2a(self[0], self[1])
    c0 = fq2_square(c0)
    c0 = f2s(c0, v1)
    c0 = f2s(c0, v2)
    c0 = f2m_xi(c0)
    c0 = f2a(c0, v0)

    c1 = f2a(self[1], self[2])
    c1 = fq2_square(c1)
    c1 = f2s(c1, v0)
    c1 = f2s(c1, v1)
    xiV2 = f2m_xi(v2)
    c1 = f2a(c1, xiV2)

    c2 = f2a(self[0], self[2])
    c2 = fq2_square(c2)
    c2 = f2s(c2, v0)
    c2 = f2a(c2, v1)
    c2 = f2s(c2, v2)
    return [c2, c1, c0]


def fq6_invert(self: list) -> list:
    XX = fq2_square(self[0])
    YY = fq2_square(self[1])
    ZZ = fq2_square(self[2])

    XY = f2m(self[0], self[1])
    XZ = f2m(self[0], self[2])
    YZ = f2m(self[1], self[2])

    A = f2s(ZZ, f2m_xi(XY))
    B = f2s(f2m_xi(XX), YZ)
    C = f2s(YY, XZ)

    F = f2m_xi(f2m(C, self[1]))
    F = f2a(F, f2m(A, self[2]))
    F = f2a(F, f2m_xi(f2m(B, self[0])))

    F = fq2_invert(F)
    return [f2m(C, F), f2m(B, F), f2m(A, F)]


def fq12_one(n: int = 0) -> list:
    return [fq6_zero(), fq6_one()]


def fq12_is_one(self: list) -> bool:
    return fq6_is_zero(self[0]) and fq6_is_one(self[1])


def fq12_conjugate(self: list) -> list:
    return [fq6_neg(self[0]), self[1]]


def fq12_frobenius(self: list) -> list:
    x = fq6_frobenius(self[0])
    x = f6m_scalar(x, xiToPMinus1Over6)
    return [x, fq6_frobenius(self[1])]


def fq12_frobenius_p2(self: list) -> list:
    x = fq6_frobenius_p2(self[0])
    x = f6m_gfp(x, xiToPSquaredMinus1Over6)
    return [x, fq6_frobenius_p2(self[1])]


def f12a(self: list, other: list) -> list:
    return [f6a(self[0], other[0]), f6a(self[1], other[1])]


def f12s(self: list, other: list) -> list:
    return [f6s(self[0], other[0]), f6s(self[1], other[1])]


def f12m(self: list, other: list) -> list:
    tx = f6m(self[0], other[1])
    t = f6m(self[1], other[0])
    tx = f6a(tx, t)
    ty = f6m(self[1], other[1])
    t = f6m(self[0], other[0])
    t = f6m_tau(t)
    return [tx, f6a(ty, t)]


def f12m_scalar(self: list, other: list) -> list:
    return [f6m(self[0], other), f6m(self[1], other)]


def fq12_exp(self: list, other: int) -> list:
    sum = fq12_one()
    for i in range(other.bit_length() - 1, -1, -1):
        t = fq12_square(sum)
        if other >> i & 1 != 0:
            sum = f12m(t, self)
        else:
            sum = t
    return sum


def fq12_square(self: list) -> list:
    v0 = f6m(self[0], self[1])
    t = f6m_tau(self[0])
    t = f6a(self[1], t)
    ty = f6a(self[0], self[1])
    ty = f6m(ty, t)
    ty = f6s(ty, v0)
    t = f6m_tau(v0)
    ty = f6s(ty, t)
    return [f6a(v0, v0), ty]


def fq12_invert(self: list) -> list:
    t1 = fq6_square(self[0])
    t2 = fq6_square(self[1])
    t1 = f6m_tau(t1)
    t1 = f6s(t2, t1)
    t2 = fq6_invert(t1)
    return f12m_scalar([fq6_neg(self[0]), self[1]], t2)


def line_function_add(r: list, p: list, q: list, r2: list) -> tuple:
    B = f2m(p[0], r[3])
    D = f2a(p[1], r[2])
    D = fq2_square(D)
    D = f2s(D, r2)
    D = f2s(D, r[3])
    D = f2m(D, r[3])

    H = f2s(B, r[0])
    I = fq2_square(H)

    E = f2a(I, I)
    E = f2a(E, E)

    J = f2m(H, E)

    L1 = f2s(D, r[1])
    L1 = f2s(L1, r[1])

    V = f2m(r[0], E)

    rOutX = fq2_square(L1)
    rOutX = f2s(rOutX, J)
    rOutX = f2s(rOutX, f2a(V, V))

    rOutZ = f2a(r[2], H)
    rOutZ = fq2_square(rOutZ)
    rOutZ = f2s(rOutZ, r[3])
    rOutZ = f2s(rOutZ, I)

    t = f2s(V, rOutX)
    t = f2m(t, L1)
    t2 = f2m(r[1], J)
    t2 = f2a(t2, t2)
    rOutY = f2s(t, t2)
    rOutT = fq2_square(rOutZ)

    t = f2a(p[1], rOutZ)
    t = fq2_square(t)
    t = f2s(t, r2)
    t = f2s(t, rOutT)

    t2 = f2m(L1, p[0])
    t2 = f2a(t2, t2)
    a = f2s(t2, t)

    c = f2m_scalar(rOutZ, q[1])
    c = f2a(c, c)

    b = fq2_neg(L1)
    b = f2m_scalar(b, q[0])
    b = f2a(b, b)

    return a, b, c, [rOutX, rOutY, rOutZ, rOutT]


def line_function_double(r: list, q: list) -> tuple:
    A = fq2_square(r[0])
    B = fq2_square(r[1])
    C = fq2_square(B)

    D = f2a(r[0], B)
    D = fq2_square(D)
    D = f2s(D, A)
    D = f2s(D, C)
    D = f2a(D, D)

    E = f2a(f2a(A, A), A)
    F = fq2_square(E)

    C8 = f2a(C, C)
    C8 = f2a(C8, C8)
    C8 = f2a(C8, C8)

    rX = f2s(F, f2a(D, D))
    rY = f2m(E, f2s(D, rX))
    rY = f2s(rY, C8)

    rZ = f2a(r[1], r[2])
    rZ = fq2_square(rZ)
    rZ = f2s(rZ, B)
    rZ = f2s(rZ, r[3])

    a = f2a(r[0], E)
    a = fq2_square(a)
    B4 = f2a(B, B)
    B4 = f2a(B4, B4)
    a = f2s(a, f2a(A, f2a(F, B4)))

    t = f2m(E, r[3])
    t = f2a(t, t)
    b = fq2_neg(t)
    b = f2m_scalar(b, q[0])

    c = f2m(rZ, r[3])
    c = f2a(c, c)
    c = f2m_scalar(c, q[1])

    rT = fq2_square(rZ)
    return a, b, c, [rX, rY, rZ, rT]


def line_function_mul(ret: list, a: list, b: list, c: list) -> list:
    a2 = [fq2_zero(), a, b]
    a2 = f6m(a2, ret[0])
    t3 = f6m_scalar(ret[1], c)

    t = f2a(b, c)
    t2 = [fq2_zero(), a, t]
    rX = f6a(ret[0], ret[1])
    rY = t3

    rX = f6m(rX, t2)
    rX = f6s(rX, a2)
    rX = f6s(rX, rY)
    a2 = f6m_tau(a2)
    rY = f6a(rY, a2)
    return [rX, rY]


def miller(q: list, p: list) -> list:
    ret = fq12_one()

    aAffine = twist_make_affine(q)
    bAffine = curve_make_affine(p)

    minusA = twist_neg(aAffine)

    r = aAffine
    r2 = fq2_square(aAffine[1])

    for i in range(len(pseudo_binary_encoding) - 1, 0, -1):
        a, b, c, r = line_function_double(r, bAffine)
        if i != len(pseudo_binary_encoding) - 1:
            ret = fq12_square(ret)

        ret = line_function_mul(ret, a, b, c)

        s = pseudo_binary_encoding[i - 1]
        if s == 1:
            a, b, c, r = line_function_add(r, aAffine, bAffine, r2)
        elif s == -1:
            a, b, c, r = line_function_add(r, minusA, bAffine, r2)
        else:
            continue

        ret = line_function_mul(ret, a, b, c)

    q1 = [
        f2m(fq2_conjugate(aAffine[0]), xiToPMinus1Over3),
        f2m(fq2_conjugate(aAffine[1]), xiToPMinus1Over2),
        fq2_one(),
        fq2_one(),
    ]

    minusQ2 = [
        f2m_scalar(aAffine[0], xiToPSquaredMinus1Over3),
        aAffine[1],
        fq2_one(),
        fq2_one(),
    ]

    r2 = fq2_square(q1[1])
    a, b, c, r = line_function_add(r, q1, bAffine, r2)

    ret = line_function_mul(ret, a, b, c)

    r2 = fq2_square(minusQ2[1])
    a, b, c, r = line_function_add(r, minusQ2, bAffine, r2)
    ret = line_function_mul(ret, a, b, c)
    return ret


def final_exponentiation(p: list) -> list:
    t1 = fq12_conjugate(p)
    inv = fq12_invert(p)

    t1 = f12m(t1, inv)

    t2 = fq12_frobenius_p2(t1)
    t1 = f12m(t1, t2)

    fp = fq12_frobenius(t1)
    fp2 = fq12_frobenius_p2(t1)
    fp3 = fq12_frobenius(fp2)

    fu = fq12_exp(t1, u)
    fu2 = fq12_exp(fu, u)
    fu3 = fq12_exp(fu2, u)

    y3 = fq12_frobenius(fu)
    fu2p = fq12_frobenius(fu2)
    fu3p = fq12_frobenius(fu3)
    y2 = fq12_frobenius_p2(fu2)

    y0 = f12m(fp, fp2)
    y0 = f12m(y0, fp3)

    y1 = fq12_conjugate(t1)
    y5 = fq12_conjugate(fu2)
    y3 = fq12_conjugate(y3)
    y4 = f12m(fu, fu2p)
    y4 = fq12_conjugate(y4)

    y6 = f12m(fu3, fu3p)
    y6 = fq12_conjugate(y6)

    t0 = fq12_square(y6)
    t0 = f12m(t0, y4)
    t0 = f12m(t0, y5)

    t1 = f12m(y3, y5)
    t1 = f12m(t1, t0)
    t0 = f12m(t0, y2)
    t1 = fq12_square(t1)
    t1 = f12m(t1, t0)
    t1 = fq12_square(t1)
    t0 = f12m(t1, y1)
    t1 = f12m(t1, y0)
    t0 = fq12_square(t0)
    t0 = f12m(t0, t1)
    return t0


def twist_make_affine(c: list) -> list:
    if fq2_is_one(c[2]):
        return c
    elif fq2_is_zero(c[2]):
        return [
            fq2_zero(),
            fq2_one(),
            fq2_zero(),
            fq2_zero()
        ]
    else:
        zInv = fq2_invert(c[2])
        zInv2 = fq2_square(zInv)
        zInv3 = f2m(zInv2, zInv)
        return [
            f2m(c[0], zInv2),
            f2m(c[1], zInv3),
            fq2_one(),
            fq2_one(),
        ]


def twist_add(a: list, b: list) -> list:
    if twist_is_infinity(a):
        return b
    if twist_is_infinity(b):
        return a

    z12 = fq2_square(a[2])
    z22 = fq2_square(b[2])

    u1 = f2m(a[0], z22)
    u2 = f2m(b[0], z12)

    t = f2m(b[2], z22)
    s1 = f2m(a[1], t)

    t = f2m(a[2], z12)
    s2 = f2m(b[1], t)

    h = f2s(u2, u1)
    xEqual = fq2_eq(h, fq2_zero())

    t = f2a(h, h)
    i = fq2_square(t)
    j = f2m(h, i)
    t = f2s(s2, s1)

    yEqual = fq2_eq(t, fq2_zero())

    if (xEqual and yEqual):
        return twist_double(a)

    r = f2a(t, t)
    v = f2m(u1, i)

    t4 = fq2_square(r)
    t = f2a(v, v)
    t6 = f2s(t4, j)

    cX = f2s(t6, t)

    t = f2s(v, cX)
    t4 = f2m(s1, j)
    t6 = f2a(t4, t4)
    t4 = f2m(r, t)
    cY = f2s(t4, t6)

    t = f2a(a[2], b[2])
    t4 = fq2_square(t)
    t = f2s(t4, z12)
    t4 = f2s(t, z22)
    cZ = f2m(t4, h)
    return [cX, cY, cZ]


def twist_double(a: list) -> list:
    A = f2m(a[0], a[0])
    B = f2m(a[1], a[1])
    C = f2m(B, B)

    t = f2a(a[0], B)
    t2 = f2m(t, t)
    t = f2s(t2, A)
    t2 = f2s(t, C)

    d = f2a(t2, t2)
    t = f2a(A, A)
    e = f2a(t, A)
    f = f2m(e, e)

    t = f2a(d, d)
    cX = f2s(f, t)

    cZ = f2m(a[1], a[2])
    cZ = f2a(cZ, cZ)

    t = f2a(C, C)
    t2 = f2a(t, t)
    t = f2a(t2, t2)
    cY = f2s(d, cX)
    t2 = f2m(e, cY)
    cY = f2s(t2, t)
    return [cX, cY, cZ]


def twist_mul(pt: list, k: int) -> list:
    if int(k) == 0:
        return [fq2_one(), fq2_one(), fq2_zero()]

    R = [[fq2_zero(), fq2_zero(), fq2_zero()],
         pt]

    for kb in bits_of(k):
        R[kb ^ 1] = twist_add(R[kb], R[kb ^ 1])
        R[kb] = twist_double(R[kb])
    return R[0]


def twist_neg(c: list) -> list:
    return [
        c[0],
        fq2_neg(c[1]),
        c[2],
        fq2_zero(),
    ]


def twist_is_infinity(c: list) -> bool:
    return fq2_is_zero(c[2])


def twist_is_on_curve(c: list) -> bool:
    c = twist_make_affine(c)
    if twist_is_infinity(c):
        return True

    y2 = fq2_square(c[1])
    x3 = fq2_square(c[0])
    x3 = f2m(x3, c[0])

    y2 = f2s(y2, x3)
    y2 = f2s(y2, twistB)
    return fq2_is_zero(y2)


def curve_add(a: list, b: list) -> list:
    if curve_is_infinity(a):
        return b
    if curve_is_infinity(b):
        return a

    z12 = fm(a[2], a[2])
    z22 = fm(b[2], b[2])

    u1 = fm(a[0], z22)
    u2 = fm(b[0], z12)

    t = fm(b[2], z22)
    s1 = fm(a[1], t)

    t = fm(a[2], z12)
    s2 = fm(b[1], t)

    h = fs(u2, u1)
    xEqual = fq_eq(h, 0)

    t = fa(h, h)

    i = fm(t, t)

    j = fm(h, i)

    t = fs(s2, s1)

    yEqual = fq_eq(t, 0)

    if (xEqual and yEqual):
        return curve_double(a)

    r = fa(t, t)

    v = fm(u1, i)

    t4 = fm(r, r)
    t = fa(v, v)
    t6 = fs(t4, j)

    cX = fs(t6, t)

    t = fs(v, cX)
    t4 = fm(s1, j)
    t6 = fa(t4, t4)
    t4 = fm(r, t)
    cY = fs(t4, t6)

    t = fa(a[2], b[2])
    t4 = fm(t, t)
    t = fs(t4, z12)
    t4 = fs(t, z22)
    cZ = fm(t4, h)
    return [cX, cY, cZ]


def curve_double(a: list) -> list:
    A = fm(a[0], a[0])
    B = fm(a[1], a[1])
    C = fm(B, B)

    t = fa(a[0], B)
    t2 = fm(t, t)
    t = fs(t2, A)
    t2 = fs(t, C)

    d = fa(t2, t2)
    t = fa(A, A)
    e = fa(t, A)
    f = fm(e, e)

    t = fa(d, d)
    cX = fs(f, t)

    cZ = fm(a[1], a[2])
    cZ = fa(cZ, cZ)

    t = fa(C, C)
    t2 = fa(t, t)
    t = fa(t2, t2)
    cY = fs(d, cX)
    t2 = fm(e, cY)
    cY = fs(t2, t)
    return [cX, cY, cZ]


def curve_mul(pt: list, k: int) -> list:
    if int(k) == 0:
        return [1, 1, 0]

    R = [[0, 0, 0],
         pt]

    for kb in bits_of(k):
        R[kb ^ 1] = curve_add(R[kb], R[kb ^ 1])
        R[kb] = curve_double(R[kb])
    return R[0]


def curve_is_infinity(c: list) -> bool:
    return c[2] == 0


def curve_neg(c: list) -> list:
    return [
        c[0],
        fq_neg(c[1]),
        c[2],
        0,
    ]


def curve_make_affine(c: list) -> list:
    if fq_eq(c[2], 1):
        return c
    elif fq_eq(c[2], 0):
        return [
            0,
            1,
            0,
            0
        ]
    else:
        zInv = fq_inv(c[2])
        t = fm(c[1], zInv)
        zInv2 = fm(zInv, zInv)
        cX = fm(c[0], zInv2)
        cY = fm(t, zInv2)
        return [
            cX,
            cY,
            1,
            1,
        ]


def curve_is_on_curve(c: list) -> bool:
    c = curve_make_affine(c)
    if curve_is_infinity(c):
        return True

    y2 = fm(c[1], c[1])
    x3 = fm(c[0], c[0])
    x3 = fm(x3, c[0])
    x3 = fa(x3, curveB)
    return fq_eq(y2, x3)


def pairing(Q: list, P: list) -> list:
    assert curve_is_on_curve(P), f'P is not on the curve.'
    assert twist_is_on_curve(Q), f'Q is not on the curve.'
    if curve_is_infinity(P) or twist_is_infinity(Q):
        return fq12_one()
    r = miller(Q, P)
    return r

@export
def compute_vk(IC: list, inputs: list) -> list:
    vk_x = IC[0]
    for i in range(len(inputs)):
        assert inputs[i] < curve_order, "verifier-gte-snark-scalar-field"
        vk_x = curve_add(vk_x, curve_mul(IC[i + 1], inputs[i]))
    return vk_x

@export
def final_result(p: list, q: list) -> int:
    p[0] = curve_neg(p[0])

    x = fq12_one()
    for i in range(4):
        if twist_is_infinity(q[i]) or curve_is_infinity(p[i]):
            continue
        x = f12m(x, pairing(q[i], p[i]))

    x = final_exponentiation(x)
    if not fq12_is_one(x):
        return 1
    return 0
