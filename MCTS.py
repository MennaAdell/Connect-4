import random
import math
import copy

ROWS, COLS = 6, 7
PLAYERS = ["You", "AI Bot"]

def other(player):
    return PLAYERS[1] if player == PLAYERS[0] else PLAYERS[0]

class GameState:
    def __init__(self, board, current_player):
        self.board = [row[:] for row in board]
        self.current_player = current_player

    def clone(self):
        return GameState(self.board, self.current_player)

    def get_legal_moves(self):
        moves = []
        for c in range(COLS):
            if self.board[0][c] == "":
                moves.append(c)
        return moves

    def get_lowest_empty_row(self, col):
        for r in range(ROWS-1, -1, -1):
            if self.board[r][col] == "":
                return r
        return None

    def do_move(self, col):
        r = self.get_lowest_empty_row(col)
        if r is None:
            raise ValueError("Invalid move")
        self.board[r][col] = self.current_player
        self.current_player = other(self.current_player)
        return r, col

    def get_winner(self):
        # Rows
        for r in range(ROWS):
            for c in range(COLS-3):
                v = self.board[r][c]
                if v and all(self.board[r][c+i] == v for i in range(4)):
                    return v
        # Cols
        for c in range(COLS):
            for r in range(ROWS-3):
                v = self.board[r][c]
                if v and all(self.board[r+i][c] == v for i in range(4)):
                    return v
        # Diagonal \
        for r in range(ROWS-3):
            for c in range(COLS-3):
                v = self.board[r][c]
                if v and all(self.board[r+i][c+i] == v for i in range(4)):
                    return v
        # Diagonal /
        for r in range(3, ROWS):
            for c in range(COLS-3):
                v = self.board[r][c]
                if v and all(self.board[r-i][c+i] == v for i in range(4)):
                    return v
        # Draw
        if all(self.board[r][c] != "" for r in range(ROWS) for c in range(COLS)):
            return "Draw"
        return None

    def rollout_policy(self, legal_moves):
        return random.choice(legal_moves)

class Node:
    def __init__(self, state, parent=None, move=None):
        self.state = state
        self.parent = parent
        self.move = move
        self.children = []
        self._untried_moves = None
        self.visits = 0
        self.wins = 0.0

    def untried_moves(self):
        if self._untried_moves is None:
            self._untried_moves = self.state.get_legal_moves()
        return self._untried_moves

    def expand(self):
        moves = self.untried_moves()
        if not moves:
            return None
        m = moves.pop(random.randrange(len(moves)))
        next_state = self.state.clone()
        next_state.do_move(m)
        child = Node(next_state, parent=self, move=m)
        self.children.append(child)
        return child

    def q(self):
        return self.wins

    def n(self):
        return self.visits

    def best_child(self, c_param=1.4):
        choices_weights = [
            (child.q() / child.n()) + c_param * math.sqrt(2 * math.log(self.n()) / child.n())
            for child in self.children
        ]
        return self.children[choices_weights.index(max(choices_weights))]

    def most_visited_child(self):
        return max(self.children, key=lambda c: c.n()) if self.children else None

class MCTS:
    def __init__(self, time_limit=None, iter_limit=800, c_param=1.4):
        self.time_limit = time_limit
        self.iter_limit = iter_limit
        self.c_param = c_param

    def _rollout(self, state: GameState):
        current = state.clone()
        while True:
            winner = current.get_winner()
            if winner is not None:
                return winner
            moves = current.get_legal_moves()
            if not moves:
                return "Draw"
            m = current.rollout_policy(moves)
            current.do_move(m)

    def _backpropagate(self, node: Node, result):
        while node is not None:
            node.visits += 1
            player_who_played = other(node.state.current_player)
            if result == "Draw":
                node.wins += 0.5
            elif result == player_who_played:
                node.wins += 1.0
            node = node.parent

    def search(self, initial_state: GameState):
        root = Node(initial_state.clone())
        if root.state.get_winner() is not None:
            return None

        iterations = 0
        import time
        start_time = time.time()
        while True:
            if self.time_limit and time.time() - start_time >= self.time_limit:
                break
            elif not self.time_limit and iterations >= self.iter_limit:
                break

            node = root
            while node.untried_moves() == [] and node.children:
                node = node.best_child(self.c_param)

            if node.untried_moves():
                node = node.expand()

            result = self._rollout(node.state)
            self._backpropagate(node, result)
            iterations += 1

        best = root.most_visited_child()
        return best.move if best else random.choice(initial_state.get_legal_moves())