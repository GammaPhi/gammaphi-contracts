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

DAO_CONTRACT = 'con_gamma_phi_dao_v1'
SPORTS_BETTING_CONTRACT = 'con_sports_betting_event_action_v4'
CURRENCY_CONTRACT = 'currency'
PHI_CONTRACT = 'con_phi_lst001'
SPORTS_BETTING_ACTION = 'sports_betting'
VALIDATOR_STAKE = 50_000_000
ME = 'my-address'
USER_1 = 'user-1'
USER_2 = 'user-2'
USER_3 = 'user-3'
USER_4 = 'user-4'
USER_5 = 'user-5'


t0 = time.time()
with open(join(dirname(module_dir), 'core', f'{PHI_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PHI_CONTRACT, signer=ME)

print(f'Time to submit PHI_CONTRACT: {time.time()-t0}')

t1 = time.time()
with open(join(dirname(module_dir), 'common', f'{CURRENCY_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CURRENCY_CONTRACT, signer=ME)

print(f'Time to submit CURRENCY_CONTRACT: {time.time()-t1}')

t1 = time.time()
with open(os.path.join(module_dir, f'{DAO_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=DAO_CONTRACT, signer=ME)

print(f'Time to submit DAO_CONTRACT: {time.time()-t1}')

t1 = time.time()
with open(os.path.join(dirname(module_dir), 'betting', f'{SPORTS_BETTING_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=SPORTS_BETTING_CONTRACT, owner=DAO_CONTRACT, signer=ME)

print(f'Time to submit SPORTS_BETTING_CONTRACT: {time.time()-t1}')

# Add actions to main contract
client.signer = ME
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


def get_betting_contract_for_signer(signer: str):
    return get_contract_for_signer(SPORTS_BETTING_CONTRACT, signer)


def to_datetime(d) -> Datetime:
    return Datetime(d.year, d.month, d.day, hour=d.hour, minute=d.minute)


def interact(signer, function, kwargs, now=datetime.today()):
    dao = get_dao_contract_for_signer(signer)
    return dao.interact(
        action=SPORTS_BETTING_ACTION,
        payload=dict(
            function=function,
            kwargs=kwargs
        ),
        environment={'now': to_datetime(now)}
    )


# Stake PHI
phi = get_phi_contract_for_signer(ME)
phi.approve(
    amount=VALIDATOR_STAKE,
    to=DAO_CONTRACT
)
tau = get_currency_contract_for_signer(ME)
dao = get_dao_contract_for_signer(ME)
dao.stake(amount=VALIDATOR_STAKE)
dao.force_change_setting(key='trusted_validators', value=[ME])
sports = get_betting_contract_for_signer(ME)

# Give users some tokens
for i in range(1, 6):
    user = globals()[f'USER_{i}']
    phi.transfer(
        amount=1_000_000,
        to=user
    )
    tau.transfer(
        amount=1_000_000,
        to=user
    )


class TestDao(unittest.TestCase):       
    def test_e2e(self):
        timestamp = int(time.time())
        date = str(datetime.today())
        event_id = sports.quick_read('total_num_events')
        # Create event
        interact(
            USER_1,
            function='add_event',
            kwargs={
                'sport': 'Tennis',
                'away_team': 'Venus',
                'home_team': 'Serena',
                'date': date,
                'timestamp': timestamp,
                'wager_name': 'moneyline',
                'num_wager_options': 2
            },
            now=datetime.today() - timedelta(days=3)
        )
        event_id_after = sports.quick_read('total_num_events')
        self.assertEqual(event_id_after - 1, event_id)
        #self.assertDictEqual(metadata, sports.quick_read('events', event_id, ['metadata']))
        self.assertEqual(USER_1, sports.quick_read('events', event_id, ['creator']))

        # Place bets
        get_currency_contract_for_signer(USER_1).approve(
            amount=1_000,
            to=SPORTS_BETTING_CONTRACT
        )
        num_bets_before = sports.quick_read('bets', USER_1, ['num_bets']) or 0
        balance_before = tau.quick_read('balances', SPORTS_BETTING_CONTRACT) or 0
        interact(
            USER_1,
            function='place_bet',
            kwargs={
                'event_id': event_id,
                'option_id': 1,
                'amount': 1_000
            },
            now=datetime.today() - timedelta(days=3)
        )
        num_bets = sports.quick_read('bets', USER_1, ['num_bets']) or 0

        self.assertEqual(num_bets - 1, num_bets_before)
        self.assertEqual(1_000, sports.quick_read('bets', event_id, [1, USER_1]))
        self.assertEqual(1_000, sports.quick_read('bets', event_id, [1]))
        self.assertEqual(1_000, sports.quick_read('bets', event_id, [USER_1]))
        self.assertEqual(1_000, sports.quick_read('bets', event_id))
        self.assertEqual(balance_before + 1_000, tau.quick_read('balances', SPORTS_BETTING_CONTRACT))

        get_currency_contract_for_signer(USER_2).approve(
            amount=2_000,
            to=SPORTS_BETTING_CONTRACT
        )
        interact(
            USER_2,
            function='place_bet',
            kwargs={
                'event_id': event_id,
                'option_id': 0,
                'amount': 2_000
            },
            now=datetime.today() - timedelta(days=3)
        )
        self.assertEqual(3_000, sports.quick_read('bets', event_id))
        self.assertEqual(2_000, sports.quick_read('bets', event_id, [0]))
        self.assertEqual(1_000, sports.quick_read('bets', event_id, [1]))
        self.assertEqual(1_000, sports.quick_read('bets', event_id, [USER_1]))
        self.assertEqual(2_000, sports.quick_read('bets', event_id, [USER_2]))
        self.assertEqual(balance_before + 3_000, tau.quick_read('balances', SPORTS_BETTING_CONTRACT))

        # Validate
        interact(
            ME,
            "validate_event",
            kwargs={
                'event_id': event_id,
                'winning_option_id': 1,
            },
            now=datetime.today() + timedelta(days=1)
        )
        self.assertEqual(ME, sports.quick_read('events', event_id, ['validator']))


        # Claim bets
        previous_dao_balance = tau.quick_read('balances', DAO_CONTRACT) or 0
        previous_validator_balance = tau.quick_read('balances', ME) or 0
        previous_user_1_balance = tau.quick_read('balances', USER_1) or 0
        interact(
            USER_1,
            "claim_bet",
            kwargs={
                'event_id': event_id,
                'option_id': 1,
            },
            now=datetime.today() + timedelta(days=3)
        )
        current_dao_phi_balance = tau.quick_read('balances', DAO_CONTRACT) or 0
        current_validator_balance = tau.quick_read('balances', ME) or 0
        current_user_1_balance = float(tau.quick_read('balances', USER_1) or 0)
        amount_in_pot = 3_000
        expected_reserve_fee = amount_in_pot * 0.004
        expected_validator_fee = amount_in_pot * 0.005
        expected_creator_fee = amount_in_pot * 0.001
        total_expected_fees = (expected_reserve_fee + expected_creator_fee + expected_validator_fee)
        self.assertEqual(previous_dao_balance + expected_reserve_fee, current_dao_phi_balance)
        self.assertEqual(previous_validator_balance + expected_validator_fee, current_validator_balance)
        self.assertEqual(previous_user_1_balance + amount_in_pot - total_expected_fees + expected_creator_fee, current_user_1_balance)

        self.assertEqual(tau.quick_read('balances', SPORTS_BETTING_CONTRACT) or 0, 0)
        tau.transfer(amount=1, to=SPORTS_BETTING_CONTRACT)
        self.assertEqual(tau.quick_read('balances', SPORTS_BETTING_CONTRACT) or 0, 1)
        self.assertRaises(
            AssertionError,
            interact,
            USER_1,
            "emergency_withdraw",
            kwargs={
                'amount': 1,
            },
            now=datetime.today()
        )
        interact(
            ME,
            "emergency_withdraw",
            kwargs={
                'amount': 1,
            },
            now=datetime.today()
        )
        self.assertEqual(tau.quick_read('balances', SPORTS_BETTING_CONTRACT) or 0, 0)

        
    def test_dispute(self):
        timestamp = int(time.time())
        date = str(datetime.today())
        event_id = sports.quick_read('total_num_events')
        metadata =  {
            'sport': 'Tennis',
            'away_team': 'Venus',
            'home_team': 'Serena',
            'date': date
        }

        # Create event
        interact(
            USER_1,
            function='add_event',
            kwargs={
                'timestamp': timestamp,
                'sport': 'Tennis',
                'away_team': 'Venus',
                'home_team': 'Serena',
                'date': date,
                'wager_name': 'moneyline',
                'num_wager_options': 3
            },
            now=datetime.today() - timedelta(days=3)
        )
        # Place bets
        get_currency_contract_for_signer(USER_1).approve(
            amount=1_000,
            to=SPORTS_BETTING_CONTRACT
        )
        interact(
            USER_1,
            function='place_bet',
            kwargs={
                'event_id': event_id,
                'option_id': 1,
                'amount': 1_000
            },
            now=datetime.today() - timedelta(days=3)
        )
        get_currency_contract_for_signer(USER_2).approve(
            amount=2_000,
            to=SPORTS_BETTING_CONTRACT
        )
        interact(
            USER_2,
            function='place_bet',
            kwargs={
                'event_id': event_id,
                'option_id': 0,
                'amount': 2_000
            },
            now=datetime.today() - timedelta(days=3)
        )

        # Validate
        interact(
            ME,
            "validate_event",
            kwargs={
                'event_id': event_id,
                'winning_option_id': 1,
            },
            now=datetime.today() + timedelta(days=1)
        )

        # Dispute
        self.assertRaises(
            AssertionError,
            interact,
            USER_1,
            "create_dispute",
            kwargs={
                'event_id': event_id,
                'current_option_id': 1,
                'expected_option_id': 0,
                'description': 'Should be option 0.'
            },
            now=datetime.today() + timedelta(days=3) # Too far in future
        )
        # Dispute
        proposal_id = interact(
            USER_1,
            "create_dispute",
            kwargs={
                'event_id': event_id,
                'current_option_id': 1,
                'expected_option_id': 0,
                'description': 'Should be option 0.'
            },
            now=datetime.today() + timedelta(days=1) # Within period
        )
        self.assertIsNotNone(proposal_id)

        # Claim bet should fail
        self.assertRaises( # Under dispute
            AssertionError,
            interact,
            USER_1,
            "claim_bet",
            kwargs={
                'event_id': event_id,
                'option_id': 1,
            },
            now=datetime.today() + timedelta(days=3)
        )
        
        # Handle dispute
        interact(
            ME,
            "vote_dispute",
            kwargs={
                'p_id': proposal_id,
                'result': True
            },
            now=datetime.today() + timedelta(days=1)
        )
        interact(
            USER_1,
            "vote_dispute",
            kwargs={
                'p_id': proposal_id,
                'result': True
            },
            now=datetime.today() + timedelta(days=1)
        )
        interact(
            USER_2,
            "vote_dispute",
            kwargs={
                'p_id': proposal_id,
                'result': True
            },
            now=datetime.today() + timedelta(days=1)
        )

        # Determine results
        self.assertRaises(
            AssertionError,
            interact,
            USER_1,
            "determine_dispute_results",
            kwargs={
                'p_id': proposal_id,
            },
            now=datetime.today() + timedelta(days=1) # Too soon
        )
        self.assertRaises(
            AssertionError,
            interact,
            USER_1,
            "determine_dispute_results",
            kwargs={
                'p_id': proposal_id,
            },
            now=datetime.today() + timedelta(days=1) # Too late
        )
        interact(
            USER_1,
            "determine_dispute_results",
            kwargs={
                'p_id': proposal_id,
            },
            now=datetime.today() + timedelta(days=2)
        )

        # Claim after dispute
        self.assertRaises(
            AssertionError,
            interact,
            USER_1, # User 1 no longer won
            "claim_bet",
            kwargs={
                'event_id': event_id,
                'option_id': 1,
            },
            now=datetime.today() + timedelta(days=2)
        )
        interact(
            USER_2,
            "claim_bet",
            kwargs={
                'event_id': event_id,
                'option_id': 0,
            },
            now=datetime.today() + timedelta(days=2)
        )
  
if __name__ == '__main__':
    unittest.main()