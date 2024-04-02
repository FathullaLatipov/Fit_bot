import os

from django.conf import settings
from telebot.types import Message
from django.utils import timezone
from telebot import custom_filters

from courses.models import ProgramMap
from ...loader import bot
from ...states import CourseInteraction
from ...models import PaidUser
from .edit_calories_backends import get_id, return_calories_and_norm


@bot.message_handler(state=CourseInteraction.initial,
                     func=lambda message: message.text == 'Сколько еще можно ккал?👀')
def calories_info(message: Message):
    user_id, chat_id = get_id(message=message)
    user_model = PaidUser.objects.get(user=user_id)
    current_day = (timezone.now().date() - user_model.paid_day).days

    # if current_day == 0:
    #     bot.send_message(user_id, '*Упс...*\n\nЭта функция будет доступна с завтрашнего дня', parse_mode='Markdown')
    # else:
    user_calories, remaining_calories, daily_norm, daily_proteins_norm, remaining_proteins = \
        return_calories_and_norm(user_model, current_day)

    if remaining_calories < 0:
        text = "❗️Вы переели свою норму ккал, ваш результат на 70% зависит от вашего питания, " \
               "поэтому желательно больше ничего не есть за сегодня…\n\n" \
               "Если крайне тяжело, то лучше отдать предпочтение овощам (огурцы, капуста, броколли, помидоры…)"
    else:

        if remaining_calories < 0:
            remaining_calories = '0'
        if remaining_proteins < 0:
            remaining_proteins = '0'

        text = f"🔥Вам можно съесть еще: {remaining_calories} ккал / {remaining_proteins}г белка"
    bot.send_message(user_id, text)


@bot.message_handler(state=CourseInteraction.initial, func=lambda message: message.text == 'Карта программы 🗺')
def handle_update_calories(message: Message):
    user_id, chat_id = get_id(message=message)
    photo = ProgramMap.objects.first()
    if photo:
        image_path = os.path.join(settings.MEDIA_ROOT, str(photo.image))
        with open(image_path, "rb") as file:
            bot.send_photo(chat_id=chat_id, photo=file, caption='Карта продукта')
    else:
        print("No photo found")


bot.add_custom_filter(custom_filters.StateFilter(bot))
