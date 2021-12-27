NUM_ROWS = NUM_COLS = 8
NUM_SQUARES = NUM_ROWS * NUM_COLS
INITIAL_BOARD = 'rnbqkbnrpppppppp                                PPPPPPPPRNBQKBNR'


# Setup vectors
white_pawn_attack_vectors = [(-1, 1), (-1, -1)]
white_pawn_first_vectors = [(-1, 0), (-2, 0)]
white_pawn_default_vectors = [(-1, 0)]

black_pawn_attack_vectors = [(1, 1), (1, -1)]
black_pawn_first_vectors = [(1, 0), (2, 0)]
black_pawn_default_vectors = [(1, 0)]

king_vectors = [(-1, -1), (1, -1), (-1, 0), (0, -1), (1, 0), (0, 1), (-1, 1), (1, 1)]
knight_vectors = [(1, 2), (2, 1), (-1, 2), (2, -1), (1, -2), (-2, 1), (-2, -1), (-1, -2)]
rook_vectors = [(1, 0), (-1, 0), (0, 1), (0, -1)]
bishop_vectors = [(-1, -1), (-1, 1), (1, -1), (1, 1)]
queen_vectors = rook_vectors + bishop_vectors


assert len(INITIAL_BOARD) == NUM_SQUARES, 'Invalid initial board.'


INITIAL_STATE = {
    'current_player': 'w',
    'board': str(INITIAL_BOARD)
}


@export
def get_initial_state(x: str = None) -> dict:
    return INITIAL_STATE


# Utility
def is_white_piece(piece: str) -> bool:
    return piece.isupper()


def is_black_piece(piece: str) -> bool:
    return piece.islower()


def coords_to_index(x: int, y: int) -> int:
    assert valid_coords(x, y), 'Invalid (x, y): ({}, {})'.format(x, y)
    return x * NUM_ROWS + y


def index_to_coords(index: int) -> tuple:
    assert valid_index(index), 'Invalid index: {}'.format(index)
    x = index // NUM_ROWS
    y = index % NUM_ROWS
    return (x, y)


def valid_index(index: int) -> bool:
    return index >= 0 and index < NUM_SQUARES


def valid_coords(x: int, y: int) -> bool:
    return x >= 0 and x < NUM_ROWS and y >= 0 and y < NUM_COLS


def find_coords_for_white_king(board: str) -> tuple:
    return index_to_coords(board.index('K'))


def find_coords_for_black_king(board: str) -> tuple:
    return index_to_coords(board.index('k'))

    
def get_attack_maps(board: str, white_only: bool = False, black_only: bool = False) -> set:
    white_moves_per_piece = {}
    black_moves_per_piece = {}
    white_attack_map = {}
    black_attack_map = {}
    white_move_map = {}
    black_move_map = {}
    for i in range(len(board)):
        piece = board[i]
        if piece == ' ':
            continue
        x, y = index_to_coords(i)
        check_path = False        
        if is_white_piece(piece):
            if black_only:
                continue
            attack_set = white_attack_map
            move_set = white_move_map
            moves_per_piece = white_moves_per_piece
            pawn_attack_vectors = white_pawn_attack_vectors
            if x == 6:
                pawn_move_vectors = white_pawn_first_vectors
            else:
                pawn_move_vectors = white_pawn_default_vectors
        else:
            if white_only:
                continue
            attack_set = black_attack_map
            move_set = black_move_map
            moves_per_piece = black_moves_per_piece
            pawn_attack_vectors = black_pawn_attack_vectors
            if x == 1:
                pawn_move_vectors = black_pawn_first_vectors
            else:
                pawn_move_vectors = black_pawn_default_vectors
        piece = piece.upper()
        move_vectors = None
        if piece == 'P':
            vectors = pawn_attack_vectors
            move_vectors = pawn_move_vectors
        elif piece == 'N':
            vectors = knight_vectors
        elif piece == 'B':
            vectors = bishop_vectors
            check_path = True
        elif piece == 'R':
            vectors = rook_vectors
            check_path = True
        elif piece == 'Q':
            vectors = queen_vectors
            check_path = True
        elif piece == 'K':
            vectors = king_vectors
        else:
            assert False, f'Invalid piece: {piece}'
        valid_moves = []
        for vector in vectors:
            pos = (vector[0] + x, vector[1] + y)
            if valid_coords(pos[0], pos[1]):
                if pos not in attack_set:
                    attack_set[pos] = []
                attack_set[pos].append(i)
                if move_vectors is None:
                    if pos not in move_set:
                        move_set[pos] = []
                    move_set[pos].append(i)
                valid_moves.append(pos)
                if check_path: # make sure no pieces blocking
                    valid = True
                    while valid:
                        pos_idx = coords_to_index(pos[0], pos[1])
                        if board[pos_idx] == ' ':
                            pos = (pos[0] + vector[0], pos[1] + vector[1])                            
                            valid = valid_coords(pos[0], pos[1])
                            if valid:
                                if pos not in attack_set:
                                    attack_set[pos] = []
                                attack_set[pos].append(i)
                                if move_vectors is None:
                                    if pos not in move_set:
                                        move_set[pos] = []
                                    move_set[pos].append(i)
                                valid_moves.append(pos)
                        else:
                            valid = False
        if move_vectors is not None:
            for vector in vectors:
                pos = (vector[0] + x, vector[1] + y)
                if valid_coords(pos[0], pos[1]):
                    if pos not in move_set:
                        move_set[pos] = []
                    move_set[pos].append(i)
                    valid_moves.append(pos)
        if len(valid_moves) > 0:
            moves_per_piece[i] = valid_moves
    return white_attack_map, black_attack_map, white_move_map, black_move_map, white_moves_per_piece, black_moves_per_piece


def get_intermediary_path(x1: int, y1: int, x2: int, y2: int) -> list:
    vector = (x2 - x1, y2 - y1)
    if vector[0] > 0 and vector[1] > 0:
        assert vector[0] == vector[1], 'Invalid vector'
        return [(x1 + i, y1 + i) for i in range(1, vector[0])]
    elif vector[0] > 0 and vector[1] == 0:
        return [(x1 + i, y1) for i in range(1, vector[0])]
    elif vector[0] == 0 and vector[1] > 0:
        return [(x1, y1 + i) for i in range(1, vector[1])]
    elif vector[0] < 0 and vector[1] < 0:
        assert vector[0] == vector[1], 'Invalid vector'
        return [(x1 - i, y1 - i) for i in range(1, -vector[0])]
    elif vector[0] < 0 and vector[1] > 0:
        assert vector[0] == -vector[1], 'Invalid vector'
        return [(x1 - i, y1 + i) for i in range(1, vector[1])]
    elif vector[0] > 0 and vector[1] < 0:
        assert vector[0] == -vector[1], 'Invalid vector'
        return [(x1 + i, y1 - i) for i in range(1, vector[0])]
    elif vector[0] < 0 and vector[1] == 0:
        return [(x1 - i, y1) for i in range(1, -vector[0])]
    elif vector[0] == 0 and vector[1] < 0:
        return [(x1, y1 - i) for i in range(1, -vector[1])]
    else:
        assert False, 'Not a valid vector.'


def is_white_king_in_check(board: str, black_attack_map: dict) -> bool:
    king_x, king_y = find_coords_for_white_king(board)
    return (king_x, king_y) in black_attack_map


def is_white_king_in_check_mate(board: list, 
                                white_move_map: dict,
                                white_attack_map: dict,
                                black_attack_map: dict,
                                ) -> bool:
    king_x, king_y = find_coords_for_white_king(board)
    pieces_causing_check = black_attack_map.get((king_x, king_y))
    # See if we are in check
    if pieces_causing_check is not None and len(pieces_causing_check) > 0:
        # Check king's ability to move away
        for x, y in king_vectors:
            n_king_x = king_x + x
            n_king_y = king_y + y
            if valid_coords(n_king_x, n_king_y):
                other_piece = board[coords_to_index(n_king_x, n_king_y)]
                if (other_piece == ' '
                    or is_black_piece(other_piece)) \
                   and (n_king_x, n_king_y) not in black_attack_map:
                    return False # Can move
        if len(pieces_causing_check) == 1:
            # Single check
            checker_index = pieces_causing_check[0]
            checker_x, checker_y = index_to_coords(checker_index)
            defenders = white_attack_map.get((checker_x, checker_y))            
            # Can this piece be attacked?
            if defenders is not None:
                for defender in defenders:
                    # simulate taking this piece
                    new_board = board.copy()
                    new_board[checker_index] = board[defender]
                    new_board[defender] = ' '
                    n0, new_black_attack_map, n2, n3, n4, n5 \
                        = get_attack_maps(new_board, black_only=True)
                    if not is_white_king_in_check(new_board, new_black_attack_map):
                        return False
            checker_piece = board[checker_index]
            if checker_piece.upper() in ('R', 'B', 'Q'):
                intermediate_path = get_intermediary_path(king_x, king_y, checker_x, checker_y)
                for pos in intermediate_path:
                    # Can we block this?
                    pos_index = coords_to_index(pos[0], pos[1])
                    defenders = white_move_map.get(pos)            
                    if defenders is not None:
                        for defender in defenders:
                            # simulate taking this piece
                            new_board = board.copy()
                            new_board[pos_index] = board[defender]
                            new_board[defender] = ' '
                            n0, new_black_attack_map, n2, n3, n4, n5 \
                                = get_attack_maps(new_board, black_only=True)
                            if not is_white_king_in_check(new_board, new_black_attack_map):
                                return False
        return True
    return False


def is_white_king_in_stale_mate(board: list, white_moves_per_piece: dict, black_attack_map: dict) -> bool:
    king_x, king_y = find_coords_for_white_king(board)
    if (king_x, king_y) not in black_attack_map: # Not in check
        return len(white_moves_per_piece) == 0 # No valid moves
    return False


def is_black_king_in_check(board: list, white_attack_map: dict) -> bool:
    king_x, king_y = find_coords_for_black_king(board)
    return (king_x, king_y) in white_attack_map


def is_black_king_in_check_mate(board: list, 
                                black_move_map: dict,
                                black_attack_map: dict,
                                white_attack_map: dict,
                                ) -> bool:
    king_x, king_y = find_coords_for_black_king(board)
    pieces_causing_check = white_attack_map.get((king_x, king_y))
    # See if we are in check
    if pieces_causing_check is not None and len(pieces_causing_check) > 0:
        # Check king's ability to move away
        for x, y in king_vectors:
            n_king_x = king_x + x
            n_king_y = king_y + y
            if valid_coords(n_king_x, n_king_y):
                other_piece = board[coords_to_index(n_king_x, n_king_y)]
                if (other_piece == ' '
                    or is_white_piece(other_piece)) \
                   and (n_king_x, n_king_y) not in white_attack_map:
                    return False # Can move
        if len(pieces_causing_check) == 1:
            # Single check
            checker_index = pieces_causing_check[0]
            checker_x, checker_y = index_to_coords(checker_index)
            defenders = black_attack_map.get((checker_x, checker_y))            
            # Can this piece be attacked?
            if defenders is not None:
                for defender in defenders:
                    # simulate taking this piece
                    new_board = board.copy()
                    new_board[checker_index] = board[defender]
                    new_board[defender] = ' '
                    new_white_attack_map, n1, n2, n3, n4, n5 \
                        = get_attack_maps(new_board, white_only=True)
                    if not is_black_king_in_check(new_board, new_white_attack_map):
                        return False
            checker_piece = board[checker_index]
            if checker_piece.upper() in ('R', 'B', 'Q'):
                intermediate_path = get_intermediary_path(king_x, king_y, checker_x, checker_y)
                for pos in intermediate_path:
                    # Can we block this?
                    pos_index = coords_to_index(pos[0], pos[1])
                    defenders = black_move_map.get(pos)            
                    if defenders is not None:
                        for defender in defenders:
                            # simulate taking this piece
                            new_board = board.copy()
                            new_board[pos_index] = board[defender]
                            new_board[defender] = ' '
                            new_white_attack_map, n1, n2, n3, n4, n5 \
                                = get_attack_maps(new_board, white_only=True)
                            if not is_black_king_in_check(new_board, new_white_attack_map):
                                return False
        return True
    return False
    

def is_black_king_in_stale_mate(board: list, black_moves_per_piece: dict, white_attack_map: dict) -> bool:
    king_x, king_y = find_coords_for_black_king(board)
    if (king_x, king_y) not in white_attack_map: # Not in check
        return len(black_moves_per_piece) == 0 # No valid moves
    return False


def opposing_team(team: str):
    if team == 'w':
        return 'b'
    elif team == 'b':
        return 'w'
    else:
        assert False, f'Invalid team: {team}.'


@export
def move(caller: str, team: str, x1: int, y1: int, x2: int, y2: int, state: Any) -> int:
    # Assert it's the right player's piece
    board = list(state['board'])

    curr_index = coords_to_index(x1, y1)
    curr_piece = board[curr_index]

    assert state['current_player'] == team, 'It is not your turn to move.'
    if team == 'w':
        assert is_white_piece(curr_piece), 'This is not your piece to move.'
    else:
        assert team == 'b', f'Invalid team: {team}'
        assert is_black_piece(curr_piece), 'This is not your piece to move.'

    opponent = opposing_team(team)

    piece_upper = curr_piece.upper()
    check_path = False
    attack_vectors = None
    is_castle_attempt = False
    if piece_upper == 'P':
        if team == 'b':
            if x1 == 1:
                vectors = black_pawn_first_vectors
            else:
                vectors = black_pawn_default_vectors
            attack_vectors = black_pawn_attack_vectors
        else:
            if x1 == 6:
                vectors = white_pawn_first_vectors
            else:
                vectors = white_pawn_default_vectors
            attack_vectors = white_pawn_attack_vectors
    elif piece_upper == 'N':
        vectors = knight_vectors
    elif piece_upper == 'B':
        vectors = bishop_vectors
        check_path = True
    elif piece_upper == 'R':
        vectors = rook_vectors
        check_path = True
    elif piece_upper == 'Q':
        vectors = queen_vectors
        check_path = True
    elif piece_upper == 'K':
        # check if castle
        if is_white_piece(curr_piece):
            if x1 == 7 and x2 == 7:
                if y1 == 4 and y2 in (6, 2):
                    is_castle_attempt = True
        else:
            if x1 == 0 and x2 == 0:
                if y1 == 4 and y2 in (6, 2):
                    is_castle_attempt = True                    
        vectors = king_vectors
    else:
        assert False, f'Invalid piece: {curr_piece}'

    attack_vectors = attack_vectors or vectors
    next_vector = (x2 - x1, y2 - y1)
    next_index = coords_to_index(x2, y2)
    state[f'{team}_en_passant'] = None

    if valid_index(next_index):
        if check_path:
            valid = False
            vector_to_use = None
            for vector in vectors:
                if vector[0] == 0:
                    valid = next_vector[0] == 0 and next_vector[1] // vector[1] >= 1
                elif vector[1] == 0:
                    valid = next_vector[1] == 0 and next_vector[0] // vector[0] >= 1
                else:
                    valid = next_vector[0] // vector[0] >= 1 and next_vector[1] // vector[1] >= 1
                if valid:
                    vector_to_use = vector
                    break
            assert valid, f'Invalid move with {curr_piece}.'
            intermediate_pos = (x1 + vector_to_use[0], y1 + vector_to_use[1])            
            while True:
                intermediate_index = coords_to_index(intermediate_pos[0], intermediate_pos[1])
                if intermediate_index != next_index:
                    assert board[intermediate_index] == ' ', 'Invalid move. Another piece is in the way.'
                    intermediate_pos = (intermediate_pos[0] + vector_to_use[0], intermediate_pos[1] + vector_to_use[1])
                else:
                    break
        else:
            if is_castle_attempt:
                assert not state.get(f'{team}_moved_king'), 'King has already moved.'
                if team == 'w':
                    l0, opponent_attack_map, \
                    l0, l0, \
                    l0, l0 \
                        = get_attack_maps(board, black_only=True)
                else:
                    opponent_attack_map, l0, \
                    l0, l0, \
                    l0, l0 \
                        = get_attack_maps(board, black_only=True)
                assert (x1, y1) not in opponent_attack_map, 'You cannot castle out of check.'
                if y2 == 6:
                    assert not state.get(f'{team}_moved_rook7'), 'Rook has already moved.'
                    for ny in [5, 6]:
                        n_index = coords_to_index(x1, ny)
                        assert board[n_index] == ' ', 'Pieces are in the way of castling.'
                        assert (x1, ny) not in opponent_attack_map, 'You cannot castle through check.'
                    rook_idx = coords_to_index(x1, 7)
                    rook_to_idx = coords_to_index(x1, 5)
                else:
                    # y2 == 2
                    assert not state.get(f'{team}_moved_rook0'), 'Rook has already moved.'
                    for ny in [1, 2, 3]:
                        n_index = coords_to_index(x1, ny)
                        assert board[n_index] == ' ', 'Pieces are in the way of castling.'
                        assert (x1, ny) not in opponent_attack_map, 'You cannot castle through check.'                    
                    rook_idx = coords_to_index(x1, 0)
                    rook_to_idx = coords_to_index(x1, 3)
                board[rook_to_idx] = board[rook_idx]
                board[rook_idx] = ' '

            elif piece_upper != 'P': 
                # Handle pawns separately
                assert next_vector in vectors, 'Invalid move. Not a valid move for this piece.'

        next_space = board[next_index]
        if next_space != ' ':
            if team == 'b':
                assert is_white_piece(next_space), 'You cannot take your own piece.'
            else:
                assert is_black_piece(next_space), 'You cannot take your own piece.'

            # Handle pawns
            if piece_upper == 'P':
                assert next_vector in attack_vectors, 'Invalid pawn attack.'
        else:
            if piece_upper == 'P':
                # Check en passant
                en_passant = state.get(f'{opponent}_en_passant')
                valid_en_passant = False
                if en_passant is not None:
                    if en_passant[0] == (x1, y1) or en_passant[1] == (x1, y1):
                        if en_passant[2] == (x2, y2):
                            valid_en_passant = True
                            en_passant_index = coords_to_index(en_passant[3][0], en_passant[3][1])
                            board[en_passant_index] = ' '
                assert valid_en_passant or next_vector in vectors, 'Invalid pawn move.'
                if next_vector[0] == 2 or next_vector[0] == -2:
                    # En passant possible next round
                    en_passant = [(x2, y2-1), (x2, y2+1), (x1 + next_vector[0]//2, y2), (x2, y2)]
                    state[f'{team}_en_passant'] = en_passant

        # Just move
        board[curr_index] = ' '
        board[next_index] = curr_piece
        if piece_upper == 'K':
            state[f'{team}_moved_king'] = True
        elif piece_upper == 'R':
            if y1 == 0:
                state[f'{team}_moved_rook0'] = True
            elif y1 == 7:
                state[f'{team}_moved_rook7'] = True
    else:
        assert False, 'Invalid move. Piece is not on the board.'

    # Check for pawn promotion and check
    if team == 'b':
        if x2 == NUM_ROWS - 1 and curr_piece == 'p':
            board[next_index] = 'q'
    else:
        if x2 == 0 and curr_piece == 'P':
            board[next_index] = 'Q'

    white_attack_map, black_attack_map, \
        white_move_map, black_move_map, \
        white_moves_per_piece, black_moves_per_piece \
         = get_attack_maps(board)

    checkmate = False
    stalemate = False
    if team == 'b':
        assert not is_black_king_in_check(board, white_attack_map), 'This move puts you in check.'
        opponent_in_check = is_white_king_in_check(board, black_attack_map)
        state['w_in_check'] = opponent_in_check
        if opponent_in_check:
            checkmate = is_white_king_in_check_mate(
                board=board,
                white_attack_map=white_attack_map,
                white_move_map=white_move_map,
                black_attack_map=black_attack_map
            )
        else:
            stalemate = is_white_king_in_stale_mate(
                board=board,
                white_moves_per_piece=white_moves_per_piece,
                black_attack_map=black_attack_map)
    else:
        assert not is_white_king_in_check(board, black_attack_map), 'This move puts you in check.'
        opponent_in_check = is_black_king_in_check(board, white_attack_map)
        state['b_in_check'] = opponent_in_check
        if opponent_in_check:
            checkmate = is_black_king_in_check_mate(
                board=board, 
                black_attack_map=black_attack_map,
                black_move_map=black_move_map,
                white_attack_map=white_attack_map
            )
        else:
            stalemate = is_black_king_in_stale_mate(
                board=board, 
                black_moves_per_piece=black_moves_per_piece,
                white_attack_map=white_attack_map
            )

    board = ''.join(board)
    state['current_player'] = opponent
    state['board'] = board

    if stalemate:
        state['stalemate'] = True
    elif checkmate:
        state['winner'] = team
        wager = state.get('wager', 0)
        is_creator = state['creator'] == caller
        creator_wins = state.get('creator_wins', 0)
        opponent_wins = state.get('opponent_wins', 0)
        if is_creator:
            creator_wins += 1
        else:
            opponent_wins += 1
        state['creator_wins'] = creator_wins
        state['opponent_wins'] = opponent_wins
        rounds = state.get('rounds', 1)
        if creator_wins > rounds // 2 or opponent_wins > rounds // 2:
            state['completed'] = True
            if wager > 0:
                return 2*wager
    return 0