from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton


class Game:

    def __init__(self, player: int) -> None:

        self.players: set = {player}
        self.player_symbols: dict = {player: 'X'}  # Maps player ID to their symbol
        self.player_nicknames: dict = {}  # Maps player ID to their nickname
        self.board: list = self.create_board()
        self.current_player_symbol: str = 'X'
        self.current_player_id: int = player  # Player 'X' starts first
        self.last_move_for: int = player


    def create_board(self) -> list[list[str]]:
        return [[' ' for _ in range(3)] for _ in range(3)]

    def print_board(self) -> str:
        return '\n'.join(['|'.join(row) for row in self.board])

    def add_player(self, player_id: int) -> None:
        """Add a second player to the game"""
        if len(self.players) < 2 and player_id not in self.players:
            self.players.add(player_id)
            self.player_symbols[player_id] = 'O'  # Second player gets 'O'
            # Current player remains as 'X' (first player) who starts

    def get_player_nickname(self, bot, chat_id: int, player_id: int) -> str:
        """Get player's nickname from Telegram API"""
        try:
            user = bot.get_chat_member(chat_id=chat_id, user_id=player_id)
            if user.user.username:
                return f"@{user.user.username}"
            elif user.user.first_name and user.user.last_name:
                return f"{user.user.first_name} {user.user.last_name}"
            else:
                return f"{user.user.first_name}" if user.user.first_name else f"Player {player_id}"
        except:
            # Fallback if we can't get user info
            return f"Player {player_id}"

    def get_player_by_symbol(self, symbol: str) -> int:
        """Get player ID by their symbol ('X' or 'O')"""
        for player_id, player_symbol in self.player_symbols.items():
            if player_symbol == symbol:
                return player_id
        return None

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