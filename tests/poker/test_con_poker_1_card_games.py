#tests/test_contract.py
import unittest
import os
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join
import random
import time

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'poker')
external_deps_dir = os.path.dirname(module_dir)


with open(os.path.join(external_deps_dir, 'rsa', 'con_rsa_encryption.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_rsa_encryption')

with open(os.path.join(external_deps_dir, 'core', 'con_phi_lst001.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_phi_lst001', signer='me')

with open(os.path.join(external_deps_dir, 'core', 'con_gamma_phi_profile_v2.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_gamma_phi_profile_v2')

with open(os.path.join(module_dir, 'con_poker_1_card_games_v1.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_poker_1_card_games')


# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(1024)


def get_contract_for_signer(signer, contract):
    client.signer = signer        
    return client.get_contract(contract)


POKER_CONTRACT = 'con_poker_1_card_games'
PHI_CONTRACT = 'con_phi_lst001'
RSA_CONTRACT = 'con_rsa_encryption'
PROFILE_CONTRACT = 'con_gamma_phi_profile_v2'
ONE_CARD_POKER = 0
BLIND_POKER = 1

# Generate rsa pairs
my_vk, my_sk = generate_keys()
your_vk, your_sk = generate_keys()
p3_vk, p3_sk = generate_keys()


def setup():
    # Give you some PHI
    phi = get_contract_for_signer('me', PHI_CONTRACT)
    phi.transfer(
        to='you',
        amount=1_000_000
    )
    phi.transfer(
        to='p3',
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
    phi = get_contract_for_signer('p3', PHI_CONTRACT)
    phi.approve(
        to=POKER_CONTRACT,
        amount=1_000_000
    )
    phi = get_contract_for_signer('me', PHI_CONTRACT)

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
    profile = get_contract_for_signer('p3', PROFILE_CONTRACT)
    profile.create_profile(
        username='p3',
        display_name='p3',
        public_rsa_key=str(p3_vk.n)+"|"+str(p3_vk.e)
    )


setup()


class MyTestCase(unittest.TestCase):
    def test_simple_1_card_game(self):
        phi = get_contract_for_signer('me', PHI_CONTRACT)

        contract = get_contract_for_signer('me', POKER_CONTRACT)

        # Start a game
        game_id = contract.start_game(
            other_players=['you'],
            ante=1.0,
        )

        # Verify game state
        self.assertEqual(contract.quick_read('games', game_id, ['creator']), 'me')
        self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), ('me',))

        self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', 'you')))

        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.respond_to_invite(
            game_id=game_id,
            accept=True
        )

        self.assertEqual(0, len(contract.quick_read('players_invites', 'you')))
        self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), ('me', 'you'))

        contract = get_contract_for_signer('me', POKER_CONTRACT)
        # Add chips for each player
        contract.add_chips_to_game(
            game_id=game_id,
            amount=100000
        )

        contract.add_player_to_game(
            game_id=game_id,
            player_to_add='p3'
        )
        self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', 'p3')))
        contract = get_contract_for_signer('p3', POKER_CONTRACT)
        contract.respond_to_invite(
            game_id=game_id,
            accept=False
        )
        self.assertEqual(0, len(contract.quick_read('players_invites', 'p3')))
        self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', 'p3', ['declined'])))
        self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), ('me', 'you'))

        contract.respond_to_invite(
            game_id=game_id,
            accept=True
        )

        self.assertEqual(0, len(contract.quick_read('players_invites', 'p3')))
        self.assertEqual(0, len(contract.quick_read('players_invites', 'p3', ['declined'])))
        self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), ('me', 'you', 'p3'))

        contract = get_contract_for_signer('you', POKER_CONTRACT)
        contract.add_chips_to_game(
            game_id=game_id,
            amount=100000
        )

        contract = get_contract_for_signer('p3', POKER_CONTRACT)
        contract.add_chips_to_game(
            game_id=game_id,
            amount=100000
        )

        for game_type in [ONE_CARD_POKER, BLIND_POKER]:
            contract = get_contract_for_signer('me', POKER_CONTRACT)

            # Start a hand
            hand_id = contract.start_hand(
                game_id=game_id,
                game_type=game_type
            )
            print(f'Hand: {hand_id}')

            stored_hand_id = contract.quick_read('games', game_id, ['current_hand'])
            self.assertEqual(hand_id, stored_hand_id)

            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertTrue(len(active_players) == 0)

            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )
            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertIn('me', active_players)
            self.assertNotIn('you', active_players)

            contract = get_contract_for_signer('you', POKER_CONTRACT)
            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )

            active_players = contract.quick_read('hands', hand_id, ['active_players'])

            self.assertIn('me', active_players)
            self.assertIn('you', active_players)

            # Deal hand
            contract = get_contract_for_signer('me', POKER_CONTRACT)
            contract.deal_cards(
                hand_id=hand_id
            )

            # Decrypt hands
            my_hand = contract.quick_read('hands', hand_id, ['me', 'player_encrypted_hand'])
            my_hand = rsa.decrypt(bytes.fromhex(my_hand), my_sk).decode('utf-8')

            your_hand = contract.quick_read('hands', hand_id, ['you', 'player_encrypted_hand'])
            your_hand = rsa.decrypt(bytes.fromhex(your_hand), your_sk).decode('utf-8')

            # Verify hands
            if game_type == ONE_CARD_POKER:
                expected_num_cards = 1
            else:
                expected_num_cards = 1

            my_cards = my_hand.split(':')[0].split(',')
            self.assertEqual(len(my_cards), expected_num_cards)
            for card in my_cards:
                self.assertEqual(len(card), 2)

            your_cards = your_hand.split(':')[0].split(',')
            self.assertEqual(len(your_cards), expected_num_cards)
            for card in your_cards:
                self.assertEqual(len(card), 2)

            print(f'My hand: {my_hand}')
            print(f'Your hand: {your_hand}')

            self.assertNotEqual(tuple(my_cards), tuple(your_cards))

            # Check
            print('bet1')
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=0.0
            )

            # Bet
            print('bet2')
            contract = get_contract_for_signer('me', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=10.0
            )

            # Raise
            print('bet3')
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=15
            )

            # Call
            print('bet4')
            contract = get_contract_for_signer('me', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=5.0
            )
            
            # Check
            print('bet5')
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=0
            )

            # Verify hand publicly
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
            winners = contract.quick_read('hands', hand_id, ['winners'])

            my_chips = contract.quick_read('games', game_id, ['me'])
            your_chips = contract.quick_read('games', game_id, ['you'])

            if my_rank > your_rank:
                self.assertNotIn('me', winners)
                self.assertIn('you', winners)
            elif my_rank < your_rank:
                self.assertIn('me', winners)
                self.assertNotIn('you', winners)
            else:
                self.assertIn('me', winners)
                self.assertIn('you', winners)

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
                game_id=game_id,
                game_type=game_type
            )
            print(f'Hand: {hand_id}')

            contract = get_contract_for_signer('me', POKER_CONTRACT)
            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )            
            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertIn('me', active_players)
            self.assertNotIn('you', active_players)

            contract = get_contract_for_signer('you', POKER_CONTRACT)
            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )

            active_players = contract.quick_read('hands', hand_id, ['active_players'])

            self.assertIn('me', active_players)
            self.assertIn('you', active_players)

            # Deal hand
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.deal_cards(
                hand_id=hand_id
            )

            # Bet
            print('bet6')
            contract = get_contract_for_signer('me', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=10.0
            )

            # Raise
            print('bet7')
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=15
            )

            # Fold
            print('bet8')
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

            # Start another hand
            contract = get_contract_for_signer('p3', POKER_CONTRACT)

            hand_id = contract.start_hand(
                game_id=game_id,
                game_type=game_type
            )

            print(f'Hand: {hand_id}')

            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertEqual(len(active_players), 0)

            dealer = contract.quick_read('hands', hand_id, ['dealer'])
            
            self.assertEqual(dealer, 'p3')
            # Ante up
            contract = get_contract_for_signer('p3', POKER_CONTRACT)
            contract.ante_up(
                hand_id=hand_id
            )
            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertIn('p3', active_players)

            contract = get_contract_for_signer('me', POKER_CONTRACT)
            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )           
            active_players = contract.quick_read('hands', hand_id, ['active_players'])
            self.assertIn('me', active_players)
            self.assertNotIn('you', active_players)

            contract = get_contract_for_signer('you', POKER_CONTRACT)
            # Ante up
            contract.ante_up(
                hand_id=hand_id
            )

            active_players = contract.quick_read('hands', hand_id, ['active_players'])

            self.assertIn('me', active_players)
            self.assertIn('you', active_players)
            self.assertIn('p3', active_players)

            # Deal hand
            contract = get_contract_for_signer('p3', POKER_CONTRACT)
            contract.deal_cards(
                hand_id=hand_id
            )

            # Bet
            print('bet6')
            contract = get_contract_for_signer('me', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=10.0
            )

            # Raise
            print('bet7')
            contract = get_contract_for_signer('you', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=15
            )

            # Fold
            print('bet8')
            contract = get_contract_for_signer('p3', POKER_CONTRACT)
            contract.bet_check_or_fold(
                hand_id=hand_id,
                bet=-1
            )

            # Payout hand
            contract.payout_hand(
                hand_id=hand_id
            )


if __name__ == '__main__':
    unittest.main()