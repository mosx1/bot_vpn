from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class Game:

    def __init__(self, player: int) -> None:

        self.players: set = {player}
        self.board: list = self.create_board()
        self.current_player: str = 'X'
        self.last_move_for: int = player


    def create_board(self) -> list[list[str]]:
        return [[' ' for _ in range(3)] for _ in range(3)]

    def print_board(self) -> str:
        return '\n'.join(['|'.join(row) for row in self.board])

    def check_winner(self):
        # Проверка строк
        for row in self.board:
            if row[0] == row[1] == row[2] != ' ':
                return row[0]
        
        # Проверка столбцов
        for col in range(3):
            if self.board[0][col] == self.board[1][col] == self.board[2][col] != ' ':
                return self.board[0][col]
        
        # Проверка диагоналей
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return self.board[0][2]
        
        # Проверка на ничью
        if all(cell != ' ' for row in self.board for cell in row):
            return 'Draw'
        
        return None

    def create_markup(self) -> InlineKeyboardMarkup:
        markup = InlineKeyboardMarkup()
        for i in range(3):
            row = []
            for j in range(3):
                row.append(InlineKeyboardButton(self.board[i][j], callback_data=f'{i},{j}'))
            markup.row(*row)
        return markup