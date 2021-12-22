#tests/test_contract.py
import unittest
import os
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'tumbler')

PAIRING_CONTRACT = 'con_pairing_v1'
VERIFIER_CONTRACT = 'con_tumbler_verifier_v1'


with open(os.path.join(module_dir, f'{PAIRING_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PAIRING_CONTRACT, signer='me')


with open(os.path.join(module_dir, f'{VERIFIER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=VERIFIER_CONTRACT, signer='me')


def get_contract_for_signer(contract: str, signer: str):
    client.signer = signer
    contract = client.get_contract(contract)
    


class MyTestCase(unittest.TestCase):
    def test_tumbler(self):
        pass

if __name__ == '__main__':
    unittest.main()