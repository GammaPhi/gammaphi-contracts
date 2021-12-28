
NUM_ROWS = NUM_COLS = 8
NUM_SQUARES = NUM_ROWS * NUM_COLS
INITIAL_BOARD = '                                                                '

OPPOSING = {
    'b': 'w',
    'w': 'b',
}

INITIAL_STATE = {
    'current_player': 'b',
    'board': str(INITIAL_BOARD),
    'creator_team': 'b',
    'opponent_team': 'w',
}

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


@export
def get_initial_state(x: str = None) -> dict:
    return INITIAL_STATE


def opposing_team(team: str) -> str:
    return OPPOSING[team]


def get_adjacent_positions(x: int, y: int) -> list:
    possible = [
        (x - 1, y),
        (x + 1, y),
        (x, y - 1),
        (x, y + 1)
    ]
    return [p for p in possible if valid_coords(p[0], p[1])]
    

def get_connecting_positions(x: int, y: int, board: list) -> set:
    team = board[coords_to_index(x, y)]
    current = [(x, y)]
    visited = set([])
    while len(current) > 0:
        tmp_current = []
        for pos in current:
            visited.add(pos)
            adjacent = get_adjacent_positions(pos[0], pos[1])
            for pos2 in adjacent:
                if pos2 not in visited:
                    if board[coords_to_index(pos2[0], pos2[1])] == team:
                        tmp_current.append(pos2)
        current = tmp_current        
    return visited


def is_encroached(connecting_positions: set, board: list, opponent: str) -> bool:
    for pos in connecting_positions:
        adjacent = get_adjacent_positions(pos[0], pos[1])
        for adj in adjacent:
            if adj not in connecting_positions:
                adj_index = coords_to_index(adj[0], adj[1])
                if board[adj_index] != opponent:
                    return False
    return True


@export
def force_end_round(state: dict, metadata: dict):
    board = list(state['board'])
    
    white_pieces = board.count('w')
    black_pieces = board.count('b')

    if white_pieces == black_pieces:
        # Tie
        winner = None
    elif white_pieces > black_pieces:
        winner = 'w'
    else:
        winner = 'b'

    if winner is None:
        state['stalemate'] = True
    else:
        state['winner'] = winner
        

@export
def move(caller: str, team: str, payload: dict, state: dict, metadata: dict):
    # Assert it's the right player's piece
    x1=payload['x1']
    y1=payload['y1']

    board = list(state['board'])

    index = coords_to_index(x1, y1)
    existing_piece = board[index]

    assert state['current_player'] == team, 'It is not your turn to move.'
    assert existing_piece == ' ', 'This tile has already been placed.'

    opponent = opposing_team(team)
    
    board[index] = team

    # Calculate state
    adjacent_positions = get_adjacent_positions(x1, y1)
    connecting_positions = get_connecting_positions(x1, y1, board)
    assert not is_encroached(connecting_positions, board, opponent), 'Cannot place a piece here. You are encroached.'
    for adjacent_pos in adjacent_positions:
        adjacent_index = coords_to_index(adjacent_pos[0], adjacent_pos[1])
        if board[adjacent_index] == opponent:
            # Check if we encroached them
            opponent_connected_positions = get_connecting_positions(adjacent_pos[0], adjacent_pos[1], board)
            if is_encroached(opponent_connected_positions, board, team):
                for encroached_pos in opponent_connected_positions:
                    encroached_index = coords_to_index(encroached_pos[0], encroached_pos[1])
                    board[encroached_index] = ' '

    board = ''.join(board)
    state['current_player'] = opponent
    state['board'] = board            
