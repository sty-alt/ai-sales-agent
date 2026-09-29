import logging
import sys
from telegram_bot.bot import TelegramBot
from agents.automation import AutomationService
from payments.processor import PaymentProcessor
import signal

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

class AIAgentSystem:
    def __init__(self):
        self.bot = TelegramBot()
        self.automation = AutomationService()
        self.payments = PaymentProcessor()
        self.running = True

    def start(self):
        """Запускает всю систему"""
        logger.info("=" * 50)
        logger.info("🚀 AI SALES AGENT SYSTEM - STARTING")
        logger.info("=" * 50)

        # Запускаем автоматизацию
        try:
            self.automation.start()
            logger.info("✅ Automation Service Started")
        except Exception as e:
            logger.error(f"❌ Failed to start automation: {e}")
            sys.exit(1)

        # Запускаем Telegram бота
        try:
            logger.info("✅ Telegram Bot Starting...")
            logger.info("Bot is now listening for messages...")
            self.bot.run()
        except KeyboardInterrupt:
            logger.info("\n⛔ Shutting down...")
            self.stop()
        except Exception as e:
            logger.error(f"❌ Bot error: {e}")
            self.stop()
            sys.exit(1)

    def stop(self):
        """Останавливает систему"""
        self.automation.stop()
        logger.info("✅ System Shutdown Complete")

    def handle_signal(self, sig, frame):
        """Обработчик сигнала Ctrl+C"""
        logger.info("\n⛔ Received interrupt signal...")
        self.stop()
        sys.exit(0)

def print_banner():
    """Выводит приветственный баннер"""
    banner = """
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║         🤖 AI SALES AGENT SYSTEM FOR TASHKENT 🤖        ║
    ║                                                           ║
    ║         Автоматизированная генерация лидов              ║
    ║                                                           ║
    ║         💼 Бизнес: $50,000 UZS/месяц                    ║
    ║         📊 ROI: Генерирует лидов автоматически          ║
    ║         🎯 Масштаб: Неограниченное количество клиентов  ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝

    📋 ФУНКЦИИ:
    ✓ AI генерация персонализированных сообщений
    ✓ Автоматическая квалификация лидов
    ✓ Telegram интеграция для клиентов
    ✓ Статистика и аналитика в реальном времени
    ✓ Система платежей

    🚀 СТАРТ: Отправьте /start в Telegram боте
    📞 КОНТАКТ: @YourBotHandle

    """
    print(banner)

if __name__ == "__main__":
    print_banner()

    try:
        system = AIAgentSystem()

        # Регистрируем обработчик сигналов
        signal.signal(signal.SIGINT, system.handle_signal)

        # Запускаем систему
        system.start()

    except KeyboardInterrupt:
        logger.info("Shutdown by user")
    except Exception as e:
        logger.error(f"Fatal error: {e}")
        sys.exit(1)
