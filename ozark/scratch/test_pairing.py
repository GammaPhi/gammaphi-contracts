from pairing_v2 import *
import time

# TESTS

'''
{'coeffs': [
    15012325621026644184045762978738412474442356583800543712126643990481298861813, 
    4267645508599519784673821560899175235932113169305747217206520518895142237067, 
    9605640887275982760085549877660272063759559624642361043769680838843663043844, 
    8527741798530570213140864223260614549490569205971543935479128986436935408273, 
    3170521800353213563435582240280934964129520522016748396998905395639804700884, 
    15282487952147349684932496442330344938300434905305660692548652058262012064788, 
    16971187067415765975504500253678755801792873843756283646571921697442136261102, 
    2076609033601584171799205032777989933146098390599741370266542789167810974568, 9956083666476842555094238955126296965718717241344979949561504280208798934772, 16599042560360271747366000606825634311946267556726426502310580624294554695499, 4754180242998611194659901576356075436720659925499469126121262195274010096072, 8506116078619111915017588317196675174068043321310924689396647807061593583064], 'modulus_coeffs': [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0], 'degree': 12}
{'coeffs': [
    15012325621026644184045762978738412474442356583800543712126643990481298861813, 
    4267645508599519784673821560899175235932113169305747217206520518895142237067,
     9605640887275982760085549877660272063759559624642361043769680838843663043844,
      8527741798530570213140864223260614549490569205971543935479128986436935408273,
       3170521800353213563435582240280934964129520522016748396998905395639804700884, 
       15282487952147349684932496442330344938300434905305660692548652058262012064788, 
       16971187067415765975504500253678755801792873843756283646571921697442136261102, 2076609033601584171799205032777989933146098390599741370266542789167810974568, 9956083666476842555094238955126296965718717241344979949561504280208798934772, 16599042560360271747366000606825634311946267556726426502310580624294554695499, 4754180242998611194659901576356075436720659925499469126121262195274010096072, 8506116078619111915017588317196675174068043321310924689396647807061593583064], 'modulus_coeffs': [82, 0, 0, 0, 0, 0, -18, 0, 0, 0, 0, 0], 'degree': 12}

(1368015179489954701390400359078579693043519447331113978918064868415326638035, 
9918110051302171585080402603319702774565515993150576347155970296011118125764)
(21888242871839275222246405745257275088696311157297823662689037894645226208491, 21888242871839275222246405745257275088696311157297823662689037894645226208572, 64)
'''

# Curve order should be prime
assert pow(2, curve_order, curve_order) == 2
# Curve order should be a factor of field_modulus**12 - 1
assert (field_modulus ** 12 - 1) % curve_order == 0


assert is_on_curve(G1, b)
assert is_on_curve(G2, b2)

assert tuple(b2['coeffs']) == tuple([19485874751759354771024239261021720505790618469301721065564631296452457478373, 266929791119991161246907387137283842545076965332900288569378510910307636690])


G12 = twist(G2)

assert is_on_curve(G12, b12)

# Check consistency of the "line function"
one, two, three = G1, double(G1), multiply(G1, 3)
negone, negtwo, negthree = multiply(G1, curve_order - 1), multiply(G1, curve_order - 2), multiply(G1, curve_order - 3)


'''
if False:
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
else:
    assert linefunc(one, two, one)[0] == FQ(0)
    assert linefunc(one, two, two)[0] == FQ(0)
    assert linefunc(one, two, three)[0] != FQ(0)
    assert linefunc(one, two, negthree)[0] == FQ(0)
    assert linefunc(one, negone, one)[0] == FQ(0)
    assert linefunc(one, negone, negone)[0] == FQ(0)
    assert linefunc(one, negone, two)[0] != FQ(0)
    assert linefunc(one, one, one)[0] == FQ(0)
    assert linefunc(one, one, two)[0] != FQ(0)
    assert linefunc(one, one, negtwo)[0] == FQ(0)

'''

assert fq_eq(fq_mul(FQ(2), FQ(2)), FQ(4))
assert fq_eq(fq_add(fq_div(FQ(2), FQ(7)), fq_div(FQ(9), FQ(7))), fq_div(FQ(11), FQ(7)))
assert FQ(2) * FQ(7) + FQ(9) * FQ(7) == FQ(11) * FQ(7)
assert fq_eq(fq_pow(FQ(9), field_modulus), FQ(9))
print('FQ works fine')

x = FQ2([1, 0])
f = FQ2([1, 2])
fpx = FQ2([2, 2])
one = FQ2([1, 0])
assert fqp_eq(fqp_add(x, f), fpx)
assert fqp_eq(fqp_div(f, f), one)
assert fqp_eq(fqp_add(fqp_div(one, f), fqp_div(x, f)), fqp_div(fqp_add(one, x), f))
assert fqp_eq(fqp_add(fqp_mul(one, f), fqp_mul(x, f)), fqp_mul(fqp_add(one, x), f))
assert fqp_eq(fqp_pow(x, (field_modulus ** 2 - 1)), one)
print('FQ2 works fine')

x = FQ12([1] + [0] * 11)
f = FQ12([1, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
fpx = FQ12([2, 2, 3, 4, 5, 6, 7, 8, 9, 10, 11, 12])
one = FQ12([1] + [0] * 11)
assert fqp_eq(fqp_add(x, f), fpx)
assert fqp_eq(fqp_div(f, f), one)
assert fqp_eq(fqp_add(fqp_div(one, f), fqp_div(x, f)), fqp_div(fqp_add(one, x), f))
assert fqp_eq(fqp_add(fqp_mul(one, f), fqp_mul(x, f)), fqp_mul(fqp_add(one, x), f))
# This check takes too long
# assert x ** (field_modulus ** 12 - 1) == one
print('FQ12 works fine')

assert eq(add(add(double(G1), G1), G1), double(double(G1)))
assert not eq(double(G1), G1)
assert eq(add(multiply(G1, 9), multiply(G1, 5)), add(multiply(G1, 12), multiply(G1, 2)))
assert is_inf(multiply(G1, curve_order))
print('G1 works fine')

assert eq(add(add(double(G2), G2), G2), double(double(G2)))
assert not eq(double(G2), G2)
assert eq(add(multiply(G2, 9), multiply(G2, 5)), add(multiply(G2, 12), multiply(G2, 2)))
assert is_inf(multiply(G2, curve_order))
assert not is_inf(multiply(G2, 2 * field_modulus - curve_order))
assert is_on_curve(multiply(G2, 9), b2)
print('G2 works fine')

assert eq(add(add(double(G12), G12), G12), double(double(G12)))
assert not eq(double(G12), G12)
assert eq(add(multiply(G12, 9), multiply(G12, 5)), add(multiply(G12, 12), multiply(G12, 2)))
assert is_on_curve(multiply(G12, 9), b12)
assert is_inf(multiply(G12, curve_order))
print('G12 works fine')

print('Starting pairing tests')
a = time.time()
one = FQ12([1] + [0] * 11)
p1 = pairing(G2, G1)
pn1 = pairing(G2, neg(G1))
assert fqp_eq(fqp_mul(p1, pn1), one)
print('Pairing check against negative in G1 passed')
np1 = pairing(neg(G2), G1)
assert fqp_eq(fqp_mul(p1, np1), one)
assert fqp_eq(pn1, np1)
print('Pairing check against negative in G2 passed')
assert fqp_eq(fqp_pow(p1, curve_order), one)
print('Pairing output has correct order')
print(G1)
print(multiply(G1, 2))
print(normalize1(multiply(G1, 2)))
p2 = pairing(G2, normalize1(multiply(G1, 2)))
print(p2)
print(fqp_mul(p1, p1))
assert fqp_eq(fqp_mul(p1, p1), p2)
print('Pairing bilinearity in G1 passed')
assert fqp_ne(p1, p2) and fqp_ne(p1, np1) and fqp_ne(p2, np1)
print('Pairing is non-degenerate')
po2 = pairing(normalize1(multiply(G2, 2)), G1)
assert fqp_eq(fqp_mul(p1, p1), po2)
print('Pairing bilinearity in G2 passed')
p3 = pairing(normalize1(multiply(G2, 27)), normalize1(multiply(G1, 37)))
po3 = pairing(G2, normalize1(multiply(G1, 999)))
assert fqp_eq(p3, po3)
print('Composite check passed')
print('Total time for pairings: %.3f' % (time.time() - a))

#print(p3)