from telebot import TeleBot
from telebot.states import State
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

            bot.edit_message_text(
                chat_id=game_message.chat.id,
                message_id=game_message.id,
                text=f"Ход игрока {game.current_player}\n{game.print_board()}", 
                reply_markup=game.create_markup()
            )
    

    @bot.callback_query_handler(func=lambda call: True)
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
                                 
                                        game.players.add(call.from_user.id)
     
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
                                    
                                    game.board[i][j] = game.current_player
                                    winner = game.check_winner()
                                    
                                    if winner:
                                        if winner == 'Draw':
                                            text = "Ничья!"
                                        else:
                                            text = f"Игрок {winner} победил!"
                                        bot.edit_message_text(
                                            chat_id=call.message.chat.id, 
                                            message_id=call.message.message_id, 
                                            text=f"{text}\n{game.print_board()}"
                                        )
                                        user_ids: set = game.players
                                        
                                        for user_id in user_ids:
                                            bot.delete_state(
                                                user_id,
                                                call.message.chat.id
                                            )
                                    else:
                                        
                                        game.current_player = 'O' if game.current_player == 'X' else 'X'
                                        game.last_move_for = call.from_user.id
                                        
                                        bot.edit_message_text(
                                            chat_id=call.message.chat.id, 
                                            message_id=call.message.message_id, 
                                            text=f"Ход игрока {game.current_player}\n{game.print_board()}", 
                                            reply_markup=game.create_markup()
                                        )
                                    
                                    bot.answer_callback_query(call.id)
                                else:
                                    bot.answer_callback_query(call.id, "Игра не активна. Начните новую /game")
                        
                        continue