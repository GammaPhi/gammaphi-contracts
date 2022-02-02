#tests/test_contract.py
import unittest
import os
from datetime import datetime, timedelta
from contracting.client import ContractingClient
from os.path import dirname, abspath, join
import time
from contracting.stdlib.bridge.time import Datetime

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'dao')

DAO_CONTRACT = 'con_gamma_phi_dao'
SPORTS_BETTING_CONTRACT = 'con_sports_betting_event_action_v1'
CURRENCY_CONTRACT = 'currency'
PHI_CONTRACT = 'con_phi_lst001'
SPORTS_BETTING_ACTION = 'sports_betting'


t0 = time.time()
with open(join(dirname(module_dir), 'core', f'{PHI_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PHI_CONTRACT, signer='me')

print(f'Time to submit PHI_CONTRACT: {time.time()-t0}')

t1 = time.time()
with open(join(dirname(module_dir), 'common', f'{CURRENCY_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CURRENCY_CONTRACT, signer='me')

print(f'Time to submit CURRENCY_CONTRACT: {time.time()-t1}')

t1 = time.time()
with open(os.path.join(module_dir, f'{DAO_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=DAO_CONTRACT, signer='me')

print(f'Time to submit DAO_CONTRACT: {time.time()-t1}')

t1 = time.time()
with open(os.path.join(dirname(module_dir), 'betting', f'{SPORTS_BETTING_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=SPORTS_BETTING_CONTRACT, owner=DAO_CONTRACT, signer='me')

print(f'Time to submit SPORTS_BETTING_CONTRACT: {time.time()-t1}')

# Add actions to main contract
client.signer = 'me'
contract = client.get_contract(DAO_CONTRACT)
contract.force_register_action(action=SPORTS_BETTING_ACTION, contract=SPORTS_BETTING_CONTRACT)


def get_contract_for_signer(contract: str, signer: str):
    client.signer = signer
    contract = client.get_contract(contract)
    return contract


def get_dao_contract_for_signer(signer: str):
    return get_contract_for_signer(DAO_CONTRACT, signer)


def get_phi_contract_for_signer(signer: str):
    return get_contract_for_signer(PHI_CONTRACT, signer)


def get_currency_contract_for_signer(signer: str):
    return get_contract_for_signer(CURRENCY_CONTRACT, signer)


def to_datetime(d) -> Datetime:
    return Datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute)



class TestDao(unittest.TestCase):       
    def test_e2e(self):
        dao = get_dao_contract_for_signer('me')
        phi = get_phi_contract_for_signer('me')

        now = datetime.today()
        
  
if __name__ == '__main__':
    unittest.main()