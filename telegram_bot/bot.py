from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup
from telegram.ext import Application, CommandHandler, MessageHandler, filters, ContextTypes, ConversationHandler, CallbackQueryHandler
from telegram.constants import ChatAction
import logging
from config.settings import TELEGRAM_BOT_TOKEN, TELEGRAM_ADMIN_ID, PRICE_PER_MONTH
from database.models import SessionLocal, Client, Agent, Lead, Payment
from agents.sales_agent import SalesAIAgent
from leads.generator import LeadGenerator
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# States для ConversationHandler
MAIN_MENU, BUSINESS_NAME, BUSINESS_TYPE, TARGET_AUDIENCE, CONFIRMING = range(5)

class TelegramBot:
    def __init__(self):
        self.app = Application.builder().token(TELEGRAM_BOT_TOKEN).build()
        self.lead_generator = LeadGenerator()
        self.setup_handlers()

    def setup_handlers(self):
        """Настраивает все обработчики команд"""

        # Основной conversation handler
        conv_handler = ConversationHandler(
            entry_points=[
                CommandHandler("start", self.start_command),
                CommandHandler("setup_agent", self.setup_agent_start),
                CallbackQueryHandler(self.button_callback, pattern="^(setup_agent|stats|help)$")
            ],
            states={
                MAIN_MENU: [
                    CallbackQueryHandler(self.button_callback, pattern="^(setup_agent|stats|help)$"),
                ],
                BUSINESS_NAME: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_business_name)
                ],
                BUSINESS_TYPE: [
                    CallbackQueryHandler(self.get_business_type, pattern="^type_")
                ],
                TARGET_AUDIENCE: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.get_target_audience)
                ],
                CONFIRMING: [
                    MessageHandler(filters.TEXT & ~filters.COMMAND, self.confirm_setup)
                ]
            },
            fallbacks=[CommandHandler("cancel", self.cancel_setup), CommandHandler("start", self.start_command)]
        )

        self.app.add_handler(conv_handler)

        # Другие команды
        self.app.add_handler(CommandHandler("help", self.help_command))
        self.app.add_handler(CommandHandler("status", self.status_command))

        # Обработчик обычных сообщений (вне conversation)
        self.app.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, self.handle_message))

    async def start_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Стартовая команда"""
        keyboard = [
            [InlineKeyboardButton("🚀 Начать работу", callback_data="setup_agent")],
            [InlineKeyboardButton("📊 Статистика", callback_data="stats")],
            [InlineKeyboardButton("❓ Помощь", callback_data="help")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"👋 Добро пожаловать в AI Sales Bot!\n\n"
            f"Я помогу вашему бизнесу автоматически генерировать лидов с помощью AI.\n\n"
            f"Что вы хотите сделать?",
            reply_markup=reply_markup
        )
        return MAIN_MENU

    async def button_callback(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработчик нажатия кнопок в главном меню"""
        query = update.callback_query
        await query.answer()

        callback_data = query.data

        if callback_data == "setup_agent":
            await query.edit_message_text("🏢 Как называется ваш бизнес?")
            return BUSINESS_NAME
        elif callback_data == "stats":
            await self.stats_command(query, context)
            return MAIN_MENU
        elif callback_data == "help":
            await self.help_command(query, context)
            return MAIN_MENU

    async def help_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Команда помощи"""
        help_text = """
        🤖 *AI Sales Bot - Руководство*

        *Основные команды:*
        /start - Главное меню
        /setup_agent - Настроить AI агента для вашего бизнеса
        /status - Текущий статус

        *Как это работает:*
        1. Вы описываете свой бизнес
        2. AI агент генерирует лидов
        3. Агент отправляет им персонализированные сообщения
        4. Вы получаете готовых покупателей

        *Цена:* 50,000 UZS/месяц

        Готовы начать? Нажмите /start
        """

        # Проверяем, это callback query или message
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(help_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(help_text, parse_mode='Markdown')

    async def setup_agent_start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Начало настройки агента"""
        await update.message.reply_text("🏢 Как называется ваш бизнес?")
        return BUSINESS_NAME

    async def get_business_name(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение названия бизнеса"""
        context.user_data['business_name'] = update.message.text

        keyboard = [
            [InlineKeyboardButton("🍽️ Ресторан", callback_data="type_restaurant")],
            [InlineKeyboardButton("🛍️ Магазин", callback_data="type_shop")],
            [InlineKeyboardButton("💼 Услуги", callback_data="type_service")],
            [InlineKeyboardButton("💅 Салон красоты", callback_data="type_salon")],
            [InlineKeyboardButton("🚗 Доставка", callback_data="type_delivery")],
            [InlineKeyboardButton("📚 Образование", callback_data="type_tutor")],
        ]
        reply_markup = InlineKeyboardMarkup(keyboard)

        await update.message.reply_text(
            f"✅ Название: {context.user_data['business_name']}\n\n"
            "Теперь выберите тип вашего бизнеса:",
            reply_markup=reply_markup
        )
        return BUSINESS_TYPE

    async def get_business_type(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение типа бизнеса через кнопку"""
        query = update.callback_query
        await query.answer()

        business_type = query.data.replace("type_", "")
        context.user_data['business_type'] = business_type

        await query.edit_message_text(
            "📍 Опишите вашу целевую аудиторию.\n"
            "Например: 'Мужчины 25-45 лет, которые ищут недорогой ремонт'"
        )
        return TARGET_AUDIENCE

    async def get_target_audience(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Получение целевой аудитории"""
        context.user_data['target_audience'] = update.message.text

        summary = f"""
        *Проверьте ваши данные:*

        📊 Бизнес: {context.user_data['business_name']}
        📂 Тип: {context.user_data['business_type']}
        👥 Аудитория: {context.user_data['target_audience']}

        Всё верно? Напишите "да" чтобы продолжить или "нет" для изменения
        """

        await update.message.reply_text(summary, parse_mode='Markdown')
        return CONFIRMING

    async def confirm_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Подтверждение и создание агента"""
        user_input = update.message.text.lower().strip()

        if user_input in ["да", "yes", "y", "ок", "ok"]:
            user_id = update.effective_user.id
            db = SessionLocal()

            try:
                # Создаём клиента
                client = Client(
                    telegram_id=str(user_id),
                    business_name=context.user_data['business_name'],
                    business_type=context.user_data['business_type'],
                    phone=update.effective_user.username or "unknown"
                )
                db.add(client)
                db.commit()

                # Создаём агента
                agent = Agent(
                    client_id=client.id,
                    name=f"Agent_{client.id}",
                    description=f"AI Agent for {client.business_name}",
                    target_audience=context.user_data['target_audience'],
                    business_context=f"Business: {client.business_name}, Type: {client.business_type}"
                )
                db.add(agent)
                db.commit()

                await update.message.reply_text(
                    f"✅ AI агент создан!\n\n"
                    f"Агент автоматически начнёт:\n"
                    f"• Генерировать лидов каждый час\n"
                    f"• Отправлять персонализированные сообщения\n"
                    f"• Квалифицировать интерес клиентов\n\n"
                    f"💰 Подписка: 50,000 UZS/месяц\n"
                    f"📊 Проверьте статистику командой /status",
                    parse_mode='Markdown'
                )

                # Запускаем первый цикл генерации лидов
                await self.trigger_lead_generation(client.id, update)

                return ConversationHandler.END
            except Exception as e:
                logger.error(f"Error creating agent: {e}")
                await update.message.reply_text(f"❌ Ошибка: {e}")
                return ConversationHandler.END
            finally:
                db.close()
        else:
            await update.message.reply_text("Введите 'да' для подтверждения или 'нет' для отмены")
            return CONFIRMING

    async def cancel_setup(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Отмена настройки"""
        await update.message.reply_text("Настройка отменена. Напишите /start для начала")
        return ConversationHandler.END

    async def trigger_lead_generation(self, client_id: int, update: Update):
        """Запускает генерацию лидов"""
        db = SessionLocal()
        try:
            client = db.query(Client).filter(Client.id == client_id).first()
            agent = db.query(Agent).filter(Agent.client_id == client_id).first()

            if agent:
                ai_agent = SalesAIAgent(agent.business_context, agent.target_audience)
                leads = self.lead_generator.generate_leads(count=5, business_type=client.business_type)

                for lead in leads:
                    msg_result = ai_agent.generate_lead_message(lead['name'], lead['field'])

                    db_lead = Lead(
                        client_id=client_id,
                        agent_id=agent.id,
                        lead_name=lead['name'],
                        lead_contact=lead['contact'],
                        lead_type="phone",
                        message_sent=msg_result.get('message', ''),
                        status="pending"
                    )
                    db.add(db_lead)

                db.commit()
                agent.leads_generated = len(leads)
                db.commit()

                await update.message.reply_text(
                    f"🎯 Первый раунд: сгенерировано {len(leads)} лидов\n"
                    f"💬 Сообщения готовы к отправке"
                )
        except Exception as e:
            logger.error(f"Lead generation error: {e}")
        finally:
            db.close()

    async def status_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Статус текущего клиента"""
        user_id = update.effective_user.id
        db = SessionLocal()

        try:
            client = db.query(Client).filter(Client.telegram_id == str(user_id)).first()

            if not client:
                reply_text = "Вы ещё не зарегистрированы. Напишите /start"
            else:
                agent = db.query(Agent).filter(Agent.client_id == client.id).first()

                if agent:
                    leads = db.query(Lead).filter(Lead.agent_id == agent.id).all()
                    conversions = len([l for l in leads if l.status == "converted"])

                    reply_text = f"""*Статус вашего агента*

📊 Генерировано лидов: {agent.leads_generated}
💬 Ответов получено: {len([l for l in leads if l.response])}
✅ Конверсий: {conversions}

🕐 Последнее обновление: только что"""
                else:
                    reply_text = "Агент не настроен. Напишите /setup_agent"
        finally:
            db.close()

        # Проверяем, это callback query или message
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(reply_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(reply_text, parse_mode='Markdown')

    async def stats_command(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Полная статистика"""
        user_id = update.effective_user.id
        db = SessionLocal()

        try:
            client = db.query(Client).filter(Client.telegram_id == str(user_id)).first()

            if not client:
                reply_text = "Вы ещё не зарегистрированы."
            else:
                agents = db.query(Agent).filter(Agent.client_id == client.id).all()

                stats_text = f"*📈 Полная статистика*\n\n"
                stats_text += f"🏢 Бизнес: {client.business_name}\n"
                stats_text += f"📂 Тип: {client.business_type}\n\n"

                total_leads = 0
                total_responses = 0
                total_conversions = 0

                for agent in agents:
                    leads = db.query(Lead).filter(Lead.agent_id == agent.id).all()
                    responses = len([l for l in leads if l.response])
                    conversions = len([l for l in leads if l.status == "converted"])

                    total_leads += len(leads)
                    total_responses += responses
                    total_conversions += conversions

                if total_leads > 0:
                    response_rate = (total_responses / total_leads) * 100
                    conversion_rate = (total_conversions / total_responses * 100) if total_responses > 0 else 0

                    stats_text += f"📊 *Метрики:*\n"
                    stats_text += f"• Всего лидов: {total_leads}\n"
                    stats_text += f"• Ответов: {total_responses} ({response_rate:.1f}%)\n"
                    stats_text += f"• Конверсий: {total_conversions} ({conversion_rate:.1f}%)\n"
                else:
                    stats_text += "Пока нет данных. Агент только начал работать."

                reply_text = stats_text
        finally:
            db.close()

        # Проверяем, это callback query или message
        if hasattr(update, 'callback_query') and update.callback_query:
            await update.callback_query.edit_message_text(reply_text, parse_mode='Markdown')
        else:
            await update.message.reply_text(reply_text, parse_mode='Markdown')

    async def handle_message(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Обработка обычных сообщений вне conversation"""
        text = update.message.text.lower()

        if "привет" in text or "hi" in text:
            await update.message.reply_text("👋 Привет! Чем я могу помочь? /help")
        elif "цена" in text or "стоимость" in text:
            await update.message.reply_text(f"💰 Подписка стоит {PRICE_PER_MONTH:,} UZS в месяц")
        else:
            await update.message.reply_text("Я не понял. Напишите /start для главного меню или /help для справки")

    def run(self):
        """Запускает бота"""
        self.app.run_polling()
