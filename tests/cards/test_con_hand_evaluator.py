#tests/test_contract.py
import unittest
import os
from os.path import dirname, abspath, join

from contracting.client import ContractingClient

client = ContractingClient()

module_dir = join(dirname(dirname(dirname(abspath(__file__)))), 'cards')

with open(os.path.join(module_dir, 'con_hand_evaluator.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_hand_evaluator')

with open(os.path.join(module_dir, 'con_5_card_hand_evaluator.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_5_card_hand_evaluator')

with open(os.path.join(module_dir, 'con_7_card_hand_evaluator.py'), 'r') as f:
    code = f.read()
    client.submit(code, name='con_7_card_hand_evaluator')


class MyTestCase(unittest.TestCase):
    def test_con_hand_evaluator(self):
        client.signer = 'me'        
        contract = client.get_contract('con_hand_evaluator')

        # 5 card hands
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

        # 7 card hands
        hand_1 = ["9c", "4c", "4s", "9d", "4h", "Qc", "6c"]
        hand_2 = ["9c", "4c", "4s", "9d", "4h", "2c", "9h"]
        
        rank_1 = contract.evaluate_cards(cards=hand_1)
        rank_2 = contract.evaluate_cards(cards=hand_2)

        self.assertEqual(rank_1, 292)
        self.assertEqual(rank_2, 236)

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

    def test_7_card_hands(self):
        client.signer = 'me'        
        contract = client.get_contract('con_7_card_hand_evaluator')

        hand_1 = ["9c", "4c", "4s", "9d", "4h", "Qc", "6c"]
        hand_2 = ["9c", "4c", "4s", "9d", "4h", "2c", "9h"]
        
        rank_1 = contract.evaluate_cards(cards=hand_1)
        rank_2 = contract.evaluate_cards(cards=hand_2)

        self.assertEqual(rank_1, 292)
        self.assertEqual(rank_2, 236)

if __name__ == '__main__':
    unittest.main()