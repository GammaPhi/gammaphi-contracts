# con_verifier_optimized_v1 (in progress)

pseudo_binary_encoding = [0, 0, 0, 1, 0, 1, 0, -1, 0, 0, 1, -1, 0, 0, 1, 0,
                          0, 1, 1, 0, -1, 0, 0, 1, 0, -1, 0, 0, 0, 0, 1, 1,
                          1, 0, 0, -1, 0, 0, 1, 0, 0, 0, 0, 0, -1, 0, 0, 1,
                          1, 0, 0, -1, 0, 0, 0, 1, 1, 0, -1, 0, 0, 1, 0, 1, 1]
curve_order = 21888242871839275222246405745257275088548364400416034343698204186575808495617
p2 = 21888242871839275222246405745257275088696311157297823662689037894645226208583
u = 4965661367192848881
np = 111032442853175714102588374283752698368366046808579839647964533820976443843465
rN1 = 20988524275117001072002809824448087578619730785600314334253784976379291040311
r2 = 3096616502983703923843567936837374451735540968419076528771170197431451843209
r3 = 14921786541159648185948152738563080959093619838510245177710943249661917737183
#xiToPSquaredMinus1Over3 = 17419166386535333598783630241015674584964973961482396687585055285806960741276
#xiTo2PSquaredMinus2Over3 = 20006444479023397533370224967097343182639219473961804911780625968796493078869
#xiToPSquaredMinus1Over6 = 1881798392815877688876180778159931906057091683336018750908411925848733129714
#xiToPMinus1Over6 = [7532670101108748540749979597679923402841328813027773483599019704565791010162, 1334504125441109323775816677333762124980877086439557453392802825656291576071]
#xiToPMinus1Over3 = [17373957475705492831721812124331982823197004514106338927670775596783233550167, 11461073415658098971834280704587444395456423268720245247603935854280982113072]
#xiToPMinus1Over2 = [20140510615310063345578764457068708762835443761990824243702724480509675468743, 16829996427371746075450799880956928810557034522864196246648550205375670302249]
#xiTo2PMinus2Over3 = [16514792769865828027011044701859348114858257981779976519405133026725453154633, 9893659366031634526915473325149983243417508801286144596494093251884139331218]
#twistB = [568440292453150825972223760836185707764922522371208948902804025364325400423, 16772280239760917788496391897731603718812008455956943122563801666366297604776]
xiToPMinus1Over6 = [16469823323077808223889137241176536799009286646108169935659301613961712198316, 8376118865763821496583973867626364092589906065868298776909617916018768340080]
xiToPMinus1Over3 = [10307601595873709700152284273816112264069230130616436755625194854815875713954, 10307601595873709700152284273816112264069230130616436755625194854815875713954]
xiToPMinus1Over2 = [3505843767911556378687030309984248845540243509899259641013678093033130930403, 2821565182194536844548159561693502659359617185244120367078079554186484126554]
xiToPSquaredMinus1Over3 = 21888242871839275220042445260109153167277707414472061641714758635765020556616
xiTo2PSquaredMinus2Over3 = 2203960485148121921418603742825762020974279258880205651966
xiToPSquaredMinus1Over6 = 21888242871839275220042445260109153167277707414472061641714758635765020556617
xiTo2PMinus2Over3 = [19937756971775647987995932169929341994314640652964949448313374472400716661030, 2581911344467009335267311115468803099551665605076196740867805258568234346338]


twistB = [266929791119991161246907387137283842545076965332900288569378510910307636690, 19485874751759354771024239261021720505790618469301721065564631296452457478373]
curveB = 3


# Extended euclidean algorithm to find modular inverses for
# integers
def fq_inv(a: int, n: int = p2) -> int:
    if a == 0:
        return 0
    lm, hm = 1, 0
    low, high = a % n, n
    while low > 1:
        r = high//low
        nm, new = hm-lm*r, high-low*r
        lm, low, hm, high = nm, new, lm, low
    return lm % n


def inverse_mod(a, n):
    t = 0
    t2 = 1
    r = n
    r2 = a

    while r2 != 0:
        q = r // r2
        (t, t2) = (t2, t - q * t2)
        (r, r2) = (r2, r - q * r2)

    if r > 1:
        return 0
    if t < 0:
        t += n
    return t


def redc(T):
    return T % p2 #
    #assert T < (R*p-1)
    m = ((T & (R-1)) * N) & (R-1)
    t = (T + m*p2) >> 256
    if t >= p2:
        t -= p2
    return t
    

def FQ(n: int) -> int:
    return redc(n) # % p2


def fq_add(self: int, other: int) -> int:
    return FQ(self + other)# % p2


def fq_mul(self: int, other: int) -> int:
    return FQ(self * other)# % p2


def fq_sub(self: int, other: int) -> int:
    return FQ(self - other)# % p2


def fq_div(self: int, other: int) -> int:
    assert isinstance(other, int), 'Invalid other. Should be an int.'
    return FQ(fq_mul(self, fq_inv(other, p2)))# % p2


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
    self = -self
    if self < 0:
        self += p2
    return self

def fq_one(n: int = None) -> int:
    return FQ(1)


def fq_zero(n: int = None) -> int:
    return FQ(0)


def bits_of(k):
    return [int(c) for c in "{0:b}".format(k)]


def FQ2(coeffs: list) -> list:
    assert len(coeffs) == 2, f'FQ2 must have 2 coefficients but had {len(coeffs)}'
    return coeffs


def FQ6(coeffs: list) -> list:
    assert len(coeffs) == 3 and len(coeffs[0]) == 2, 'FQ6 must have 3 FQ2s'
    return coeffs


def FQ12(coeffs: list) -> list:
    assert len(coeffs) == 2 and len(coeffs[0]) == 3 and len(coeffs[0][0]) == 2, 'FQ12 must have 2 FQ6s'
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


def fq2_add(self: list, other: list) -> list:
    return [fq_add(self[0], other[0]), fq_add(self[1], other[1])]


def fq2_sub(self: list, other: list) -> list:
    return [fq_sub(self[0], other[0]), fq_sub(self[1], other[1])]


def fq2_mul(self: list, other: list) -> list:
    tx = fq_mul(self[0], other[1])
    t = fq_mul(other[0], self[1])
    tx = fq_add(tx, t)

    ty = fq_mul(self[1], other[1])
    t = fq_mul(self[0], other[0])
    ty = fq_sub(ty, t)

    return [tx, ty]


def fq2_mul_scalar(self: list, other: int) -> list:
    x = fq_mul(self[0], other)
    y = fq_mul(self[1], other)
    return [x, y]


def fq2_mul_xi(self: list) -> list:
    tx = fq_add(self[0], self[0])
    tx = fq_add(tx, tx)
    tx = fq_add(tx, tx)
    tx = fq_add(tx, self[0])

    tx = fq_add(tx, self[1])

    ty = fq_add(self[1], self[1])
    ty = fq_add(ty, ty)
    ty = fq_add(ty, ty)
    ty = fq_add(ty, self[1])
    
    ty = fq_sub(ty, self[0])

    return [tx, ty]


def fq2_eq(self: list, other: list) -> bool:
    return self[0] == other[0] and self[1] == other[1]


def fq2_square(self: list) -> list:
    tx = fq_sub(self[1], self[0])
    ty = fq_add(self[0], self[1])
    ty = fq_mul(tx, ty)

    tx = fq_mul(self[0], self[1])
    tx = fq_add(tx, tx)
    return [tx, ty]


def fq2_invert(self: list) -> list:
    t1 = fq_mul(self[0], self[0])
    t2 = fq_mul(self[1], self[1])
    t1 = fq_add(t1, t2)
    inv = fq_inv(t1)
    t1 = fq_neg(self[0])
    x = fq_mul(t1, inv)
    y = fq_mul(self[1], inv)
    return [x, y]
    

def fq6_one(n: int = 0) -> list:
    return [fq2_zero(), fq2_zero(), fq2_one()]


def fq6_zero(n: int = 0) -> list:
    return [fq2_zero(), fq2_zero(), fq2_zero()]


def fq6_is_zero(self: list) -> bool:
    return fq2_is_zero(self[0]) and fq2_is_zero(self[1]) and fq2_is_zero(self[2])


def fq6_is_one(self: list) -> bool:
    return fq2_is_zero(self[0]) and fq2_is_zero(self[1]) and fq6_is_one(self[2])


def fq6_neg(self: list) -> list:
    return [fq2_neg(self[0]), fq2_neg(self[1]), fq2_neg(self[2])]


def fq6_frobenius(self: list) -> list:
    x = fq2_conjugate(self[0])
    y = fq2_conjugate(self[1])
    z = fq2_conjugate(self[2])
    x = fq2_mul(x, xiTo2PMinus2Over3)
    y = fq2_mul(y, xiToPMinus1Over3)
    return [x, y, z]


def fq6_frobenius_p2(self: list) -> list:
    x = fq2_mul_scalar(self[0], xiTo2PSquaredMinus2Over3)
    y = fq2_mul_scalar(self[1], xiToPSquaredMinus1Over3) 
    return [x, y, self[2]]


def fq6_add(self: list, other: list) -> list:
    return [fq2_add(self[0], other[0]), fq2_add(self[1], other[1]), fq2_add(self[2], other[2])]


def fq6_sub(self: list, other: list) -> list:
    return [fq2_sub(self[0], other[0]), fq2_sub(self[1], other[1]), fq2_sub(self[2], other[2])]
    

def fq6_mul(self: list, other: list) -> list:
    v0 = fq2_mul(self[2], other[2])
    v1 = fq2_mul(self[1], other[1])
    v2 = fq2_mul(self[0], other[0])
    t0 = fq2_add(self[0], self[1])
    t1 = fq2_add(other[0], other[1])
    tz = fq2_mul(t0, t1)
    tz = fq2_sub(tz, v1)
    tz = fq2_sub(tz, v2)
    tz = fq2_mul_xi(tz)
    tz = fq2_add(tz, v0)

    t0 = fq2_add(self[1], self[2])
    t1 = fq2_add(other[1], other[2])
    ty = fq2_mul(t0, t1)
    t0 = fq2_mul_xi(v2)
    ty = fq2_sub(ty, v0)
    ty = fq2_sub(ty, v1)
    ty = fq2_add(ty, t0)

    t0 = fq2_add(self[0], self[2])
    t1 = fq2_add(other[0], other[2])
    tx = fq2_mul(t0, t1)
    tx = fq2_sub(tx, v0)
    tx = fq2_add(tx, v1)
    tx = fq2_sub(tx, v2)

    return [tx, ty, tz]


def fq6_mul_scalar(self: list, other: list) -> list:
    return [fq2_mul(self[0], other), fq2_mul(self[1], other), fq2_mul(self[2], other)]


def fq6_mul_gfp(self: list, other: int) -> list:
    return [fq2_mul_scalar(self[0], other), fq2_mul_scalar(self[1], other), fq2_mul_scalar(self[2], other)]


def fq6_mul_tau(self: list) -> list:
    tz = fq2_mul_xi(self[0])
    ty = self[1]
    return [ty, self[2], tz]


def fq6_square(self: list) -> list:
    v0 = fq2_square(self[2])
    v1 = fq2_square(self[1])
    v2 = fq2_square(self[0])

    c0 = fq2_add(self[0], self[1])
    c0 = fq2_square(c0)
    c0 = fq2_sub(c0, v1)
    c0 = fq2_sub(c0, v2)
    c0 = fq2_mul_xi(c0)
    c0 = fq2_add(c0, v0)

    c1 = fq2_add(self[1], self[2])
    c1 = fq2_square(c1)
    c1 = fq2_sub(c1, v0)
    c1 = fq2_sub(c1, v1)
    xiV2 = fq2_mul_xi(v2)
    c1 = fq2_add(c1, xiV2)

    c2 = fq2_add(self[0], self[2])
    c2 = fq2_square(c2)
    c2 = fq2_sub(c2, v0)
    c2 = fq2_add(c2, v1)
    c2 = fq2_sub(c2, v2)

    return [c2, c1, c0]


def fq6_invert(self: list) -> list:
    t1 = fq2_mul(self[0], self[1])
    t1 = fq2_mul_xi(t1)

    A = fq2_square(self[2])
    A = fq2_sub(A, t1)

    B = fq2_square(self[0])
    B = fq2_mul_xi(B)

    t1 = fq2_add(self[1], self[2])
    B = fq2_sub(B, t1)

    C = fq2_square(self[1])
    t1 = fq2_mul(self[0], self[2])
    C = fq2_sub(C, t1)

    F = fq2_mul(C, self[1])
    F = fq2_mul_xi(F)
    t1 = fq2_mul(A, self[2])
    F = fq2_add(F, t1)
    t1 = fq2_mul(B, self[0])
    t1 = fq2_mul_xi(t1)
    F = fq2_add(F, t1)

    F = fq2_invert(F)

    return [fq2_mul(C, F), fq2_mul(B, F), fq2_mul(A, F)]


def fq12_one(n: int = 0) -> list:
    return [fq6_one(), fq6_zero()]


def fq12_zero(n: int = 0) -> list:
    return [fq6_zero(), fq6_zero()]


def fq12_is_zero(self: list) -> bool:
    return fq6_is_zero(self[0]) and fq6_is_zero(self[1])


def fq12_is_one(self: list) -> bool:
    return fq6_is_zero(self[0]) and fq6_is_one(self[1])


def fq12_conjugate(self: list) -> list:
    return [fq6_neg(self[0]), self[1]]


def fq12_neg(self: list) -> list:
    return [fq6_neg(self[0]), fq6_neg(self[1])]


def fq12_frobenius(self: list) -> list:
    x = fq6_frobenius(self[0])
    x = fq6_mul_scalar(x, xiToPMinus1Over6)
    return [x, fq6_frobenius(self[1])]


def fq12_frobenius_p2(self: list) -> list:
    x = fq6_frobenius_p2(self[0])
    x = fq6_mul_gfp(x, xiToPSquaredMinus1Over6)
    return [x, fq6_frobenius_p2(self[1])]


def fq12_add(self: list, other: list) -> list:
    return [fq6_add(self[0], other[0]), fq6_add(self[1], other[1])]


def fq12_sub(self: list, other: list) -> list:
    return [fq6_sub(self[0], other[0]), fq6_sub(self[1], other[1])]
    

def fq12_mul(self: list, other: list) -> list:
    tx = fq6_mul(self[0], other[1])
    t = fq6_mul(self[1], other[0])
    tx = fq6_add(tx, t)
    ty = fq6_mul(self[1], other[1])
    t = fq6_mul(self[0], other[0])
    t = fq6_mul_tau(t)
    return [tx, fq6_add(ty, t)]


def fq12_mul_scalar(self: list, other: list) -> list:
    return [fq6_mul(self[0], other), fq6_mul(self[1], other)]


def fq12_exp(self: list, other: int) -> list:
    sum = fq12_one()
    for i in range(other.bit_length()-1, -1, -1):
        t = fq12_square(sum)
        if other >> i & 1 != 0:
            sum = fq12_mul(t, self)
        else:
            sum = t
    return sum


def fq12_square(self: list) -> list:
    v0 = fq6_mul(self[0], self[1])
    t = fq6_mul_tau(self[0])
    t = fq6_add(self[1], t)
    ty = fq6_add(self[0], self[1])
    ty = fq6_mul(ty, t)
    ty = fq6_sub(ty, v0)
    t = fq6_mul_tau(v0)
    ty = fq6_sub(ty, t)
    return [fq6_add(v0, v0), ty]


def fq12_invert(self: list) -> list:
    t1 = fq6_square(self[0])
    t2 = fq6_square(self[1])
    t1 = fq6_mul_tau(t1)
    t1 = fq6_sub(t2, t1)
    t2 = fq6_invert(t1)
    return fq12_mul_scalar([fq6_neg(self[0]), self[1]], t2)


def line_function_add(r: list, p: list, q: list, r2: list) -> tuple:
    B = fq2_mul(p[0], r[3])
    D = fq2_add(p[1], r[2])
    D = fq2_square(D)
    D = fq2_sub(D, r2)
    D = fq2_sub(D, r[3])
    D = fq2_mul(D, r[3])

    H = fq2_sub(B, r[0])
    I = fq2_square(H)

    E = fq2_add(I, I)
    E = fq2_add(E, E)

    J = fq2_mul(H, E)

    L1 = fq2_sub(D, r[1])
    L1 = fq2_sub(L1, r[1])

    V = fq2_mul(r[0], E)
    rOutX = fq2_square(L1)
    rOutX = fq2_sub(rOutX, J)
    rOutX = fq2_sub(rOutX, V)
    rOutX = fq2_sub(rOutX, V)

    rOutZ = fq2_add(r[2], H)
    rOutZ = fq2_square(rOutZ)
    rOutZ = fq2_sub(rOutZ, r[3])
    rOutZ = fq2_sub(rOutZ, I)

    t = fq2_sub(V, rOutX)
    t = fq2_mul(t, L1)
    t2 = fq2_mul(r[1], J)
    t2 = fq2_add(t2, t2)
    rOutY = fq2_sub(t, t2)
    rOutT = fq2_square(rOutZ)

    t = fq2_add(p[1], rOutZ)
    t = fq2_square(t)
    t = fq2_sub(t, r2)
    t = fq2_sub(t, rOutT)

    t2 = fq2_mul(L1, p[0])
    t2 = fq2_add(t2, t2)
    a = fq2_sub(t2, t)

    c = fq2_mul_scalar(rOutZ, q[1])
    c = fq2_add(c, c)

    b = fq2_neg(L1)
    b = fq2_mul_scalar(b, q[0])
    b = fq2_add(b, b)

    return a, b, c, [rOutX, rOutY, rOutZ, rOutT]


def line_function_double(r: list, q: list) -> tuple:
    A = fq2_square(r[0])
    B = fq2_square(r[1])
    C = fq2_square(B)

    D = fq2_add(r[0], B)
    D = fq2_square(D)
    D = fq2_sub(D, A)
    D = fq2_sub(D, C)
    D = fq2_add(D, D)

    E = fq2_add(A, A)
    E = fq2_add(E, A)

    G = fq2_square(E)

    rX = fq2_sub(G, D)
    rX = fq2_sub(rX, D)
    
    rZ = fq2_add(r[1], r[2])
    rZ = fq2_square(rZ)
    rZ = fq2_sub(rZ, B)
    rZ = fq2_sub(rZ, r[3])
    
    rY = fq2_sub(D, rX)
    rY = fq2_mul(rY, E)

    t = fq2_add(C, C)
    t = fq2_add(t, t)
    rY = fq2_sub(rY, t)
    rT = fq2_square(rZ)

    t = fq2_mul(E, rT)
    t = fq2_add(t, t)
    b = fq2_neg(t)
    b = fq2_mul_scalar(b, q[0])

    a = fq2_add(r[0], E)
    a = fq2_square(a)
    a = fq2_sub(a, A)
    a = fq2_sub(a, G)
    t = fq2_add(B, B)
    t = fq2_add(t, t)
    a = fq2_sub(a, t)

    c = fq2_mul(rZ, r[3])
    c = fq2_add(c, c)
    c = fq2_mul_scalar(c, q[1])
    
    return a, b, c, [rX, rY, rZ, rT]


def line_function_mul(ret: list, a: list, b: list, c: list) -> list:
    a2 = [fq2_zero(), a, b]
    a2 = fq6_mul(a2, ret[0])
    t3 = fq6_mul_scalar(ret[1], c)

    t = fq2_add(b, c)
    t2 = [fq2_zero(), a, t]
    ret[0] = fq6_add(ret[0], ret[1])
    ret[1] = t3

    ret[0] = fq6_mul(ret[0], t2)
    ret[0] = fq6_sub(ret[0], a2)
    ret[0] = fq6_sub(ret[0], ret[1])
    a2 = fq6_mul_tau(a2)
    ret[1] = fq6_add(ret[1], a2)
    return ret


def miller(q: list, p: list) -> list:
    ret = fq12_one()
    
    aAffine = twist_make_affine(q)
    bAffine = curve_make_affine(p)

    minusA = twist_neg(aAffine)

    r = aAffine

    r2 = fq2_square(aAffine[1])

    for i in range(len(pseudo_binary_encoding)-1, 0, -1):
        a, b, c, newR = line_function_double(r, bAffine)
        if i != len(pseudo_binary_encoding) - 1:
            ret = fq12_square(ret)

        ret = line_function_mul(ret, a, b, c)
        r = newR

        s = pseudo_binary_encoding[i-1]
        if s == 1:
            a, b, c, newR = line_function_add(r, aAffine, bAffine, r2)
        elif s == -1:
            a, b, c, newR = line_function_add(r, minusA, bAffine, r2)
        else:
            continue

        ret = line_function_mul(ret, a, b, c)

    q1 = [
        fq2_mul(fq2_conjugate(aAffine[0]), xiToPMinus1Over3),
        fq2_mul(fq2_conjugate(aAffine[1]), xiToPMinus1Over2),
        fq2_one(),
        fq2_one(), 
    ]

    minusQ2 = [
        fq2_mul_scalar(aAffine[0], xiToPSquaredMinus1Over3),
        aAffine[1],
        fq2_one(),
        fq2_one(),
    ]

    r2 = fq2_square(q1[1])
    a, b, c, newR = line_function_add(r, q1, bAffine, r2)
    ret = line_function_mul(ret, a, b, c)
    r = newR

    r2 = fq2_square(minusQ2[1])
    a, b, c, newR = line_function_add(r, minusQ2, bAffine, r2)
    ret = line_function_mul(ret, a, b, c)
    r = newR

    return ret


def final_exponentiation(p: list) -> list:
    t1 = [fq6_neg(p[0]), p[1]]

    inv = fq12_invert(p)
    t1 = fq12_mul(t1, inv)

    t2 = fq12_frobenius_p2(t1)
    t1 = fq12_mul(t1, t2)

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

    y0 = fq12_mul(fp, fp2)
    y0 = fq12_mul(y0, fp3)

    y1 = fq12_conjugate(t1)
    y5 = fq12_conjugate(fu2)
    y3 = fq12_conjugate(y3)
    y4 = fq12_mul(fu, fu2p)
    y4 = fq12_conjugate(y4)

    y6 = fq12_mul(fu3, fu3p)
    y6 = fq12_conjugate(y6)

    t0 = fq12_square(y6)
    t0 = fq12_mul(t0, y4)
    t0 = fq12_mul(t0, y5)
    t1 = fq12_mul(y3, y5)
    t1 = fq12_mul(t1, t0)
    t0 = fq12_mul(t0, y2)
    t1 = fq12_square(t1)
    t1 = fq12_mul(t1, t0)
    t1 = fq12_square(t1)
    t0 = fq12_mul(t1, y1)
    t1 = fq12_mul(t1, y0)
    t0 = fq12_square(t0)
    t0 = fq12_mul(t0, t1)

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
        zInv3 = fq2_mul(zInv2, zInv)
        return [
            fq2_mul(c[0], zInv2),
            fq2_mul(c[1], zInv3),
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

    u1 = fq2_mul(a[0], z22)
    u2 = fq2_mul(b[0], z12)

    t = fq2_mul(b[2], z22)
    s1 = fq2_mul(a[1], t)

    t = fq2_mul(a[2], z12)
    s2 = fq2_mul(b[1], t)

    h = fq2_sub(u2, u1)
    xEqual = fq2_eq(h, fq2_zero())

    t = fq2_add(h, h)

    i = fq2_square(t)

    j = fq2_mul(h, i)

    t = fq2_sub(s2, s1)

    yEqual = fq2_eq(t, fq2_zero())

    if (xEqual and yEqual):
        return twist_double(a)

    r = fq2_add(t, t)

    v = fq2_mul(u1, i)

    t4 = fq2_square(r)
    t = fq2_add(v, v)
    t6 = fq2_sub(t4, j)

    cX = fq2_sub(t6, t)

    t = fq2_sub(v, cX)
    t4 = fq2_mul(s1, j)
    t6 = fq2_add(t4, t4)
    t4 = fq2_mul(r, t)
    cY = fq2_sub(t4, t6)

    t = fq2_add(a[2], b[2])
    t4 = fq2_square(t)
    t = fq2_sub(t4, z12)
    t4 = fq2_sub(t, z22)
    cZ = fq2_mul(t4, h)

    return [cX, cY, cZ]


def twist_double(a: list) -> list:
    A = fq2_mul(a[0], a[0])
    B = fq2_mul(a[1], a[1])
    C = fq2_mul(B, B)

    t = fq2_add(a[0], B)
    t2 = fq2_mul(t, t)
    t = fq2_sub(t2, A)
    t2 = fq2_sub(t, C)

    d = fq2_add(t2, t2)
    t = fq2_add(A, A)
    e = fq2_add(t, A)
    f = fq2_mul(e, e)

    t = fq2_add(d, d)
    cX = fq2_sub(f, t)

    cZ = fq2_mul(a[1], a[2])
    cZ = fq2_add(cZ, cZ)
    
    t = fq2_add(C, C)
    t2 = fq2_add(t, t)
    t = fq2_add(t2, t2)
    cY = fq2_sub(d, cX)
    t2 = fq2_mul(e, cY)
    cY = fq2_sub(t2, t)

    return [cX, cY, cZ]


def twist_mul(pt: list, k: int) -> list:
    if int(k) == 0:
        return [fq2_one(), fq2_one(), fq2_zero()]

    R = [[fq2_zero(), fq2_zero(), fq2_zero()],
         pt]

    for kb in bits_of(k):
        R[kb^1] = twist_add(R[kb], R[kb^1])
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
    print(f'C: {c}')
    c = twist_make_affine(c)
    print(f'C Affine: {c}')
    if twist_is_infinity(c):
        return True

    y2 = fq2_square(c[1])
    x3 = fq2_square(c[0])
    x3 = fq2_mul(x3, c[0])

    y2 = fq2_sub(y2, x3)
    y2 = fq2_sub(y2, twistB)

    print(f'Y2: {y2}')
    return fq2_is_zero(y2)


def curve_add(a: list, b: list) -> list:
    if curve_is_infinity(a):
        return b
    if curve_is_infinity(b):
        return a

    z12 = fq_mul(a[2], a[2])
    z22 = fq_mul(b[2], b[2])

    u1 = fq_mul(a[0], z22)
    u2 = fq_mul(b[0], z12)

    t = fq_mul(b[2], z22)
    s1 = fq_mul(a[1], t)

    t = fq_mul(a[2], z12)
    s2 = fq_mul(b[1], t)

    h = fq_sub(u2, u1)
    xEqual = fq_eq(h, fq_zero())

    t = fq_add(h, h)

    i = fq_mul(t, t)

    j = fq_mul(h, i)

    t = fq_sub(s2, s1)

    yEqual = fq_eq(t, fq_zero())

    if (xEqual and yEqual):
        return curve_double(a)

    r = fq_add(t, t)

    v = fq_mul(u1, i)

    t4 = fq_mul(r, r)
    t = fq_add(v, v)
    t6 = fq_sub(t4, j)

    cX = fq_sub(t6, t)

    t = fq_sub(v, cX)
    t4 = fq_mul(s1, j)
    t6 = fq_add(t4, t4)
    t4 = fq_mul(r, t)
    cY = fq_sub(t4, t6)

    t = fq_add(a[2], b[2])
    t4 = fq_mul(t, t)
    t = fq_sub(t4, z12)
    t4 = fq_sub(t, z22)
    cZ = fq_mul(t4, h)

    return [cX, cY, cZ]


def curve_double(a: list) -> list:
    A = fq_mul(a[0], a[0])
    B = fq_mul(a[1], a[1])
    C = fq_mul(B, B)

    t = fq_add(a[0], B)
    t2 = fq_mul(t, t)
    t = fq_sub(t2, A)
    t2 = fq_sub(t, C)

    d = fq_add(t2, t2)
    t = fq_add(A, A)
    e = fq_add(t, A)
    f = fq_mul(e, e)

    t = fq_add(d, d)
    cX = fq_sub(f, t)

    cZ = fq_mul(a[1], a[2])
    cZ = fq_add(cZ, cZ)
    
    t = fq_add(C, C)
    t2 = fq_add(t, t)
    t = fq_add(t2, t2)
    cY = fq_sub(d, cX)
    t2 = fq_mul(e, cY)
    cY = fq_sub(t2, t)

    return [cX, cY, cZ]


def curve_mul(pt: list, k: int) -> list:
    if int(k) == 0:
        return [fq_one(), fq_one(), fq_zero()]

    R = [[fq_zero(), fq_zero(), fq_zero()],
         pt]

    for kb in bits_of(k):
        R[kb^1] = curve_add(R[kb], R[kb^1])
        R[kb] = curve_double(R[kb])
    return R[0]


def curve_is_infinity(c: list) -> bool:
    return c[2] == fq_zero()


def curve_neg(c: list) -> list:
    return [
        c[0],
        fq_neg(c[1]),
        c[2],
        fq_zero(),
    ]


def curve_make_affine(c: list) -> list:
    if fq_eq(c[2], fq_one()):
        return c
    elif fq_eq(c[2], fq_zero()):
        return [
            fq_zero(),
            fq_one(),
            fq_zero(),
            fq_zero()
        ]
    else:
        zInv = fq_inv(c[2])
        t = fq_mul(c[1], zInv)
        zInv2 = fq_mul(zInv, zInv)
        cX = fq_mul(c[0], zInv2)
        cY = fq_mul(t, zInv2)
        return [
            cX,
            cY,
            fq2_one(),
            fq2_one(),
        ]


def curve_is_on_curve(c: list) -> bool:
    c = curve_make_affine(c)
    if curve_is_infinity(c):
        return True
    
    y2 = fq_mul(c[1], c[1])
    x3 = fq_mul(c[0], c[0])
    x3 = fq_mul(x3, c[0])
    x3 = fq_add(x3, curveB)

    return fq_eq(y2, x3)


def pairing(Q: list, P: list) -> list:
    assert curve_is_on_curve(P), f'P is not on the curve.'
    #print(Q)
    assert twist_is_on_curve(Q), f'Q is not on the curve.'
    print(f'P: {P}')
    print(f'Q: {Q}')
    if curve_is_infinity(P) or twist_is_infinity(Q):
        return fq12_one()
    r = miller(Q, P)
    return r


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
        vk_x = curve_add(vk_x, curve_mul(IC[i+1], inputs[i]))

    p = [
        curve_neg(proof['A']),
        vk['vk_alfa_1'],
        vk_x,
        proof['C']
    ]
    q = [
        (proof['B'][0], proof['B'][1], proof['B'][2]),
        vk['vk_beta_2'],
        vk['vk_gamma_2'],
        vk['vk_delta_2']
    ]

    x = fq12_one()
    for i in range(4):
        if twist_is_infinity(q[i]) or curve_is_infinity(p[i]):
            continue
        print(x)
        x = fq12_mul(x, pairing(q[i], p[i]))
    print(x)
    x = final_exponentiation(x)    
    print(x)

    if not fq12_is_one(x):
        return 1
    return 0


#@export
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


# TEST


twistGen = [[9496696083199853777875401760424613833161720860855390556979200160215841136960, 11461925177900819176832270005713103520318409907105193817603008068482420711462], [6170940445994484564222204938066213705353407449799250191249554538140978927342, 18540402224736191443939503902445128293982106376239432540843647066670759668214], [0, 1], [0, 1]]
twistGen = [[11559732032986387107991004021392285783925812861821192530917403151452391805634, 10857046999023057135944570762232829481370756359578518086990519993285655852781], [4082367875863433681332203403145435568316851327593401208105741076214120093531, 8495653923123431417604973247489272438418190587263600148770280649306958101930], [0, 1], [0, 1]]
curveGen = [1, 2, 1, 1]

assert fq2_eq(fq2_mul(twistB, twistB), fq2_square(twistB))

G2 = (FQ2([10857046999023057135944570762232829481370756359578518086990519993285655852781, 11559732032986387107991004021392285783925812861821192530917403151452391805634]),
      FQ2([8495653923123431417604973247489272438418190587263600148770280649306958101930, 4082367875863433681332203403145435568316851327593401208105741076214120093531]),
      fq2_one(),
      fq2_one(),
    )

assert twist_double(twistGen) == twist_mul(twistGen, 2), 'Invalid'
assert curve_double(curveGen) == curve_mul(curveGen, 2), 'Invalid curveGen'
assert twist_double(twistGen) == twist_add(twistGen, twistGen), 'Invalid add'

assert curve_is_on_curve(curveGen), 'bad curve'
#assert twist_is_on_curve(G2), 'bad twist'
assert twist_is_on_curve(twistGen), 'bad twist'

a1 = curve_mul(curveGen, 1)
b1 = twist_mul(twistGen, 1)


an1 = curve_mul(curveGen, 21888242871839275222246405745257275088548364400416034343698204186575808495616)

assert pairing(b1, a1), 'bad pairing'
assert pairing(b1, an1), 'bad neg pairing'





proof_data = { 'pi_a':
   [ '13774734694806893345431794156356514571363079254825067879443184821206447822750',
     '5209428786776521202856824112990553528771784326411286192918798384107382954954',
     '1' ],
  'pi_b':
   [ [ '5173078677927959662734785177277144661908479282203617744477925437547277462997',
       '5008919259924401514229994859356982028735024574680767144772652733435392622987' ],
     [ '16237021846884756770715728474067652062799669637447076030779615223774369289462',
       '2712062232854900554770345916314277164381058075864652478551356549239494502978' ],
     [ '1', '0' ] ],
  'pi_c':
   [ '11709473128502841396551378248174338037383283271432381215788718530577500746586',
     '4008944338641772649658914022116044050220759783362908976331068335514955377268',
     '1' ],
  'publicSignals':
   [ '19472974227534089877661842339747066589074924514634613071633204486088526229164',
     '18099330611372391564551405916666174527872771719801289262717800528837024370849',
     '104194005008344116962432275389062747476573328740969784167625267554300778358',
     '0',
     '0',
     '0' ] }

a = proof_data['pi_a']
b = proof_data['pi_b']
c = proof_data['pi_c']

inputs = proof_data['publicSignals']

if not verify_proof(a=a, b=b, c=c, inputs=inputs):
    print('Failed.')
else:
    print('Succeeded.')
