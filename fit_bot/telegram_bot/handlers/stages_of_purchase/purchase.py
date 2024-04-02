import os
import time

from django.utils import timezone
from telebot.types import Message, InlineKeyboardMarkup, \
    InlineKeyboardButton, CallbackQuery, ReplyKeyboardRemove, ReplyKeyboardMarkup, KeyboardButton
from telebot import custom_filters

from datetime import date
from django.shortcuts import get_object_or_404
from django.db.models import F
import schedule

from ..mainmenu import create_inline_markup, get_id, create_keyboard_markup, paid_user_main_menu
from ...loader import bot
from ...states import PurchaseStates, AfterPurchaseStates, CourseInteraction
from ...models import UnpaidUser, PaidUser, BankCards

# ADMIN_CHAT_ID = 58790442
ADMIN_CHAT_ID = 58790442
user_data = {}

photo_path = "photos_official/liza.jpeg"


def get_image(filename):
    try:
        current_path = os.path.abspath(os.getcwd())
        image_path = os.path.join(current_path, 'media', filename)

        with open(image_path, 'rb') as photo:
            return photo.read()

    except Exception as e:
        print(Exception, e)


photo = get_image(photo_path)


def add_data(user, tag, info):
    if user not in user_data:
        user_data[user] = {}
    user_data[user][tag] = info


# @bot.callback_query_handler(func=lambda call: call.data == 'Go_for_it')
# def after_greeting(call: CallbackQuery):
#     user_id, chat_id = get_id(call=call)
#
#     markup = create_keyboard_markup('Появились вопросики...')
#
#     test = 'AgACAgIAAxkBAAIxZmTWibqN_mHYK-1uJs08CdoexIw0AAI4zDEb8Jm5SqYMWroMFb56AQADAgADeQADMAQ'
#     official = 'AgACAgIAAxkBAAEBJA9k2rj2-rChgpOYjuzj5M0XhhxWVwAC4coxG3dI2EqAfXmGAAHDqlABAAMCAAN5AAMwBA'
#     text = '*👋 Привет, меня зовут Лиза*\n\n' \
#            'Я – виртуальный ассистент Ибрата и буду помогать вам на всем ' \
#            'пути взаимодействия с ботом ☺️'
#
#     bot.send_photo(chat_id, photo=official, caption=text, reply_markup=markup, parse_mode='Markdown')
#
#     markup = create_inline_markup(('Тинькофф (Россия)', 'tinkoff'), ('Click/Payme (Узбекистан)', 'click'),
#                                   ('Другое', 'other'))
#
#     bot.send_message(chat_id, text='Чтобы получить доступ к программе, выберите удобный для вас способ оплаты:',
#                      reply_markup=markup)


@bot.callback_query_handler(func=lambda call: call.data in ['tinkoff', 'click', 'other', 'registration'])
def after_greeting(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    answer = call.data
    if answer == 'other':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))
        bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                              text='Чтобы выбрать другой способ оплаты, напишите Ибрату @ibrat21', reply_markup=markup)
    elif answer == 'tinkoff':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))

        bot.edit_message_text(chat_id=chat_id,
                              message_id=call.message.message_id,
                              text='*🧗Инициалы...*\n\nВведите, пожалуйста, свои имя и фамилию, '
                                   'чтобы мы подтвердили вас '
                                   '\n\nНапример: "Иван Иванов"',
                              reply_markup=markup,
                              parse_mode='Markdown')
        add_data(user_id, 'chosen_method', 'тинькоф')
        bot.set_state(user_id, PurchaseStates.initial, chat_id)

    elif answer == 'registration':
        markup = create_inline_markup(('назад', 'back_to_bank_choose'))

        bot.edit_message_text(chat_id=chat_id,
                              message_id=call.message.message_id,
                              text='*🧗Инициалы...*\n\nВведите, пожалуйста, свои имя и фамилию, '
                                   'чтобы мы подтвердили вас '
                                   '\n\nНапример: "Иван Иванов"',
                              parse_mode='Markdown')
        add_data(user_id, 'chosen_method', 'click')
        bot.set_state(user_id, PurchaseStates.initial, chat_id)


@bot.callback_query_handler(func=lambda call: call.data == 'back_to_bank_choose')
def back_button_while_purchase(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    markup = create_inline_markup(('Тинькофф (Россия)', 'tinkoff'), ('Click/Payme (Узбекистан)', 'click'),
                                  ('Другое', 'other'))

    bot.edit_message_text(chat_id=chat_id, message_id=call.message.message_id,
                          text='Чтобы получить доступ к программе, выберите удобный для вас способ оплаты:',
                          reply_markup=markup)


@bot.message_handler(state=PurchaseStates.initial)
def ask_initials(message: Message):
    user_id, chat_id = get_id(message=message)
    initials = message.text.strip()
    if len(initials.split()) == 2:
        markup = create_inline_markup(('Продолжить', 'confirm_payment'), ('Изменить', 'back'))
        bot.send_message(user_id, text=f'Вы ввели следущие инициалы: *{initials}*, продолжить?',
                         reply_markup=markup, parse_mode='Markdown')
        add_data(user_id, 'initials', initials)
        bot.set_state(user_id, PurchaseStates.choose_bank, chat_id)
    else:
        bot.send_message(user_id, 'Пожалуйста, введите свои инициалы через пробел. ')


@bot.callback_query_handler(state=PurchaseStates.initial, func=lambda call: call.data in ['continue', 'back'])
def handle_initials(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'continue':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        search_term = user_data[user_id]['chosen_method']
        cards_with_term = BankCards.objects.filter(bank_name__icontains=search_term)
        card_number = [card.card_number for card in cards_with_term][0]

        markup = create_inline_markup(('Оплатил(а)', 'paid'), ('Назад', 'back'))

        price = '5 000 RUB' if search_term == 'тинькоф' else '604 000 сум'
        name = 'Тинькоф' if search_term == 'тинькоф' else 'Click / Payme'

        bot.send_photo(user_id, photo=photo,
                       caption=f"*🔥 Доступ к программе уже близко!*\n\nОсталось перевести оплату {price} "
                               f"по реквизитам:"
                               f"\n\n{card_number}\n\n{name}",
                       reply_markup=markup,
                       parse_mode='Markdown')
        bot.set_state(user_id, PurchaseStates.choose_bank, chat_id)
    else:
        bot.edit_message_text(chat_id=chat_id, text='Хорошо! Можете ввести инициалы еще раз:',
                              message_id=call.message.message_id, reply_markup=None)


@bot.callback_query_handler(state=PurchaseStates.choose_bank, func=lambda call: call.data in ['paid', 'back'])
def handle_payment(call):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'paid':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        markup = create_inline_markup(('Подтверждаю', 'confirm_payment'), ('Назад', 'go_back'))
        bot.send_message(chat_id=chat_id,
                         text="Если уже оплатили, нажмите на кнопку «Подтверждаю» ✅",
                         reply_markup=markup)
    elif answer == 'back':
        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
        markup = create_inline_markup(('Продолжить', 'continue'), ('Изменить', 'back'))
        initials = user_data[user_id]['initials']
        bot.send_message(user_id, text=f'Вы ввели следущие инициалы: *{initials}*, продолжить?',
                         reply_markup=markup, parse_mode='Markdown')
        bot.set_state(user_id, PurchaseStates.initial, chat_id)


def check_user_is_paid(message, user_id, chat_id=None):
    time.sleep(30)
    try:
        markup = InlineKeyboardMarkup()
        unpaid_user = UnpaidUser.objects.get(user_id=user_id)
        # print(unpaid_user.has_paid)
        if unpaid_user.has_paid is True:
            try:
                PaidUser.objects.filter(user=user_id).delete()
            except Exception as e:
                pass
            PaidUser.objects.create(user=user_id, username=unpaid_user.username, full_name=unpaid_user.full_name,
                                    paid_day=timezone.now().date(), calories=1,
                                    proteins=1, timezone='Tashkent', has_finished=False)
            button1 = InlineKeyboardButton(text='Чат коучинга', url='https://t.me/+o5lBij2LZyMyZDMy')
            markup.add(button1)
            bot.send_photo(chat_id=user_id, photo=photo, caption='*Ваша подписка подтверждена!*❤️‍🔥\n\n'
                                                                 'Для дальнейших действий переходите в '
                                                                 'общий чат коучинга, нажав на кнопку',
                           reply_markup=markup, parse_mode='Markdown')
            paid_user_main_menu(message, user_id=user_id, chat_id=user_id)
            return
        else:
            check_user_is_paid(message, user_id, chat_id)

    except Exception as e:
        print(e)


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data in ['confirm_payment', 'go_back'])
def confirm_payment(call):
    user_id, chat_id = get_id(call=call)

    markup = create_inline_markup(('Подтвердить', f'confsubs{user_id}'), ('Отмена', f'canc{user_id}'))
    bot.set_state(ADMIN_CHAT_ID, PurchaseStates.choose_bank, ADMIN_CHAT_ID)
    if call.data == 'confirm_payment':
        if call.from_user.username is not None:
            try:
                bot.send_message(user_id, "Ваша подписка активируется в ближайшее время...")
                check_user_is_paid(user_id, chat_id, call.message)
            except Exception as e:
                pass
                # schedule.every(1).minute.do(check_user_is_paid, user_id)
    #         bot.send_message(ADMIN_CHAT_ID,
    #                          f"Пользователь {user_id}, {' '.join(user_data[user_id]['initials'].split()[-3:-1])} "
    #                          f"@{call.from_user.username} прошел регистрацию",
    #                          reply_markup=markup)
    #     else:
    #         bot.send_message(ADMIN_CHAT_ID,
    #                          f"Пользователь {user_id}, {' '.join(user_data[user_id]['initials'].split()[-3:-1])} "
    #                          f"username отсутствует, прошел регистрацию.",
    #                          reply_markup=markup)
    #     bot.answer_callback_query(call.id)
    #
    # else:
    #     bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    #     search_term = user_data[user_id]['chosen_method']
    #     cards_with_term = BankCards.objects.filter(bank_name__icontains=search_term)
    #     card_number = [card.card_number for card in cards_with_term][0]
    #
    #     markup = create_inline_markup(('Оплатил(а)', 'paid'), ('Назад', 'back'))
    #
    #     price = '5 000 RUB' if search_term == 'тинькоф' else '604 000 сум'
    #     name = 'Тинькоф' if search_term == 'тинькоф' else 'Click / Payme'
    #
    #     bot.send_photo(photo=photo,
    #                    chat_id=user_id,
    #                    caption=f"*🔥 Доступ к программе уже близко!*\n\nОсталось перевести оплату {price} "
    #                            f"по реквизитам:"
    #                            f"\n\n{card_number}\n\n{name}",
    #                    reply_markup=markup,
    #                    parse_mode='Markdown')

    try:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
    except:
        pass


@bot.callback_query_handler(state=PurchaseStates.choose_bank,
                            func=lambda call: call.data[:8] == 'confsubs' or call.data[:4] == 'canc')
def approve_payment(call):
    # print(call.data[:4], call.data[:8])
    if call.data[:8] == 'confsubs':
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        markup = InlineKeyboardMarkup()
        user = UnpaidUser.objects.get(user_id=int(call.data[8:]))
        try:
            PaidUser.objects.filter(user=int(call.data[8:])).delete()
        except Exception as e:
            pass
        # print(user.username)
        button1 = InlineKeyboardButton(text='Чат коучинга', url='https://t.me/+o5lBij2LZyMyZDMy')
        # button1 = InlineKeyboardButton(text='Заполнить!', callback_data='fillthetest')
        markup.add(button1)
        UnpaidUser.objects.filter(user_id=int(call.data[8:])).update(has_paid=True)
        PaidUser.objects.create(user=int(call.data[8:]), username=user.username, full_name=user.full_name,
                                paid_day=timezone.now().date(), calories=1,
                                proteins=1, timezone='Tashkent', has_finished=False)
        search_term = user_data[int(call.data[8:])]['chosen_method']
        BankCards.objects.filter(bank_name__icontains=search_term).update(
            number_of_activations=F('number_of_activations') + 1)
        # official = 'AgACAgIAAxkBAAEBJBJk2rllWOyWYpscLJxfu7UWvw_dmwACgswxG3Rr2Er9A73F4DaK6QEAAwIAA3kAAzAE'
        # bot.send_photo(chat_id=int(call.data[8:]), photo=photo, caption='*Ваша подписка подтверждена!*❤️‍🔥\n\n'
        #                                                                 'Для дальнейших действий переходите в '
        #                                                                 'общий чат коучинга, нажав на кнопку',
        #                reply_markup=markup, parse_mode='Markdown')
        user_id = int(call.data[8:])
        paid_user_main_menu(call.message, user_id=user_id, chat_id=user_id)

        # bot.set_state(user_id=int(call.data[8:]), state=AfterPurchaseStates.initial, chat_id=int(call.data[8:]))

    else:
        bot.delete_message(chat_id=call.message.chat.id, message_id=call.message.message_id)
        bot.send_message(int(call.data[4:]),
                         'Кажется, что-то пошло не так и вам не одобрили подписку,'
                         ' либо вы случайно нажали на кнопку оплаты')


bot.add_custom_filter(custom_filters.StateFilter(bot))

# @bot.message_handler(func=lambda message: message.text == 'Приобрести подписку на курс')
# def subscription(message: Message):
#     user_id = message.from_user.id
#     bot.send_message(chat_id=user_id, text='Секундочку...')
#     if user_id not in user_data:
#         user_data[user_id] = {'state': States.START}
#     user_id = message.chat.id
#     markup = InlineKeyboardMarkup()
#     button1 = InlineKeyboardButton(text='Ознакомлен!', callback_data='acknowledged')
#     markup.add(button1)
#     bot.send_document(chat_id=user_id,
#                       document=open('/app/fit_bot/telegram_bot/data/assets/Original ticket-542.pdf', 'rb'),
#                       caption='Для того, чтобы приобрести подписку на продукт, '
#                               '\nВам необходимо ознакомиться с договором оферты:', reply_markup=markup)
# @bot.callback_query_handler(func=lambda call: call.data == 'acknowledged')
