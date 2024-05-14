import copy
from telebot import types
from connect import bot, form_text_markdownv2
#значения 0, +, null
class Game:
    def __init__(self, message) -> None:
        self.arr = [[None, None, None],
                    [None, None, None],
                    [None, None, None]]
        self.last_user = False
        self.key = False
        self.users = []
        self.users.append(message.from_user.id)
        inlineKey = types.InlineKeyboardMarkup()
        inlineKey.add(types.InlineKeyboardButton(text="Присоединиться", callback_data='{"key": "start_game_zero", "id": "' + str(self.users[0]) + '"}'))
        bot.send_message(message.chat.id, "[" + form_text_markdownv2(str(message.from_user.first_name) + " " + str((message.from_user.last_name or ""))) + "](tg://user?id\=" + str(self.users[0]) + ")" +
                         " хочет сыграть в крестики нолики", parse_mode="MarkdownV2", reply_markup=inlineKey)

    def game_zero(self, call, call_data = False):
        if self.last_user == True and self.users[1] == call.from_user.id and self.key:
            bot.answer_callback_query(callback_query_id=call.id, text='Не твой ход')
            return
        elif self.last_user == False and self.users[0] == call.from_user.id and self.key:
            bot.answer_callback_query(callback_query_id=call.id, text='Не твой ход')
            return
        elif call.from_user.id not in self.users:
            bot.answer_callback_query(callback_query_id=call.id, text='Не твоя игра. Для начала своей игры отправь сообщение /gg', show_alert=True)
            return
        if call.from_user.id == self.users[0]:
            value = True
        elif call.from_user.id == self.users[1]:
            value = False
        self.inlineKey = types.InlineKeyboardMarkup()
        if (call_data):
            if ((self.arr[int(call_data["h"])][int(call_data["w"])]) == None):
                bot.send_message(call.message.chat.id, str(value))
                self.arr[int(call_data["h"])][int(call_data["w"])] = bool(value)
            else:
                bot.answer_callback_query(callback_query_id=call.id, text='Поле занято')
                return
        queue = self.itemsGame()
        self.key = True
        bot.edit_message_text(chat_id=call.message.chat.id, message_id=call.message.id, text=queue, reply_markup=self.inlineKey)

    def itemsGame(self):
        len_arr = len(self.arr)
        reversArr = self.arr
        p = 0
        l = 0
        while p < len_arr:
            while l < len_arr:
                reversArr[p][l] = self.arr[l][p]
                l+=1
            p+=1
        if self.last_user == False:
            queue = "❌ Ход крестиков ❌"
            vinText = "⭕️"
            self.last_user = True
        else:
            queue = "⭕️ Ход ноликов ⭕️"
            vinText = "❌"
            self.last_user = False
        a = []
        for i in self.arr:
            for q in i:
                if q == None:
                    a.append(q)
        if len(a) == 0:
            self.inlineKey = types.InlineKeyboardMarkup()
            return "Ничья"
        h = 0
        while h < len_arr:
            w = 0
            qualy_diagonal = 0
            qualy_diagonal_revers = 0
            qualy_h = 0
            tempArr = []
            if (self.arr[h].count(True) == 3) or (reversArr[h].count(True) == 3):
                self.inlineKey = types.InlineKeyboardMarkup()
                return "Победа ❌"
            elif (self.arr[h].count(False) == 3) or (reversArr[h] == 3):
                self.inlineKey = types.InlineKeyboardMarkup()
                return "Победа ⭕️"
            while w < len_arr:
                #для печати кнопок
                if self.arr[h][w] == False:
                    text = "⭕️"
                elif self.arr[h][w] == True:
                    text = "❌"
                else:
                    text = "⬜️"
                if self.arr[w][w] == self.arr[h][h] and self.arr[w][w] != None:
                    qualy_diagonal+=1
                    print('test1')
                    if qualy_diagonal == len_arr:
                        self.inlineKey = types.InlineKeyboardMarkup()
                        return "Победа " + vinText
                if reversArr[w][w] == reversArr[h][h] and self.arr[w][w] != None:
                    qualy_diagonal_revers+=1
                    print('test2')
                    if qualy_diagonal_revers == len_arr:
                        self.inlineKey = types.InlineKeyboardMarkup()
                        return "Победа " + vinText
                # if self.arr[w][h] == self.arr[len_arr - w - 1][h] and self.arr[w][h] != None:
                #     qualy_h+=1
                #     print('test3')
                #     if qualy_h == len_arr:
                #         self.inlineKey = types.InlineKeyboardMarkup()
                #         return "Победа " + vinText
                tempArr.append(types.InlineKeyboardButton(text=text, callback_data='{"key": "gz", "h":"' + str(h) + '", "w":"' + str(w) + '", "id": "' + str(self.users[0]) + '"}'))
                w+=1
            self.inlineKey.add(*tempArr)
            h+=1
        print(self.arr)
        return queue