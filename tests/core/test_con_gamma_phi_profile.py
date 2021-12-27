#tests/test_contract.py
import unittest
import os
import uuid
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'profile')

PROFILE_CONTRACT = 'con_gamma_phi_profile_v4'
PROFILE_IMPL_CONTRACT = 'con_gamma_phi_profile_impl_v1'
CHANNEL_IMPL_CONTRACT = 'con_gamma_phi_channel_impl_v1'
RSA_CONTRACT = 'con_rsa_encryption'

with open(os.path.join(module_dir, f'{PROFILE_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PROFILE_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{PROFILE_IMPL_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PROFILE_IMPL_CONTRACT, owner=PROFILE_CONTRACT, signer='me')

with open(os.path.join(dirname(module_dir), 'rsa', f'{RSA_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=RSA_CONTRACT)

with open(os.path.join(module_dir, f'{CHANNEL_IMPL_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CHANNEL_IMPL_CONTRACT, owner=PROFILE_CONTRACT, signer='me')


client.signer = 'me'
contract = client.get_contract(PROFILE_CONTRACT)
contract.register_action(action='profile', contract=PROFILE_IMPL_CONTRACT)
contract.register_action(action='channel', contract=CHANNEL_IMPL_CONTRACT)

# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(1024)


class MyTestCase(unittest.TestCase):
    def setUp(self):
        client.signer = "you"
        self.contract = client.get_contract(PROFILE_CONTRACT)

    def test_channels(self):
        keystore = {}
        users = [str(uuid.uuid4())[:10] for i in range(10)]
        for user in users:
            vk, sk = generate_keys()
            keystore[user] = sk
            client.signer = user
            contract = client.get_contract(PROFILE_CONTRACT)
            contract.interact(
                action='profile',
                payload=dict(
                    action="create_profile",
                    username=user,
                    public_rsa_key=f'{vk.n}|{vk.e}'
                )
            )
        # create a channel
        user = users[0]
        client.signer = user
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='channel',
            payload=dict(
                action='create_channel',
                users=users[1:4],
                channel_name='mychannel'
            )
        )
        self.assertEqual(user, contract.quick_read('channels', 'mychannel', ['owner']))

        expected_key = None
        for i in range(4):
            # Make sure they get the encrypted keys
            user = users[i]
            key = contract.quick_read('metadata', user, ['keys', 'mychannel'])
            print(f'Key for user {i}: {key}')
            self.assertIsNotNone(key)
            decrypted_key = rsa.decrypt(bytes.fromhex(key), keystore[user]).decode('utf-8')
            print(f'Decrypted key: {decrypted_key}')
            if i == 0:
                expected_key = decrypted_key
            else:
                self.assertEqual(decrypted_key, expected_key)
        for i in range(4, 10):
            # Make sure they don't get the encrypted keys
            user = users[i]
            key = contract.quick_read('metadata', user, ['keys', 'mychannel'])
            print(f'Key for user {i}: {key}')
            self.assertIsNone(key)
        
        # update a channel
        user = users[0]
        client.signer = user
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='channel',
            payload=dict(
                action='update_channel',
                users=users[2:5],
                channel_name='mychannel'
            )
        )
        expected_key2 = None
        for i in range(10):
            # Make sure they get the encrypted keys
            user = users[i]
            key = contract.quick_read('metadata', user, ['keys', 'mychannel'])
            print(f'Key for user {i}: {key}')
            if i in list(range(5, 10)):
                self.assertIsNone(key)
            else:
                self.assertIsNotNone(key)
                decrypted_key = rsa.decrypt(bytes.fromhex(key), keystore[user]).decode('utf-8')
                print(f'Decrypted key: {decrypted_key}')
                if i == 0:
                    expected_key2 = decrypted_key
                    self.assertNotEqual(expected_key, expected_key2)
                elif i == 1:
                    self.assertEqual(decrypted_key, expected_key)
                    self.assertNotEqual(decrypted_key, expected_key2)
                else:
                    self.assertEqual(expected_key2, decrypted_key)

    def test_create_simple_profile(self):
        n = self.contract.quick_read('total_users')
        self.contract.interact(
            action='profile',
            payload=dict(
                action="create_profile",
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
        )

        self.assertEqual('hello123', self.contract.quick_read('metadata', 'you', ['username']))
        self.assertEqual('hello123', self.contract.quick_read('metadata', 'you', ['display_name']))
        self.assertEqual('you', self.contract.quick_read('usernames', 'hello123'))
        self.assertEqual(n+1, self.contract.quick_read('total_users'))

    def test_change_username(self):
        client.signer = "a1"
        contract = client.get_contract(PROFILE_CONTRACT)

        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='u1',
            )
        )

        self.assertEqual('u1', contract.quick_read('metadata', 'a1', ['username']))
        self.assertEqual('u1', contract.quick_read('metadata', 'a1', ['display_name']))
        self.assertEqual('a1', contract.quick_read('usernames', 'u1'))

        contract.interact(
            action='profile',
            payload=dict(
                action='update_profile',
                key='username',
                value='u2',
            )
        )

        self.assertEqual('u2', contract.quick_read('metadata', 'a1', ['username']))
        self.assertEqual('u1', contract.quick_read('metadata', 'a1', ['display_name']))
        self.assertEqual('a1', contract.quick_read('usernames', 'u2'))

    def test_force_change_username(self):
        client.signer = "c1"
        contract = client.get_contract(PROFILE_CONTRACT)

        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='uc1',
            )
        )

        self.assertEqual('uc1', contract.quick_read('metadata', 'c1', ['username']))
        self.assertEqual('uc1', contract.quick_read('metadata', 'c1', ['display_name']))
        self.assertEqual('c1', contract.quick_read('usernames', 'uc1'))

        self.assertRaises(AssertionError,
            contract.interact,
            action='profile',
            payload=dict(
                action='force_update_profile',
                user_address='c1',
                key='username',
                value='uc2',
            )
        )

        client.signer = "me"
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='profile',
            payload=dict(
                action='force_update_profile',
                user_address='c1',
                key='username',
                value='uc2',
            )
        )

        self.assertEqual('uc2', contract.quick_read('metadata', 'c1', ['username']))
        self.assertEqual('uc1', contract.quick_read('metadata', 'c1', ['display_name']))
        self.assertEqual('c1', contract.quick_read('usernames', 'uc2'))

    def test_force_update_metadata(self):
        client.signer = "c1"
        contract = client.get_contract(PROFILE_CONTRACT)

        self.assertRaises(AssertionError,
            contract.interact,
            action='profile',
            payload=dict(
                action='force_update_metadata',
                user_address='c1',
                key='hello',
                value='world',
            )
        )

        self.assertIsNone(contract.quick_read('metadata', 'c1', ['hello']))

        client.signer = "me"
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='profile',
            payload=dict(
                action='force_update_metadata',
                user_address='c1',
                key='hello',
                value='world',
            )
        )

        self.assertEqual('world', contract.quick_read('metadata', 'c1', ['hello']))

    def test_force_update_usernames(self):
        client.signer = "c1"
        contract = client.get_contract(PROFILE_CONTRACT)

        self.assertRaises(AssertionError,
            contract.interact,
            action='profile',
            payload=dict(
                action='force_update_usernames',
                key='hello1',
                value='world',
            )
        )

        self.assertIsNone(contract.quick_read('usernames', 'hello1'))

        client.signer = "me"
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='profile',
            payload=dict(
                action='force_update_usernames',
                key='hello1',
                value='world',
            )
        )

        self.assertEqual('world', contract.quick_read('usernames', 'hello1'))

    def test_delete_username(self):
        client.signer = "b3"
        contract = client.get_contract(PROFILE_CONTRACT)

        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='u5',
            )
        )

        self.assertEqual('u5', contract.quick_read('metadata', 'b3', ['username']))
        self.assertEqual('u5', contract.quick_read('metadata', 'b3', ['display_name']))
        self.assertEqual('b3', contract.quick_read('usernames', 'u5'))

        contract.interact(
            action='profile',
            payload=dict(
                action='delete_profile'
            )
        )

        self.assertIsNone(contract.quick_read('metadata', 'b3', ['username']))
        self.assertIsNone(contract.quick_read('metadata', 'b3', ['display_name']))
        self.assertIsNone(contract.quick_read('usernames', 'u5'))

    def test_force_delete_username(self):
        client.signer = "b3"
        contract = client.get_contract(PROFILE_CONTRACT)

        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='u5',
            )
        )

        self.assertEqual('u5', contract.quick_read('metadata', 'b3', ['username']))
        self.assertEqual('u5', contract.quick_read('metadata', 'b3', ['display_name']))
        self.assertEqual('b3', contract.quick_read('usernames', 'u5'))

        # Only owner can call force
        self.assertRaises(AssertionError,
            contract.interact,
            action='profile',
            payload=dict(
                action='force_delete_profile',
                user_address='b3',
            )
        )

        client.signer = "me"
        contract = client.get_contract(PROFILE_CONTRACT)

        contract.interact(
            action='profile',
            payload=dict(
                action='force_delete_profile',
                user_address='b3',
            )
        )

        self.assertIsNone(contract.quick_read('metadata', 'b3', ['username']))
        self.assertIsNone(contract.quick_read('metadata', 'b3', ['display_name']))
        self.assertIsNone(contract.quick_read('usernames', 'u5'))

    def test_frens(self):
        client.signer = "someone"
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='hello',
            )
        )

        client.signer = "me"
        contract = client.get_contract(PROFILE_CONTRACT)
        contract.interact(
            action='profile',
            payload=dict(
                action='create_profile',
                username='hello2',
            )
        )

        self.assertEqual(0, len(contract.quick_read('metadata', 'me', ['frens'])))
        contract.interact(
            action='profile',
            payload=dict(
                action='add_frens',
                frens=['someone']
            )
        )
        self.assertEqual(1, len(contract.quick_read('metadata', 'me', ['frens'])))
        self.assertEqual('someone', contract.quick_read('metadata', 'me', ['frens'])[0])

        contract.interact(
            action='profile',
            payload=dict(
                action='remove_frens',
                frens=['someone']
            )
        )
        self.assertEqual(0, len(contract.quick_read('metadata', 'me', ['frens'])))
        contract.interact(
            action='profile',
            payload=dict(
                action='add_frens',
                frens=['hello']
            )
        )
        self.assertEqual(1, len(contract.quick_read('metadata', 'me', ['frens'])))
        self.assertEqual('someone', contract.quick_read('metadata', 'me', ['frens'])[0])

    def test_create_profile_with_invalid_rsa_key(self):
        pass

    def test_create_profile_with_invalid_username(self):
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username='_something'
            )
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username='-something'
            )    
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username='some.thing'
            )  
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username='some thing'
            )  
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username=''
            )  
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username=None
            )  
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username=15
            )  
        )
        self.assertRaises(
            Exception, 
            self.contract.interact,
            action='profile',
            payload=dict(
                action='create_profile',
                username='somethingveryverylonglkasjdlkgjasdlgkjasdklgjaskdlgjasdklgjad'
            )  
        )

if __name__ == '__main__':
    unittest.main()