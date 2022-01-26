#tests/test_contract.py
import unittest
import os
import uuid
from contracting.client import ContractingClient
from os.path import dirname, abspath, join
import time

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'scheduler')

SCHEDULER_CONTRACT = 'con_scheduler'
CURRENCY_CONTRACT = 'currency'
SCHEDULED_ACTION_CONTRACT = 'con_scheduled_action'

with open(join(dirname(module_dir), 'common', f'{CURRENCY_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CURRENCY_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{SCHEDULER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=SCHEDULER_CONTRACT, signer='me')

with open(os.path.join(module_dir, f'{SCHEDULED_ACTION_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=SCHEDULED_ACTION_CONTRACT, owner=SCHEDULER_CONTRACT, signer='me')


class MyTestCase(unittest.TestCase):
    def setUp(self):
        client.signer = "you"
        self.contract = client.get_contract(SCHEDULER_CONTRACT)


    def test_channels(self):
        client.signer = 'me'
        tau = client.get_contract(CURRENCY_CONTRACT)
        tau.approve(
            to=SCHEDULER_CONTRACT,
            amount=100
        )
        contract = client.get_contract(SCHEDULER_CONTRACT)
        contract.schedule_action(
            command={
                'contract': SCHEDULED_ACTION_CONTRACT,
                'payload': {

                }
            }, 
            deposit=100,
            run_at=int(time.time())
        )

        pass

if __name__ == '__main__':
    unittest.main()