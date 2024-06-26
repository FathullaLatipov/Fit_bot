import os

from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardRemove, CallbackQuery
from telebot import custom_filters
from django.utils import timezone

from .edit_calories_backends import return_calories_and_norm, get_id, create_main_editing_menu, get_meal_info_text, \
    create_keyboard_markup, meal_info, update_courseday_calories, update_meal, redact_menu_markup
from ...loader import bot
from ...states import CourseInteraction, AfterPurchaseStates
from ...models import PaidUser, CourseDay, Meal, UnpaidUser, FinishedUser
from ..mainmenu import paid_user_main_menu, create_inline_markup

user_data = {}
photo_path = "photof/food.png"
photo_liza = "photos_official/liza.jpeg"


def get_image(filename):
    try:
        current_path = os.path.abspath(os.getcwd())
        # print(current_path)
        image_path = os.path.join(current_path, 'media', filename)
        # print(image_path)

        with open(image_path, 'rb') as photo:
            return photo.read()

    except Exception as e:
        print(Exception, e)


photo_f = get_image(photo_path)
photo = get_image(photo_liza)

for_meal_from_user = {}


@bot.message_handler(state=CourseInteraction.initial, func=lambda message: message.text == 'Мой дневник калорий 📆')
def handle_update_calories(message: Message):
    try:
        user_id, chat_id = get_id(message=message)

        user = PaidUser.objects.get(user=user_id)
        # print(user.username)
        current_day = int((timezone.now().date() - user.paid_day).days)
        if not user.has_finished:
            text, markup = create_main_editing_menu(user, current_day)

            pht_official = 'AgACAgIAAxkBAAEBLMxk40CkwmfZWooYJUzq9TBeNZECFgACoc0xGzBEGEu0HBxFbSMbMwEAAwIAA3kAAzAE'

            pht_test = 'AgACAgIAAxkBAAIxumTjQgFFi1hILZKHBX7te2r2uFV9AAL0yjEbDvkhSyfOKdqx2dvIAQADAgADeQADMAQ'
            print(user.has_finished)

            bot.send_photo(chat_id=user_id,
                           photo=photo_f,
                           caption=text,
                           reply_markup=markup,
                           parse_mode='Markdown')
        else:
            try:
                FinishedUser.objects.create(user=user.user, username=user.username, full_name=user.full_name,
                                            paid_day=user.paid_day, calories=user.calories, proteins=user.proteins,
                                            timezone=user.timezone,
                                            пол=user.пол, цель=user.цель, место=user.место, уровень=user.уровень)
            except Exception as e:
                pass
            bot.send_message(user_id, 'Кажется, курс закончился!')
            UnpaidUser.objects.filter(user_id=user_id).update(has_paid=False)
            user_id, chat_id = get_id(message=message)
            user, created = UnpaidUser.objects.get_or_create(user_id=user_id)
            if created:
                user.save()
            try:
                paid_user = PaidUser.objects.get(user=user_id)
                if not paid_user.has_finished:
                    paid_user_main_menu(message)
                    return
                elif paid_user.has_finished and user.has_paid:
                    bot.set_state(user_id, AfterPurchaseStates.initial, chat_id)
                    return

            except PaidUser.DoesNotExist:
                pass

            username, full_name = message.from_user.username, message.from_user.full_name

            user = UnpaidUser(user_id=message.from_user.id, username=username, full_name=full_name)
            user.save()

            markup = create_keyboard_markup('Появились вопросики...')

            text = '*👋 Привет, меня зовут Лиза*\n\n' \
                   'Я – виртуальный ассистент Ибрата и буду помогать вам на всем ' \
                   'пути взаимодействия с ботом ☺️'

            bot.send_photo(chat_id, caption=text, photo=photo, reply_markup=markup, parse_mode='Markdown')

            markup = create_inline_markup(('Пройти регистрацию', 'registration'))

            bot.send_message(chat_id, text='Чтобы получить доступ к программе, пройдите регистрацию 📝',
                             reply_markup=markup)
    except Exception as E:
        bot.send_message(58790442, f"Ошибка {E} ошибка в функции handle_update_calories")


@bot.message_handler(state=CourseInteraction.go_to_menu)
def handle_go_to_menu(message: Message):
    user_id, chat_id = get_id(message=message)
    user, created = UnpaidUser.objects.get_or_create(user_id=user_id)
    if created:
        user.save()
    try:
        paid_user = PaidUser.objects.get(user=user_id)
        if paid_user:
            paid_user_main_menu(message)
        elif not paid_user and user.has_paid:
            bot.set_state(user_id, AfterPurchaseStates.initial, chat_id)
        return
    except PaidUser.DoesNotExist:
        pass

    username, full_name = message.from_user.username, message.from_user.full_name

    user = UnpaidUser(user_id=message.from_user.id, username=username, full_name=full_name)
    user.save()

    markup = create_keyboard_markup('Появились вопросики...')

    test = 'AgACAgIAAxkBAAIxZmTWibqN_mHYK-1uJs08CdoexIw0AAI4zDEb8Jm5SqYMWroMFb56AQADAgADeQADMAQ'
    official = 'AgACAgIAAxkBAAEBJA9k2rj2-rChgpOYjuzj5M0XhhxWVwAC4coxG3dI2EqAfXmGAAHDqlABAAMCAAN5AAMwBA'
    text = '*👋 Привет, меня зовут Лиза*\n\n' \
           'Я – виртуальный ассистент Ибрата и буду помогать вам на всем ' \
           'пути взаимодействия с ботом ☺️'

    bot.send_photo(chat_id, caption=text, photo=photo, reply_markup=markup, parse_mode='Markdown')

    # markup = create_inline_markup(('Тинькофф (Россия)', 'tinkoff'), ('Click/Payme (Узбекистан)', 'click'),
    #                               ('Другое', 'other'))
    markup = create_inline_markup(('Пройти регистрацию', 'registration'))

    # bot.send_message(chat_id, text='Чтобы получить доступ к программе, выберите удобный для вас способ оплаты:',
    #                  reply_markup=markup)
    bot.send_message(chat_id, text='Чтобы получить доступ к программе, пройдите регистрацию 📝',
                     reply_markup=markup)


@bot.callback_query_handler(state=CourseInteraction.initial,
                            func=lambda call: call.data in ["breakfast", "lunch", "dinner", "snack", "progress"])
def handle_meal_callback(call):
    user_id, chat_id = get_id(call=call)
    meal = call.data
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    if user_id not in user_data:
        user_data[user_id] = {current_day: {}}
    if current_day not in user_data[user_id]:
        user_data[user_id][current_day] = {}
    if meal not in user_data[user_id][current_day]:
        user_data[user_id][current_day][meal] = {}

    user_data[user_id][current_day]['selected_meal'] = meal

    text, markup = meal_info(user, current_day, user_data, user_id, meal)

    bot.delete_message(chat_id=chat_id,
                       message_id=call.message.message_id)

    bot.send_message(text=text,
                     chat_id=chat_id,
                     reply_markup=markup,
                     parse_mode='Markdown')


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


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'back')
def back_to_menu(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    bot.delete_message(chat_id=chat_id,
                       message_id=call.message.message_id)

    text, markup = create_main_editing_menu(user, current_day)

    pht_official = 'AgACAgIAAxkBAAEBLMxk40CkwmfZWooYJUzq9TBeNZECFgACoc0xGzBEGEu0HBxFbSMbMwEAAwIAA3kAAzAE'

    pht_test = 'AgACAgIAAxkBAAIxumTjQgFFi1hILZKHBX7te2r2uFV9AAL0yjEbDvkhSyfOKdqx2dvIAQADAgADeQADMAQ'

    bot.send_photo(chat_id=user_id,
                   caption=text,
                   photo=photo,
                   reply_markup=markup,
                   parse_mode='Markdown')


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'add_remove')
def handle_add_remove_callback(call):
    user_id, chat_id = get_id(call=call)

    markup = create_keyboard_markup('Отмена!')

    text = "Для начала, введите название блюда"

    bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)
    bot.send_message(user_id, text=text, reply_markup=markup)
    bot.set_state(user_id, CourseInteraction.enter_meal_name, chat_id)


@bot.message_handler(state=CourseInteraction.enter_meal_name, content_types=['text'])
def handle_entered_meal_name(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text

    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    if answer == 'Отмена!':
        markup = create_keyboard_markup('Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Карта программы 🗺', 'Появились вопросики...')

        bot.send_message(text="Вы отменили добавление нового блюда.",
                         chat_id=chat_id,
                         reply_markup=markup)

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text,
                         chat_id=chat_id,
                         reply_markup=markup,
                         parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)

    else:
        if user_id not in for_meal_from_user:
            for_meal_from_user[user_id] = {}
        for_meal_from_user[user_id]['name'] = answer

        bot.send_message(user_id, 'Введите четко подсчитанное количество *калорий*:',
                         reply_markup=ReplyKeyboardRemove(), parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.enter_meal_calories, chat_id)


@bot.message_handler(state=CourseInteraction.enter_meal_calories, content_types=['text'])
def handle_meal_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    try:
        answer = answer.replace(',', '.')
        answer = float(answer)
        if -1 < float(answer) < 5001:
            for_meal_from_user[user_id]['calories'] = answer
            bot.send_message(user_id, 'Введите количество *белка* для данного продукта:', parse_mode='Markdown')
            bot.set_state(user_id, CourseInteraction.enter_meal_protein, chat_id)
        else:
            bot.send_message(user_id, 'Можно ввести только от 1 до 5000.')
    except Exception:
        bot.send_message(user_id, 'Кажется, вы ввели что-то неправильно. Попробуйте снова.')


@bot.message_handler(state=CourseInteraction.enter_meal_protein, content_types=['text'])
def handle_meal_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    try:
        answer = answer.replace(',', '.')
        answer = float(answer)
        if -1 < float(answer) < 5001:
            for_meal_from_user[user_id]['proteins'] = answer

            markup = create_keyboard_markup('Продолжить', 'Изменить', 'Отмена!')
            bot.send_message(user_id, f'Хорошо! Вы добавляете "*{for_meal_from_user[user_id]["name"]}*". \n\n'
                                      f'Калории: *{for_meal_from_user[user_id]["calories"]}*\n'
                                      f'Белки: *{for_meal_from_user[user_id]["proteins"]}*\n\nПродолжить, '
                                      f'изменить или отменить?', reply_markup=markup, parse_mode='Markdown')
            bot.set_state(user_id, CourseInteraction.continue_meal_name, chat_id)
        else:
            bot.send_message(user_id, 'Можно ввести только от 1 до 5000.')
    except Exception:
        bot.send_message(user_id, 'Кажется, вы ввели что-то неправильно. Попробуйте снова.')


@bot.message_handler(state=CourseInteraction.continue_meal_name, content_types=['text'])
def handle_meal_name(message: Message):
    user_id, chat_id = get_id(message=message)
    answer = message.text
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days
    if answer == 'Продолжить':

        paid_user_main_menu(message)

        selected_meal = user_data[user_id][current_day]['selected_meal']
        product = f"{for_meal_from_user[user_id]['name']}"

        if product in user_data[user_id][current_day][selected_meal]:
            old_calories, _, old_proteins, _ = user_data[user_id][current_day][selected_meal][product].split()
            old_calories = float(old_calories)
            old_proteins = float(old_proteins.rstrip('г'))

            new_calories = float(for_meal_from_user[user_id]['calories']) + old_calories
            new_proteins = float(for_meal_from_user[user_id]['proteins']) + old_proteins

            user_data[user_id][current_day][selected_meal][product] = f"{new_calories} ккал {new_proteins}г белков"
        else:
            user_data[user_id][current_day][selected_meal][product] = \
                f"{for_meal_from_user[user_id]['calories']} ккал {for_meal_from_user[user_id]['proteins']}г белков"

        course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day)
        meal, _ = Meal.objects.get_or_create(course_day=course_day,
                                             meal_type=user_data[user_id][current_day]['selected_meal'])
        update_meal(meal,
                    round(float(for_meal_from_user[user_id]['calories']), 1),  # калории
                    round(float(for_meal_from_user[user_id]['proteins']), 1))

        update_courseday_calories(course_day)

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup, parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)
    elif answer == 'Изменить':
        markup = create_keyboard_markup('Отмена!')
        bot.send_message(chat_id=user_id,
                         text='Введите новое название блюда:',
                         reply_markup=markup)
        bot.set_state(user_id, CourseInteraction.enter_meal_name, chat_id)
    elif answer == 'Отмена!':

        markup = create_keyboard_markup('Мой дневник калорий 📆',
                                        'Сколько еще можно ккал?👀', 'Карта программы 🗺', 'Появились вопросики...')

        bot.send_message(text="Вы отменили добавление нового блюда.",
                         chat_id=chat_id, reply_markup=markup)
        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text,
                         chat_id=chat_id,
                         reply_markup=markup,
                         parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)
    else:
        bot.send_message(chat_id=chat_id,
                         text='Пожалуйста, воспользуйтесь кнопками "Продолжить", "Изменить" или "Отмена!"')


@bot.callback_query_handler(state=CourseInteraction.initial, func=lambda call: call.data == 'redact')
def redact_entered_meals(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    user = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user.paid_day).days

    user_calories, remaining_calories, daily_norm, daily_proteins_norm, \
        remaining_proteins = return_calories_and_norm(user, current_day)

    text, meals_text = get_meal_info_text(user_data[user_id][current_day]['selected_meal'],
                                          user_calories['breakfast'], user_data[user_id][current_day][
                                              user_data[user_id][current_day]['selected_meal']])
    if meals_text != 'Кажется, вы еще ничего не добавили!':

        to_send = ''
        oo = meals_text.split("\n")
        markup = redact_menu_markup(len(oo) - 1)
        user_data[user_id][current_day]['variants_to_delete'] = {}
        for i in range(1, len(oo)):
            to_send += f'{i} {oo[i - 1]}\n'
            user_data[user_id][current_day]['variants_to_delete'][i] = oo[i - 1]

        bot.edit_message_text(message_id=call.message.message_id, chat_id=chat_id,
                              text=f'Хорошо! Выберите номер блюда, которое вы хотите отредактировать: \n\n{to_send}',
                              reply_markup=markup)
    else:
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Назад', callback_data='back')
        markup.add(button)
        bot.edit_message_text(message_id=call.message.message_id, chat_id=chat_id,
                              text=f'Кажется, вы еще ничего не добавили!',
                              reply_markup=markup)
    bot.set_state(user_id, CourseInteraction.redacting, chat_id)


@bot.callback_query_handler(state=CourseInteraction.redacting, func=lambda call: call.data)
def handle_redacting(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)

    if call.data.isdigit():
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days
        user_data[user_id][current_day]['selected_meal_to_delete'] = int(call.data)
        markup = InlineKeyboardMarkup()
        button = InlineKeyboardButton(text='Удалить', callback_data='delete')
        button1 = InlineKeyboardButton(text='Назад', callback_data='back')
        markup.add(button)
        markup.add(button1)

        selected_to_delete = user_data[user_id][current_day]['variants_to_delete'][
            user_data[user_id][current_day]['selected_meal_to_delete']].split("-")[1].strip()

        bot.edit_message_text(chat_id=chat_id, text=f'Хотите удалить данное блюдо: *{selected_to_delete}*?',
                              message_id=call.message.message_id, reply_markup=markup, parse_mode='Markdown')

        bot.set_state(user_id, CourseInteraction.delete_product, chat_id)

    else:
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])

        bot.edit_message_text(text, chat_id, call.message.message_id, reply_markup=markup, parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)


@bot.callback_query_handler(state=CourseInteraction.delete_product, func=lambda call: call.data)
def delete_or_not_product(call: CallbackQuery):
    user_id, chat_id = get_id(call=call)
    answer = call.data
    if answer == 'back':
        redact_entered_meals(call)
    else:
        user = PaidUser.objects.get(user=user_id)
        current_day = (timezone.now().date() - user.paid_day).days

        course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day)
        meal, _ = Meal.objects.get_or_create(course_day=course_day,
                                             meal_type=user_data[user_id][current_day]['selected_meal'])

        selected_to_delete = user_data[user_id][current_day]['variants_to_delete'][
            user_data[user_id][current_day]['selected_meal_to_delete']].split("-")[-1].strip()

        calories, _, protein, _ = selected_to_delete.split()
        calories = float(calories)
        protein = float(protein[:-1])

        meal.calories -= calories
        meal.protein -= protein

        meal.save()
        for product, value in list(
                user_data[user_id][current_day][user_data[user_id][current_day]["selected_meal"]].items()):
            if value == selected_to_delete:
                del user_data[user_id][current_day][user_data[user_id][current_day]["selected_meal"]][product]

        selected_to_delete = user_data[user_id][current_day]['variants_to_delete'][
            user_data[user_id][current_day]['selected_meal_to_delete']].split("-")[1].strip()

        bot.delete_message(chat_id=chat_id, message_id=call.message.message_id)

        keyboard_markup = create_keyboard_markup('Мой дневник калорий 📆',
                                                 'Сколько еще можно ккал?👀', 'Карта программы 🗺',
                                                 'Появились вопросики...')

        bot.send_message(text=f'Вы удалили *{selected_to_delete}*!',
                         chat_id=chat_id,
                         reply_markup=keyboard_markup,
                         parse_mode='Markdown')

        text, markup = meal_info(user, current_day, user_data, user_id,
                                 user_data[user_id][current_day]['selected_meal'])
        bot.send_message(text=text, chat_id=chat_id, reply_markup=markup, parse_mode='Markdown')
        bot.set_state(user_id, CourseInteraction.initial, chat_id)


bot.add_custom_filter(custom_filters.StateFilter(bot))
