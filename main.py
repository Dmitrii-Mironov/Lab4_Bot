import logging
import requests
import random
from os import getenv
from telegram import Update
from telegram.ext import ApplicationBuilder, CommandHandler, ContextTypes

UNSPLASH_API_KEY = '1kykB36JXxQm5aFcUryMsXHfk8ZYFIRj9ch5XixVgmU'

# Настройка логирования
logging.basicConfig(format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO)

class PhotoBot:
    def __init__(self, token):
        self.token = token
        self.user_settings = {}
        self.sent_images = {}
        self.application = ApplicationBuilder().token(self.token).build()

        # Регистрация обработчиков команд
        self.application.add_handler(CommandHandler("start", self.start))
        self.application.add_handler(CommandHandler("set_settings", self.set_settings))
        self.application.add_handler(CommandHandler("random", self.random_photo))
        self.application.add_handler(CommandHandler("search", self.search))
        self.application.add_handler(CommandHandler("get_settings", self.get_settings))

    def run(self):
        self.application.run_polling()# Запуск бота

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        await update.message.reply_text(
            'Привет! Используйте /random для случайной фотографии или /search <ключевое_слово> для поиска.')

    def get_random_photo(self):
        response = requests.get('https://api.unsplash.com/photos/random', headers={
            'Authorization': f'Client-ID {UNSPLASH_API_KEY}'
        })
        if response.status_code == 200:
            return response.json()['urls']['regular']
        else:
            raise Exception("Ошибка получения случайной фотографии")

    async def random_photo(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        try:
            photo_url = self.get_random_photo()
            await update.message.reply_photo(photo=photo_url)
        except Exception as e:
            await update.message.reply_text(str(e))

    async def search(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        keyword = ' '.join(context.args)  # Получаем ключевое слово из аргументов

        if keyword:
            if keyword not in self.sent_images:
                self.sent_images[keyword] = []

            # Получаем настройки пользователя
            settings = self.user_settings.get(user_id, {})
            size = settings.get('size', 'regular')  # Значение по умолчанию
            orientation = settings.get('orientation', 'landscape')  # Значение по умолчанию

            # Запрос к Unsplash API
            url = f'https://api.unsplash.com/search/photos?query={keyword}&client_id={UNSPLASH_API_KEY}&size={size}&orientation={orientation}'
            response = requests.get(url)

            if response.status_code == 200:
                data = response.json()
                images = data.get('results', [])

                # Фильтруем изображения, которые уже были отправлены
                available_images = [img['urls']['regular'] for img in images if
                                    img['urls']['regular'] not in self.sent_images[keyword]]

                if available_images:
                    selected_image = random.choice(available_images)# Выбираем случайное изображение

                    # Отправляем изображение
                    await context.bot.send_photo(chat_id=update.effective_chat.id, photo=selected_image)
                    await update.message.reply_text(f"Вот изображение по запросу '{keyword}'!")

                    self.sent_images[keyword].append(selected_image)# Добавляем изображение в список отправленных
                else:
                    await update.message.reply_text(
                        f"Все изображения по запросу '{keyword}' уже были отправлены. Попробуйте другой запрос.")
            else:
                await update.message.reply_text("Ошибка при получении изображений с Unsplash.")
        else:
            await update.message.reply_text("Пожалуйста, укажите ключевое слово для поиска.")

    async def get_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        settings = self.user_settings.get(user_id, {})

        if settings:
            settings_message = "Текущие настройки:\n"
            for param, value in settings.items():
                settings_message += f"{param}: {value}\n"
            await update.message.reply_text(settings_message)
        else:
            await update.message.reply_text("У вас еще нет настроек. Используйте /set_settings для их установки.")

    async def set_settings(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        if len(context.args) < 2:
            await update.message.reply_text("Используйте: /set_settings <параметр> <значение>.\nДоступные параметры: size, orientation.")
            return

        param = context.args[0].lower()
        value = context.args[1].lower()

        if param not in ['size', 'orientation']:
            await update.message.reply_text("Доступные параметры: size, orientation.")
            return

        if user_id not in self.user_settings:
            self.user_settings[user_id] = {}

        self.user_settings[user_id][param] = value
        await update.message.reply_text(f"Настройка {param} установлена на {value}.")

def main():
    TOKEN = getenv("BOT_TOKEN")
    bot = PhotoBot(TOKEN)
    bot.run()

if __name__ == '__main__':
    main()

