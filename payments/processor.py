from datetime import datetime, timedelta
from database.models import SessionLocal, Payment, Client
import logging

logger = logging.getLogger(__name__)

class PaymentProcessor:
    def __init__(self):
        self.monthly_price = 50000  # UZS
        self.currencies = {
            "UZS": 1,
            "USD": 12500,
            "RUB": 143
        }

    def create_invoice(self, client_id: int, currency: str = "UZS") -> dict:
        """
        Создаёт счёт для клиента
        """
        db = SessionLocal()

        try:
            client = db.query(Client).filter(Client.id == client_id).first()

            if not client:
                return {"error": "Client not found"}

            # Конвертируем цену
            rate = self.currencies.get(currency, 1)
            amount = self.monthly_price / rate

            # Создаём платёж
            payment = Payment(
                client_id=client_id,
                amount=amount,
                currency=currency,
                status="pending",
                payment_method="transfer",
                transaction_id=f"TXN_{client_id}_{datetime.utcnow().timestamp()}",
                expires_at=datetime.utcnow() + timedelta(days=3)
            )
            db.add(payment)
            db.commit()

            invoice = {
                "id": payment.id,
                "client_name": client.business_name,
                "amount": amount,
                "currency": currency,
                "created_at": payment.created_at.isoformat(),
                "expires_at": payment.expires_at.isoformat(),
                "transaction_id": payment.transaction_id,
                "description": "AI Sales Agent Monthly Subscription"
            }

            logger.info(f"✅ Invoice created: {payment.transaction_id}")
            return invoice

        finally:
            db.close()

    def process_payment(self, transaction_id: str) -> dict:
        """
        Обрабатывает платёж и активирует подписку
        """
        db = SessionLocal()

        try:
            payment = db.query(Payment).filter(
                Payment.transaction_id == transaction_id
            ).first()

            if not payment:
                return {"error": "Payment not found"}

            if payment.status == "completed":
                return {"error": "Payment already completed"}

            # Отмечаем платёж как завершённый
            payment.status = "completed"

            # Активируем подписку на месяц
            client = db.query(Client).filter(Client.id == payment.client_id).first()
            client.is_active = True
            client.subscription_end = datetime.utcnow() + timedelta(days=30)

            db.commit()

            logger.info(f"✅ Payment processed: {transaction_id}")

            return {
                "status": "success",
                "client_id": client.id,
                "subscription_end": client.subscription_end.isoformat(),
                "message": "Подписка активирована на 30 дней"
            }

        except Exception as e:
            logger.error(f"❌ Payment processing error: {e}")
            return {"error": str(e)}
        finally:
            db.close()

    def check_subscription_expiry(self):
        """
        Проверяет истекшие подписки и деактивирует их
        """
        db = SessionLocal()

        try:
            expired_clients = db.query(Client).filter(
                Client.subscription_end < datetime.utcnow(),
                Client.is_active == True
            ).all()

            for client in expired_clients:
                client.is_active = False
                logger.info(f"⏰ Subscription expired for client {client.id}")

            db.commit()
            return len(expired_clients)

        finally:
            db.close()

    def get_payment_methods(self) -> dict:
        """
        Возвращает доступные методы оплаты для Ташкента
        """
        return {
            "methods": [
                {
                    "name": "Visa/MasterCard",
                    "code": "card",
                    "available": True,
                    "description": "Кредитная карта"
                },
                {
                    "name": "Click",
                    "code": "click",
                    "available": True,
                    "description": "Узбекская платёжная система"
                },
                {
                    "name": "Payme",
                    "code": "payme",
                    "available": True,
                    "description": "Мобильный кошелёк"
                },
                {
                    "name": "Bank Transfer",
                    "code": "transfer",
                    "available": True,
                    "description": "Банковский перевод"
                }
            ]
        }

    def get_invoice_text(self, invoice: dict) -> str:
        """
        Генерирует текст счёта для отправки клиенту
        """
        text = f"""
        📋 *СЧЁТ НА ОПЛАТУ*

        {invoice['client_name']}

        Услуга: {invoice['description']}
        Сумма: {invoice['amount']} {invoice['currency']}

        ID Транзакции: `{invoice['transaction_id']}`

        Действителен до: {invoice['expires_at'][:10]}

        *Способы оплаты:*
        • Click (Узбекистан)
        • Payme (Узбекистан)
        • Visa/MasterCard
        • Банковский перевод

        После оплаты отправьте скриншот подтверждения.
        """
        return text.strip()

    def get_revenue_stats(self) -> dict:
        """
        Получает статистику доходов
        """
        db = SessionLocal()

        try:
            completed_payments = db.query(Payment).filter(
                Payment.status == "completed"
            ).all()

            total_revenue = sum([p.amount * self.currencies.get(p.currency, 1) / 12500 for p in completed_payments])  # In USD
            active_subscriptions = db.query(Client).filter(Client.is_active == True).count()

            return {
                "total_revenue_usd": total_revenue,
                "active_subscriptions": active_subscriptions,
                "monthly_mrr": active_subscriptions * (self.monthly_price / 12500),  # MRR in USD
                "total_payments": len(completed_payments)
            }

        finally:
            db.close()
