#tests/test_contract.py
import unittest
import os
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'poker')
external_deps_dir = os.path.dirname(module_dir)


with open(os.path.join(external_deps_dir, 'cards', 'con_5_card_hand_evaluator.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_5_card_hand_evaluator')

with open(os.path.join(external_deps_dir, 'rsa', 'con_rsa_encryption.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_rsa_encryption')

with open(os.path.join(external_deps_dir, 'con_phi_lst001.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_phi_lst001', signer='me')

with open(os.path.join(external_deps_dir, 'con_gamma_phi_profile_v1.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_gamma_phi_profile_v1')

with open(os.path.join(module_dir, 'con_poker_5_card_stud_v1.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_poker_5_card_stud')


# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(1024)


def get_contract_for_signer(signer, contract):
    client.signer = signer        
    return client.get_contract(contract)


POKER_CONTRACT = 'con_poker_5_card_stud'
PHI_CONTRACT = 'con_phi_lst001'
RSA_CONTRACT = 'con_rsa_encryption'
PROFILE_CONTRACT = 'con_gamma_phi_profile_v1'


class MyTestCase(unittest.TestCase):
    def test_simple_card_game(self):
        contract = get_contract_for_signer(
            'me',
            POKER_CONTRACT
        )

        # Give you some PHI
        phi = get_contract_for_signer('me', PHI_CONTRACT)
        phi.transfer(
            to='you',
            amount=1_000_000
        )

        # Approve PHI
        phi.approve(
            to=POKER_CONTRACT,
            amount=1_000_000
        )
        phi = get_contract_for_signer('you', PHI_CONTRACT)
        phi.approve(
            to=POKER_CONTRACT,
            amount=1_000_000
        )
        phi = get_contract_for_signer('me', PHI_CONTRACT)

        # Generate rsa pairs
        my_vk, my_sk = generate_keys()
        your_vk, your_sk = generate_keys()

        # Create gamma phi profiles
        profile = get_contract_for_signer('me', PROFILE_CONTRACT)
        profile.create_profile(
            username='me',
            display_name='me',
            public_rsa_key=str(my_vk.n)+"|"+str(my_vk.e)
        )
        profile = get_contract_for_signer('you', PROFILE_CONTRACT)
        profile.create_profile(
            username='you',
            display_name='you',
            public_rsa_key=str(your_vk.n)+"|"+str(your_vk.e)
        )

        contract = get_contract_for_signer('me', POKER_CONTRACT)

        # Start a game
        game_id = contract.start_game(
            other_players=['you'],
            ante=1.0,
        )

        # Verify game state
        self.assertEqual(contract.quick_read('games', game_id, ['creator']), 'me')
        self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), ('me', 'you'))

        # Add chips for each player
        contract.add_chips_to_game(
            game_id=game_id,
            amount=100000
        )

        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.add_chips_to_game(
            game_id=game_id,
            amount=100000
        )

        contract = get_contract_for_signer('me', POKER_CONTRACT)

        # Start a hand
        hand_id = contract.start_hand(
            game_id=game_id
        )

        stored_hand_id = contract.quick_read('games', game_id, ['current_hand'])
        self.assertEqual(hand_id, stored_hand_id)

        # Decrypt hands
        my_hand = contract.quick_read('hands', hand_id, ['me', 'player_encrypted_hand'])
        my_hand = rsa.decrypt(bytes.fromhex(my_hand), my_sk).decode('utf-8')

        your_hand = contract.quick_read('hands', hand_id, ['you', 'player_encrypted_hand'])
        your_hand = rsa.decrypt(bytes.fromhex(your_hand), your_sk).decode('utf-8')

        # Verify hands
        my_cards = my_hand.split(':')[0].split(',')
        self.assertEqual(len(my_cards), 5)
        for card in my_cards:
            self.assertEqual(len(card), 2)

        your_cards = your_hand.split(':')[0].split(',')
        self.assertEqual(len(your_cards), 5)
        for card in your_cards:
            self.assertEqual(len(card), 2)

        print(my_hand)
        print(your_hand)

        # Check
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=0.0
        )

        # Bet
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=10.0
        )

        # Raise
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=15
        )

        # Call
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=5.0
        )
        
        # Check
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=0
        )

        # Verify hand publically
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.verify_hand(
            hand_id=hand_id,
            player_hand_str=your_hand
        )
        # Verify from a hidden hand
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.verify_hand(
            hand_id=hand_id,
            player_hand_str=my_hand
        )

        # Payout hand
        contract.payout_hand(
            hand_id=hand_id
        )

        # Check some state
        my_rank = contract.quick_read('hands', hand_id, ['me', 'rank'])
        your_rank = contract.quick_read('hands', hand_id, ['you', 'rank'])

        my_chips = contract.quick_read('games', game_id, ['me'])
        your_chips = contract.quick_read('games', game_id, ['you'])

        if my_rank > your_rank:
            self.assertLess(my_chips, your_chips)
        elif my_rank < your_rank:
            self.assertGreater(my_chips, your_chips)
        else:
            self.assertEqual(my_chips, your_chips)

        # Withdraw chips
        current_phi_balance = phi.quick_read('balances', 'me')
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.withdraw_chips_from_game(
            game_id=game_id,
            amount=20
        )
        new_phi_balance = phi.quick_read('balances', 'me')
        my_new_chips = contract.quick_read('games', game_id, ['me'])

        self.assertEqual(current_phi_balance + 20, new_phi_balance)
        self.assertEqual(my_new_chips + 20, my_chips)
            

        your_chips = contract.quick_read('games', game_id, ['you'])

        # Start another hand
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        hand_id = contract.start_hand(
            game_id=game_id
        )

        # Bet
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=10.0
        )

        # Raise
        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=15
        )

        # Fold
        contract = get_contract_for_signer('me', POKER_CONTRACT)
        contract.bet_check_or_fold(
            hand_id=hand_id,
            bet=-1
        )

        # Payout hand
        contract.payout_hand(
            hand_id=hand_id
        )

        your_chips_after = contract.quick_read('games', game_id, ['you'])
        self.assertEqual(your_chips + 11, your_chips_after)


if __name__ == '__main__':
    unittest.main()