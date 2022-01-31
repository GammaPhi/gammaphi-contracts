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
CURRENCY_CONTRACT = 'currency'
PHI_CONTRACT = 'con_phi_lst001'


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
    def test_staking(self):
        dao = get_dao_contract_for_signer('me')
        phi = get_phi_contract_for_signer('me')

        now = datetime.today()
        
        self.assertEqual(0, dao.quick_read('stakes', 'me') or 0)

        balance_before = phi.quick_read('balances', 'me')

        # Stake
        phi.approve(amount=1000, to=DAO_CONTRACT)
        dao.stake(amount=1000, environment={'now': to_datetime(now)})

        self.assertEqual(1000, dao.quick_read('stakes', 'me'))
        self.assertEqual(balance_before - 1000, phi.quick_read('balances', 'me'))

        # Unstake before time limit
        self.assertRaises(
            AssertionError,
            dao.stake,
            amount=0,
            environment={'now': to_datetime(now)}
        )
        self.assertEqual(1000, dao.quick_read('stakes', 'me'))
        self.assertEqual(balance_before - 1000, phi.quick_read('balances', 'me'))

        # Unstake after time limit
        dao.stake(amount=0, environment={'now': to_datetime(now + timedelta(weeks=4))})

        self.assertEqual(0, dao.quick_read('stakes', 'me'))
        self.assertEqual(balance_before, phi.quick_read('balances', 'me'))

    def __proposal_helper(self, voter_data, proposal_func, kwargs):
        now = datetime.today()

        voters = list(sorted(voter_data.keys()))
        for p in voters:
            amount = voter_data[p]['stake']
            phi = get_phi_contract_for_signer('me')
            phi.transfer(amount=amount, to=p)

            # Stake
            dao = get_dao_contract_for_signer(p)
            phi = get_phi_contract_for_signer(p)
            phi.approve(amount=amount, to=DAO_CONTRACT)
            dao.stake(amount=amount, environment={'now': to_datetime(now)})

        dao = get_dao_contract_for_signer('someone')

        p_id = dao.quick_read('proposal_id')

        dao_func = getattr(dao, proposal_func)
        kwargs['environment'] = {'now': to_datetime(now)}
        dao_func(**kwargs)

        # Vote
        for p in voters:
            dao = get_dao_contract_for_signer(p)
            self.assertFalse(dao.quick_read('sig', p_id, [p]))
            dao.vote(p_id=p_id, result=voter_data[p]['vote'], environment={'now': to_datetime(now)})
            self.assertEqual(dao.quick_read('sig', p_id, [p]), voter_data[p]['vote'])

        self.assertEqual(tuple(voters), tuple(dao.quick_read('proposal_details', p_id, ['voters'])))
        dao = get_dao_contract_for_signer('me')
        result = dao.determine_results(p_id=p_id, environment={'now': to_datetime(now + timedelta(days=8))})

        return result, p_id

    def test_change_setting_proposal(self):
        proposal_func = 'create_change_setting_proposal'
        voter_data = {
            'p1': {
                'stake': 10000,
                'vote': True
            },
            'p2': {
                'stake': 10000,
                'vote': False
            },
            'p3': {
                'stake': 10000,
                'vote': True
            }
        }
        kwargs = dict(
            setting='hello',
            value='world',
            voting_time_in_days=7,
            description='changing a setting',
            to_float=False, 
        )

        result, p_id = self.__proposal_helper(voter_data, proposal_func, kwargs)

        dao = get_dao_contract_for_signer('me')

        self.assertEqual(dao.quick_read('proposal_id'), p_id + 1)
        self.assertEqual('change_setting', dao.quick_read('proposal_details', p_id, ['type']))
        self.assertEqual('changing a setting', dao.quick_read('proposal_details', p_id, ['description']))
        self.assertEqual('hello', dao.quick_read('proposal_details', p_id, ['setting']))
        self.assertEqual('world', dao.quick_read('proposal_details', p_id, ['value']))
        self.assertTrue(result)
        self.assertEqual('world', dao.quick_read('settings', 'hello'))

        # Test other voting cases
        voter_data = {
            'p1': {
                'stake': 10000,
                'vote': True
            },
            'p2': {
                'stake': 10000,
                'vote': False
            },
            'p3': {
                'stake': 10000,
                'vote': False
            }
        }
        kwargs = dict(
            setting='hello',
            value='world2',
            voting_time_in_days=7,
            description='changing a setting',
            to_float=False, 
        )
        result, p_id = self.__proposal_helper(voter_data, proposal_func, kwargs)
        self.assertFalse(result)
        self.assertEqual('world', dao.quick_read('settings', 'hello'))

        # Check quorum
        voter_data = {
            'p1': {
                'stake': 10000,
                'vote': True
            },
            'p2': {
                'stake': 10000,
                'vote': True
            },
            'p3': {
                'stake': 10000,
                'vote': True
            }
        }
        kwargs = dict(
            setting='hello',
            value='world3',
            voting_time_in_days=7,
            description='changing a setting',
            to_float=False, 
        )

        quorum = dao.quick_read('settings', 'min_quorum')
        total_votes = sum([voter_data[x]['stake'] for x in voter_data.keys()])
        total_staked = dao.quick_read('total_staked')

        self.assertEqual(total_votes, total_staked)

        amount_to_stake = (total_votes / quorum) - total_votes + 2
        print('amount to stake: {}'.format(amount_to_stake))

        phi = get_phi_contract_for_signer('me')
        phi.transfer(amount=amount_to_stake, to='you')
        dao = get_dao_contract_for_signer('you')
        phi = get_phi_contract_for_signer('you')
        phi.approve(amount=amount_to_stake, to=DAO_CONTRACT)
        dao.stake(amount=amount_to_stake - 2, environment={'now': to_datetime(datetime.today())})
        
        result, p_id = self.__proposal_helper(voter_data, proposal_func, kwargs)
        self.assertTrue(result)

        dao.stake(amount=amount_to_stake, environment={'now': to_datetime(datetime.today())})
        
        result, p_id = self.__proposal_helper(voter_data, proposal_func, kwargs)
        self.assertFalse(result)


if __name__ == '__main__':
    unittest.main()