#tests/test_contract.py
import unittest
import os
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join
import uuid


client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'poker')
external_deps_dir = os.path.dirname(module_dir)

POKER_CONTRACT = 'con_poker_card_games_v3'
PHI_CONTRACT = 'con_phi_lst001'
RSA_CONTRACT = 'con_rsa_encryption'
PROFILE_CONTRACT = 'con_gamma_phi_profile_v4'
EVALUATOR_CONTRACT = 'con_hand_evaluator_v1'
OTP_CONTRACT = 'con_otp_v1'
ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
HOLDEM_POKER = 3


with open(os.path.join(external_deps_dir, 'rsa', f'{RSA_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=RSA_CONTRACT)

with open(os.path.join(external_deps_dir, 'otp', f'{OTP_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=OTP_CONTRACT)

with open(os.path.join(external_deps_dir, 'core', 'con_phi_lst001.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_phi_lst001', signer='me')

with open(os.path.join(external_deps_dir, 'core', f'{PROFILE_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PROFILE_CONTRACT)

with open(os.path.join(external_deps_dir, 'cards', f'{EVALUATOR_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=EVALUATOR_CONTRACT)

with open(os.path.join(module_dir, f'{POKER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=POKER_CONTRACT)


# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(512)


def get_contract_for_signer(signer, contract):
    client.signer = signer        
    return client.get_contract(contract)


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
        for game_type in [HOLDEM_POKER, ONE_CARD_POKER, BLIND_POKER, STUD_POKER]:
            phi = get_contract_for_signer('me', PHI_CONTRACT)

            if game_type == STUD_POKER:
                n_cards_totals = [5, 5, 5, 7, 7, 7]
                n_hole_cards = [1, 3, 5, 1, 2, 7]
            else:
                n_cards_totals = [None]
                n_hole_cards = [None]

            for r in range(len(n_cards_totals)):

                contract = get_contract_for_signer('me', POKER_CONTRACT)
    
                # Start a game
                game_id = contract.start_game(
                    name=f'MyGame-{str(uuid.uuid4())[:12]}',
                    other_players=['you'],
                    game_type=game_type,
                    n_hole_cards=n_hole_cards[r],
                    n_cards_total=n_cards_totals[r],
                    bet_type=0,
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

                contract = get_contract_for_signer('me', POKER_CONTRACT)

                # Start a hand
                hand_id = contract.start_hand(
                    game_id=game_id,
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
                elif game_type == BLIND_POKER:
                    expected_num_cards = 1
                elif game_type == HOLDEM_POKER:
                    expected_num_cards = 2
                elif game_type == STUD_POKER:
                    expected_num_cards = n_cards_totals[r]
                else:
                    raise RuntimeError("Unknown game type")

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


                # Holdem specific checks
                if game_type == HOLDEM_POKER:
                    community_encrypted = contract.quick_read('hands', hand_id, ['community_encrypted'])
                    print(community_encrypted)
                    community = []
                    for i in range(1, 4):
                        my_pad1 = contract.quick_read('hands', hand_id, ['me', f'player_encrypted_pad{i}'])
                        your_pad1 = contract.quick_read('hands', hand_id, ['you', f'player_encrypted_pad{i}'])
                        my_pad1 = rsa.decrypt(bytes.fromhex(my_pad1), my_sk).decode('utf-8')
                        your_pad1 = rsa.decrypt(bytes.fromhex(your_pad1), your_sk).decode('utf-8')
                        #print(my_pad1)
                        #print(your_pad1)
                        mp1 = int(my_pad1.split(':')[0])
                        yp1 = int(your_pad1.split(':')[0])
                        ms1 = int(my_pad1.split(':')[1])
                        ys1 = int(your_pad1.split(':')[1])
                        otp = client.get_contract(OTP_CONTRACT)
                        c1 = community_encrypted[i-1]
                        _c1 = otp.decrypt_hex(
                            encrypted_str=c1,
                            otp=yp1,
                            safe=False
                        )
                        __c1 = otp.decrypt(
                            encrypted_str=_c1,
                            otp=mp1,
                            safe=False
                        )
                        community.append(__c1)
                        contract = get_contract_for_signer('me', POKER_CONTRACT)
                        contract.reveal_otp(
                            hand_id=hand_id,
                            pad=mp1,
                            salt=ms1,
                            index=i
                        )
                        contract = get_contract_for_signer('you', POKER_CONTRACT)
                        contract.reveal_otp(
                            hand_id=hand_id,
                            pad=yp1,
                            salt=ys1,
                            index=i
                        )
                        contract = get_contract_for_signer('me', POKER_CONTRACT)
                        contract.reveal(
                            hand_id=hand_id,
                            index=i
                        )

                        # Bet
                        contract = get_contract_for_signer('you', POKER_CONTRACT)
                        contract.bet_check_or_fold(
                            hand_id=hand_id,
                            bet=5.0
                        )
                        
                        # Check
                        contract = get_contract_for_signer('me', POKER_CONTRACT)
                        contract.bet_check_or_fold(
                            hand_id=hand_id,
                            bet=5.0
                        )
                        contract = get_contract_for_signer('you', POKER_CONTRACT)
                        contract.bet_check_or_fold(
                            hand_id=hand_id,
                            bet=0.0
                        )
                        contract = get_contract_for_signer('me', POKER_CONTRACT)
                        round = contract.quick_read('hands', hand_id, ['round'])
                        self.assertEqual(round, i+1)

                    print(community)

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
                    self.assertIn('me', winners)
                    self.assertNotIn('you', winners)
                elif my_rank < your_rank:
                    self.assertNotIn('me', winners)
                    self.assertIn('you', winners)
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
                    game_id=game_id
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
                    game_id=game_id
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