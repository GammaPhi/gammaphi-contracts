#tests/test_contract.py
import unittest
import os
from os.path import dirname, abspath, join

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = dirname(dirname(dirname(abspath(__file__))))

OTP_CONTRACT = 'con_otp_v1'

with open(join(module_dir, 'otp', f'{OTP_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=OTP_CONTRACT, signer='me')


class MyTestCase(unittest.TestCase):
    def test_otp(self):
        client.signer = 'me'        
        contract = client.get_contract(OTP_CONTRACT)

        otp = contract.generate_otp(n_bits=80)
        print(otp)
        
        plain_text = "Kh,As,9c"
        encrypted = contract.encrypt(
            message_str=plain_text,
            otp=otp
        )

        print(plain_text)
        print(encrypted)

        self.assertNotEqual(plain_text, encrypted)

        decrypted = contract.decrypt(
            encrypted_str=encrypted,
            otp=otp
        )

        print(decrypted)

        self.assertEqual(plain_text, decrypted)

if __name__ == '__main__':
    unittest.main()