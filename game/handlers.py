from telebot import TeleBot
from telebot.types import Message, CallbackQuery
from telebot.storage import StateMemoryStorage

from game.states import GameStates
from game.game import Game

from enums.chat_types import ChatTypes


def register_handlers(bot: TeleBot, storage: StateMemoryStorage) -> None:

    @bot.message_handler(
        commands=['game'],
        chat_types=[ChatTypes.private.value]
    )
    def _(message: Message) -> None:
        bot.reply_to(
            message,
            'Начать игру можно только в групповом чате.'
        )

    @bot.message_handler(
        commands=['game'],
        chat_types=[
            ChatTypes.group.value,
            ChatTypes.supergroup.value
        ]
    )
    def new_game(message: Message) -> None:

        bot.set_state(
            message.from_user.id,
            GameStates.in_game,
            message.chat.id
        )

        with bot.retrieve_data(
            message.from_user.id,
            message.chat.id
        ) as data:

            game_message: Message = bot.send_message(
                message.chat.id,
                'Загрузка...'
            )

            data['games'] = {game_message.id: Game(message.from_user.id)}
            game: Game = data['games'][game_message.id]

            # Get player nicknames
            player_x_nickname = game.get_player_nickname(bot, message.chat.id, message.from_user.id)

            bot.edit_message_text(
                chat_id=game_message.chat.id,
                message_id=game_message.id,
                text=f"Крестики: {player_x_nickname}\nНолики: Ожидание соперника\n\nХод: {player_x_nickname}\n{game.print_board()}",
                reply_markup=game.create_markup()
            )
    

    @bot.callback_query_handler(func=lambda call: not str(call.data).startswith('{"key":'))
    def handle_move(call: CallbackQuery) -> None:

        storage_data: dict = storage.data.copy()

        for key, value in storage_data.items():
            if 'data' in value:
                if 'games' in value['data']:
                    if call.message.id in value['data']['games']:

                        storage_data: list[str] = str(key).split(':')
                        storage_user_id = int(storage_data[3])
                        storage_chat_id = int(storage_data[2])

                        with bot.retrieve_data(
                            storage_user_id,
                            storage_chat_id
                        ) as data:
                            if 'games' in data:
                                if call.message.id in data['games']:

                                    game: Game = data['games'][call.message.id]

                                    if call.from_user.id in game.players and len(game.players) == 1:
                                        bot.answer_callback_query(
                                            call.id,
                                            'Ожидайте первого хода соперника.'
                                        )
                                        return

                                    if call.from_user.id not in game.players and len(game.players) == 1:

                                        game.add_player(call.from_user.id)

                                        bot.set_state(
                                            call.from_user.id,
                                            GameStates.in_game,
                                            call.message.chat.id
                                        )
                                        with bot.retrieve_data(
                                            call.from_user.id,
                                            call.message.chat.id
                                        ) as data:

                                            data['games'] = {call.message.id: game}

                                        # Update game message to show both players
                                        player_x_id = game.get_player_by_symbol('X')
                                        player_o_id = game.get_player_by_symbol('O')

                                        player_x_nickname = game.get_player_nickname(bot, call.message.chat.id, player_x_id)
                                        player_o_nickname = game.get_player_nickname(bot, call.message.chat.id, player_o_id)

                                        current_player_nickname = player_x_nickname if game.current_player_symbol == 'X' else player_o_nickname

                                        bot.edit_message_text(
                                            chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f"Крестики: {player_x_nickname}\nНолики: {player_o_nickname}\n\nХод: {current_player_nickname}\n{game.print_board()}",
                                            reply_markup=game.create_markup()
                                        )
                                        return

                                    if call.from_user.id not in game.players and len(game.players) == 2:
                                        bot.answer_callback_query(
                                            call.id,
                                            "Вы не можете войти в данную игру. Для создания своей нажмите /game"
                                        )
                                        return

                                    if call.from_user.id == game.last_move_for:
                                        bot.answer_callback_query(
                                            call.id,
                                            "Ожидайте ход соперника"
                                        )
                                        return
                                    i, j = map(int, call.data.split(','))

                                    if game.board[i][j] != ' ':
                                        bot.answer_callback_query(call.id, "Эта клетка уже занята!")
                                        return

                                    game.board[i][j] = game.current_player_symbol
                                    winner = game.check_winner()

                                    if winner:
                                        if winner == 'Draw':
                                            text = "Ничья!"
                                        else:
                                            # Get winner's nickname
                                            winner_id = game.get_player_by_symbol(winner)
                                            winner_nickname = game.get_player_nickname(bot, call.message.chat.id, winner_id)
                                            text = f"Победитель: {winner_nickname}!"
                                        bot.edit_message_text(
                                            chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f"{text}\n{game.print_board()}",
                                            reply_markup=None  # Remove buttons after game ends
                                        )
                                        user_ids: set = game.players

                                        for user_id in user_ids:
                                            bot.delete_state(
                                                user_id,
                                                call.message.chat.id
                                            )
                                    else:
                                        # Switch to next player
                                        game.current_player_symbol = 'O' if game.current_player_symbol == 'X' else 'X'
                                        game.current_player_id = game.get_player_by_symbol(game.current_player_symbol)
                                        game.last_move_for = call.from_user.id

                                        # Update message with current player's nickname
                                        player_x_id = game.get_player_by_symbol('X')
                                        player_o_id = game.get_player_by_symbol('O')

                                        player_x_nickname = game.get_player_nickname(bot, call.message.chat.id, player_x_id)
                                        player_o_nickname = game.get_player_nickname(bot, call.message.chat.id, player_o_id)

                                        current_player_nickname = player_x_nickname if game.current_player_symbol == 'X' else player_o_nickname

                                        bot.edit_message_text(
                                            chat_id=call.message.chat.id,
                                            message_id=call.message.message_id,
                                            text=f"Крестики: {player_x_nickname}\nНолики: {player_o_nickname}\n\nХод: {current_player_nickname}\n{game.print_board()}",
                                            reply_markup=game.create_markup()
                                        )

                                    bot.answer_callback_query(call.id)
                                else:
                                    bot.answer_callback_query(call.id, "Игра не активна. Начните новую /game")

                        continue