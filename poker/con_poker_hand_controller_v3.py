# con_poker_hand_controller_v3

import con_rsa_encryption as rsa
import con_otp_v1 as otp
import con_hand_evaluator_v1 as evaluator

random.seed()

ONE_CARD_POKER = 0
BLIND_POKER = 1
STUD_POKER = 2
HOLDEM_POKER = 3
OMAHA_POKER = 4
MAX_RANDOM_NUMBER = 99999999
NO_LIMIT = 0
POT_LIMIT = 1
FLOP = 1
TURN = 2
RIVER = 3

def get_players_and_assert_exists(game_id: str, games: Any) -> dict:
    players = games[game_id, 'players']
    assert players is not None, f'Game {game_id} does not exist.'
    return players


def active_player_sort(players: list) -> int:
    def sort(player):
        return players.index(player)
    return sort


def create_hand_id(name: str) -> str:
    return hashlib.sha3(":".join([name, str(now)]))


@export
def start_hand(game_id: str, dealer: str, games: Any, hands: Any) -> str:
    players = get_players_and_assert_exists(game_id, games)    
    assert dealer in players, 'You are not a part of this game.'
    assert len(players) > 1, 'You cannot start a hand by yourself.'

    previous_hand_id = games[game_id, 'current_hand']
    if previous_hand_id is not None:
        assert hands[previous_hand_id, 'payed_out'], 'The previous hand has not been payed out yet.'

    hand_id = create_hand_id(name=game_id)
    # Update game state
    games[game_id, 'current_hand'] = hand_id
    # Update hand state
    hands[hand_id, 'previous_hand_id'] = previous_hand_id
    hands[hand_id, 'game_id'] = game_id
    hands[hand_id, 'dealer'] = dealer
    hands[hand_id, 'folded'] = []
    hands[hand_id, 'completed'] = False
    hands[hand_id, 'payed_out'] = False
    hands[hand_id, 'reached_dealer'] = False
    hands[hand_id, 'active_players'] = []
    hands[hand_id, 'current_bet'] = 0
    hands[hand_id, 'pot'] = 0
    hands[hand_id, 'all_in'] = []
    return hand_id

@export
def ante_up(hand_id: str, player: str, games: Any, hands: Any):
    game_id = hands[hand_id, 'game_id']
    assert game_id is not None, 'This game does not exist.'
    players = get_players_and_assert_exists(game_id, games)    
    assert player in players, 'You are not a part of this game.'
    ante = games[game_id, 'ante']
    chips = games[game_id, player]
    assert chips is not None and chips >= ante, 'You do not have enough chips.'
    active_players = hands[hand_id, 'active_players'] or []
    assert player not in active_players, 'You have already paid the ante.'
    game_type = games[game_id, 'game_type']
    if game_type == STUD_POKER:
        max_players = 52 // games[game_id, 'n_cards_total']
    elif game_type == HOLDEM_POKER:
        max_players = 10
    elif game_type == OMAHA_POKER:
        max_players = 10
    else:
        max_players = 50
    assert len(active_players) < max_players, f'A maximum of {max_players} is allowed for this game type.'
    # Pay ante
    hands[hand_id, player, 'bet'] = ante
    hands[hand_id, player, 'max_bet'] = chips
    games[game_id, player] -= ante
    # Update hand state
    active_players.append(player)
    active_players.sort(key=active_player_sort(players))
    hands[hand_id, 'active_players'] = active_players
    hands[hand_id, 'current_bet'] = ante
    hands[hand_id, 'pot'] += ante
    if chips == ante:
        # All in
        all_in = hands[hand_id, 'all_in']
        all_in.append(player)
        hands[hand_id, 'all_in'] = all_in


@export
def deal_cards(hand_id: str, dealer: str, games: Any, hands: Any, player_metadata: Any):

    active_players = hands[hand_id, 'active_players']

    assert dealer == hands[hand_id, 'dealer'], 'You are not the dealer.'
    assert len(active_players) > 1, f'Not enough active players: {len(active_players)} <= 1'
    assert dealer in active_players, 'You are not actively part of this hand.'

    game_id = hands[hand_id, 'game_id']
    game_type = games[game_id, 'game_type']

    cards = evaluator.get_deck()

    n_cards_total = games[game_id, 'n_cards_total']
    n_hole_cards = games[game_id, 'n_hole_cards']

    if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
        community_cards = [",".join(cards[0:3]), cards[3], cards[4]]
    else:
        community_cards = None

    for i in range(len(active_players)):
        player = active_players[i]
        player_key = player_metadata[player, 'public_rsa_key']
        assert player_key is not None, f'Player {player} has not setup their encryption keys.'
        keys = player_key.split('|')
        assert len(keys) == 2, 'Invalid keys'

        if game_type == ONE_CARD_POKER:
            player_hand = cards[i: i+1]
        elif game_type == BLIND_POKER:
            # Player's hand is actually everyone elses hand
            player_hand = cards[0:i] + cards[i+1:len(active_players)]
            assert len(player_hand) == len(active_players)-1, f'Something went wrong. {len(player_hand)} != {len(active_players)-1}'
        elif game_type == STUD_POKER:
            player_hand = cards[n_cards_total*i:n_cards_total*i+n_cards_total]            
            assert len(player_hand) == n_cards_total, 'Something went wrong.'
        elif game_type == HOLDEM_POKER:
            player_hand = cards[5+2*i:5+2*i+2]
        elif game_type == OMAHA_POKER:
            player_hand = cards[5+4*i:5+4*i+4]
        else:
            assert False, 'Invalid game type.'

        player_hand_str = ",".join(player_hand)

        if n_hole_cards is not None and n_hole_cards < n_cards_total:
            public_hand_str = ",".join(player_hand[n_hole_cards:])
        else:
            public_hand_str = None

        salt = str(random.randint(0, MAX_RANDOM_NUMBER))

        if community_cards is not None:
            # TODO make this more efficient
            pad1 = otp.generate_otp(80)
            pad2 = otp.generate_otp(20)
            pad3 = otp.generate_otp(20)
            salt1 = str(random.randint(0, MAX_RANDOM_NUMBER))
            salt2 = str(random.randint(0, MAX_RANDOM_NUMBER))
            salt3 = str(random.randint(0, MAX_RANDOM_NUMBER))
            if i == 0:
                community_cards[0] = otp.encrypt(community_cards[0], pad1, safe=False)
                community_cards[1] = otp.encrypt(community_cards[1], pad2, safe=False)
                community_cards[2] = otp.encrypt(community_cards[2], pad3, safe=False)
            else:
                community_cards[0] = otp.encrypt_hex(community_cards[0], pad1, safe=False)
                community_cards[1] = otp.encrypt_hex(community_cards[1], pad2, safe=False)
                community_cards[2] = otp.encrypt_hex(community_cards[2], pad3, safe=False)
            pad1_with_salt = f'{pad1}:{salt1}'
            pad2_with_salt = f'{pad2}:{salt2}'
            pad3_with_salt = f'{pad3}:{salt3}'
            encrypted_pad1 = rsa.encrypt(
                message_str=pad1_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            encrypted_pad2 = rsa.encrypt(
                message_str=pad2_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            encrypted_pad3 = rsa.encrypt(
                message_str=pad3_with_salt,
                n=int(keys[0]),
                e=int(keys[1])    
            )
            hands[hand_id, player, 'player_encrypted_pad1'] = encrypted_pad1
            hands[hand_id, player, 'player_encrypted_pad2'] = encrypted_pad2
            hands[hand_id, player, 'player_encrypted_pad3'] = encrypted_pad3
            hands[hand_id, player, 'house_encrypted_pad1'] = hashlib.sha3(pad1_with_salt)
            hands[hand_id, player, 'house_encrypted_pad2'] = hashlib.sha3(pad2_with_salt)
            hands[hand_id, player, 'house_encrypted_pad3'] = hashlib.sha3(pad3_with_salt)

        player_hand_str_with_salt = f'{player_hand_str}:{salt}'

        # Encrypt players hand with their personal keys
        player_encrypted_hand = rsa.encrypt(
            message_str=player_hand_str_with_salt,
            n=int(keys[0]),
            e=int(keys[1])    
        )
        
        # For verification purposes
        house_encrypted_hand = hashlib.sha3(player_hand_str_with_salt)

        if public_hand_str is not None:
            hands[hand_id, player, 'public_hand'] = public_hand_str
        hands[hand_id, player, 'player_encrypted_hand'] = player_encrypted_hand
        hands[hand_id, player, 'house_encrypted_hand'] = house_encrypted_hand

    # Update hand state
    all_in = hands[hand_id, 'all_in']
    dealer_index = active_players.index(dealer)
    split = (dealer_index+1)%len(active_players)
    ordered_players = active_players[split:] + active_players[:split]
    next_better = get_next_better(active_players, [], all_in, dealer)
    hands[hand_id, 'next_better'] = next_better
    hands[hand_id, 'active_players'] = ordered_players
    if community_cards is not None:
        hands[hand_id, 'community_encrypted'] = community_cards
        hands[hand_id, 'community'] = [None, None, None]


def find_winners(ranks: dict, players: list) -> list:
    sorted_rank_values = sorted(ranks.keys(), reverse=True)
    player_set = set(players)
    for rank in sorted_rank_values:
        players_with_rank = ranks[rank]
        intersection = player_set.intersection(set(players_with_rank))
        if len(intersection) > 0:
            # Found players
            winners = list(intersection)
            break
    return winners


def get_next_better(players: list, folded: list, all_in: list, current_better: str) -> str:
    if len(folded) >= len(players) - 1:
        return None # No one needs to bet, only one player left in the hand
    if len(players) == len(all_in):
        return None # No one needs to bet, everyone is all in
    non_folded_players = [p for p in players if p not in folded and p not in all_in]
    if len(non_folded_players) == 1:
        # No need to bet in this case
        return None
    current_index = non_folded_players.index(current_better)    
    #assert current_index >= 0, 'Current better has folded, which does not make sense.'
    return non_folded_players[(current_index + 1) % len(non_folded_players)]


def handle_done_betting(hand_id: str, game_type: int, next_better: str, active_players: list, folded: list, all_in: list, dealer: str, hands: Any) -> str:
    if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
        # multi rounds
        round = hands[hand_id, 'round'] or 0
        round += 1
        hands[hand_id, 'round'] = round
        if round == 4:
            hands[hand_id, 'completed'] = True
        else:
            # Find first available person left of dealer
            dealer_index = active_players.index(dealer)
            for i in range(len(active_players) - 1):
                player = active_players[(dealer_index+i+1)%len(active_players)]
                if player not in folded and player not in all_in:
                    next_better = player
                    break
            hands[hand_id, f'needs_reveal{round}'] = True            
    else:
        hands[hand_id, 'completed'] = True
    return next_better


def assertRevealedOtps(player: str, hand_id: str, hands: Any) -> bool:
    return (hands[hand_id, player, 'pad1'] is not None
        and hands[hand_id, player, 'pad2'] is not None
        and hands[hand_id, player, 'pad3'] is not None)

@export
def bet_check_or_fold(hand_id: str, bet: float, player: str, games: Any, hands: Any):    
    assert hands[hand_id, player, 'player_encrypted_hand'] is not None, 'Hand does not exist'
    assert not hands[hand_id, 'completed'], 'This hand has already completed.'
    assert hands[hand_id, 'next_better'] == player, 'It is not your turn to bet.'

    active_players = hands[hand_id, 'active_players']
    folded = hands[hand_id, 'folded']
    all_in = hands[hand_id, 'all_in']

    call_bet = hands[hand_id, 'current_bet'] or 0
    player_previous_bet  = hands[hand_id, player, 'bet'] or 0
    dealer = hands[hand_id, 'dealer']

    next_better = get_next_better(active_players, folded, all_in, player)

    if next_better is None:
        # No need to bet, this is the end of the hand
        hands[hand_id, 'completed'] = True
    else:
        next_index = active_players.index(next_better)
        current_index = active_players.index(player)
        possible_round_end = next_index < current_index
        
        game_id = hands[hand_id, 'game_id']
        game_type = games[game_id, 'game_type']

        if game_type == OMAHA_POKER or game_type == HOLDEM_POKER:
            # Make sure community cards are revealed
            round = hands[hand_id, 'round']
            if round is not None and round in (TURN, FLOP, RIVER):
                assert not hands[hand_id, f'needs_reveal{round}'], 'Required community cards have not been revealed.'

        next_players_bet = hands[hand_id, next_better, 'bet']
        if bet < 0:
            # Folding
            if game_type == OMAHA_POKER or game_type == HOLDEM_POKER:
                # Make sure they revealed
                assert assertRevealedOtps(player, hand_id, hands), 'Please reveal your portion of the community cards.'
            folded.append(player)
            hands[hand_id, 'folded'] = folded
            if player in all_in:
                all_in.remove(player)
                hands[hand_id, 'all_in'] = all_in
            if len(folded) == len(active_players) - 1:
                hands[hand_id, 'completed'] = True
            current_bet = call_bet
        else:
            if bet == 0:
                # Checking
                max_bet = hands[hand_id, player, 'max_bet']
                if max_bet == player_previous_bet and player not in all_in:
                    all_in.append(player)
                    hands[hand_id, 'all_in'] = all_in
                current_bet = player_previous_bet
            else:
                # Betting
                assert games[game_id, player] >= bet, 'You do not have enough chips to make this bet'
                bet_type = games[game_id, 'bet_type']
                if bet_type == POT_LIMIT:
                    pot = hands[hand_id, 'pot']
                    assert bet <= pot, f'Cannot overbet the pot in pot-limit mode.'
                current_bet = player_previous_bet + bet
                max_bet = hands[hand_id, player, 'max_bet']
                if max_bet == current_bet and player not in all_in:
                    all_in.append(player)
                    hands[hand_id, 'all_in'] = all_in
                hands[hand_id, player, 'bet'] = current_bet
                hands[hand_id, 'current_bet'] = current_bet
                hands[hand_id, 'pot'] += bet
                games[game_id, player] -= bet
            assert max_bet == current_bet or current_bet >= call_bet, 'Current bet is above your bet and you did not go all in.'                    
        if possible_round_end and next_players_bet is not None and next_players_bet == current_bet:            
            next_better = handle_done_betting(hand_id, game_type, next_better, active_players, folded, all_in, dealer, hands)

    hands[hand_id, 'next_better'] = next_better


@export
def reveal_otp(hand_id: str, pad: int, salt: int, index: int, player: str, hands: Any):
    assert index in (FLOP, TURN, RIVER), 'Invalid index.'
    active_players = hands[hand_id, 'active_players']
    assert active_players is not None, 'This hand does not exist.'
    player_index = active_players.index(player)
    assert player_index >= 0, 'You are not in this hand.'
    # verify authenticity of key
    assert hashlib.sha3(f'{pad}:{salt}') == hands[hand_id, player, f'house_encrypted_pad{index}'], 'Invalid key or salt.'
    hands[hand_id, player, f'pad{index}'] = pad


@export
def reveal(hand_id: str, index: int, hands: Any) -> str:
    assert index in (FLOP, TURN, RIVER), 'Invalid index.'
    active_players = hands[hand_id, 'active_players']
    community = hands[hand_id, 'community']
    enc = hands[hand_id, 'community_encrypted'][index-1]
    n_players = len(active_players)
    for i in range(n_players):
        player = active_players[-1-i]
        pad = hands[hand_id, player, f'pad{index}']
        assert pad is not None, f'Player {player} has not revealed their pad.'
        if i != n_players - 1:
            enc = otp.decrypt_hex(
                encrypted_str=enc,
                otp=int(pad),
                safe=False
            )
        else:
            enc = otp.decrypt(
                encrypted_str=enc,
                otp=int(pad),
                safe=False
            )
    community[index-1] = enc
    hands[hand_id, 'community'] = community
    hands[hand_id, f'needs_reveal{index}'] = False
    return enc


@export
def verify_hand(hand_id: str, player_hand_str: str, player: str, games: Any, hands: Any) -> str:
    assert hands[hand_id, 'completed'], 'This hand has not completed yet.'
    folded = hands[hand_id, 'folded']
    assert player not in folded, 'No need to verify your hand because you folded.'
    active_players = hands[hand_id, 'active_players']
    assert player in active_players, 'You are not an active player in this hand.'

    # Check if player has bet enough
    bet_should_equal = hands[hand_id, 'current_bet']
    assert bet_should_equal is not None, 'There is no current bet.'

    player_bet = hands[hand_id, player, 'bet']
    assert player_bet is not None, 'You have not bet yet.'

    assert bet_should_equal == player_bet or player in hands[hand_id, 'all_in'], 'Bets have not stabilized.'

    # For verification purposes
    house_encrypted_hand = hashlib.sha3(player_hand_str)

    previous_house_encrypted_hand = hands[hand_id, player, 'house_encrypted_hand']

    verified = previous_house_encrypted_hand is not None and \
        previous_house_encrypted_hand == house_encrypted_hand

    if not verified:
        # BAD ACTOR NEEDS TO BE PUNISHED
        folded.append(player)
        hands[hand_id, 'folded'] = folded

        return 'Verification failed. Your hand has been forfeited.'

    else:
        cards = player_hand_str.split(':')[0].split(',')

        game_id = hands[hand_id, 'game_id']
        game_type = games[game_id, 'game_type']

        if game_type == BLIND_POKER:
            j = 0
            for p in active_players:
                if p != player:
                    if p not in folded:
                        card = cards[j]
                        rank = evaluator.evaluate([card])
                        if hands[hand_id, p, 'rank'] is None:
                            hands[hand_id, p, 'rank'] = rank
                            hands[hand_id, p, 'hand'] = card
                    j += 1        
        else:
            if game_type == HOLDEM_POKER or game_type == OMAHA_POKER:
                # Add community cards
                community = hands[hand_id, 'community']
                assert community is not None, 'Please reveal the community cards first.'
                assert community[0] is not None and community[1] is not None and community[2] is not None, 'Please reveal all community cards.'
                cards.extend(community[0].split(','))
                cards.extend(community[1:])
            rank = evaluator.evaluate(cards)
            hands[hand_id, player, 'rank'] = rank
            hands[hand_id, player, 'hand'] = cards

        return 'Verification succeeded.'


def calculate_ranks(hand_id: str, players: list, hands: Any) -> dict:
    ranks = {}
    for p in players:
        rank = hands[hand_id, p, 'rank']
        assert rank is not None, f'Player {p} has not verified their hand yet.'
        if rank not in ranks:
            ranks[rank] = []
        ranks[rank].append(p)
    return ranks


@export
def payout_hand(hand_id: str, games: Any, hands: Any):
    pot = hands[hand_id, 'pot']
    assert pot > 0, 'There is no pot to claim!'
    assert not hands[hand_id, 'payed_out'], 'This hand has already been payed out.'
    
    folded = hands[hand_id, 'folded']
    all_in = hands[hand_id, 'all_in']
    active_players = hands[hand_id, 'active_players']

    remaining = [p for p in active_players if p not in folded]
    assert len(remaining) > 0, 'There are no remaining players.'

    payouts = {}

    if len(remaining) == 1:
        # Just pay out, everyone else folded
        payouts[remaining[0]] = pot
    else:
        ranks = calculate_ranks(hand_id, remaining, hands)
        if len(all_in) > 0:
            # Need to calculate split pots
            all_in_map = {}
            for player in all_in:
                # Check all in amount
                amount = hands[hand_id, player, 'max_bet']
                all_in_map[player] = amount
            all_pots = sorted(all_in_map.values())
            unique_pots = []
            for bet in all_pots:
                if bet not in unique_pots:
                    unique_pots.append(bet)
            total_payed_out = 0
            previous_pot_payout = 0
            for bet in unique_pots:
                players_in_pot = []
                for player in remaining:
                    if player not in all_in_map or all_in_map[player] >= bet:
                        players_in_pot.append(player)
                pot_winners = find_winners(ranks, players_in_pot)
                pot_payout = (bet * len(players_in_pot)) - previous_pot_payout
                total_payed_out += pot_payout
                payout = pot_payout / len(pot_winners)
                for winner in pot_winners:
                    if winner not in payouts:
                        payouts[winner] = 0
                    payouts[winner] += payout     
                previous_pot_payout += pot_payout
                      
            remaining_to_payout = pot - total_payed_out
            not_all_in = set(remaining).difference(set(all_in))
            assert remaining_to_payout >= 0, 'Invalid remaining to payout.'
            assert remaining_to_payout == 0 or len(not_all_in) > 0, 'Invalid state when calculating side pots.'            
            if remaining_to_payout > 0:
                if len(not_all_in) == 1:
                    winners = not_all_in
                else:
                    winners = find_winners(ranks, not_all_in)
                payout = remaining_to_payout / len(winners)
                for winner in winners:
                    if winner not in payouts:
                        payouts[winner] = 0
                    payouts[winner] += payout
        else:
            winners = find_winners(ranks, remaining)
            payout = pot / len(winners)
            for winner in winners:
                payouts[winner] = payout

    game_id = hands[hand_id, 'game_id']
    for player, payout in payouts.items():
        games[game_id, player] += payout

    hands[hand_id, 'winners'] = list(payouts.keys())
    hands[hand_id, 'payouts'] = payouts
    hands[hand_id, 'payed_out'] = True


@export
def leave_hand(game_id: str, hand_id: str, player: str, force: bool, hands: Any, games: Any):
    active_players = hands[hand_id, 'active_players'] or []
    if player in active_players:
        if not force:
            dealer = hands[hand_id, 'dealer']
            assert player != dealer, 'Dealer cannot leave hand.'            
        folded = hands[hand_id, 'folded']
        all_in = hands[hand_id, 'all_in']
        next_better = hands[hand_id, 'next_better']
        # Check game type
        game_type = games[game_id, 'game_type']
        if game_type == OMAHA_POKER or game_type == HOLDEM_POKER:
            has_revealed = assertRevealedOtps(player, hand_id, hands)
            if force and not has_revealed:
                # Have to undo the hand :(
                force_undo_hand(game_id, hand_id, hands, games)
            else:
                assert has_revealed, 'Please reveal your portion of the community cards.'
        if next_better == player:
            next_better = get_next_better(active_players, folded, all_in, player)
            hands[hand_id, 'next_better'] = next_better
        if player not in folded:
            folded.append(player)
            hands[hand_id, 'folded'] = folded
        if player in all_in:
            all_in.remove(player)
            hands[hand_id, 'all_in'] = all_in


def force_undo_hand(game_id: str, hand_id: str, hands: Any, games: Any):
    active_players = hands[hand_id, 'active_players'] or []
    hands[hand_id, 'force_undo'] = True
    hands[hand_id, 'completed'] = True
    hands[hand_id, 'payed_out'] = True
    for player in active_players:
        bet = hands[hand_id, player, 'bet'] or 0
        if bet > 0:
            games[game_id, player] += bet