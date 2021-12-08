#tests/test_contract.py
import unittest
import os
from os.path import dirname, abspath, join

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'cards')

with open(os.path.join(module_dir, 'con_che_dp_tables.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_che_dp_tables')

with open(os.path.join(module_dir, 'con_che_flush_tables.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_che_flush_tables')

with open(os.path.join(module_dir, 'con_5_card_hand_evaluator.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_5_card_hand_evaluator')


class MyTestCase(unittest.TestCase):

    def test_5_card_hands(self):
        client.signer = 'me'        
        contract = client.get_contract('con_5_card_hand_evaluator')

        hand_straight_flush = ["2c", "3c", "4c", "5c", "6c"]
        hand_full_house = ["2c", "2h", "4c", "4h", "4d"]
        hand_straight = ["2c", "3c", "4c", "5c", "6h"]
        hand_flush = ["2c", "3c", "4c", "5c", "7c"]
        hand_2_pair = ["2c", "2h", "4c", "4h", "5d"]
        hand_1_pair = ["2c", "2h", "4c", "6h", "5d"]
        hand_jack_high = ["2c", "3h", "7c", "8h", "Jd"]

        rank_straight_flush = contract.evaluate_cards(cards=hand_straight_flush)
        rank_full_house = contract.evaluate_cards(cards=hand_full_house)
        rank_straight = contract.evaluate_cards(cards=hand_straight)
        rank_flush = contract.evaluate_cards(cards=hand_flush)
        rank_2_pair = contract.evaluate_cards(cards=hand_2_pair)
        rank_1_pair = contract.evaluate_cards(cards=hand_1_pair)
        rank_jack_high = contract.evaluate_cards(cards=hand_jack_high)

        self.assertLess(rank_straight_flush, rank_flush)
        self.assertLess(rank_straight_flush, rank_full_house)
        self.assertLess(rank_flush, rank_straight)
        self.assertLess(rank_straight, rank_2_pair)
        self.assertLess(rank_2_pair, rank_1_pair)
        self.assertLess(rank_1_pair, rank_jack_high)
        self.assertLess(rank_full_house, rank_straight)
        print(f"Royal Flush: {contract.evaluate_cards(cards=['As','Ks','Qs','Js','Ts'])}")
        print(f"Worst: {contract.evaluate_cards(cards=['2s','3s','4s','5s','7c'])}")

if __name__ == '__main__':
    unittest.main()