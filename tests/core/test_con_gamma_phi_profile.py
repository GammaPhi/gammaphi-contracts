#tests/test_contract.py
import unittest
import os
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'core')


with open(os.path.join(module_dir, 'con_gamma_phi_profile_v1.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_gamma_phi_profile', signer='me')


# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(1024)


class MyTestCase(unittest.TestCase):
    def setUp(self):
        client.signer = "you"
        self.contract = client.get_contract('con_gamma_phi_profile')

    def test_create_simple_profile(self):
        self.assertEqual(0, self.contract.quick_read('total_users'))
        self.contract.create_profile(
            username='hello123',
            #display_name=None,
            #telegram=None,
            #twitter=None,
            #instagram=None,
            #facebook=None,
            #discord=None,
            #icon_base64_svg=None,
            #icon_base64_png=None,
            #icon_url=None,
            #public_rsa_key=None
        )

        self.assertEqual('hello123', self.contract.quick_read('metadata', 'you', ['username']))
        self.assertEqual('hello123', self.contract.quick_read('metadata', 'you', ['display_name']))
        self.assertEqual('you', self.contract.quick_read('usernames', 'hello123'))
        self.assertEqual(1, self.contract.quick_read('total_users'))

    def test_create_profile_with_invalid_rsa_key(self):
        pass

    def test_create_profile_with_invalid_username(self):
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username='_something'
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username='-something'
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username='some.thing'
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username='some thing'
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username=''
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username=None
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username=15
        )
        self.assertRaises(
            Exception, 
            self.contract.create_profile,
            username='somethingveryverylonglkasjdlkgjasdlgkjasdklgjaskdlgjasdklgjad'
        )

if __name__ == '__main__':
    unittest.main()