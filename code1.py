import asyncio
import logging
from balethon import Client
from balethon.conditions import private, regex
from balethon.objects import Message, InlineKeyboard, ReplyKeyboard, CallbackQuery
import sqlite3
import json
import random
import datetime
from typing import Dict, List, Optional
import math

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class AdvancedStrategicGameBot:
    def __init__(self, token: str):
        self.bot = Client(token)
        self.setup_handlers()
        self.user_data = {}
        self.setup_database()
        
    def setup_database(self):
        """ایجاد دیتابیس پیشرفته برای بازی"""
        self.conn = sqlite3.connect('advanced_strategic_game.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        # جدول بازیکنان
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                first_name TEXT,
                last_name TEXT,
                join_date TEXT,
                level INTEGER DEFAULT 1,
                experience INTEGER DEFAULT 0,
                gold INTEGER DEFAULT 2000,
                food INTEGER DEFAULT 1000,
                wood INTEGER DEFAULT 800,
                stone INTEGER DEFAULT 600,
                iron INTEGER DEFAULT 400,
                mana INTEGER DEFAULT 100,
                army INTEGER DEFAULT 200,
                last_action_time TEXT,
                alliance_id INTEGER,
                rank TEXT DEFAULT 'Beginner'
            )
        ''')
        
        # جدول شهرها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS cities (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                user_id INTEGER,
                city_name TEXT,
                level INTEGER DEFAULT 1,
                population INTEGER DEFAULT 2000,
                happiness INTEGER DEFAULT 85,
                defense INTEGER DEFAULT 200,
                position_x INTEGER,
                position_y INTEGER,
                last_attack_time TEXT,
                FOREIGN KEY (user_id) REFERENCES players (user_id)
            )
        ''')
        
        # جدول ساختمان‌ها
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS buildings (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                city_id INTEGER,
                building_type TEXT,
                level INTEGER DEFAULT 1,
                upgrade_finish_time TEXT,
                is_under_construction BOOLEAN DEFAULT FALSE,
                FOREIGN KEY (city_id) REFERENCES cities (id)
            )
        ''')
        
        self.conn.commit()

    def create_main_menu_keyboard(self):
        """ایجاد کیبورد اصلی بازی"""
        keyboard = ReplyKeyboard(resize_keyboard=True)
        keyboard.row("🏰 شهر من", "⚔️ ارتش من")
        keyboard.row("📊 منابع و بازار", "🔮 تحقیقات")
        keyboard.row("🗺️ نقشه جهان", "👥 اتحادها")
        keyboard.row("⚡ اقدامات سریع", "📋 پروفایل")
        return keyboard

    def create_city_management_keyboard(self):
        """ایجاد کیبورد مدیریت شهر"""
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🏛️ ساختمان‌ها", "city_buildings"),
            ("👥 جمعیت", "city_population")
        )
        keyboard.row(
            ("🛡️ دفاع", "city_defense"),
            ("💰 درآمد", "city_income")
        )
        keyboard.row(
            ("⚡ ارتقاء شهر", "upgrade_city"),
            ("📊 آمار شهر", "city_stats")
        )
        keyboard.row(
            ("🔙 منوی اصلی", "main_menu")
        )
        return keyboard

    def create_army_management_keyboard(self):
        """ایجاد کیبورد مدیریت ارتش"""
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🪖 پیاده‌نظام", "train_infantry"),
            ("🏹 کمانداران", "train_archers")
        )
        keyboard.row(
            ("🐎 سواره نظام", "train_cavalry"),
            ("♟️ سلاح‌های محاصره", "train_siege")
        )
        keyboard.row(
            ("⚔️ حمله", "attack_menu"),
            ("🛡️ دفاع", "defense_menu")
        )
        keyboard.row(
            ("📊 وضعیت ارتش", "army_status"),
            ("🔙 منوی اصلی", "main_menu")
        )
        return keyboard

    def create_buildings_keyboard(self):
        """ایجاد کیبورد ساختمان‌ها"""
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🏯 سالن شهر", "build_town_hall"),
            ("🏠 خانه‌ها", "build_houses")
        )
        keyboard.row(
            ("🛖 مزرعه", "build_farm"),
            ("⛏️ معدن", "build_mine")
        )
        keyboard.row(
            ("🏭 کارخانه", "build_factory"),
            ("🎯 مرکز آموزش", "build_training")
        )
        keyboard.row(
            ("🏰 دیوارها", "build_walls"),
            ("🔒 دروازه", "build_gate")
        )
        keyboard.row(
            ("🔙 مدیریت شهر", "city_management")
        )
        return keyboard

    def create_quick_actions_keyboard(self):
        """ایجاد کیبورد اقدامات سریع"""
        keyboard = InlineKeyboard()
        keyboard.row(
            ("⛏️ جمع‌آوری منابع", "collect_resources"),
            ("🔍 جاسوسی", "spy_enemies")
        )
        keyboard.row(
            ("⚡ سرعت‌بخشیدن", "speed_up"),
            ("🎁 پاداش روزانه", "daily_reward")
        )
        keyboard.row(
            ("🏆 مسابقات", "tournaments"),
            ("📈 رتبه‌بندی", "rankings")
        )
        keyboard.row(
            ("🔙 منوی اصلی", "main_menu")
        )
        return keyboard

    def setup_handlers(self):
        """تنظیم هندلرهای پیشرفته"""
        
        # هندلر شروع - با regex به جای command
        @self.bot.on_message(private & regex("^/start$"))
        async def start_game(client: Client, message: Message):
            user_id = message.from_user.id
            await self.register_player(user_id, message.from_user)
            
            welcome_text = """
🎮 **به پیشرفته‌ترین بازی استراتژیک خوش آمدید!**

🏰 **امکانات اصلی:**
• 🏰 مدیریت شهر پیشرفته
• ⚔️ سیستم جنگی واقعی
• 📊 اقتصاد پیچیده
• 🔮 تحقیقات و تکنولوژی
• 👥 سیستم اتحادها
• 🗺️ نقشه جهان گسترده

🎯 **برای شروع از دکمه‌های زیر استفاده کنید:**
            """
            
            await message.reply(welcome_text, reply_markup=self.create_main_menu_keyboard())

        # هندلر مدیریت شهر
        @self.bot.on_message(private & regex("🏰 شهر من"))
        async def city_management(client: Client, message: Message):
            user_id = message.from_user.id
            city_info = await self.get_city_info(user_id)
            
            city_text = f"""
🏰 **مدیریت شهر {city_info['name']}**

📊 **وضعیت فعلی:**
• 🎯 سطح: {city_info['level']}
• 👥 جمعیت: {city_info['population']:,}
• 😊 رضایت: {city_info['happiness']}%
• 🛡️ دفاع: {city_info['defense']}

💎 **منابع:**
• 🥇 طلا: {city_info['gold']:,}
• 🌾 غذا: {city_info['food']:,}
• 🪵 چوب: {city_info['wood']:,}
• 🪨 سنگ: {city_info['stone']:,}
• ⚙️ آهن: {city_info['iron']:,}

🔧 **برای مدیریت شهر از دکمه‌های زیر استفاده کنید:**
            """
            
            await message.reply(city_text, reply_markup=self.create_city_management_keyboard())

        # هندلر مدیریت ارتش
        @self.bot.on_message(private & regex("⚔️ ارتش من"))
        async def army_management(client: Client, message: Message):
            user_id = message.from_user.id
            army_info = await self.get_army_info(user_id)
            
            army_text = f"""
⚔️ **مدیریت ارتش**

🎯 **نیروهای شما:**
• 🪖 پیاده‌نظام: {army_info['infantry']:,}
• 🏹 کمانداران: {army_info['archers']:,}
• 🐎 سواره نظام: {army_info['cavalry']:,}
• ♟️ سلاح‌های محاصره: {army_info['siege']:,}

⚡ **قدرت کلی:**
• 💥 قدرت حمله: {army_info['attack_power']:,}
• 🛡️ قدرت دفاع: {army_info['defense_power']:,}
• 🎯 دقت: {army_info['accuracy']}%

🔧 **برای تقویت ارتش از دکمه‌های زیر استفاده کنید:**
            """
            
            await message.reply(army_text, reply_markup=self.create_army_management_keyboard())

        # هندلر منابع و بازار
        @self.bot.on_message(private & regex("📊 منابع و بازار"))
        async def resources_market(client: Client, message: Message):
            keyboard = InlineKeyboard()
            keyboard.row(
                ("💰 بازار", "open_market"),
                ("⚡ تولید", "production_stats")
            )
            keyboard.row(
                ("📈 تجارت", "trading_menu"),
                ("🔄 مبادله", "exchange_resources")
            )
            keyboard.row(
                ("🔙 منوی اصلی", "main_menu")
            )
            
            resources_text = """
📊 **منابع و بازار**

💎 **سیستم اقتصادی پیشرفته:**
• 📈 بازار واقعی با نوسان قیمت
• 🔄 مبادله منابع
• ⚡ افزایش تولید
• 🤝 تجارت با بازیکنان

🎮 **از دکمه‌های زیر برای مدیریت اقتصاد استفاده کنید:**
            """
            
            await message.reply(resources_text, reply_markup=keyboard)

        # هندلر نقشه جهان
        @self.bot.on_message(private & regex("🗺️ نقشه جهان"))
        async def world_map(client: Client, message: Message):
            keyboard = InlineKeyboard()
            keyboard.row(
                ("🔍 جستجو", "search_location"),
                ("🎯 حمله", "map_attack")
            )
            keyboard.row(
                ("🤝 اتحاد", "map_alliance"),
                ("📊 اطلاعات", "map_info")
            )
            keyboard.row(
                ("🔄 بروزرسانی", "refresh_map"),
                ("🔙 منوی اصلی", "main_menu")
            )
            
            map_text = """
🗺️ **نقشه جهان**

🌍 **ویژگی‌های نقشه:**
• 🎯 موقعیت‌یابی دقیق
• 🔍 جستجوی پیشرفته
• ⚔️ نقاط حمله
• 🤝 پایگاه‌های اتحاد

🎮 **برای کاوش در جهان از دکمه‌های زیر استفاده کنید:**
            """
            
            await message.reply(map_text, reply_markup=keyboard)

        # هندلر اقدامات سریع
        @self.bot.on_message(private & regex("⚡ اقدامات سریع"))
        async def quick_actions(client: Client, message: Message):
            await message.reply(
                "⚡ **اقدامات سریع**\n\n🎯 کارهای که می‌توانید سریع انجام دهید:",
                reply_markup=self.create_quick_actions_keyboard()
            )

        # هندلر پروفایل
        @self.bot.on_message(private & regex("📋 پروفایل"))
        async def player_profile(client: Client, message: Message):
            user_id = message.from_user.id
            profile = await self.get_player_profile(user_id)
            
            profile_text = f"""
📋 **پروفایل بازیکن**

👤 **اطلاعات شخصی:**
• 🆔 نام: {profile['name']}
• 🎯 سطح: {profile['level']}
• ⭐ تجربه: {profile['exp']:,}
• 🏆 رتبه: {profile['rank']}

🏰 **امپراتوری:**
• 🏙️ شهرها: {profile['cities_count']}
• ⚔️ نیروی نظامی: {profile['total_army']:,}
• 💰 ثروت: {profile['total_wealth']:,}

📊 **آمار:**
• 🎯 پیروزی: {profile['wins']}
• 💔 شکست: {profile['losses']}
• ⚔️ مجموع نبردها: {profile['total_battles']}
            """
            
            keyboard = InlineKeyboard()
            keyboard.row(
                ("📈 آمار کامل", "full_stats"),
                ("🏆 دستاوردها", "achievements")
            )
            keyboard.row(
                ("🔙 منوی اصلی", "main_menu")
            )
            
            await message.reply(profile_text, reply_markup=keyboard)

        # هندلر منو - با regex به جای command
        @self.bot.on_message(private & regex("^/menu$"))
        async def show_menu(client: Client, message: Message):
            menu_text = """
🎮 **منوی اصلی بازی استراتژیک**

🎯 **دسترسی سریع به تمام بخش‌ها:**
• 🏰 مدیریت شهر و توسعه
• ⚔️ آموزش و مدیریت نیروها  
• 📊 اقتصاد و تجارت
• 🗺️ کاوش و نبرد
• 👥 تعامل با سایر بازیکنان
            """
            await message.reply(menu_text, reply_markup=self.create_main_menu_inline_keyboard())

        # هندلر کال‌بک‌ها
        @self.bot.on_callback_query()
        async def handle_callbacks(client: Client, callback_query: CallbackQuery):
            user_id = callback_query.from_user.id
            data = callback_query.data
            
            # مدیریت منوی اصلی
            if data == "main_menu":
                await self.show_main_menu(callback_query)
            
            # مدیریت شهر
            elif data == "city_management":
                await self.show_city_management(callback_query)
            elif data == "city_buildings":
                await self.show_buildings_menu(callback_query)
            elif data == "upgrade_city":
                await self.upgrade_city(callback_query)
            
            # مدیریت ارتش
            elif data == "train_infantry":
                await self.train_troops(callback_query, "infantry")
            elif data == "train_archers":
                await self.train_troops(callback_query, "archers")
            elif data == "attack_menu":
                await self.show_attack_menu(callback_query)
            
            # اقدامات سریع
            elif data == "collect_resources":
                await self.collect_resources(callback_query)
            elif data == "daily_reward":
                await self.claim_daily_reward(callback_query)
            
            # سایر کال‌بک‌ها
            elif data == "player_profile":
                await self.show_player_profile(callback_query)
            elif data == "resources_market":
                await self.show_resources_market(callback_query)
            elif data == "world_map":
                await self.show_world_map(callback_query)
            elif data == "quick_actions":
                await self.show_quick_actions(callback_query)
            elif data == "army_management":
                await self.show_army_management(callback_query)
            
            await callback_query.answer()

    async def show_main_menu(self, callback_query: CallbackQuery):
        """نمایش منوی اصلی"""
        welcome_text = """
🎮 **منوی اصلی بازی استراتژیک**

🎯 **دسترسی سریع به تمام بخش‌ها:**
• 🏰 مدیریت شهر و توسعه
• ⚔️ آموزش و مدیریت نیروها  
• 📊 اقتصاد و تجارت
• 🗺️ کاوش و نبرد
• 👥 تعامل با سایر بازیکنان
        """
        await callback_query.message.edit_text(
            welcome_text, 
            reply_markup=self.create_main_menu_inline_keyboard()
        )

    async def show_city_management(self, callback_query: CallbackQuery):
        """نمایش مدیریت شهر"""
        user_id = callback_query.from_user.id
        city_info = await self.get_city_info(user_id)
        
        city_text = f"""
🏰 **مدیریت شهر {city_info['name']}**

📊 **وضعیت فعلی شهر:**
• 🎯 سطح: {city_info['level']}
• 👥 جمعیت: {city_info['population']:,}
• 😊 رضایت: {city_info['happiness']}%
• 🛡️ دفاع: {city_info['defense']}

🔧 **امکانات مدیریت:**
        """
        await callback_query.message.edit_text(
            city_text,
            reply_markup=self.create_city_management_keyboard()
        )

    async def show_buildings_menu(self, callback_query: CallbackQuery):
        """نمایش منوی ساختمان‌ها"""
        buildings_text = """
🏗️ **سیستم ساختمان‌سازی**

🔨 **انواع ساختمان‌های قابل ساخت:**
• 🏯 سالن شهر (مرکز فرماندهی)
• 🏠 خانه‌ها (افزایش جمعیت)
• 🛖 مزرعه (تولید غذا)
• ⛏️ معدن (استخراج منابع)
• 🏭 کارخانه (تولید پیشرفته)
• 🎯 مرکز آموزش (نیروهای نظامی)
• 🏰 دیوارها (سیستم دفاعی)

💰 **برای ساخت هر ساختمان روی آن کلیک کنید:**
        """
        await callback_query.message.edit_text(
            buildings_text,
            reply_markup=self.create_buildings_keyboard()
        )

    async def train_troops(self, callback_query: CallbackQuery, unit_type: str):
        """آموزش نیروهای نظامی"""
        unit_names = {
            "infantry": "🪖 پیاده‌نظام",
            "archers": "🏹 کمانداران", 
            "cavalry": "🐎 سواره نظام",
            "siege": "♟️ سلاح‌های محاصره"
        }
        
        training_text = f"""
⚔️ **آموزش {unit_names[unit_type]}**

🎯 **اطلاعات واحد:**
• ⚔️ قدرت حمله: {random.randint(15, 25)}
• 🛡️ قدرت دفاع: {random.randint(10, 20)}
• 🎯 دقت: {random.randint(70, 90)}%
• ⏱️ زمان آموزش: 30 دقیقه

💰 **هزینه‌ها:**
• 🥇 طلا: {random.randint(50, 100)}
• 🌾 غذا: {random.randint(20, 50)}
• ⚙️ آهن: {random.randint(10, 30)}

🔢 **تعداد مورد نظر برای آموزش را انتخاب کنید:**
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("1️⃣ 10 واحد", f"train_{unit_type}_10"),
            ("2️⃣ 50 واحد", f"train_{unit_type}_50")
        )
        keyboard.row(
            ("3️⃣ 100 واحد", f"train_{unit_type}_100"),
            ("4️⃣ 500 واحد", f"train_{unit_type}_500")
        )
        keyboard.row(
            ("🔙 مدیریت ارتش", "army_management")
        )
        
        await callback_query.message.edit_text(training_text, reply_markup=keyboard)

    async def collect_resources(self, callback_query: CallbackQuery):
        """جمع‌آوری منابع"""
        collected = {
            'gold': random.randint(100, 300),
            'food': random.randint(200, 500),
            'wood': random.randint(150, 400),
            'stone': random.randint(100, 250),
            'iron': random.randint(50, 150)
        }
        
        collection_text = f"""
⛏️ **جمع‌آوری منابع تکمیل شد!**

💰 **منابع جمع‌آوری شده:**
• 🥇 طلا: {collected['gold']:,}
• 🌾 غذا: {collected['food']:,}  
• 🪵 چوب: {collected['wood']:,}
• 🪨 سنگ: {collected['stone']:,}
• ⚙️ آهن: {collected['iron']:,}

🎯 **منابع جدید در انبارهای شما ذخیره شد.**

⏱️ **جمع‌آوری بعدی: 1 ساعت دیگر**
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🔄 دوباره جمع‌آوری", "collect_resources"),
            ("🔙 اقدامات سریع", "quick_actions")
        )
        
        await callback_query.message.edit_text(collection_text, reply_markup=keyboard)

    async def claim_daily_reward(self, callback_query: CallbackQuery):
        """دریافت پاداش روزانه"""
        rewards = {
            'gold': random.randint(500, 1000),
            'food': random.randint(800, 1500),
            'wood': random.randint(600, 1200),
            'stone': random.randint(400, 800),
            'iron': random.randint(200, 500),
            'mana': random.randint(50, 150)
        }
        
        reward_text = f"""
🎁 **پاداش روزانه دریافت شد!**

🎉 **مبارک! امروز این پاداش‌ها را دریافت کردید:**
• 🥇 طلا: {rewards['gold']:,}
• 🌾 غذا: {rewards['food']:,}
• 🪵 چوب: {rewards['wood']:,}
• 🪨 سنگ: {rewards['stone']:,}
• ⚙️ آهن: {rewards['iron']:,}
• 🔮 مانا: {rewards['mana']:,}

⭐ **فردا پاداش بهتری در انتظار شماست!**
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("📅 پاداش هفتگی", "weekly_reward"),
            ("🔙 اقدامات سریع", "quick_actions")
        )
        
        await callback_query.message.edit_text(reward_text, reply_markup=keyboard)

    def create_main_menu_inline_keyboard(self):
        """ایجاد کیبورد اینلاین برای منوی اصلی"""
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🏰 شهر", "city_management"),
            ("⚔️ ارتش", "army_management")
        )
        keyboard.row(
            ("📊 منابع", "resources_market"),
            ("🗺️ نقشه", "world_map")
        )
        keyboard.row(
            ("⚡ اقدامات", "quick_actions"),
            ("📋 پروفایل", "player_profile")
        )
        return keyboard

    async def show_attack_menu(self, callback_query: CallbackQuery):
        """نمایش منوی حمله"""
        attack_text = """
⚔️ **منوی حمله**

🎯 **گزینه‌های حمله:**
• 🔍 جستجوی دشمنان ضعیف
• 🎯 حمله به بازیکنان خاص
• 🏹 حمله غافلگیرانه
• 🤝 حمله گروهی با اتحاد

⚠️ **هشدار:** هر حمله ممکن است با مقاومت روبرو شود!
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🔍 جستجوی دشمن", "search_enemy"),
            ("🎯 حمله مستقیم", "direct_attack")
        )
        keyboard.row(
            ("🏹 حمله غافلگیرانه", "surprise_attack"),
            ("🤝 حمله گروهی", "group_attack")
        )
        keyboard.row(
            ("🔙 مدیریت ارتش", "army_management")
        )
        
        await callback_query.message.edit_text(attack_text, reply_markup=keyboard)

    async def upgrade_city(self, callback_query: CallbackQuery):
        """ارتقاء شهر"""
        upgrade_text = """
⚡ **ارتقاء شهر**

🏰 **ارتقاء به سطح بعدی:**
• 📈 افزایش جمعیت حداکثر
• 🛡️ تقویت دفاع شهر
• 💰 افزایش درآمد منابع
• 🏗️ باز شدن ساختمان‌های جدید

💰 **هزینه ارتقاء:**
• 🥇 طلا: 5,000
• 🪵 چوب: 3,000
• 🪨 سنگ: 2,000
• ⚙️ آهن: 1,000

⏱️ **زمان ارتقاء: 2 ساعت**
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("✅ ارتقاء دهید", "confirm_upgrade"),
            ("❌ انصراف", "city_management")
        )
        
        await callback_query.message.edit_text(upgrade_text, reply_markup=keyboard)

    async def show_player_profile(self, callback_query: CallbackQuery):
        """نمایش پروفایل بازیکن"""
        user_id = callback_query.from_user.id
        profile = await self.get_player_profile(user_id)
        
        profile_text = f"""
📋 **پروفایل بازیکن**

👤 **اطلاعات شخصی:**
• 🆔 نام: {profile['name']}
• 🎯 سطح: {profile['level']}
• ⭐ تجربه: {profile['exp']:,}
• 🏆 رتبه: {profile['rank']}

🏰 **امپراتوری:**
• 🏙️ شهرها: {profile['cities_count']}
• ⚔️ نیروی نظامی: {profile['total_army']:,}
• 💰 ثروت: {profile['total_wealth']:,}

📊 **آمار:**
• 🎯 پیروزی: {profile['wins']}
• 💔 شکست: {profile['losses']}
• ⚔️ مجموع نبردها: {profile['total_battles']}
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("📈 آمار کامل", "full_stats"),
            ("🏆 دستاوردها", "achievements")
        )
        keyboard.row(
            ("🔙 منوی اصلی", "main_menu")
        )
        
        await callback_query.message.edit_text(profile_text, reply_markup=keyboard)

    async def show_resources_market(self, callback_query: CallbackQuery):
        """نمایش بازار منابع"""
        resources_text = """
📊 **بازار منابع**

💰 **قیمت‌های فعلی:**
• 🌾 غذا: 1 طلا = 2 غذا
• 🪵 چوب: 1 طلا = 1.5 چوب
• 🪨 سنگ: 1 طلا = 1 سنگ
• ⚙️ آهن: 1 طلا = 0.5 آهن

🔄 **امکانات بازار:**
• خرید و فروش منابع
• مبادله با بازیکنان
• تحلیل بازار
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🛒 خرید", "buy_resources"),
            ("💰 فروش", "sell_resources")
        )
        keyboard.row(
            ("🤝 مبادله", "exchange_menu"),
            ("📈 تحلیل", "market_analysis")
        )
        keyboard.row(
            ("🔙 منوی اصلی", "main_menu")
        )
        
        await callback_query.message.edit_text(resources_text, reply_markup=keyboard)

    async def show_world_map(self, callback_query: CallbackQuery):
        """نمایش نقشه جهان"""
        map_text = """
🗺️ **نقشه جهان**

🌍 **موقعیت فعلی شما:**
• 📍 مختصات: X: 150, Y: 200
• 🏰 شهرهای نزدیک: 3
• ⚔️ دشمنان در محدوده: 2
• 🤝 متحدان: 1

🎯 **گزینه‌های کاوش:**
        """
        
        keyboard = InlineKeyboard()
        keyboard.row(
            ("🔍 جستجو", "search_location"),
            ("🎯 حمله", "map_attack")
        )
        keyboard.row(
            ("🤝 اتحاد", "map_alliance"),
            ("📊 اطلاعات", "map_info")
        )
        keyboard.row(
            ("🔄 بروزرسانی", "refresh_map"),
            ("🔙 منوی اصلی", "main_menu")
        )
        
        await callback_query.message.edit_text(map_text, reply_markup=keyboard)

    async def show_quick_actions(self, callback_query: CallbackQuery):
        """نمایش اقدامات سریع"""
        await callback_query.message.edit_text(
            "⚡ **اقدامات سریع**\n\n🎯 کارهای که می‌توانید سریع انجام دهید:",
            reply_markup=self.create_quick_actions_keyboard()
        )

    async def show_army_management(self, callback_query: CallbackQuery):
        """نمایش مدیریت ارتش"""
        user_id = callback_query.from_user.id
        army_info = await self.get_army_info(user_id)
        
        army_text = f"""
⚔️ **مدیریت ارتش**

🎯 **نیروهای شما:**
• 🪖 پیاده‌نظام: {army_info['infantry']:,}
• 🏹 کمانداران: {army_info['archers']:,}
• 🐎 سواره نظام: {army_info['cavalry']:,}
• ♟️ سلاح‌های محاصره: {army_info['siege']:,}

⚡ **قدرت کلی:**
• 💥 قدرت حمله: {army_info['attack_power']:,}
• 🛡️ قدرت دفاع: {army_info['defense_power']:,}
• 🎯 دقت: {army_info['accuracy']}%
        """
        
        await callback_query.message.edit_text(
            army_text,
            reply_markup=self.create_army_management_keyboard()
        )

    # متدهای کمکی برای بازی
    async def register_player(self, user_id: int, user_info):
        """ثبت نام بازیکن جدید"""
        try:
            self.cursor.execute('''
                INSERT OR IGNORE INTO players 
                (user_id, username, first_name, last_name, join_date) 
                VALUES (?, ?, ?, ?, ?)
            ''', (
                user_id,
                user_info.username,
                user_info.first_name,
                user_info.last_name,
                datetime.datetime.now().isoformat()
            ))
            self.conn.commit()
            logger.info(f"بازیکن جدید ثبت شد: {user_id}")
        except Exception as e:
            logger.error(f"خطا در ثبت بازیکن: {e}")

    async def get_city_info(self, user_id: int) -> Dict:
        """دریافت اطلاعات شهر"""
        return {
            'name': 'شهر اصلی',
            'level': 1,
            'population': 2000,
            'happiness': 85,
            'defense': 200,
            'gold': 2000,
            'food': 1000,
            'wood': 800,
            'stone': 600,
            'iron': 400
        }

    async def get_army_info(self, user_id: int) -> Dict:
        """دریافت اطلاعات ارتش"""
        return {
            'infantry': 100,
            'archers': 50,
            'cavalry': 30,
            'siege': 5,
            'attack_power': 1250,
            'defense_power': 980,
            'accuracy': 75
        }

    async def get_player_profile(self, user_id: int) -> Dict:
        """دریافت پروفایل بازیکن"""
        return {
            'name': 'فرمانده',
            'level': 1,
            'exp': 0,
            'rank': 'تازه‌کار',
            'cities_count': 1,
            'total_army': 185,
            'total_wealth': 4800,
            'wins': 0,
            'losses': 0,
            'total_battles': 0
        }

# اجرای ربات
if __name__ == "__main__":
    # 🔹 توکن ربات خود را اینجا قرار دهید
    bot_token = "223105173:M1QA1X4zfHNCBHY8ytUskGvf_nO2GgRyEJw"
    
    game_bot = AdvancedStrategicGameBot(bot_token)
    print("🤖 ربات بازی استراتژیک در حال اجرا است...")
    game_bot.bot.run()