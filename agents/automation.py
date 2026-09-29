from apscheduler.schedulers.background import BackgroundScheduler
from apscheduler.triggers.interval import IntervalTrigger
from database.models import SessionLocal, Agent, Lead, Client
from agents.sales_agent import SalesAIAgent
from leads.generator import LeadGenerator
import logging
from datetime import datetime

logger = logging.getLogger(__name__)

class AutomationService:
    def __init__(self):
        self.scheduler = BackgroundScheduler()
        self.lead_generator = LeadGenerator()
        self.setup_jobs()

    def setup_jobs(self):
        """Настраивает автоматические задачи"""

        # Генерация лидов каждый час
        self.scheduler.add_job(
            self.generate_leads_job,
            IntervalTrigger(hours=1),
            id='generate_leads',
            name='Generate new leads'
        )

        # Проверка ответов каждые 30 минут
        self.scheduler.add_job(
            self.process_responses_job,
            IntervalTrigger(minutes=30),
            id='process_responses',
            name='Process lead responses'
        )

        # Отправка follow-up каждые 4 часа
        self.scheduler.add_job(
            self.followup_job,
            IntervalTrigger(hours=4),
            id='followup',
            name='Send follow-up messages'
        )

        # Анализ метрик каждый день
        self.scheduler.add_job(
            self.analyze_metrics_job,
            IntervalTrigger(hours=24),
            id='analyze_metrics',
            name='Analyze metrics'
        )

    def generate_leads_job(self):
        """Генерирует новых лидов для активных агентов"""
        logger.info("🎯 Starting lead generation job...")
        db = SessionLocal()

        try:
            agents = db.query(Agent).filter(Agent.is_active == True).all()

            for agent in agents:
                client = db.query(Client).filter(Client.id == agent.client_id).first()

                if client:
                    # Генерируем лидов
                    leads = self.lead_generator.generate_leads(
                        count=5,
                        business_type=client.business_type
                    )

                    # Создаём AI агента
                    ai_agent = SalesAIAgent(
                        agent.business_context,
                        agent.target_audience
                    )

                    # Для каждого лида генерируем сообщение
                    for lead in leads:
                        msg_result = ai_agent.generate_lead_message(
                            lead['name'],
                            lead['field']
                        )

                        # Сохраняем в БД
                        db_lead = Lead(
                            client_id=client.id,
                            agent_id=agent.id,
                            lead_name=lead['name'],
                            lead_contact=lead['contact'],
                            lead_type="phone",
                            message_sent=msg_result['message'],
                            status="pending"
                        )
                        db.add(db_lead)

                    db.commit()
                    agent.leads_generated += len(leads)
                    db.commit()

                    logger.info(f"✅ Generated {len(leads)} leads for agent {agent.id}")

        except Exception as e:
            logger.error(f"❌ Lead generation error: {e}")
        finally:
            db.close()

    def process_responses_job(self):
        """Обрабатывает ответы от лидов"""
        logger.info("💬 Processing lead responses...")
        db = SessionLocal()

        try:
            # Находим лиды с ответами, которые ещё не обработаны
            pending_leads = db.query(Lead).filter(
                Lead.response != None,
                Lead.status == "pending"
            ).all()

            for lead in pending_leads:
                agent = db.query(Agent).filter(Agent.id == lead.agent_id).first()

                if agent:
                    ai_agent = SalesAIAgent(
                        agent.business_context,
                        agent.target_audience
                    )

                    # Квалифицируем лид
                    qualification = ai_agent.qualify_lead(lead.response)

                    lead.status = qualification.get("action", "pending")

                    if qualification.get("interest_level") == "high":
                        agent.conversions += 1
                        lead.status = "converted"

                    db.commit()
                    logger.info(f"✅ Processed lead {lead.id}: {lead.status}")

        except Exception as e:
            logger.error(f"❌ Response processing error: {e}")
        finally:
            db.close()

    def followup_job(self):
        """Отправляет follow-up сообщения"""
        logger.info("📬 Sending follow-up messages...")
        db = SessionLocal()

        try:
            # Находим лиды с ответами, но без конверсии
            followup_leads = db.query(Lead).filter(
                Lead.response != None,
                Lead.status == "follow_up"
            ).all()

            for lead in followup_leads:
                agent = db.query(Agent).filter(Agent.id == lead.agent_id).first()

                if agent:
                    ai_agent = SalesAIAgent(
                        agent.business_context,
                        agent.target_audience
                    )

                    # Генерируем follow-up
                    followup_msg = ai_agent.generate_follow_up(
                        lead.lead_name,
                        lead.message_sent,
                        lead.response
                    )

                    # В реальной системе здесь была бы отправка в Telegram/Email
                    logger.info(f"📬 Follow-up for {lead.lead_name}: {followup_msg[:50]}...")

        except Exception as e:
            logger.error(f"❌ Follow-up error: {e}")
        finally:
            db.close()

    def analyze_metrics_job(self):
        """Анализирует метрики всех агентов"""
        logger.info("📊 Analyzing metrics...")
        db = SessionLocal()

        try:
            agents = db.query(Agent).all()

            for agent in agents:
                leads = db.query(Lead).filter(Lead.agent_id == agent.id).all()

                total_leads = len(leads)
                responses = len([l for l in leads if l.response])
                conversions = len([l for l in leads if l.status == "converted"])

                if total_leads > 0:
                    ai_agent = SalesAIAgent(
                        agent.business_context,
                        agent.target_audience
                    )

                    metrics = ai_agent.analyze_business_metrics(
                        total_leads,
                        responses,
                        conversions
                    )

                    logger.info(
                        f"📊 Agent {agent.id} metrics: "
                        f"Response Rate: {metrics['response_rate']:.1f}%, "
                        f"Conversion Rate: {metrics['conversion_rate']:.1f}%"
                    )

        except Exception as e:
            logger.error(f"❌ Metrics analysis error: {e}")
        finally:
            db.close()

    def start(self):
        """Запускает планировщик"""
        self.scheduler.start()
        logger.info("🚀 Automation service started")

    def stop(self):
        """Остановить планировщик"""
        self.scheduler.shutdown()
        logger.info("⛔ Automation service stopped")
