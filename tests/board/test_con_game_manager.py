#tests/test_contract.py
import unittest
import os
import uuid
import rsa # For generating keys only
from contracting.client import ContractingClient
from os.path import dirname, abspath, join

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'board')

MAIN_CONTRACT = 'con_game_manager_v1'
MAIN_CONTRACT_IMPL = 'con_game_manager_impl_v1'
CHECKERS_CONTRACT = 'con_checkers_v1'
CHESS_CONTRACT = 'con_chess_v1'
GO_CONTRACT = 'con_go_v1'
PHI_CONTRACT = 'con_phi_lst001'

with open(join(dirname(module_dir), 'core', f'{PHI_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=PHI_CONTRACT, signer='me')

with open(join(module_dir, f'{MAIN_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=MAIN_CONTRACT, signer='me')

with open(join(module_dir, f'{CHECKERS_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CHECKERS_CONTRACT, signer='me')

with open(join(module_dir, f'{CHESS_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=CHESS_CONTRACT, signer='me')

with open(join(module_dir, f'{GO_CONTRACT}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=GO_CONTRACT, signer='me')

with open(join(module_dir, f'{MAIN_CONTRACT_IMPL}.py'), 'r') as f:
    code = f.read()
    client.submit(code, name=MAIN_CONTRACT_IMPL, owner=MAIN_CONTRACT, signer='me')


# Add actions to main contract
client.signer = 'me'
contract = client.get_contract(MAIN_CONTRACT)
contract.register_action(action='games', contract=MAIN_CONTRACT_IMPL)

# Delegate PHI
client.signer = 'me'
phi = client.get_contract(PHI_CONTRACT)
phi.transfer(
    to='you',
    amount=10_000_000
)
client.signer = 'me'
phi = client.get_contract(PHI_CONTRACT)
phi.approve(
    amount = 10_000_000,
    to=MAIN_CONTRACT
)
client.signer = 'you'
phi = client.get_contract(PHI_CONTRACT)
phi.approve(
    amount = 10_000_000,
    to=MAIN_CONTRACT
)


def printFormattedBoard(state: dict, NUM_ROWS: int = 8):
    board = state['board']
    print("-" * (NUM_ROWS+2))
    for i in range(NUM_ROWS):
        print("|"+board[i*NUM_ROWS: i*NUM_ROWS+NUM_ROWS]+"|")
    print("-" * (NUM_ROWS+2))
    print('Winner: {}'.format(state.get('winner')))


def move(team: str, x1: int, y1: int, x2: list = None, y2: list = None, game_type: str = 'checkers'):
    contract = client.get_contract(MAIN_CONTRACT)
    game_num = contract.quick_read('metadata', game_type, ['me', 'count'])
    game_id = contract.quick_read('metadata', game_type, ['me', f'game-{game_num}'])
    state = get_state_for_game(game_id, game_type=game_type)
    creator_team = state['creator_team']
    creator = state['creator']  
    opponent = state['opponent']  
    if team == 'w':
        if creator_team == 'b':
            client.signer = opponent
        else:
            client.signer = creator
    else:
        if creator_team == 'b':
            client.signer = creator
        else:
            client.signer = opponent
    contract = client.get_contract(MAIN_CONTRACT)
    contract.interact(
        action="games",
        payload={
            'action': 'move',
            "type": game_type,
            'game_id': game_id,
            'x1': x1,
            'y1': y1,
            'x2': x2,
            'y2': y2,
        }
    )
    state = contract.quick_read('metadata', game_type, [game_id, 'state'])
    printFormattedBoard(state)


def get_state_for_game(game_id: str, game_type: str='checkers') -> dict:
    return contract.quick_read('metadata', game_type, [game_id, 'state'])


def play_game():
    move("b", 2, 1, [3], [0])
    move("w", 5, 0, [4], [1])
    move("b", 2, 3, [3], [2])
    move("w", 4, 1, [2], [3])
    move("b", 1, 2, [3], [4])
    move("w", 6, 1, [5], [0])
    move("b", 1, 4, [2], [3])
    move("w", 5, 6, [4], [7])
    move("b", 3, 4, [4], [3])
    move("w", 5, 4, [3, 1], [2, 4])
    move("b", 0, 5, [2], [3])
    move("w", 5, 0, [4], [1])
    move("b", 2, 3, [3], [2])
    move("w", 4, 1, [2], [3])
    move("b", 0, 1, [1], [2])
    move("w", 2, 3, [0], [1])
    move("b", 0, 3, [1], [2])
    move("w", 0, 1, [2], [3])
    move("b", 3, 0, [4], [1])
    move("w", 5, 2, [3], [0])
    move("b", 1, 0, [2], [1])
    move("w", 3, 0, [1], [2])
    move("b", 2, 5, [3], [6])
    move("w", 4, 7, [2], [5])
    move("b", 1, 6, [3], [4])
    move("w", 2, 3, [4], [5])
    move("b", 2, 7, [3], [6])
    move("w", 4, 5, [2], [7])
    move("b", 0, 7, [1], [6])
    move("w", 2, 7, [0], [5])


def play_chess():
    move("w", 6, 4, 4, 4, game_type="chess")
    move("b", 1, 1, 2, 1, game_type="chess")
    move("w", 6, 6, 5, 6, game_type="chess")
    move("b", 1, 0, 3, 0, game_type="chess")
    move("w", 7, 5, 4, 2, game_type="chess")
    move("b", 1, 7, 2, 7, game_type="chess")
    move("w", 7, 3, 5, 5, game_type="chess")
    move("b", 2, 1, 3, 1, game_type="chess")
    move("w", 7, 6, 6, 4, game_type="chess")
    move("b", 3, 0, 4, 0, game_type="chess")
    # Castle
    move("w", 7, 4, 7, 6, game_type="chess")
    move("b", 1, 2, 2, 2, game_type="chess")
    # En passant
    move("w", 6, 1, 4, 1, game_type="chess")
    move("b", 4, 0, 5, 1, game_type="chess")
    # Checkmate
    move("w", 5, 5, 1, 5, game_type="chess")


def play_go():
    move("b", 1, 1, game_type="go")
    move("w", 6, 4, game_type="go")
    move("b", 6, 3, game_type="go")
    move("w", 1, 2, game_type="go")
    move("b", 6, 5, game_type="go")
    move("w", 1, 3, game_type="go")
    move("b", 5, 4, game_type="go")
    move("w", 1, 4, game_type="go")
    move("b", 7, 3, game_type="go")
    move("w", 7, 4, game_type="go")
    move("b", 7, 5, game_type="go")


class MyTestCase(unittest.TestCase):

    def test_simple_go(self):
        client.signer = "me"
        contract = client.get_contract(MAIN_CONTRACT)

        num_games_me = contract.quick_read('metadata', 'chess', ['go', 'count']) or 0
        num_games_you = contract.quick_read('metadata', 'chess', ['go', 'count']) or 0

        game_id = contract.interact(
            action="games",
            payload={
                "action": "create",
                "type": "go",
                "other_player": "you",                
            }
        )

        client.signer = "you"
        contract = client.get_contract(MAIN_CONTRACT)
        contract.interact(
            action="games",
            payload={
                "action": "join",
                "type": "go",
                "game_id": game_id
            }
        )

        num_games_me_after = contract.quick_read('metadata', 'go', ['me', 'count']) or 0
        num_games_you_after = contract.quick_read('metadata', 'go', ['you', 'count']) or 0

        self.assertEqual(num_games_me_after, num_games_me + 1)
        self.assertEqual(num_games_you_after, num_games_you + 1)

        self.assertIsNotNone(game_id)
        game_num = contract.quick_read('metadata', 'go', ['me', 'count'])
        self.assertEqual(game_id, contract.quick_read('metadata', 'go', ['me', f'game-{game_num}']))

        state = get_state_for_game(game_id, game_type='go')
        winner = state.get('winner')
        self.assertIsNone(winner)

        print(f'Game ID: {game_id}')
        # Play game
        play_go()

        client.signer = "you"
        contract = client.get_contract(MAIN_CONTRACT)
        contract.interact(
            action="games",
            payload={
                "action": "end_game",
                "type": "go",
                "game_id": game_id
            }
        )

        state = get_state_for_game(game_id, game_type='go')
        winner = state.get('winner')
        self.assertEqual(winner, 'b')


    def test_simple_chess(self):
        return
        client.signer = "me"
        contract = client.get_contract(MAIN_CONTRACT)

        num_games_me = contract.quick_read('metadata', 'chess', ['me', 'count']) or 0
        num_games_you = contract.quick_read('metadata', 'chess', ['you', 'count']) or 0

        game_id = contract.interact(
            action="games",
            payload={
                "action": "create",
                "type": "chess",
                "other_player": "you",                
            }
        )

        client.signer = "you"
        contract = client.get_contract(MAIN_CONTRACT)
        contract.interact(
            action="games",
            payload={
                "action": "join",
                "type": "chess",
                "game_id": game_id
            }
        )

        num_games_me_after = contract.quick_read('metadata', 'chess', ['me', 'count']) or 0
        num_games_you_after = contract.quick_read('metadata', 'chess', ['you', 'count']) or 0

        self.assertEqual(num_games_me_after, num_games_me + 1)
        self.assertEqual(num_games_you_after, num_games_you + 1)

        self.assertIsNotNone(game_id)
        game_num = contract.quick_read('metadata', 'chess', ['me', 'count'])
        self.assertEqual(game_id, contract.quick_read('metadata', 'chess', ['me', f'game-{game_num}']))

        state = get_state_for_game(game_id, game_type='chess')
        winner = state.get('winner')
        self.assertIsNone(winner)

        print(f'Game ID: {game_id}')
        # Play game
        play_chess()

        state = get_state_for_game(game_id, game_type='chess')
        winner = state.get('winner')
        self.assertEqual(winner, 'w')


    def test_simple_checkers(self):
        return
        client.signer = "me"
        contract = client.get_contract(MAIN_CONTRACT)

        num_games_me = contract.quick_read('metadata', 'checkers', ['me', 'count']) or 0
        num_games_you = contract.quick_read('metadata', 'checkers', ['you', 'count']) or 0

        game_id = contract.interact(
            action="games",
            payload={
                "action": "create",
                "type": "checkers",
                "other_player": "you",                
            }
        )

        client.signer = "you"
        contract = client.get_contract(MAIN_CONTRACT)
        contract.interact(
            action="games",
            payload={
                "action": "join",
                "type": "checkers",
                "game_id": game_id
            }
        )

        num_games_me_after = contract.quick_read('metadata', 'checkers', ['me', 'count']) or 0
        num_games_you_after = contract.quick_read('metadata', 'checkers', ['you', 'count']) or 0

        self.assertEqual(num_games_me_after, num_games_me + 1)
        self.assertEqual(num_games_you_after, num_games_you + 1)

        self.assertIsNotNone(game_id)
        game_num = contract.quick_read('metadata', 'checkers', ['me', 'count'])
        self.assertEqual(game_id, contract.quick_read('metadata', 'checkers', ['me', f'game-{game_num}']))

        state = get_state_for_game(game_id)
        winner = state.get('winner')
        self.assertIsNone(winner)

        print(f'Game ID: {game_id}')
        # Play game
        play_game()

        state = get_state_for_game(game_id)
        winner = state.get('winner')
        self.assertEqual(winner, 'w')

    def test_betting_checkers(self):
        return
        client.signer = "you"
        contract = client.get_contract(MAIN_CONTRACT)

        rounds = 3
        wager = 1000

        contract_balance = phi.quick_read('balances', MAIN_CONTRACT) or 0
        self.assertEqual(0, contract_balance)

        game_id = contract.interact(
            action="games",
            payload={
                "action": "create",
                #"other_player": "me",
                "rounds": rounds,
                "wager": wager,
                "type": "checkers",
                "public": True             
            }
        )

        contract_balance = phi.quick_read('balances', MAIN_CONTRACT) or 0
        self.assertEqual(wager, contract_balance)
        
        client.signer = "me"
        contract = client.get_contract(MAIN_CONTRACT)
        contract.interact(
            action="games",
            payload={
                "action": "join",
                "type": "checkers",
                "game_id": game_id
            }
        )

        contract_balance = phi.quick_read('balances', MAIN_CONTRACT) or 0
        self.assertEqual(wager * 2, contract_balance)

        state = get_state_for_game(game_id)
        winner = state.get('winner')
        self.assertIsNone(winner)

        print(f'Game ID: {game_id}')
        for r in range(rounds * 2):
            print(f"Round: {r}")
            # Play game
            play_game()

            state = get_state_for_game(game_id)
            winner = state.get('winner')
            self.assertEqual(winner, 'w')

            contract_balance = phi.quick_read('balances', MAIN_CONTRACT) or 0
            if r % rounds == rounds - 1:
                self.assertEqual(0, contract_balance)
                # Play again
                client.signer = "you"
                contract = client.get_contract(MAIN_CONTRACT)
                contract.interact(
                    action="games",
                    payload={
                        "action": "play_again",
                        "type": "checkers",
                        "game_id": game_id
                    }
                )
                client.signer = "me"
                contract = client.get_contract(MAIN_CONTRACT)
                contract.interact(
                    action="games",
                    payload={
                        "action": "pay_up",
                        "type": "checkers",
                        "game_id": game_id
                    }
                )
            else:
                self.assertEqual(wager * 2, contract_balance)
                # Move to next round
                client.signer = "me"
                contract = client.get_contract(MAIN_CONTRACT)
                contract.interact(
                    action="games",
                    payload={
                        "action": "next_round",
                        "type": "checkers",
                        "game_id": game_id
                    }
                )



  
        

if __name__ == '__main__':
    unittest.main()