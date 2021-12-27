#tests/test_contract.py
import unittest
import os
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'tumbler')

PAIRING_CONTRACT = 'con_pairing_v1'
VERIFIER_CONTRACT = 'con_tumbler_verifier_v1'
MERKE_TREE_CONTRACT = 'con_merkle_tree_v1'
PHI_CONTRACT = 'con_phi_lst001'

with open(join(dirname(module_dir), 'core', f'{PHI_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PHI_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{PAIRING_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PAIRING_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{VERIFIER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=VERIFIER_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{MERKE_TREE_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=MERKE_TREE_CONTRACT, signer='me')

def get_contract_for_signer(contract: str, signer: str):
    client.signer = signer
    contract = client.get_contract(contract)
    return contract


def print_merkle_tree_state(contract):
    roots = contract.quick_read('roots_var')
    zeros = contract.quick_read('zeros_var')
    filled_subtrees = contract.quick_read('filled_subtrees_var')
    levels = contract.quick_read('levels')
    next_index = contract.quick_read('next_index')
    current_root_index = contract.quick_read('current_root_index')
    
    print(f'roots: {roots}')
    print(f'zeros: {zeros}')
    print(f'filled_subtrees: {filled_subtrees}')
    print(f'levels: {levels}')
    print(f'next_index: {next_index}')
    print(f'current_root_index: {current_root_index}')


class MyTestCase(unittest.TestCase):
    def test_merkle_tree(self):
        contract = get_contract_for_signer(MERKE_TREE_CONTRACT, 'me')

        print_merkle_tree_state(contract)
        denomination = contract.quick_read('denomination')
        phi = get_contract_for_signer(PHI_CONTRACT, 'me')

        for i in range(10):
            phi.approve(
                amount=denomination,
                to=MERKE_TREE_CONTRACT
            )
            contract.deposit(commitment=str(i), encrypted_note="something")

        print_merkle_tree_state(contract)

        root = '1628e3f493811c350db14359de7eae19077b37d13f52577a3766b2ade9545c0a'
        root_int = int(root, 16)
        print(int(root, 16))
        contract.withdraw(
            proof={
                'A': (132235235253, 12235235235),
                'B': ([132235235253, 12235235235], [132235235253, 12235235235]),
                'C': ([132235235253, 12235235235], [132235235253, 12235235235]),
            },
            root=root,
            nullifier_hash=10352523523,
            recipient=13593858203523,
            relayer=2352352352352,
            fee=1,
            refund=0
        )



    def test_tumbler(self):
        pass

if __name__ == '__main__':
    unittest.main()