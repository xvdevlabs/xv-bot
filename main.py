from dotenv import load_dotenv
import logging
import json
import os
from datetime import datetime
from typing import Dict, List, Optional
from telegram import Update, InlineKeyboardButton, InlineKeyboardMarkup, ReplyKeyboardMarkup, KeyboardButton
from telegram.ext import Application, CommandHandler, CallbackQueryHandler, MessageHandler, filters, ContextTypes
import sqlite3
import uuid

logging.basicConfig(
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s', level=logging.INFO
)
logger = logging.getLogger(__name__)

load_dotenv()
BOT_TOKEN = os.getenv("BOT_TOKEN")

ADMIN_IDS = [int(x.strip()) for x in os.getenv("ADMIN_ID", "").split(",") if x.strip()]

def init_database():
    conn = sqlite3.connect('xv_dev_labs.db')
    cursor = conn.cursor()
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS projects (
            id TEXT PRIMARY KEY,
            client_id INTEGER,
            service_type TEXT,
            description TEXT,
            status TEXT DEFAULT 'pending',
            created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
            updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
        )
    ''')
    
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_preferences (
            user_id INTEGER PRIMARY KEY,
            language TEXT DEFAULT 'en',
            current_messages TEXT DEFAULT '[]'
        )
    ''')
    
    conn.commit()
    conn.close()

LANGUAGES = {
    'en': {
        'welcome': "🎉 Welcome to XV Dev Labs! 🚀\n\nWe're here to help you with your blockchain and development needs. How can we assist you today? Please choose an option below:",
        'ask_question': "❓ Ask a Question",
        'support': "🛠️ Support",
        'services': "💼 Services",
        'project_status': "📊 My Project Status",
        'back': "⬅️ Back",
        'what_question': "💭 What would you like to know? Please feel free to ask any question!",
        'send_project_id': "🔍 Please send your project ID to get support:",
        'invalid_id': "❌ Invalid project ID. Please check and try again.",
        'how_help': "✅ Project found! How can we help you with this project?",
        'choose_service': "🔧 Choose a service you need:",
        'vyper_contract': "🐍 Vyper Smart Contract",
        'solidity_contract': "⚡ Solidity Smart Contract",
        'unit_test': "🧪 Unit Test",
        'fuzz_test': "🔬 Fuzz Test",
        'security_audit': "🔐 Security Review/Audit",
        'create_website': "🌐 Create Website",
        'create_bot': "🤖 Create Bot",
        'describe_needs': "📝 Please describe exactly what you need for {}:",
        'finish': "✅ Finish",
        'thanks_contact': "🙏 Thank you! Our team will review your request and contact you soon.",
        'enter_project_id': "🆔 Please enter your project ID to check status:",
        'project_not_found': "❌ Project not found. Please check your project ID.",
        'language_changed': "✅ Language changed to English",
        'select_language': "🌍 Select your preferred language:",
        'collecting_messages': "📝 You can send multiple messages. Click 'Finish' when done.",
    },
    'ru': {
        'welcome': "🎉 Добро пожаловать в XV Dev Labs! 🚀\n\nМы здесь, чтобы помочь вам с вашими потребностями в блокчейне и разработке. Как мы можем помочь вам сегодня? Пожалуйста, выберите опцию ниже:",
        'ask_question': "❓ Задать вопрос",
        'support': "🛠️ Поддержка",
        'services': "💼 Услуги",
        'project_status': "📊 Статус моего проекта",
        'back': "⬅️ Назад",
        'what_question': "💭 Что бы вы хотели узнать? Пожалуйста, задавайте любой вопрос!",
        'send_project_id': "🔍 Пожалуйста, отправьте ID вашего проекта для получения поддержки:",
        'invalid_id': "❌ Недействительный ID проекта. Пожалуйста, проверьте и попробуйте снова.",
        'how_help': "✅ Проект найден! Как мы можем помочь вам с этим проектом?",
        'choose_service': "🔧 Выберите нужную услугу:",
        'vyper_contract': "🐍 Смарт-контракт Vyper",
        'solidity_contract': "⚡ Смарт-контракт Solidity",
        'unit_test': "🧪 Модульное тестирование",
        'fuzz_test': "🔬 Фаззинг тестирование",
        'security_audit': "🔐 Аудит безопасности",
        'create_website': "🌐 Создание сайта",
        'create_bot': "🤖 Создание бота",
        'describe_needs': "📝 Пожалуйста, опишите точно, что вам нужно для {}:",
        'finish': "✅ Завершить",
        'thanks_contact': "🙏 Спасибо! Наша команда рассмотрит ваш запрос и свяжется с вами в ближайшее время.",
        'enter_project_id': "🆔 Пожалуйста, введите ID вашего проекта для проверки статуса:",
        'project_not_found': "❌ Проект не найден. Пожалуйста, проверьте ID проекта.",
        'language_changed': "✅ Язык изменен на русский",
        'select_language': "🌍 Выберите предпочитаемый язык:",
        'collecting_messages': "📝 Вы можете отправить несколько сообщений. Нажмите 'Завершить', когда закончите.",
    },
    'ar': {
        'welcome': "🎉 مرحباً بكم في XV Dev Labs! 🚀\n\nنحن هنا لمساعدتكم في احتياجاتكم من البلوك تشين والتطوير. كيف يمكننا مساعدتكم اليوم؟ يرجى اختيار خيار أدناه:",
        'ask_question': "❓ اسأل سؤال",
        'support': "🛠️ الدعم",
        'services': "💼 الخدمات",
        'project_status': "📊 حالة مشروعي",
        'back': "⬅️ العودة",
        'what_question': "💭 ماذا تريد أن تعرف؟ يرجى طرح أي سؤال!",
        'send_project_id': "🔍 يرجى إرسال معرف مشروعك للحصول على الدعم:",
        'invalid_id': "❌ معرف مشروع غير صالح. يرجى المراجعة والمحاولة مرة أخرى.",
        'how_help': "✅ تم العثور على المشروع! كيف يمكننا مساعدتك في هذا المشروع؟",
        'choose_service': "🔧 اختر الخدمة التي تحتاجها:",
        'vyper_contract': "🐍 عقد ذكي Vyper",
        'solidity_contract': "⚡ عقد ذكي Solidity",
        'unit_test': "🧪 اختبار الوحدة",
        'fuzz_test': "🔬 اختبار Fuzz",
        'security_audit': "🔐 مراجعة/تدقيق الأمان",
        'create_website': "🌐 إنشاء موقع ويب",
        'create_bot': "🤖 إنشاء بوت",
        'describe_needs': "📝 يرجى وصف ما تحتاجه بالضبط لـ {}:",
        'finish': "✅ إنهاء",
        'thanks_contact': "🙏 شكراً لك! سيراجع فريقنا طلبك وسيتواصل معك قريباً.",
        'enter_project_id': "🆔 يرجى إدخال معرف مشروعك للتحقق من الحالة:",
        'project_not_found': "❌ المشروع غير موجود. يرجى التحقق من معرف المشروع.",
        'language_changed': "✅ تم تغيير اللغة إلى العربية",
        'select_language': "🌍 اختر لغتك المفضلة:",
        'collecting_messages': "📝 يمكنك إرسال عدة رسائل. انقر 'إنهاء' عند الانتهاء.",
    },
    'fa': {
        'welcome': "🎉 به XV Dev Labs خوش آمدید! 🚀\n\nما اینجا هستیم تا در نیازهای بلاک‌چین و توسعه شما کمک کنیم. امروز چگونه می‌توانیم به شما کمک کنیم؟ لطفاً یکی از گزینه‌های زیر را انتخاب کنید:",
        'ask_question': "❓ سوال بپرسید",
        'support': "🛠️ پشتیبانی",
        'services': "💼 خدمات",
        'project_status': "📊 وضعیت پروژه من",
        'back': "⬅️ بازگشت",
        'what_question': "💭 چه چیزی می‌خواهید بدانید؟ لطفاً هر سوالی بپرسید!",
        'send_project_id': "🔍 لطفاً شناسه پروژه خود را برای دریافت پشتیبانی ارسال کنید:",
        'invalid_id': "❌ شناسه پروژه نامعتبر. لطفاً بررسی کرده و دوباره تلاش کنید.",
        'how_help': "✅ پروژه پیدا شد! چگونه می‌توانیم در این پروژه به شما کمک کنیم؟",
        'choose_service': "🔧 خدمتی را که نیاز دارید انتخاب کنید:",
        'vyper_contract': "🐍 قرارداد هوشمند Vyper",
        'solidity_contract': "⚡ قرارداد هوشمند Solidity",
        'unit_test': "🧪 تست واحد",
        'fuzz_test': "🔬 تست Fuzz",
        'security_audit': "🔐 بررسی/ممیزی امنیت",
        'create_website': "🌐 ایجاد وب‌سایت",
        'create_bot': "🤖 ایجاد ربات",
        'describe_needs': "📝 لطفاً دقیقاً توضیح دهید که برای {} چه نیاز دارید:",
        'finish': "✅ پایان",
        'thanks_contact': "🙏 متشکرم! تیم ما درخواست شما را بررسی کرده و به زودی با شما تماس خواهد گرفت.",
        'enter_project_id': "🆔 لطفاً شناسه پروژه خود را برای بررسی وضعیت وارد کنید:",
        'project_not_found': "❌ پروژه پیدا نشد. لطفاً شناسه پروژه را بررسی کنید.",
        'language_changed': "✅ زبان به فارسی تغییر کرد",
        'select_language': "🌍 زبان مورد نظر خود را انتخاب کنید:",
        'collecting_messages': "📝 می‌توانید چندین پیام ارسال کنید. وقتی تمام کردید 'پایان' را کلیک کنید.",
    },
    'de': {
        'welcome': "🎉 Willkommen bei XV Dev Labs! 🚀\n\nWir sind hier, um Ihnen bei Ihren Blockchain- und Entwicklungsbedürfnissen zu helfen. Wie können wir Ihnen heute helfen? Bitte wählen Sie eine Option unten:",
        'ask_question': "❓ Frage stellen",
        'support': "🛠️ Support",
        'services': "💼 Dienstleistungen",
        'project_status': "📊 Mein Projektstatus",
        'back': "⬅️ Zurück",
        'what_question': "💭 Was möchten Sie wissen? Bitte stellen Sie jede Frage!",
        'send_project_id': "🔍 Bitte senden Sie Ihre Projekt-ID für Support:",
        'invalid_id': "❌ Ungültige Projekt-ID. Bitte überprüfen und erneut versuchen.",
        'how_help': "✅ Projekt gefunden! Wie können wir Ihnen bei diesem Projekt helfen?",
        'choose_service': "🔧 Wählen Sie einen benötigten Service:",
        'vyper_contract': "🐍 Vyper Smart Contract",
        'solidity_contract': "⚡ Solidity Smart Contract",
        'unit_test': "🧪 Unit Test",
        'fuzz_test': "🔬 Fuzz Test",
        'security_audit': "🔐 Sicherheitsüberprüfung/Audit",
        'create_website': "🌐 Website erstellen",
        'create_bot': "🤖 Bot erstellen",
        'describe_needs': "📝 Bitte beschreiben Sie genau, was Sie für {} benötigen:",
        'finish': "✅ Fertig",
        'thanks_contact': "🙏 Vielen Dank! Unser Team wird Ihre Anfrage prüfen und sich bald bei Ihnen melden.",
        'enter_project_id': "🆔 Bitte geben Sie Ihre Projekt-ID ein, um den Status zu überprüfen:",
        'project_not_found': "❌ Projekt nicht gefunden. Bitte überprüfen Sie Ihre Projekt-ID.",
        'language_changed': "✅ Sprache auf Deutsch geändert",
        'select_language': "🌍 Wählen Sie Ihre bevorzugte Sprache:",
        'collecting_messages': "📝 Sie können mehrere Nachrichten senden. Klicken Sie 'Fertig', wenn Sie fertig sind.",
    },
    'fr': {
        'welcome': "🎉 Bienvenue chez XV Dev Labs! 🚀\n\nNous sommes là pour vous aider avec vos besoins en blockchain et développement. Comment pouvons-nous vous aider aujourd'hui? Veuillez choisir une option ci-dessous:",
        'ask_question': "❓ Poser une question",
        'support': "🛠️ Support",
        'services': "💼 Services",
        'project_status': "📊 Statut de mon projet",
        'back': "⬅️ Retour",
        'what_question': "💭 Que souhaitez-vous savoir? N'hésitez pas à poser n'importe quelle question!",
        'send_project_id': "🔍 Veuillez envoyer votre ID de projet pour obtenir du support:",
        'invalid_id': "❌ ID de projet invalide. Veuillez vérifier et réessayer.",
        'how_help': "✅ Projet trouvé! Comment pouvons-nous vous aider avec ce projet?",
        'choose_service': "🔧 Choisissez un service dont vous avez besoin:",
        'vyper_contract': "🐍 Contrat intelligent Vyper",
        'solidity_contract': "⚡ Contrat intelligent Solidity",
        'unit_test': "🧪 Test unitaire",
        'fuzz_test': "🔬 Test Fuzz",
        'security_audit': "🔐 Audit de sécurité",
        'create_website': "🌐 Créer un site web",
        'create_bot': "🤖 Créer un bot",
        'describe_needs': "📝 Veuillez décrire exactement ce dont vous avez besoin pour {}:",
        'finish': "✅ Terminer",
        'thanks_contact': "🙏 Merci! Notre équipe examinera votre demande et vous contactera bientôt.",
        'enter_project_id': "🆔 Veuillez entrer votre ID de projet pour vérifier le statut:",
        'project_not_found': "❌ Projet non trouvé. Veuillez vérifier votre ID de projet.",
        'language_changed': "✅ Langue changée en français",
        'select_language': "🌍 Sélectionnez votre langue préférée:",
        'collecting_messages': "📝 Vous pouvez envoyer plusieurs messages. Cliquez 'Terminer' quand vous avez fini.",
    }
}

USER_STATES = {}

class XVDevLabsBot:
    def __init__(self):
        init_database() 

    def get_user_language(self, user_id: int) -> str:
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT language FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        return result[0] if result else 'en'

    def set_user_language(self, user_id: int, language: str):
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_id, language)
            VALUES (?, ?)
        ''', (user_id, language))
        conn.commit()
        conn.close()

    def get_text(self, user_id: int, key: str) -> str:
        lang = self.get_user_language(user_id)
        return LANGUAGES.get(lang, LANGUAGES['en']).get(key, LANGUAGES['en'][key])

    def create_main_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(self.get_text(user_id, 'ask_question'), callback_data='ask_question')],
            [InlineKeyboardButton(self.get_text(user_id, 'support'), callback_data='support')],
            [InlineKeyboardButton(self.get_text(user_id, 'services'), callback_data='services')],
            [InlineKeyboardButton(self.get_text(user_id, 'project_status'), callback_data='project_status')],
            [InlineKeyboardButton("🌍 Language", callback_data='change_language')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_back_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [[InlineKeyboardButton(self.get_text(user_id, 'back'), callback_data='back_to_main')]]
        return InlineKeyboardMarkup(keyboard)

    def create_services_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(self.get_text(user_id, 'vyper_contract'), callback_data='service_vyper')],
            [InlineKeyboardButton(self.get_text(user_id, 'solidity_contract'), callback_data='service_solidity')],
            [InlineKeyboardButton(self.get_text(user_id, 'unit_test'), callback_data='service_unittest')],
            [InlineKeyboardButton(self.get_text(user_id, 'fuzz_test'), callback_data='service_fuzztest')],
            [InlineKeyboardButton(self.get_text(user_id, 'security_audit'), callback_data='service_audit')],
            [InlineKeyboardButton(self.get_text(user_id, 'create_website'), callback_data='service_website')],
            [InlineKeyboardButton(self.get_text(user_id, 'create_bot'), callback_data='service_bot')],
            [InlineKeyboardButton(self.get_text(user_id, 'back'), callback_data='back_to_main')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_language_keyboard(self) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton("🇺🇸 English", callback_data='lang_en')],
            [InlineKeyboardButton("🇷🇺 Русский", callback_data='lang_ru')],
            [InlineKeyboardButton("🇸🇦 العربية", callback_data='lang_ar')],
            [InlineKeyboardButton("🇮🇷 فارسی", callback_data='lang_fa')],
            [InlineKeyboardButton("🇩🇪 Deutsch", callback_data='lang_de')],
            [InlineKeyboardButton("🇫🇷 Français", callback_data='lang_fr')],
            [InlineKeyboardButton("⬅️ Back", callback_data='back_to_main')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def create_finish_back_keyboard(self, user_id: int) -> InlineKeyboardMarkup:
        keyboard = [
            [InlineKeyboardButton(self.get_text(user_id, 'finish'), callback_data='finish_service')],
            [InlineKeyboardButton(self.get_text(user_id, 'back'), callback_data='services')]
        ]
        return InlineKeyboardMarkup(keyboard)

    def is_valid_project_id(self, project_id: str) -> bool:
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT id FROM projects WHERE id = ?', (project_id,))
        result = cursor.fetchone()
        conn.close()
        return result is not None

    def get_project_status(self, project_id: str) -> Optional[Dict]:
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT * FROM projects WHERE id = ?', (project_id,))
        result = cursor.fetchone()
        conn.close()
        if result:
            return {
                'id': result[0],
                'client_id': result[1],
                'service_type': result[2],
                'description': result[3],
                'status': result[4],
                'created_at': result[5],
                'updated_at': result[6]
            }
        return None

    def save_user_messages(self, user_id: int, messages: List[str]):
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('''
            INSERT OR REPLACE INTO user_preferences (user_id, language, current_messages)
            VALUES (?, ?, ?)
        ''', (user_id, self.get_user_language(user_id), json.dumps(messages)))
        conn.commit()
        conn.close()

    def get_user_messages(self, user_id: int) -> List[str]:
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT current_messages FROM user_preferences WHERE user_id = ?', (user_id,))
        result = cursor.fetchone()
        conn.close()
        if result and result[0]:
            return json.loads(result[0])
        return []

    def clear_user_messages(self, user_id: int):
        self.save_user_messages(user_id, [])

    async def start(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        welcome_text = self.get_text(user_id, 'welcome')
        keyboard = self.create_main_keyboard(user_id)
        
        if update.message:
            await update.message.reply_text(welcome_text, reply_markup=keyboard)
        else:
            await update.callback_query.edit_message_text(welcome_text, reply_markup=keyboard)

    async def button_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        query = update.callback_query
        await query.answer()
        user_id = query.from_user.id
        data = query.data

        if data == 'back_to_main':
            USER_STATES.pop(user_id, None)
            self.clear_user_messages(user_id)
            await self.start(update, context)
            
        elif data == 'ask_question':
            USER_STATES[user_id] = 'asking_question'
            text = self.get_text(user_id, 'what_question')
            keyboard = self.create_back_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == 'support':
            USER_STATES[user_id] = 'support_enter_id'
            text = self.get_text(user_id, 'send_project_id')
            keyboard = self.create_back_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == 'services':
            USER_STATES[user_id] = 'choosing_service'
            text = self.get_text(user_id, 'choose_service')
            keyboard = self.create_services_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == 'project_status':
            USER_STATES[user_id] = 'check_project_status'
            text = self.get_text(user_id, 'enter_project_id')
            keyboard = self.create_back_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == 'change_language':
            text = self.get_text(user_id, 'select_language')
            keyboard = self.create_language_keyboard()
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data.startswith('lang_'):
            lang = data.split('_')[1]
            self.set_user_language(user_id, lang)
            text = self.get_text(user_id, 'language_changed')
            keyboard = self.create_main_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data.startswith('service_'):
            service_type = data.replace('service_', '')
            service_names = {
                'vyper': self.get_text(user_id, 'vyper_contract'),
                'solidity': self.get_text(user_id, 'solidity_contract'),
                'unittest': self.get_text(user_id, 'unit_test'),
                'fuzztest': self.get_text(user_id, 'fuzz_test'),
                'audit': self.get_text(user_id, 'security_audit'),
                'website': self.get_text(user_id, 'create_website'),
                'bot': self.get_text(user_id, 'create_bot')
            }
            
            USER_STATES[user_id] = f'service_description_{service_type}'
            self.clear_user_messages(user_id)
            
            text = self.get_text(user_id, 'describe_needs').format(service_names.get(service_type, service_type))
            text += f"\n\n{self.get_text(user_id, 'collecting_messages')}"
            keyboard = self.create_finish_back_keyboard(user_id)
            await query.edit_message_text(text, reply_markup=keyboard)
            
        elif data == 'finish_service':
            messages = self.get_user_messages(user_id)
            if messages:
                admin_text = f"🆕 New service request from user {user_id}:\n"
                admin_text += f"Service: {USER_STATES.get(user_id, '').replace('service_description_', '')}\n"
                admin_text += f"Messages:\n" + "\n".join(f"• {msg}" for msg in messages)
        
                for admin_id in ADMIN_IDS:
                    try:
                        await context.bot.send_message(admin_id, admin_text)
                    except Exception as e:
                        logger.error(f"Failed to send to admin {admin_id}: {e}")
        
                self.clear_user_messages(user_id)
                USER_STATES.pop(user_id, None)
        
                text = self.get_text(user_id, 'thanks_contact')
                keyboard = self.create_main_keyboard(user_id)
                await query.edit_message_text(text, reply_markup=keyboard)

    async def message_handler(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        user_id = update.effective_user.id
        message_text = update.message.text
        
        state = USER_STATES.get(user_id)
        
        if state == 'asking_question':
            username = update.effective_user.username or "No username"
            first_name = update.effective_user.first_name or "Unknown"
            
            admin_text = f"❓ NEW QUESTION\n"
            admin_text += f"👤 User: {first_name} (@{username})\n"
            admin_text += f"🆔 User ID: {user_id}\n"
            admin_text += f"💬 Question:\n{message_text}\n\n"
            admin_text += f"Reply with: /reply {user_id} your_message"
            
            message_sent = False
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(admin_id, admin_text)
                    message_sent = True
                    logger.info(f"Question sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send question to admin {admin_id}: {e}")
            
            if message_sent:
                confirmation = "✅ Your question has been sent to our team. We'll get back to you soon!"
            else:
                confirmation = "❌ Sorry, there was an issue sending your question. Please try again later."
                
            keyboard = self.create_main_keyboard(user_id)
            await update.message.reply_text(confirmation, reply_markup=keyboard)
            USER_STATES.pop(user_id, None)
            
        elif state == 'support_enter_id':
            if self.is_valid_project_id(message_text.strip()):
                USER_STATES[user_id] = f'support_project_{message_text.strip()}'
                text = self.get_text(user_id, 'how_help')
                keyboard = self.create_back_keyboard(user_id)
                await update.message.reply_text(text, reply_markup=keyboard)
            else:
                text = self.get_text(user_id, 'invalid_id')
                keyboard = self.create_back_keyboard(user_id)
                await update.message.reply_text(text, reply_markup=keyboard)
                
        elif state == 'check_project_status':
            project_id = message_text.strip()
            project = self.get_project_status(project_id)
            
            if project:
                status_text = f"📋 Project Status:\n"
                status_text += f"🆔 ID: {project['id']}\n"
                status_text += f"🔧 Service: {project['service_type']}\n"
                status_text += f"📊 Status: {project['status']}\n"
                status_text += f"📅 Created: {project['created_at']}\n"
                status_text += f"🔄 Updated: {project['updated_at']}\n"
                if project['description']:
                    status_text += f"📝 Description: {project['description'][:100]}..."
            else:
                status_text = self.get_text(user_id, 'project_not_found')
            
            keyboard = self.create_main_keyboard(user_id)
            await update.message.reply_text(status_text, reply_markup=keyboard)
            USER_STATES.pop(user_id, None)
            
        elif state and state.startswith('service_description_'):
            messages = self.get_user_messages(user_id)
            messages.append(message_text)
            self.save_user_messages(user_id, messages)
            
            confirmation = f"✅ Message added ({len(messages)} total)! Send more details or click 'Finish' when done."
            keyboard = self.create_finish_back_keyboard(user_id)
            await update.message.reply_text(confirmation, reply_markup=keyboard)
            
        elif state and state.startswith('support_project_'):
            project_id = state.replace('support_project_', '')
            username = update.effective_user.username or "No username"
            first_name = update.effective_user.first_name or "Unknown"
            
            admin_text = f"🛠️ SUPPORT REQUEST\n"
            admin_text += f"👤 User: {first_name} (@{username})\n"
            admin_text += f"🆔 User ID: {user_id}\n"
            admin_text += f"📋 Project ID: {project_id}\n"
            admin_text += f"💬 Message:\n{message_text}\n\n"
            admin_text += f"Reply with: /reply {user_id} your_message"
            
            message_sent = False
            for admin_id in ADMIN_IDS:
                try:
                    await context.bot.send_message(admin_id, admin_text)
                    message_sent = True
                    logger.info(f"Support request sent to admin {admin_id}")
                except Exception as e:
                    logger.error(f"Failed to send support request to admin {admin_id}: {e}")
            
            if message_sent:
                confirmation = "✅ Your support request has been sent to our team. We'll assist you soon!"
            else:
                confirmation = "❌ Sorry, there was an issue sending your request. Please try again later."
                
            keyboard = self.create_main_keyboard(user_id)
            await update.message.reply_text(confirmation, reply_markup=keyboard)
            USER_STATES.pop(user_id, None)

    async def admin_broadcast(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        """Broadcast message to all users who have interacted with the bot"""
        if update.effective_user.id not in ADMIN_IDS:
            return
            
        if not context.args:
            await update.message.reply_text("Usage: /broadcast <message>")
            return
            
        message = " ".join(context.args)
        
        conn = sqlite3.connect('xv_dev_labs.db')
        cursor = conn.cursor()
        cursor.execute('SELECT DISTINCT user_id FROM user_preferences')
        users = cursor.fetchall()
        conn.close()
        
        success_count = 0
        total_count = len(users)
        
        broadcast_msg = f"📢 Broadcast from XV Dev Labs:\n\n{message}"
        
        for (user_id,) in users:
            try:
                await context.bot.send_message(user_id, broadcast_msg)
                success_count += 1
            except Exception as e:
                logger.error(f"Failed to broadcast to user {user_id}: {e}")
        
        await update.message.reply_text(
            f"✅ Broadcast sent to {success_count}/{total_count} users"
        )

    async def admin_reply(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            return
            
        if len(context.args) < 2:
            await update.message.reply_text(
                "Usage: /reply <user_id> <message>"
            )
            return
            
        try:
            user_id = int(context.args[0])
            message = " ".join(context.args[1:])
            
            reply_text = f"💬 Response from XV Dev Labs Team:\n\n{message}"
            
            await context.bot.send_message(user_id, reply_text)
            await update.message.reply_text(f"✅ Reply sent to user {user_id}")
            
        except ValueError:
            await update.message.reply_text("❌ Invalid user ID")
        except Exception as e:
            logger.error(f"Failed to send reply: {e}")
            await update.message.reply_text("❌ Failed to send reply")

    async def admin_create_project(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in ADMIN_IDS:
                return
                
            if len(context.args) < 3:
                await update.message.reply_text(
                    "Usage: /create_project <client_id> <service_type> <description>"
                )
                return
                
            try:
                client_id = int(context.args[0])
                service_type = context.args[1]
                description = " ".join(context.args[2:])
                
                project_id = str(uuid.uuid4())[:8]  
                
                conn = sqlite3.connect('xv_dev_labs.db')
                cursor = conn.cursor()
                cursor.execute('''
                    INSERT INTO projects (id, client_id, service_type, description, status)
                    VALUES (?, ?, ?, ?, 'pending')
                ''', (project_id, client_id, service_type, description))
                conn.commit()
                conn.close()
                
                await update.message.reply_text(
                    f"✅ Project created!\n🆔 Project ID: {project_id}\n👤 Client ID: {client_id}\n🔧 Service: {service_type}"
                )
                
                try:
                    await context.bot.send_message(
                        client_id, 
                        f"🎉 Your project has been created!\n🆔 Project ID: {project_id}\n🔧 Service: {service_type}\n📝 Description: {description}\n📊 Status: Pending"
                    )
                except Exception as e:
                    logger.error(f"Failed to notify client {client_id}: {e}")
                    
            except ValueError:
                await update.message.reply_text("❌ Invalid client ID. Must be a number.")
            except Exception as e:
                logger.error(f"Error creating project: {e}")
                await update.message.reply_text("❌ Error creating project.")

    async def admin_update_status(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in ADMIN_IDS:
                return
                
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Usage: /update_status <project_id> <new_status> [message]"
                )
                return
                
            project_id = context.args[0]
            new_status = context.args[1]
            message = " ".join(context.args[2:]) if len(context.args) > 2 else ""
            
            project = self.get_project_status(project_id)
            if not project:
                await update.message.reply_text("❌ Project not found.")
                return
                
            conn = sqlite3.connect('xv_dev_labs.db')
            cursor = conn.cursor()
            cursor.execute('''
                UPDATE projects SET status = ?, updated_at = CURRENT_TIMESTAMP 
                WHERE id = ?
            ''', (new_status, project_id))
            conn.commit()
            conn.close()
            
            await update.message.reply_text(f"✅ Project {project_id} status updated to: {new_status}")
            
            client_id = project['client_id']
            notification = f"📢 Project Update!\n🆔 Project ID: {project_id}\n📊 New Status: {new_status}"
            if message:
                notification += f"\n💬 Message: {message}"
                
            try:
                await context.bot.send_message(client_id, notification)
            except Exception as e:
                logger.error(f"Failed to notify client {client_id}: {e}")

    async def admin_send_update(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in ADMIN_IDS:
                return
                
            if len(context.args) < 2:
                await update.message.reply_text(
                    "Usage: /send_update <project_id> <message>"
                )
                return
                
            project_id = context.args[0]
            message = " ".join(context.args[1:])
            
            project = self.get_project_status(project_id)
            if not project:
                await update.message.reply_text("❌ Project not found.")
                return
                
            client_id = project['client_id']
            notification = f"📢 Project Update!\n🆔 Project ID: {project_id}\n💬 {message}"
            
            try:
                await context.bot.send_message(client_id, notification)
                await update.message.reply_text(f"✅ Update sent to client {client_id}")
            except Exception as e:
                logger.error(f"Failed to send update to client {client_id}: {e}")
                await update.message.reply_text("❌ Failed to send update to client.")

    async def admin_list_projects(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
            if update.effective_user.id not in ADMIN_IDS:
                return
                
            conn = sqlite3.connect('xv_dev_labs.db')
            cursor = conn.cursor()
            cursor.execute('SELECT id, client_id, service_type, status, created_at FROM projects ORDER BY created_at DESC LIMIT 10')
            projects = cursor.fetchall()
            conn.close()
            
            if not projects:
                await update.message.reply_text("📭 No projects found.")
                return
                
            text = "📋 Recent Projects:\n\n"
            for project in projects:
                text += f"🆔 {project[0]} | 👤 {project[1]} | 🔧 {project[2]} | 📊 {project[3]}\n"
                
            await update.message.reply_text(text)

    async def admin_help(self, update: Update, context: ContextTypes.DEFAULT_TYPE):
        if update.effective_user.id not in ADMIN_IDS:
            return
            
        help_text = """
        🔧 Admin Commands:

        /create_project <client_id> <service_type> <description>
        - Create a new project

        /update_status <project_id> <new_status> [message]
        - Update project status and notify client

        /send_update <project_id> <message>
        - Send update message to client

        /list_projects
        - Show recent projects

        /broadcast <message>
        - Broadcast message to all users

        /reply <user_id> <message>
        - Reply to a specific user

        /admin_help
        - Show this help message
                """
        await update.message.reply_text(help_text)

def main():
    bot = XVDevLabsBot()
    
    application = Application.builder().token(BOT_TOKEN).build()
    
    application.add_handler(CommandHandler("start", bot.start))
    application.add_handler(CallbackQueryHandler(bot.button_handler))
    application.add_handler(MessageHandler(filters.TEXT & ~filters.COMMAND, bot.message_handler))
    
    application.add_handler(CommandHandler("create_project", bot.admin_create_project))
    application.add_handler(CommandHandler("update_status", bot.admin_update_status))
    application.add_handler(CommandHandler("send_update", bot.admin_send_update))
    application.add_handler(CommandHandler("list_projects", bot.admin_list_projects))
    application.add_handler(CommandHandler("admin_help", bot.admin_help))
    application.add_handler(CommandHandler("reply", bot.admin_reply))
    application.add_handler(CommandHandler("broadcast", bot.admin_broadcast))
    
    print("🚀 XV Dev Labs Bot starting...")
    application.run_polling()

if __name__ == '__main__':
    main()