# con_checkers_v1

NUM_ROWS = NUM_COLS = 8
NUM_SQUARES = NUM_ROWS * NUM_COLS
INITIAL_BOARD = ' b b b bb b b b  b b b b                w w w w  w w w ww w w w '

assert len(INITIAL_BOARD) == NUM_SQUARES, 'Invalid initial board.'


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


MOVE_VECTORS = {
    'b': [(1, 1), (1, -1)],
    'w': [(-1, 1), (-1, -1)],
    'B': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
    'W': [(-1, -1), (-1, 1), (1, -1), (1, 1)],
}

JUMP_VECTORS = {
    'b': [(2, 2), (2, -2)],
    'w': [(-2, 2), (-2, -2)],
    'B': [(-2, -2), (-2, 2), (2, -2), (2, 2)],
    'W': [(-2, -2), (-2, 2), (2, -2), (2, 2)],
}

OPPOSING = {
    'b': 'w',
    'B': 'w',
    'w': 'b',
    'W': 'b'
}

INITIAL_STATE = {
    'current_player': 'b',
    'board': str(INITIAL_BOARD),
    'creator_team': 'b',
    'opponent_team': 'w',
}


@export
def get_initial_state(x: str = None) -> dict:
    return INITIAL_STATE


def opposing_team(team: str) -> str:
    return OPPOSING[team.lower()]


def check_for_jumps(board: str, team: str) -> bool:
    has_jumps = False
    opponent = opposing_team(team)
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            piece = board[row*NUM_ROWS+col]
            if piece.lower() == team:
                for valid_jump in JUMP_VECTORS[piece]:
                    next_x = row + valid_jump[0]
                    next_y = col + valid_jump[1]                    
                    if valid_coords(next_x, next_y) and board[coords_to_index(next_x, next_y)] == ' ':                        
                        # Check if opponent piece is in between
                        inbetween_x = row + valid_jump[0] // 2
                        inbetween_y = col + valid_jump[1] // 2
                        inbetween_index = coords_to_index(inbetween_x, inbetween_y)
                        if board[inbetween_index].lower() == opponent:
                            has_jumps = True
                            break
            if has_jumps:
                break
        if has_jumps:
            break
    return has_jumps


def check_for_moves(board: str, team: str) -> bool:
    has_moves = False
    for row in range(NUM_ROWS):
        for col in range(NUM_COLS):
            piece = board[row*NUM_ROWS+col]
            if piece.lower() == team:
                for valid_move in MOVE_VECTORS[piece]:
                    next_x = row + valid_move[0]
                    next_y = col + valid_move[1]                    
                    if valid_coords(next_x, next_y) and board[coords_to_index(next_x, next_y)] == ' ':                        
                        # Check if opponent piece is in between
                        has_moves = True
                        break
            if has_moves:
                break
        if has_moves:
            break
    return has_moves


@export
def force_end_round(state: dict, metadata: dict):
    if state.get('winner') is None:
        state['stalemate'] = True


@export
def move(caller: str, team: str, payload: dict, state: dict, metadata: dict):
    
    x1=payload['x1']
    y1=payload['y1']
    x2=payload['x2']
    y2=payload['y2']
    
    board = list(state['board'])
    curr_x = x1
    curr_y = y1
    curr_index = coords_to_index(x1, y1)
    curr_piece = board[curr_index]
    assert state['current_player'] == team, 'It is not your turn to move.'
    assert curr_piece.lower() == team, 'This is not your piece to move.'
    opponent = opposing_team(team)
    valid_moves = MOVE_VECTORS[curr_piece]
    valid_jumps = JUMP_VECTORS[curr_piece]
    for i in range(len(x2)):
        next_x = x2[i]
        next_y = y2[i]
        next_vector = (next_x - curr_x, next_y - curr_y)
        next_index = coords_to_index(next_x, next_y)
        if next_vector in valid_jumps and board[next_index] == ' ':
            # Check there is an opposing piece
            inbetween_x = curr_x + next_vector[0] // 2
            inbetween_y = curr_y + next_vector[1] // 2
            inbetween_index = coords_to_index(inbetween_x, inbetween_y)
            assert board[inbetween_index].lower() == opponent, 'You cannot jump this square.'
            board[inbetween_index] = ' '
            board[curr_index] = ' '
            board[next_index] = curr_piece            
        elif next_vector in valid_moves and board[next_index] == ' ':
            # Check for jumps
            assert not check_for_jumps(board, team), 'Must perform jump.'
            # Simple move
            board[next_index] = curr_piece
            board[curr_index] = ' '
        else:
            assert False, 'Invalid move.'

        # Check for kings
        if team == 'b' and next_x == NUM_ROWS - 1:
            if curr_piece == curr_piece.lower():
                assert i == len(x2) -1, 'Cannot make a move after promoting to a king.'
                board[next_index] = board[next_index].upper()
        elif team == 'w' and next_x == 0:
            if curr_piece == curr_piece.lower():
                assert i == len(x2) -1, 'Cannot make a move after promoting to a king.'
                board[next_index] = board[next_index].upper()
        curr_x = next_x
        curr_y = next_y
        curr_index = next_index

    opponent_has_jumps = check_for_jumps(board, opponent)
    opponent_has_moves = check_for_moves(board, opponent)

    board = ''.join(board)
    state['current_player'] = opponent
    state['board'] = board

    if not opponent_has_jumps and not opponent_has_moves:
        state['winner'] = team
            
