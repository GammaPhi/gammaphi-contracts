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
GAME_CONTROLLER_CONTRACT = 'con_poker_game_controller_v2'
HAND_CONTROLLER_CONTRACT = 'con_poker_hand_controller_v3'
PHI_CONTRACT = 'con_phi_lst001'
RSA_CONTRACT = 'con_rsa_encryption'
PROFILE_CONTRACT = 'con_gamma_phi_profile_v4'
EVALUATOR_CONTRACT = 'con_hand_evaluator_v1'
OTP_CONTRACT = 'con_otp_v1'
ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
HOLDEM_POKER = 3
OMAHA_POKER = 4
DEFAULT_CHIPS = 100_000
ME = 'me'
OTHER_PLAYERS = [str(uuid.uuid4())[:12] for _ in range(7)]
ALL_PLAYERS = OTHER_PLAYERS + [ME]
KEY_STORE = {}


with open(os.path.join(external_deps_dir, 'rsa', f'{RSA_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=RSA_CONTRACT)

with open(os.path.join(external_deps_dir, 'otp', f'{OTP_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=OTP_CONTRACT)

with open(os.path.join(external_deps_dir, 'core', f'{PHI_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PHI_CONTRACT, signer=ME)

with open(os.path.join(external_deps_dir, 'core', f'{PROFILE_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PROFILE_CONTRACT)

with open(os.path.join(external_deps_dir, 'cards', f'{EVALUATOR_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=EVALUATOR_CONTRACT)

with open(os.path.join(module_dir, f'{POKER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=POKER_CONTRACT)

with open(os.path.join(module_dir, f'{HAND_CONTROLLER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=HAND_CONTROLLER_CONTRACT, owner=POKER_CONTRACT)

with open(os.path.join(module_dir, f'{GAME_CONTROLLER_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=GAME_CONTROLLER_CONTRACT, owner=POKER_CONTRACT)


# Generate keys with rsa library
def generate_keys():
    return rsa.newkeys(512)


def get_contract_for_signer(signer, contract):
    client.signer = signer        
    return client.get_contract(contract)


def setup_players(players: list):
    # Give players some PHI
    for p in players:
        if p != ME:
            phi = get_contract_for_signer(ME, PHI_CONTRACT)
            phi.transfer(
                to=p,
                amount=10_000_000
            )

        phi = get_contract_for_signer(p, PHI_CONTRACT)
        phi.approve(
            to=POKER_CONTRACT,
            amount=10_000_000
        )
        vk, sk = generate_keys()
        KEY_STORE[p] = sk
        profile = get_contract_for_signer(p, PROFILE_CONTRACT)
        profile.create_profile(
            username=p,
            public_rsa_key=str(vk.n)+"|"+str(vk.e)
        )

def setup_game(creator: str, other_players: list, **kwargs):
    # Start a game
    contract = get_contract_for_signer(creator, POKER_CONTRACT)
    game_id = contract.start_game(
        name=f'MyGame-{str(uuid.uuid4())[:12]}',
        other_players=other_players,
        game_config=dict(
            game_type=kwargs['game_type'],
            n_hole_cards=kwargs.get('n_hole_cards'),
            n_cards_total=kwargs.get('n_card_totals'),
            bet_type=kwargs.get('bet_type', 0),
            ante=kwargs.get('ante', 1.0),
        )       
    )

    contract.add_chips_to_game(
        game_id=game_id,
        amount=kwargs.get('chips', {}).get(ME, DEFAULT_CHIPS)
    )

    for p in other_players:
        contract = get_contract_for_signer(p, POKER_CONTRACT)
        contract.respond_to_invite(
            game_id=game_id,
            accept=True
        )
        contract.add_chips_to_game(
            game_id=game_id,
            amount=kwargs.get('chips', {}).get(p, DEFAULT_CHIPS)
        )

    return game_id

def ante_up(players: list, hand_id: str):
    # Start a game
    for p in players:
        contract = get_contract_for_signer(p, POKER_CONTRACT)
        contract.ante_up(
            hand_id=hand_id
        )

def decrypt_hand(player: str, hand_id: str):
    # Decrypt hands
    contract = get_contract_for_signer(player, POKER_CONTRACT)
    hand = contract.quick_read('hands', hand_id, [player, 'player_encrypted_hand'])
    return rsa.decrypt(bytes.fromhex(hand), KEY_STORE[player]).decode('utf-8')


def reveal_community_cards_for_player(player: str, index: int, hand_id: str):
    contract = get_contract_for_signer(player, POKER_CONTRACT)
    pad_with_salt = contract.quick_read('hands', hand_id, [player, f'player_encrypted_pad{index}'])
    pad_with_salt = rsa.decrypt(bytes.fromhex(pad_with_salt), KEY_STORE[player]).decode('utf-8')

    pad = int(pad_with_salt.split(':')[0])
    salt = int(pad_with_salt.split(':')[1])
    contract.reveal_otp(
        hand_id=hand_id,
        pad=pad,
        salt=salt,
        index=index
    )

def reveal_community_cards(index: int, hand_id: str):
    contract = get_contract_for_signer(ME, POKER_CONTRACT)
    players = contract.quick_read('hands', hand_id, ['active_players'])
    folded = contract.quick_read('hands', hand_id, ['folded'])
    for player in players:
        if player in folded:
            continue
        reveal_community_cards_for_player(player, index, hand_id)

    contract = get_contract_for_signer(ME, POKER_CONTRACT)
    contract.reveal(
        hand_id=hand_id,
        index=index
    )
    
    community = contract.quick_read('hands', hand_id, ['community'])
    return community[index-1]


def place_bet(player: str, bet: float, hand_id: str):
    contract = get_contract_for_signer(player, POKER_CONTRACT)
    contract.bet_check_or_fold(
        hand_id=hand_id,
        bet=bet
    )

def leave_game(player: str, game_id: str):
    contract = get_contract_for_signer(player, POKER_CONTRACT)
    contract.leave_game(
        game_id=game_id,
    )


def kick_from_game(creator: str, player: str, game_id: str):
    contract = get_contract_for_signer(creator, POKER_CONTRACT)
    contract.kick_from_game(
        game_id=game_id,
        player=player
    )


def verify_hands(hand_id: str):
    contract = get_contract_for_signer(ME, POKER_CONTRACT)
    players = contract.quick_read('hands', hand_id, ['active_players'])
    folded = contract.quick_read('hands', hand_id, ['folded'])
    for player in players:
        if player not in folded:
            hand = decrypt_hand(player, hand_id)
            contract = get_contract_for_signer(player, POKER_CONTRACT)
            contract.verify_hand(
                hand_id=hand_id,
                player_hand_str=hand
            )

setup_players(ALL_PLAYERS)


class MyTestCase(unittest.TestCase):
    # Assertion helpers
    def assert_chips_remaining(self, player: str, game_id: str, expected_chips: float):
        contract = get_contract_for_signer(ME, POKER_CONTRACT)
        chips = contract.quick_read('games', game_id, [player])
        self.assertEqual(chips, expected_chips)

    def assert_chips_in_pot(self, player: str, hand_id: str, expected_chips: float):
        contract = get_contract_for_signer(ME, POKER_CONTRACT)
        chips = contract.quick_read('hands', hand_id, [player, 'bet'])
        self.assertEqual(chips, expected_chips)

    def assert_total_chips_in_pot(self, hand_id: str, expected_chips: float):
        contract = get_contract_for_signer(ME, POKER_CONTRACT)
        chips = contract.quick_read('hands', hand_id, ['pot'])
        self.assertEqual(chips, expected_chips)

    # Actual tests
    def test_simple_community_games(self):
        for game_type in [HOLDEM_POKER, OMAHA_POKER]:
            game_id = setup_game(
                creator=ME,
                other_players=OTHER_PLAYERS,
                game_type=game_type,
            )
            contract = get_contract_for_signer(ME, POKER_CONTRACT)
            original_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])
            # Start a hand
            hand_id = contract.start_hand(
                game_id=game_id,
            )
            ante_up(ALL_PLAYERS, hand_id)
            for player in ALL_PLAYERS:
                self.assert_chips_in_pot(player, hand_id, 1.0)
            self.assert_total_chips_in_pot(hand_id, len(ALL_PLAYERS) * 1.0)

            contract.deal_cards(hand_id=hand_id)

            for player in ALL_PLAYERS:
                place_bet(player, 1.0, hand_id)
                self.assert_chips_in_pot(player, hand_id, 2.0)
            self.assert_total_chips_in_pot(hand_id, len(ALL_PLAYERS) * 2.0)

            # make sure you can't bet before this reveal
            self.assertRaises(AssertionError,
                place_bet,
                ALL_PLAYERS[0],
                1.0,
                hand_id
            )

            reveal_community_cards(1, hand_id)

            for player in ALL_PLAYERS:
                place_bet(player, 1.0, hand_id)
                self.assert_chips_in_pot(player, hand_id, 3.0)
            self.assert_total_chips_in_pot(hand_id, len(ALL_PLAYERS) * 3.0)

            # make sure you can't bet before this reveal
            self.assertRaises(AssertionError,
                place_bet,
                ALL_PLAYERS[0],
                1.0,
                hand_id
            )

            reveal_community_cards(2, hand_id)

            for player in ALL_PLAYERS:
                place_bet(player, 1.0, hand_id)
                self.assert_chips_in_pot(player, hand_id, 4.0)
            self.assert_total_chips_in_pot(hand_id, len(ALL_PLAYERS) * 4.0)

            # make sure you can't bet before this reveal
            self.assertRaises(AssertionError,
                place_bet,
                ALL_PLAYERS[0],
                1.0,
                hand_id
            )
            
            reveal_community_cards(3, hand_id)

            for player in ALL_PLAYERS:
                place_bet(player, 1.0, hand_id)
                self.assert_chips_in_pot(player, hand_id, 5.0)
            self.assert_total_chips_in_pot(hand_id, len(ALL_PLAYERS) * 5.0)

            verify_hands(hand_id)

            # Payout hand
            contract.payout_hand(
                hand_id=hand_id
            )

            final_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])
            self.assertEqual(original_total, final_total)

    def test_leave_hand(self):
        game_id = setup_game(
            creator=ME,
            other_players=OTHER_PLAYERS,
            game_type=HOLDEM_POKER,
        )
        contract = get_contract_for_signer(ME, POKER_CONTRACT)
        original_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])
        left_from_game = 0

        # Test leaving early
        leave_game(OTHER_PLAYERS[1], game_id)
        left_from_game -= DEFAULT_CHIPS

        # Start a hand
        hand_id = contract.start_hand(
            game_id=game_id,
        )

        all_players = ALL_PLAYERS.copy()
        all_players.remove(OTHER_PLAYERS[1])

        ante_up(all_players, hand_id)
        expected_chips = len(all_players)

        for player in all_players:
            self.assert_chips_in_pot(player, hand_id, 1.0)
        self.assert_total_chips_in_pot(hand_id, expected_chips)

        contract.deal_cards(hand_id=hand_id)

        self.assertRaises(AssertionError,
            leave_game,
            player=OTHER_PLAYERS[0],
            game_id=game_id
        )
  
        # Needs to reveal community cards
        self.assertRaises(AssertionError,
            place_bet,
            OTHER_PLAYERS[0], -1, hand_id
        )

        print(contract.quick_read('hands', hand_id, ['next_better']))
        print(OTHER_PLAYERS[0])
        print(contract.quick_read('hands', hand_id, ['active_players']))
        print(all_players)
        print(OTHER_PLAYERS)

        reveal_community_cards_for_player(OTHER_PLAYERS[0], 1, hand_id)
        reveal_community_cards_for_player(OTHER_PLAYERS[0], 2, hand_id)
        reveal_community_cards_for_player(OTHER_PLAYERS[0], 3, hand_id)

        place_bet(OTHER_PLAYERS[0], -1, hand_id)
        leave_game(OTHER_PLAYERS[0], game_id)
        left_from_game -= DEFAULT_CHIPS - 1

        all_players.remove(OTHER_PLAYERS[0])

        # TODO Should dealer be able to leave game? I think not while in play
        self.assertRaises(AssertionError,
            leave_game,
            ME, game_id
        )

        reveal_community_cards_for_player(OTHER_PLAYERS[3], 1, hand_id)
        reveal_community_cards_for_player(OTHER_PLAYERS[3], 2, hand_id)
        reveal_community_cards_for_player(OTHER_PLAYERS[3], 3, hand_id)

        # Kick from game with reveal
        kick_from_game(ME, OTHER_PLAYERS[3], game_id)
        all_players.remove(OTHER_PLAYERS[3])
        left_from_game -= DEFAULT_CHIPS - 1

        expected_chips += len(all_players)
        for player in all_players:
            place_bet(player, 1.0, hand_id)
            self.assert_chips_in_pot(player, hand_id, 2.0)
        self.assert_total_chips_in_pot(hand_id, expected_chips)

        reveal_community_cards(1, hand_id)

        # Kick from game without reveal
        kick_from_game(ME, OTHER_PLAYERS[2], game_id)
        all_players.remove(OTHER_PLAYERS[2])
        left_from_game -= DEFAULT_CHIPS - 2

        self.assertTrue(contract.quick_read('hands', hand_id, ['completed']))
        self.assertTrue(contract.quick_read('hands', hand_id, ['payed_out']))

        final_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])
        self.assertEqual(original_total, final_total - left_from_game)

    def test_community_games_going_all_in(self):
        for game_type in [HOLDEM_POKER, OMAHA_POKER]:
            game_id = setup_game(
                creator=ME,
                other_players=OTHER_PLAYERS,
                game_type=game_type,
                chips={
                    ME: 100,
                    OTHER_PLAYERS[3]: 500
                }
            )
            contract = get_contract_for_signer(ME, POKER_CONTRACT)
            original_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])

            # Start a hand
            hand_id = contract.start_hand(
                game_id=game_id,
            )
            ante_up(ALL_PLAYERS, hand_id)
            contract.deal_cards(hand_id=hand_id)

            for player in OTHER_PLAYERS:
                place_bet(player, 1, hand_id)

            all_in = contract.quick_read('hands', hand_id, ['all_in'])
            self.assertEqual(0, len(all_in))

            # Go all in
            place_bet(ME, 99, hand_id)
            for player in OTHER_PLAYERS:                
                place_bet(player, 98, hand_id)

            all_in = contract.quick_read('hands', hand_id, ['all_in'])
            self.assertEqual(1, len(all_in))
            self.assertEqual(ME, all_in[0])

            self.assertEqual(1, contract.quick_read('hands', hand_id, ['round']))
            reveal_community_cards(1, hand_id)

            # Others keep betting
            for player in OTHER_PLAYERS:                
                place_bet(player, 1, hand_id)

            self.assertEqual(2, contract.quick_read('hands', hand_id, ['round']))
            reveal_community_cards(2, hand_id)

            for i in range(len(OTHER_PLAYERS)):
                player = OTHER_PLAYERS[i]
                if i == 3:
                    # Go all in
                    place_bet(player, 399, hand_id)
                    all_in = contract.quick_read('hands', hand_id, ['all_in'])
                    self.assertEqual(2, len(all_in))
                    self.assertIn(ME, all_in)
                    self.assertIn(OTHER_PLAYERS[3], all_in)
                elif i < 3:            
                    place_bet(player, 1, hand_id)
                else:
                    # Call
                    place_bet(player, 399, hand_id)

            for i in range(3):
                # Fold
                player = OTHER_PLAYERS[i]
                reveal_community_cards_for_player(player, 1, hand_id)
                reveal_community_cards_for_player(player, 2, hand_id)
                reveal_community_cards_for_player(player, 3, hand_id)
                place_bet(player, -1, hand_id)

            for i in range(4, len(OTHER_PLAYERS)):
                player = OTHER_PLAYERS[i]
                place_bet(player, 0, hand_id)

            self.assertEqual(3, contract.quick_read('hands', hand_id, ['round']))
            reveal_community_cards(3, hand_id)

            for i in range(4, len(OTHER_PLAYERS)):
                player = OTHER_PLAYERS[i]
                place_bet(player, 1, hand_id)

            self.assertEqual(4, contract.quick_read('hands', hand_id, ['round']))
            reveal_community_cards(3, hand_id)

            verify_hands(hand_id)

            # Payout hand
            contract.payout_hand(
                hand_id=hand_id
            )

            final_total = sum([contract.quick_read('games', game_id, [p]) for p in ALL_PLAYERS])
            self.assertEqual(original_total, final_total)

    def test_simple_1_card_game(self):
        for game_type in [ONE_CARD_POKER, BLIND_POKER, STUD_POKER]:
            phi = get_contract_for_signer(ME, PHI_CONTRACT)

            if game_type == STUD_POKER:
                n_cards_totals = [5, 5, 7, 7]
                n_hole_cards = [1, 5, 3, 7]
            else:
                n_cards_totals = [None]
                n_hole_cards = [None]

            for r in range(len(n_cards_totals)):

                contract = get_contract_for_signer(ME, POKER_CONTRACT)
    
                # Start a game
                game_id = contract.start_game(
                    name=f'MyGame-{str(uuid.uuid4())[:12]}',
                    other_players=[OTHER_PLAYERS[0]],
                    game_config=dict(
                        game_type=game_type,
                        n_hole_cards=n_hole_cards[r],
                        n_cards_total=n_cards_totals[r],
                        bet_type=0,
                        ante=1.0,
                    )
                )

                # Verify game state
                self.assertEqual(contract.quick_read('games', game_id, ['creator']), ME)
                self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), (ME,))

                self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', OTHER_PLAYERS[0])))

                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.respond_to_invite(
                    game_id=game_id,
                    accept=True
                )

                self.assertEqual(0, len(contract.quick_read('players_invites', OTHER_PLAYERS[0])))
                self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), (ME, OTHER_PLAYERS[0]))

                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                # Add chips for each player
                contract.add_chips_to_game(
                    game_id=game_id,
                    amount=100000
                )

                contract.add_player_to_game(
                    game_id=game_id,
                    player_to_add=OTHER_PLAYERS[2]
                )
                self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', OTHER_PLAYERS[2])))
                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)
                contract.respond_to_invite(
                    game_id=game_id,
                    accept=False
                )
                self.assertEqual(0, len(contract.quick_read('players_invites', OTHER_PLAYERS[2])))
                self.assertEqual((game_id,), tuple(contract.quick_read('players_invites', OTHER_PLAYERS[2], ['declined'])))
                self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), (ME, OTHER_PLAYERS[0]))

                contract.respond_to_invite(
                    game_id=game_id,
                    accept=True
                )

                self.assertEqual(0, len(contract.quick_read('players_invites', OTHER_PLAYERS[2])))
                self.assertEqual(0, len(contract.quick_read('players_invites', OTHER_PLAYERS[2], ['declined'])))
                self.assertEqual(tuple(contract.quick_read('games', game_id, ['players'])), (ME, OTHER_PLAYERS[0], OTHER_PLAYERS[2]))

                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.add_chips_to_game(
                    game_id=game_id,
                    amount=100000
                )

                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)
                contract.add_chips_to_game(
                    game_id=game_id,
                    amount=100000
                )

                contract = get_contract_for_signer(ME, POKER_CONTRACT)

                # Start a hand
                hand_id = contract.start_hand(
                    game_id=game_id,
                )

                stored_hand_id = contract.quick_read('games', game_id, ['current_hand'])
                self.assertEqual(hand_id, stored_hand_id)

                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertTrue(len(active_players) == 0)

                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )
                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertIn(ME, active_players)
                self.assertNotIn(OTHER_PLAYERS[0], active_players)

                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )

                active_players = contract.quick_read('hands', hand_id, ['active_players'])

                self.assertIn(ME, active_players)
                self.assertIn(OTHER_PLAYERS[0], active_players)

                # Deal hand
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.deal_cards(
                    hand_id=hand_id
                )

                # Decrypt hands
                my_hand = contract.quick_read('hands', hand_id, [ME, 'player_encrypted_hand'])
                my_hand = rsa.decrypt(bytes.fromhex(my_hand), KEY_STORE[ME]).decode('utf-8')

                your_hand = contract.quick_read('hands', hand_id, [OTHER_PLAYERS[0], 'player_encrypted_hand'])
                your_hand = rsa.decrypt(bytes.fromhex(your_hand), KEY_STORE[OTHER_PLAYERS[0]]).decode('utf-8')

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

                self.assertNotEqual(tuple(my_cards), tuple(your_cards))

                dealer = contract.quick_read('hands', hand_id, ['dealer'])
                self.assertEqual(dealer, ME)

                round = contract.quick_read('hands', hand_id, ['round'])

                # Check
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=0.0
                )
                
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=10.0
                )

                # Raise
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=15
                )

                round = contract.quick_read('hands', hand_id, ['round'])

                # Call
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=5.0
                )

                # Verify hand publicly
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.verify_hand(
                    hand_id=hand_id,
                    player_hand_str=your_hand
                )
                # Verify from a hidden hand
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.verify_hand(
                    hand_id=hand_id,
                    player_hand_str=my_hand
                )

                # Payout hand
                contract.payout_hand(
                    hand_id=hand_id
                )

                # Check some state
                my_rank = contract.quick_read('hands', hand_id, [ME, 'rank'])
                your_rank = contract.quick_read('hands', hand_id, [OTHER_PLAYERS[0], 'rank'])
                winners = contract.quick_read('hands', hand_id, ['winners'])

                my_chips = contract.quick_read('games', game_id, [ME])
                your_chips = contract.quick_read('games', game_id, [OTHER_PLAYERS[0]])

                if my_rank > your_rank:
                    self.assertIn(ME, winners)
                    self.assertNotIn(OTHER_PLAYERS[0], winners)
                elif my_rank < your_rank:
                    self.assertNotIn(ME, winners)
                    self.assertIn(OTHER_PLAYERS[0], winners)
                else:
                    self.assertIn(ME, winners)
                    self.assertIn(OTHER_PLAYERS[0], winners)

                # Withdraw chips
                current_phi_balance = phi.quick_read('balances', ME)
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.withdraw_chips_from_game(
                    game_id=game_id,
                    amount=20
                )
                new_phi_balance = phi.quick_read('balances', ME)
                my_new_chips = contract.quick_read('games', game_id, [ME])

                self.assertEqual(current_phi_balance + 20, new_phi_balance)
                self.assertEqual(my_new_chips + 20, my_chips)
                    

                your_chips = contract.quick_read('games', game_id, [OTHER_PLAYERS[0]])

                # Start another hand
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                hand_id = contract.start_hand(
                    game_id=game_id
                )

                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )            
                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertIn(ME, active_players)
                self.assertNotIn(OTHER_PLAYERS[0], active_players)

                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )

                active_players = contract.quick_read('hands', hand_id, ['active_players'])

                self.assertIn(ME, active_players)
                self.assertIn(OTHER_PLAYERS[0], active_players)

                # Deal hand
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.deal_cards(
                    hand_id=hand_id
                )

                # Bet
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=10.0
                )

                # Raise
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=15
                )

                # Fold
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=-1
                )

                # Payout hand
                contract.payout_hand(
                    hand_id=hand_id
                )

                your_chips_after = contract.quick_read('games', game_id, [OTHER_PLAYERS[0]])
                self.assertEqual(your_chips + 11, your_chips_after)

                # Start another hand
                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)

                hand_id = contract.start_hand(
                    game_id=game_id
                )

                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertEqual(len(active_players), 0)

                dealer = contract.quick_read('hands', hand_id, ['dealer'])
                
                self.assertEqual(dealer, OTHER_PLAYERS[2])
                # Ante up
                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)
                contract.ante_up(
                    hand_id=hand_id
                )
                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertIn(OTHER_PLAYERS[2], active_players)

                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )           
                active_players = contract.quick_read('hands', hand_id, ['active_players'])
                self.assertIn(ME, active_players)
                self.assertNotIn(OTHER_PLAYERS[0], active_players)

                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                # Ante up
                contract.ante_up(
                    hand_id=hand_id
                )

                active_players = contract.quick_read('hands', hand_id, ['active_players'])

                self.assertIn(ME, active_players)
                self.assertIn(OTHER_PLAYERS[0], active_players)
                self.assertIn(OTHER_PLAYERS[2], active_players)

                # Deal hand
                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)
                contract.deal_cards(
                    hand_id=hand_id
                )

                # Bet
                contract = get_contract_for_signer(ME, POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=10.0
                )

                # Raise
                contract = get_contract_for_signer(OTHER_PLAYERS[0], POKER_CONTRACT)
                contract.bet_check_or_fold(
                    hand_id=hand_id,
                    bet=15
                )

                # Fold
                contract = get_contract_for_signer(OTHER_PLAYERS[2], POKER_CONTRACT)
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