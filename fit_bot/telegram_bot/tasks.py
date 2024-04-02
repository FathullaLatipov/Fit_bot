import threading

import schedule
import time

from django.core.exceptions import ObjectDoesNotExist
from telebot.types import Message, InlineKeyboardMarkup, InlineKeyboardButton
from telebot import apihelper
from django.utils import timezone
from datetime import timedelta
from django.db.models import Q, F
from apscheduler.schedulers.background import BackgroundScheduler
import pytz
import datetime

from .models import PaidUser, FinishedUser, CourseDay, UnpaidUser
from courses.models import Категории, Content, Mailing, Training
from .loader import bot
from .states import States
from .handlers.courses_interaction.edit_calories_backends import return_calories_and_norm

# from .warm_up_bot.handlers.mailings import check_unfinished_users
# from .warm_up_bot.handlers.mailings import get_cursor

user_data = {}

def send_daily_content():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
            matching_category = Категории.objects.get(
                пол=user.пол,
                цель=user.цель,
                место=user.место,
                уровень=user.уровень
            )

            delta_days = (timezone.now().date() - user.paid_day).days
            current_day = delta_days

            daily_contents = Mailing.objects.filter(
                category=matching_category,
                day=current_day,
            )

            for content in daily_contents:
                updated_caption = content.caption.replace("calories", str(user.calories)).replace("name", user.full_name)

                if content.content_type == 'V':
                    video_file_id = content.video.video_file_id
                    bot.send_video(chat_id=user.user, video=video_file_id, caption=updated_caption)
                elif content.content_type == 'T':
                    bot.send_message(chat_id=user.user, text=updated_caption)
                elif content.content_type == 'P':
                    bot.send_photo(chat_id=user.user, photo=content.photo_file_id, caption=updated_caption)
                elif content.content_type == 'G':
                    bot.send_document(chat_id=user.user, document=content.gif_file_id, caption=updated_caption)
        except ObjectDoesNotExist:
            # Обработка случая, когда объект категории не найден
            print("Категория не найдена для данного пользователя")
            continue
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(58790442, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(58790442, f"Error {error_code}: {e.result.reason} ошибка в функции send_daily_content")
        except Exception as E:
            bot.send_message(58790442, f"Ошибка: {E} ошибка в функции send_daily_content")



def check_calories():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
            name = user.full_name
            current_day = (timezone.now().date() - user.paid_day).days

            user_calories, remaining_calories, daily_norm, daily_proteins_norm, remaining_proteins \
                = return_calories_and_norm(user, current_day)

            if daily_norm - remaining_calories < daily_norm * 0.8:
                bot.send_message(chat_id=user.user,
                                 text=f'*{name}*! Пожалуйста, не забудьте заполнить ваш дневник калорий на '
                                      f'сегодняшний день 📓',
                                 parse_mode='Markdown')
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(58790442, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(58790442, f"Error {error_code}: {e.result.reason} в функции check_calories")
        except Exception as E:
            bot.send_message(58790442, f"Ошибка: {E} task 93")


def check_for_daily_content():
    paid_users = PaidUser.objects.all()

    for user in paid_users:
        current_day = (timezone.now().date() - user.paid_day).days
        try:
            if current_day != 0:
                course_day, created = CourseDay.objects.get_or_create(user=user, day=current_day, defaults={'has_requested': False})
                # inf not course_day.has_requested:
                #     bot.send_message(chat_id=user.user, text="Не забудьте открыть тренировки на сегодня!")
        except apihelper.ApiException as e:
            error_code = e.result.status_code
            if error_code == 403:
                bot.send_message(58790442, f"User {user.user} blocked the bot. Removing from the database.")
                user.delete()
            else:
                bot.send_message(58790442, f"Error {error_code}: {e.result.reason} в функции check_for_daily_content")
        except Exception as E:
            bot.send_message(58790442, f"Ошибка: {E} task 115")


def check_and_send_content():
    current_time_utc = datetime.datetime.now(pytz.utc)

    paid_users = PaidUser.objects.all()

    for user in paid_users:
        try:
            delta_days = (timezone.now().date() - user.paid_day).days
            # print(delta_days)
            user_timezone_str = user.timezone

            if user_timezone_str:
                user_timezone = pytz.timezone(user_timezone_str)
                current_time_local = current_time_utc.astimezone(user_timezone)

            if delta_days == 22:
                finished_user = FinishedUser.objects.create(
                    user=user.user,
                    username=user.username,
                    full_name=user.full_name,
                    paid_day=user.paid_day,
                    calories=user.calories,
                    timezone=user.timezone,
                    пол=user.пол,
                    цель=user.цель,
                    место=user.место,
                    уровень=user.уровень,
                )
                finished_user.save()
                UnpaidUser.objects.filter(user_id=user.user).update(has_paid=False)
                user.delete()

        except Exception as E:
            bot.send_message(58790442, f"Ошибка: {E} task 150")


def change_calories_norm():
    paid_users = PaidUser.objects.all()
    print(paid_users)
    for user in paid_users:
        try:
            delta_days = (timezone.now().date() - user.paid_day).days
            if delta_days == 8:
                if user.цель == "G":
                    print(user.calories)
                    PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 1.022)
                    print(user.calories)
                else:
                    print(user.calories)
                    PaidUser.objects.filter(user=user.user).update(calories=F('calories') * 0.834)
                    print(user.calories)
                bot.send_message(chat_id=user.user,
                                 text=f'{user.full_name}, мы обновили вашу норму калорий!\n\n'
                                      f'Вы можете увидеть новую норму в дневнике калорий')
        except Exception as E:
            bot.send_message(58790442, f"Ошибка: {E} task 160")


schedule.every().day.at("01:00").do(change_calories_norm)
schedule.every().day.at("09:00").do(send_daily_content)
schedule.every().day.at("18:00").do(check_calories)
schedule.every().day.at("20:00").do(check_for_daily_content)
# schedule.every(10).seconds.do(check_calories)
# schedule.every(10).seconds.do(check_for_daily_content)
# schedule.every(10).seconds.do(change_calories_norm)
# schedule.every().day.at("00:00").do(check_and_send_content)
# schedule.every(1).minutes.do(check_unfinished_users)
# schedule.every(15).seconds.do(check_and_send_content)


def run_scheduler():
    while True:
        try:
            schedule.run_pending()
        except Exception as e:
            bot.send_message(58790442, f"Ошибка: {e} task 182")

        time.sleep(1)


scheduler_thread = threading.Thread(target=run_scheduler)
