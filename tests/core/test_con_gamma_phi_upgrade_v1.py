#tests/test_contract.py
import unittest
import os
from os.path import dirname, abspath, join

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = dirname(dirname(abspath(__file__)))

with open(join(module_dir, 'con_phi_lst001.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_phi_lst001', signer='me')

with open(join(module_dir, 'con_phi_lst001.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_phi', signer='me')

with open(join(module_dir, 'con_gamma_phi_upgrade_v1.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_gamma_phi_upgrade_v1', signer='me')


class MyTestCase(unittest.TestCase):
    def test_user_can_withdraw(self):
        client.signer = 'me'        
        phi_old = client.get_contract('con_phi')
        phi_new = client.get_contract('con_phi_lst001')

        phi_new.transfer(
            amount=200000,
            to='con_gamma_phi_upgrade_v1'
        )
        phi_old.transfer(
            amount=100000,
            to='you'
        )

        self.assertEqual(phi_old.quick_read('balances', 'you'), 100000)
        self.assertEqual(phi_new.quick_read('balances', 'con_gamma_phi_upgrade_v1'), 200000)

        client.signer = 'you'
        contract = client.get_contract('con_gamma_phi_upgrade_v1')
        phi_old = client.get_contract('con_phi')

        phi_old.approve(
            amount=100000,
            to='con_gamma_phi_upgrade_v1'
        )

        contract.redeem_phi()

        self.assertEqual(phi_old.quick_read('balances', 'you'), 0)
        self.assertEqual(phi_new.quick_read('balances', 'you'), 100000)
        self.assertEqual(phi_new.quick_read('balances', 'con_gamma_phi_upgrade_v1'), 100000)

        self.assertRaises(Exception,
            contract.withdraw_phi_new,
            amount=1000
        )

        client.signer = 'me'

        balance_before = phi_new.quick_read('balances', 'me')
        contract = client.get_contract('con_gamma_phi_upgrade_v1')
        contract.withdraw_phi_new(amount=100000)

        self.assertEqual(phi_new.quick_read('balances', 'con_gamma_phi_upgrade_v1'), 0)
        balance_after = phi_new.quick_read('balances', 'me')
        self.assertEqual(balance_before + 100000, balance_after)


if __name__ == '__main__':
    unittest.main()