#tests/test_contract.py
import unittest
import os

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = os.path.dirname(os.path.dirname(__file__))

with open(os.path.join(module_dir, 'con_rsa_encryption.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_rsa_encryption')


class MyTestCase(unittest.TestCase):
    def test_encrypt_rsa_lib(self):
        client.signer = 'me'        
        contract = client.get_contract('con_rsa_encryption')

        # Generate keys with rsa library
        import rsa
        (pubkey, privkey) = rsa.newkeys(2048)


        message = "hello world"

        encrypted = contract.encrypt(
            message_str=message,
            n=pubkey.n,
            e=pubkey.e
        )

        print("encrypted: %s" % encrypted)


        encrypted_bytes = bytes.fromhex(encrypted)

        decrypted = rsa.decrypt(encrypted_bytes, privkey).decode('utf-8')
        print("decrypted: %s" % decrypted)


        self.assertNotEqual(encrypted, message)
        self.assertEqual(decrypted, message)

    def test_encrypt_pycryptodome_lib(self):
        client.signer = 'me'        
        contract = client.get_contract('con_rsa_encryption')

        # Load RSA keys with PyCryptodome
        from Crypto.PublicKey import RSA
        from Crypto.Cipher import PKCS1_v1_5
        from Crypto.Random import get_random_bytes
        with open(os.path.join(module_dir, 'rsa_keys'), mode='rb') as f:
            keydata = f.read()
        key = RSA.import_key(keydata)
        
        pubkey = key.publickey()

        message = "hello world"

        encrypted = contract.encrypt(
            message_str=message,
            n=pubkey.n,
            e=pubkey.e
        )

        print("encrypted: %s" % encrypted)


        encrypted_bytes = bytes.fromhex(encrypted)

        decrypted = PKCS1_v1_5.new(key).decrypt(encrypted_bytes, get_random_bytes(16)).decode('utf-8')
        print("decrypted: %s" % decrypted)


        self.assertNotEqual(encrypted, message)
        self.assertEqual(decrypted, message)

if __name__ == '__main__':
    unittest.main()