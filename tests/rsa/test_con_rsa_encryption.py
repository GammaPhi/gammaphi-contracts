#tests/test_contract.py
import unittest
import os
from os.path import dirname, abspath, join

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'rsa')

with open(join(module_dir, 'con_rsa_encryption.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_rsa_encryption')


class MyTestCase(unittest.TestCase):

    def test_encrypt_compat(self):
        client.signer = 'me'        
        contract = client.get_contract('con_rsa_encryption')

        # Example message
        message = "hello world"

        # Encrypt message through smart contract
        encrypted = contract.encrypt(
            message_str=message,
            n=22463395453379572494299964953834160277809074231190028763086659783000303770191045279852939309635191780711647336382876624936502351944448350464569010948062029408619485755391858230491389744247574318025703699137270695895996923006430070408349011468244191849613201595788561756711987075851787623500708504610902708052729982112357592620403745835233981562046305040255740022461302510941541535906636268505594248261459049343064251415318778780768709858796689824249324489420357772513299328409898422798133125429122431700921367648878124433422169127986207654407526339663793221775301455974983089726351377291893029316034225554448166888491,
            e=65537
        )
        print("encrypted by js: %s" % encrypted)
        self.assertNotEqual(encrypted, message)


    def test_encrypt_rsa_lib(self):
        client.signer = 'me'        
        contract = client.get_contract('con_rsa_encryption')

        # Generate keys with rsa library
        import rsa
        (pubkey, privkey) = rsa.newkeys(2048)

        # Example message
        message = "hello world"

        # Encrypt message through smart contract
        encrypted = contract.encrypt(
            message_str=message,
            n=pubkey.n,
            e=pubkey.e
        )
        print("encrypted: %s" % encrypted)

        # Decrypt with rsa library
        decrypted = rsa.decrypt(bytes.fromhex(encrypted), privkey).decode('utf-8')
        print("decrypted: %s" % decrypted)

        # Verify
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

        # Example message
        message = "hello world"

        # Encrypt message through smart contract
        encrypted = contract.encrypt(
            message_str=message,
            n=pubkey.n,
            e=pubkey.e
        )
        print("encrypted: %s" % encrypted)

        # Decrypt with PyCryptodome library
        decrypted = PKCS1_v1_5.new(key).decrypt(bytes.fromhex(encrypted), get_random_bytes(16)).decode('utf-8')
        print("decrypted: %s" % decrypted)

        self.assertNotEqual(encrypted, message)
        self.assertEqual(decrypted, message)

if __name__ == '__main__':
    unittest.main()