
from pairing_v1 import *;

v = 1868033
#v = 0b111001000000100000001
u = pow(v, 3)

#p = 36*pow(u,4) + 36*pow(u,3) + 24*pow(u,2) + 6*u + 1
#order = 36*pow(u,4) + 36*pow(u,3) + 18*pow(u,2) + 6*u + 1

#p = 65000549695646603732796438742359905742825358107623003571877145026864184071783 #(((u + 1)*6*u + 4)*u + 1)*6*u + 1
#order = 65000549695646603732796438742359905742570406053903786389881062969044166799969 #p - 6*u*u
p = field_modulus
order = curve_order
xi = FQ2([1, 3])
xi1 = [
    fqp_pow(xi,1*(p-1)//6),
    fqp_pow(xi,2*(p-1)//6),
    fqp_pow(xi,3*(p-1)//6),
    fqp_pow(xi,4*(p-1)//6),
    fqp_pow(xi,5*(p-1)//6)
]

#xi2 = [(x * x.conjugate_of()) for x in xi1]


def fqp_frobenius(p12: Any) -> Any:
    coeffs = []
    for i in range(6):
        p2 = FQ2(p12['coeffs'][i*2:i*2+2])
        p2 = FQ2([fq_neg(p2['coeffs'][0]),p2['coeffs'][1]])
        if i > 1:
            p2 = fqp_mul(p2, xi1[i-1])
        coeffs.extend(p2['coeffs'])
    return FQ12(coeffs)


def fqp_frobenius_p2(p12: Any) -> Any:
    coeffs = []
    for i in range(6):
        p2 = FQ2(p12['coeffs'][i*2:i*2+2])
        if i > 1:
            p2 = fqp_mul(p2, xi1[i-1])
        coeffs.extend(p2['coeffs'])
    return FQ12(coeffs)
    

def fqp_conjugate_of(p12: Any) -> Any:
    coeffs = p12['coeffs'].copy()
    for i in range(p12['degree']):
        if i % 2 == 0:
            coeffs[i] = fq_neg(coeffs[i])
    return FQ12(coeffs)

@export
def final_exponentiate(inp: Any) -> Any:
        # Algorithm 31 from https://eprint.iacr.org/2010/354.pdf

    t1 = fqp_conjugate_of(inp)
    inv = fqp_inv(inp)

    t1 = fqp_mul(t1, inv)
    # Now t1 = inp^(p**6-1)

    t2 = fqp_frobenius_p2(t1)
    t1 = fqp_mul(t1,t2)

    fp1 = fqp_frobenius(t1)
    fp2 = fqp_frobenius_p2(t1)
    fp3 = fqp_frobenius(fp2)

    fu1 = fqp_pow(t1,u)
    fu2 = fqp_pow(fu1,u)
    fu3 = fqp_pow(fu2,u)

    y3 = fqp_frobenius(fu1)
    fu2p = fqp_frobenius(fu2)
    fu3p = fqp_frobenius(fu3)
    y2 = fqp_frobenius_p2(fu2)

    y0 = fqp_mul(fp1,fp2)
    y0 = fqp_mul(y0,fp3)

    y1 = fqp_conjugate_of(t1)
    y5 = fqp_conjugate_of(fu2)
    y3 = fqp_conjugate_of(y3)
    y4 = fqp_mul(fu1,fu2p)
    y4 = fqp_conjugate_of(y4)

    y6 = fqp_mul(fu3,fu3p)
    y6 = fqp_conjugate_of(y6)

    t0 = fqp_mul(y6,y6)
    t0 = fqp_mul(t0,y4)
    t0 = fqp_mul(t0,y5)

    t1 = fqp_mul(y3,y5)
    t1 = fqp_mul(t1,t0)
    t0 = fqp_mul(t0,y2)
    t1 = fqp_mul(t1,t1)
    t1 = fqp_mul(t1,t0)
    t1 = fqp_mul(t1,t1)
    t0 = fqp_mul(t1,y1)
    t1 = fqp_mul(t1,y0)
    t0 = fqp_mul(t0,t0)
    t0 = fqp_mul(t0,t1)

    return t0
