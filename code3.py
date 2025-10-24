import asyncio
import random
import sqlite3
from datetime import datetime, timedelta
from balethon import Client
from balethon.conditions import private
from balethon.objects import Message

# توکن ربات خود را اینجا قرار دهید
BOT_TOKEN = "223105173:M1QA1X4zfHNCBHY8ytUskGvf_nO2GgRyEJw"

class PVPStrategicGame:
    def __init__(self, token):
        self.client = Client(token)
        self.setup_database()
        self.setup_handlers()
    
    def setup_database(self):
        """ایجاد دیتابیس برای ذخیره اطلاعات بازیکنان"""
        self.conn = sqlite3.connect('pvp_game.db', check_same_thread=False)
        self.cursor = self.conn.cursor()
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS players (
                user_id INTEGER PRIMARY KEY,
                username TEXT,
                level INTEGER DEFAULT 1,
                gold INTEGER DEFAULT 1000,
                food INTEGER DEFAULT 500,
                wood INTEGER DEFAULT 300,
                stone INTEGER DEFAULT 200,
                soldiers INTEGER DEFAULT 10,
                archers INTEGER DEFAULT 5,
                cavalry INTEGER DEFAULT 2,
                farm INTEGER DEFAULT 2,
                barracks INTEGER DEFAULT 1,
                mine INTEGER DEFAULT 1,
                last_attack TEXT,
                defense_power INTEGER DEFAULT 100,
                wins INTEGER DEFAULT 0,
                losses INTEGER DEFAULT 0
            )
        ''')
        
        self.cursor.execute('''
            CREATE TABLE IF NOT EXISTS battles (
                battle_id INTEGER PRIMARY KEY AUTOINCREMENT,
                attacker_id INTEGER,
                defender_id INTEGER,
                result TEXT,
                loot INTEGER,
                battle_time TEXT
            )
        ''')
        self.conn.commit()
    
    def get_player(self, user_id):
        """دریافت اطلاعات بازیکن"""
        self.cursor.execute('SELECT * FROM players WHERE user_id = ?', (user_id,))
        player = self.cursor.fetchone()
        if player:
            return {
                'user_id': player[0],
                'username': player[1],
                'level': player[2],
                'gold': player[3],
                'food': player[4],
                'wood': player[5],
                'stone': player[6],
                'soldiers': player[7],
                'archers': player[8],
                'cavalry': player[9],
                'farm': player[10],
                'barracks': player[11],
                'mine': player[12],
                'last_attack': player[13],
                'defense_power': player[14],
                'wins': player[15],
                'losses': player[16]
            }
        return None
    
    def create_player(self, user_id, username):
        """ایجاد بازیکن جدید"""
        self.cursor.execute('''
            INSERT INTO players (user_id, username) 
            VALUES (?, ?)
        ''', (user_id, username))
        self.conn.commit()
    
    def update_player(self, user_id, **updates):
        """آپدیت اطلاعات بازیکن"""
        set_clause = ', '.join([f"{key} = ?" for key in updates.keys()])
        values = list(updates.values())
        values.append(user_id)
        
        self.cursor.execute(f'''
            UPDATE players SET {set_clause} WHERE user_id = ?
        ''', values)
        self.conn.commit()

    def create_keyboard(self, buttons):
        """ایجاد کیبورد ساده"""
        # در Balethon می‌توانیم از reply_markup با فرمت دیکشنری استفاده کنیم
        keyboard = []
        row = []
        for i, button in enumerate(buttons):
            row.append(button)
            if (i + 1) % 2 == 0 or i == len(buttons) - 1:
                keyboard.append(row)
                row = []
        return {"keyboard": keyboard, "resize_keyboard": True}

    def get_main_menu_keyboard(self):
        """منوی اصلی با دکمه‌ها"""
        buttons = [
            "🏰 پایگاه", "📊 منابع",
            "⚔️ ارتش", "🏗️ ساختمان‌ها", 
            "🌍 PVP", "⚡ حمله",
            "🏆 رده‌بندی", "🛡️ دفاع",
            "❓ راهنما"
        ]
        return self.create_keyboard(buttons)

    def get_base_keyboard(self):
        """منوی پایگاه"""
        buttons = [
            "⬆️ ارتقاء پایگاه", "🛡️ تقویت دفاع",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def get_resources_keyboard(self):
        """منوی منابع"""
        buttons = [
            "⛏️ جمع‌آوری منابع",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def get_army_keyboard(self):
        """منوی ارتش"""
        buttons = [
            "🛡️ استخدام سرباز", "🏹 استخدام کماندار",
            "🐎 استخدام سواره", "🎯 آموزش ارتش",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def get_buildings_keyboard(self):
        """منوی ساختمان‌ها"""
        buttons = [
            "🏠 ساخت مزرعه", "⚔️ ساخت سربازخانه",
            "⛏️ ساخت معدن", "🛖 ساخت انبار",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def get_pvp_keyboard(self):
        """منوی PVP"""
        buttons = [
            "🎯 پیدا کردن حریف",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def get_attack_keyboard(self):
        """منوی حمله"""
        buttons = [
            "1", "2", "3",
            "4", "5",
            "🏠 منوی اصلی"
        ]
        return self.create_keyboard(buttons)

    def setup_handlers(self):
        # هندلر همه پیام‌ها
        @self.client.on_message(private)
        async def handle_all_messages(message: Message):
            user_id = message.author.id
            text_msg = message.text
            
            if not text_msg:
                await self.show_main_menu(message)
                return
            
            # ایجاد بازیکن جدید اگر وجود ندارد
            if not self.get_player(user_id):
                username = message.author.first_name or "بازیکن"
                self.create_player(user_id, username)
            
            # دستور start
            if text_msg.startswith('/start'):
                await self.show_main_menu(message)
            
            # منوی اصلی
            elif text_msg in ["منوی اصلی", "🏠 منوی اصلی", "بازگشت"]:
                await self.show_main_menu(message)
            
            # پایگاه
            elif text_msg in ["🏰 پایگاه", "⬆️ ارتقاء پایگاه", "🛡️ تقویت دفاع"]:
                if text_msg == "🏰 پایگاه":
                    await self.show_base(message)
                elif text_msg == "⬆️ ارتقاء پایگاه":
                    await self.upgrade_base(message)
                elif text_msg == "🛡️ تقویت دفاع":
                    await self.upgrade_defense(message)
            
            # منابع
            elif text_msg in ["📊 منابع", "⛏️ جمع‌آوری منابع"]:
                if text_msg == "📊 منابع":
                    await self.show_resources(message)
                elif text_msg == "⛏️ جمع‌آوری منابع":
                    await self.collect_resources(message)
            
            # ارتش
            elif text_msg in ["⚔️ ارتش", "🛡️ استخدام سرباز", "🏹 استخدام کماندار", "🐎 استخدام سواره"]:
                if text_msg == "⚔️ ارتش":
                    await self.show_army(message)
                elif text_msg == "🛡️ استخدام سرباز":
                    await self.recruit_unit(message, "soldier")
                elif text_msg == "🏹 استخدام کماندار":
                    await self.recruit_unit(message, "archer")
                elif text_msg == "🐎 استخدام سواره":
                    await self.recruit_unit(message, "cavalry")
            
            # ساختمان‌ها
            elif text_msg in ["🏗️ ساختمان‌ها", "🏠 ساخت مزرعه", "⚔️ ساخت سربازخانه", "⛏️ ساخت معدن"]:
                if text_msg == "🏗️ ساختمان‌ها":
                    await self.show_buildings(message)
                elif text_msg == "🏠 ساخت مزرعه":
                    await self.build_building(message, "farm")
                elif text_msg == "⚔️ ساخت سربازخانه":
                    await self.build_building(message, "barracks")
                elif text_msg == "⛏️ ساخت معدن":
                    await self.build_building(message, "mine")
            
            # PVP و حمله
            elif text_msg in ["🌍 PVP", "⚡ حمله", "🎯 پیدا کردن حریف"]:
                if text_msg in ["🌍 PVP", "⚡ حمله"]:
                    await self.show_pvp_menu(message)
                elif text_msg == "🎯 پیدا کردن حریف":
                    await self.attack_players(message)
            
            # رده‌بندی
            elif text_msg == "🏆 رده‌بندی":
                await self.show_leaderboard(message)
            
            # دفاع
            elif text_msg == "🛡️ دفاع":
                await self.show_defense(message)
            
            # راهنما
            elif text_msg == "❓ راهنما":
                await self.show_help(message)
            
            # حمله با شماره
            elif text_msg.isdigit() and 1 <= int(text_msg) <= 5:
                await self.process_attack_by_number(message, int(text_msg))
            
            else:
                await self.show_main_menu(message)

    async def show_main_menu(self, message):
        """نمایش منوی اصلی"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        welcome_text = (
            "🎮 **به بازی استراتژیک PVP خوش آمدید!**\n\n"
            f"👋 سلام {player['username']}!\n"
            f"⭐ سطح: {player['level']} | 💰 طلا: {player['gold']}\n"
            f"🏆 رکورد: {player['wins']} برد - {player['losses']} باخت\n\n"
            "لطفاً از منوی زیر انتخاب کنید:"
        )
        
        await message.reply(welcome_text, reply_markup=self.get_main_menu_keyboard())

    async def show_base(self, message):
        """نمایش اطلاعات پایگاه"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        base_info = (
            f"🏰 **پایگاه شما**\n\n"
            f"⭐ سطح: {player['level']}\n"
            f"👤 فرمانده: {player['username']}\n"
            f"💪 قدرت دفاع: {player['defense_power']}\n\n"
            f"🏆 رکورد: {player['wins']} برد - {player['losses']} باخت\n\n"
            f"**ساختمان‌ها:**\n"
            f"🏠 مزرعه: {player['farm']}\n"
            f"⚔️ سربازخانه: {player['barracks']}\n"
            f"⛏️ معدن: {player['mine']}"
        )
        
        await message.reply(base_info, reply_markup=self.get_base_keyboard())

    async def show_resources(self, message):
        """نمایش منابع"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        resources_info = (
            f"📊 **منابع شما**\n\n"
            f"💰 طلا: {player['gold']}\n"
            f"🌾 غذا: {player['food']}\n"
            f"🌲 چوب: {player['wood']}\n"
            f"🪨 سنگ: {player['stone']}\n\n"
            f"📈 درآمد ساعتی:\n"
            f"💰 طلا: +{player['mine'] * 25} (از معدن)\n"
            f"🌾 غذا: +{player['farm'] * 50} (از مزارع)"
        )
        
        await message.reply(resources_info, reply_markup=self.get_resources_keyboard())

    async def collect_resources(self, message):
        """جمع‌آوری منابع"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        gold_income = player['mine'] * 25
        food_income = player['farm'] * 50
        
        self.update_player(user_id,
                         gold=player['gold'] + gold_income,
                         food=player['food'] + food_income)
        
        await message.reply(
            f"✅ منابع جمع‌آوری شد!\n\n"
            f"💰 +{gold_income} طلا\n"
            f"🌾 +{food_income} غذا\n\n"
            f"💰 طلا جدید: {player['gold'] + gold_income}\n"
            f"🌾 غذا جدید: {player['food'] + food_income}",
            reply_markup=self.get_resources_keyboard()
        )

    async def show_army(self, message):
        """نمایش ارتش"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        attack_power = self.calculate_attack_power(player)
        
        army_info = (
            f"⚔️ **ارتش شما**\n\n"
            f"🛡️ سربازان: {player['soldiers']}\n"
            f"🏹 کمانداران: {player['archers']}\n"
            f"🐎 سواره نظام: {player['cavalry']}\n\n"
            f"💪 قدرت حمله: {attack_power}\n"
            f"💪 قدرت دفاع: {player['defense_power']}"
        )
        
        await message.reply(army_info, reply_markup=self.get_army_keyboard())

    async def show_buildings(self, message):
        """نمایش ساختمان‌ها"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        buildings_info = (
            f"🏗️ **ساختمان‌های شما**\n\n"
            f"🏠 مزرعه: سطح {player['farm']}\n"
            f"   ➕ تولید غذا: {player['farm'] * 50} در ساعت\n"
            f"   💰 هزینه ارتقاء: {player['farm'] * 200} طلا\n\n"
            f"⚔️ سربازخانه: سطح {player['barracks']}\n"
            f"   ➕ ظرفیت ارتش: +{player['barracks'] * 10}\n"
            f"   💰 هزینه ارتقاء: {player['barracks'] * 300} طلا\n\n"
            f"⛏️ معدن: سطح {player['mine']}\n"
            f"   ➕ تولید طلا: {player['mine'] * 25} در ساعت\n"
            f"   💰 هزینه ارتقاء: {player['mine'] * 250} طلا"
        )
        
        await message.reply(buildings_info, reply_markup=self.get_buildings_keyboard())

    async def show_pvp_menu(self, message):
        """نمایش منوی PVP"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        pvp_info = (
            "⚔️ **منوی PVP**\n\n"
            "در این بخش می‌توانید:\n"
            "• با بازیکنان واقعی بجنگید\n"
            "• غنائم جنگی کسب کنید\n"
            "• در رده‌بندی صعود کنید\n\n"
            f"💪 قدرت حمله: {self.calculate_attack_power(player)}\n"
            f"🛡️ قدرت دفاع: {player['defense_power']}\n"
            f"🏆 رکورد: {player['wins']}-{player['losses']}"
        )
        
        await message.reply(pvp_info, reply_markup=self.get_pvp_keyboard())

    async def attack_players(self, message):
        """نمایش لیست بازیکنان برای حمله"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        # بررسی زمان آخرین حمله
        last_attack = player.get('last_attack')
        if last_attack:
            last_attack_time = datetime.fromisoformat(last_attack)
            if datetime.now() - last_attack_time < timedelta(minutes=2):
                remaining = timedelta(minutes=2) - (datetime.now() - last_attack_time)
                await message.reply(f"⏰ باید {int(remaining.total_seconds() / 60)} دقیقه دیگر صبر کنید!", reply_markup=self.get_pvp_keyboard())
                return
        
        # پیدا کردن حریفان
        self.cursor.execute('''
            SELECT user_id, username, level, defense_power, wins, losses
            FROM players 
            WHERE user_id != ? 
            ORDER BY level DESC 
            LIMIT 5
        ''', (user_id,))
        opponents = self.cursor.fetchall()
        
        if not opponents:
            await message.reply("🤷‍♂️ در حال حاضر حریفی برای مبارزه پیدا نشد!", reply_markup=self.get_pvp_keyboard())
            return
        
        opponents_text = "🎯 **حریفان قابل حمله:**\n\n"
        
        for i, opp in enumerate(opponents, 1):
            opp_id, opp_name, opp_level, opp_defense, opp_wins, opp_losses = opp
            opponents_text += f"{i}. {opp_name} (سطح {opp_level})\n"
            opponents_text += f"   💪 قدرت: {opp_defense} | 🏆 {opp_wins}-{opp_losses}\n\n"
        
        opponents_text += "برای حمله، شماره حریف را انتخاب کنید:"
        
        # ذخیره لیست حریفان برای کاربر
        if not hasattr(self, 'user_opponents'):
            self.user_opponents = {}
        self.user_opponents[user_id] = opponents
        
        await message.reply(opponents_text, reply_markup=self.get_attack_keyboard())

    async def process_attack_by_number(self, message, opponent_num):
        """پردازش حمله با شماره"""
        user_id = message.author.id
        
        if user_id not in self.user_opponents:
            await message.reply("❌ ابتدا باید لیست حریفان را مشاهده کنید! 'حمله' را انتخاب کنید.", reply_markup=self.get_pvp_keyboard())
            return
        
        opponents = self.user_opponents[user_id]
        
        if opponent_num < 1 or opponent_num > len(opponents):
            await message.reply(f"❌ شماره حریف باید بین 1 تا {len(opponents)} باشد!", reply_markup=self.get_pvp_keyboard())
            return
        
        # پیدا کردن حریف انتخاب شده
        opponent = opponents[opponent_num - 1]
        defender_id = opponent[0]
        
        await self.process_battle(message, user_id, defender_id)

    async def show_leaderboard(self, message):
        """نمایش رده‌بندی"""
        self.cursor.execute('''
            SELECT username, level, wins, losses, gold, defense_power
            FROM players 
            ORDER BY wins DESC, level DESC 
            LIMIT 10
        ''')
        top_players = self.cursor.fetchall()
        
        leaderboard_text = "🏆 **رده‌بندی برترین بازیکنان:**\n\n"
        
        for i, player in enumerate(top_players, 1):
            username, level, wins, losses, gold, defense = player
            leaderboard_text += f"{i}. {username}\n"
            leaderboard_text += f"   ⭐ سطح {level} | 🏆 {wins} برد | 💰 {gold} طلا\n\n"
        
        user_id = message.author.id
        player_data = self.get_player(user_id)
        rank = self.get_player_rank(user_id)
        
        leaderboard_text += f"🎯 **رتبه شما:** {rank}\n"
        leaderboard_text += f"🏆 بردها: {player_data['wins']} | 💔 باخت‌ها: {player_data['losses']}"
        
        await message.reply(leaderboard_text, reply_markup=self.get_main_menu_keyboard())

    async def show_defense(self, message):
        """نمایش وضعیت دفاع"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        defense_info = (
            f"🛡️ **وضعیت دفاع**\n\n"
            f"💪 قدرت دفاع فعلی: {player['defense_power']}\n"
            f"🛡️ سربازان دفاعی: {player['soldiers']}\n"
            f"🏹 کمانداران دفاعی: {player['archers']}\n"
            f"🐎 سواره نظام دفاعی: {player['cavalry']}\n\n"
            f"📊 آمار دفاع:\n"
            f"✅ دفاع موفق: {player['wins']} بار\n"
            f"❌ دفاع شکست خورده: {player['losses']} بار"
        )
        
        defense_keyboard = self.create_keyboard(["🛡️ تقویت دفاع", "🏠 منوی اصلی"])
        
        await message.reply(defense_info, reply_markup=defense_keyboard)

    async def show_help(self, message):
        """نمایش راهنما"""
        help_text = (
            "❓ **راهنمای بازی**\n\n"
            "🎮 **هدف بازی:**\n"
            "ساخت پایگاه قدرتمند و جنگ با بازیکنان دیگر\n\n"
            "**منوهای اصلی:**\n"
            "🏰 پایگاه - اطلاعات کلی و ارتقاء\n"
            "📊 منابع - مدیریت منابع\n"
            "⚔️ ارتش - استخدام نیروها\n"
            "🏗️ ساختمان‌ها - ساخت و ارتقاء\n"
            "🌍 PVP - نبرد با بازیکنان\n"
            "🏆 رده‌بندی - جدول رقابت\n"
            "🛡️ دفاع - وضعیت دفاع\n\n"
            "💡 **نکته:** هر 2 دقیقه یکبار می‌توانید حمله کنید!"
        )
        
        await message.reply(help_text, reply_markup=self.get_main_menu_keyboard())

    async def upgrade_base(self, message):
        """ارتقاء پایگاه"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        cost = player['level'] * 500
        
        if player['gold'] >= cost:
            self.update_player(user_id,
                             level=player['level'] + 1,
                             gold=player['gold'] - cost,
                             defense_power=player['defense_power'] + 50)
            
            await message.reply(
                f"✅ پایگاه به سطح {player['level'] + 1} ارتقاء یافت!\n\n"
                f"💰 هزینه: {cost} طلا\n"
                f"💪 قدرت دفاع: +50\n"
                f"💰 طلا باقی‌مانده: {player['gold'] - cost}",
                reply_markup=self.get_base_keyboard()
            )
        else:
            await message.reply(
                f"❌ برای ارتقاء به {cost} طلا نیاز دارید! طلای فعلی: {player['gold']}",
                reply_markup=self.get_base_keyboard()
            )

    async def upgrade_defense(self, message):
        """تقویت دفاع"""
        user_id = message.author.id
        player = self.get_player(user_id)
        cost = 200
        
        if player['gold'] >= cost:
            self.update_player(user_id,
                             gold=player['gold'] - cost,
                             defense_power=player['defense_power'] + 20)
            
            await message.reply(
                f"✅ دفاع تقویت شد!\n\n"
                f"💰 هزینه: {cost} طلا\n"
                f"💪 قدرت دفاع جدید: {player['defense_power'] + 20}\n"
                f"💰 طلا باقی‌مانده: {player['gold'] - cost}",
                reply_markup=self.get_base_keyboard()
            )
        else:
            await message.reply(
                f"❌ برای تقویت دفاع به {cost} طلا نیاز دارید! طلای فعلی: {player['gold']}",
                reply_markup=self.get_base_keyboard()
            )

    async def recruit_unit(self, message, unit_type):
        """استخدام واحد نظامی"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        costs = {'soldier': 50, 'archer': 80, 'cavalry': 150}
        units = {'soldier': 'soldiers', 'archer': 'archers', 'cavalry': 'cavalry'}
        unit_names = {'soldier': 'سرباز', 'archer': 'کماندار', 'cavalry': 'سواره نظام'}
        
        cost = costs[unit_type]
        unit_name = unit_names[unit_type]
        
        if player['gold'] >= cost:
            current_units = player[units[unit_type]]
            self.update_player(user_id,
                             gold=player['gold'] - cost,
                             **{units[unit_type]: current_units + 1})
            
            await message.reply(
                f"✅ یک {unit_name} استخدام شد!\n\n"
                f"💰 هزینه: {cost} طلا\n"
                f"👥 تعداد جدید: {current_units + 1}\n"
                f"💰 طلا باقی‌مانده: {player['gold'] - cost}",
                reply_markup=self.get_army_keyboard()
            )
        else:
            await message.reply(
                f"❌ برای استخدام {unit_name} به {cost} طلا نیاز دارید! طلای فعلی: {player['gold']}",
                reply_markup=self.get_army_keyboard()
            )

    async def build_building(self, message, building_type):
        """ساخت ساختمان"""
        user_id = message.author.id
        player = self.get_player(user_id)
        
        buildings = {'farm': 'مزرعه', 'barracks': 'سربازخانه', 'mine': 'معدن'}
        costs = {'farm': 200, 'barracks': 300, 'mine': 250}
        
        building_name = buildings[building_type]
        cost = costs[building_type] * player[building_type]
        current_level = player[building_type]
        
        if player['gold'] >= cost:
            self.update_player(user_id,
                             gold=player['gold'] - cost,
                             **{building_type: current_level + 1})
            
            await message.reply(
                f"✅ {building_name} به سطح {current_level + 1} ارتقاء یافت!\n\n"
                f"💰 هزینه: {cost} طلا\n"
                f"💰 طلا باقی‌مانده: {player['gold'] - cost}",
                reply_markup=self.get_buildings_keyboard()
            )
        else:
            await message.reply(
                f"❌ برای ارتقاء {building_name} به {cost} طلا نیاز دارید! طلای فعلی: {player['gold']}",
                reply_markup=self.get_buildings_keyboard()
            )

    async def process_battle(self, message, attacker_id, defender_id):
        """پردازش نبرد"""
        attacker = self.get_player(attacker_id)
        defender = self.get_player(defender_id)
        
        if not attacker or not defender:
            await message.reply("❌ بازیکن پیدا نشد!", reply_markup=self.get_pvp_keyboard())
            return
        
        # شبیه‌سازی نبرد
        attack_power = self.calculate_attack_power(attacker)
        defense_power = defender['defense_power']
        
        # افزودن شانس
        attack_power += random.randint(-30, 30)
        defense_power += random.randint(-20, 20)
        
        if attack_power > defense_power:
            # پیروزی
            victory_margin = (attack_power - defense_power) / attack_power
            loot = min(defender['gold'] * 0.15, 400)
            
            self.update_player(attacker_id, 
                             wins=attacker['wins'] + 1,
                             gold=attacker['gold'] + loot)
            self.update_player(defender_id,
                             losses=defender['losses'] + 1,
                             gold=defender['gold'] - loot)
            
            result_text = (
                f"🎉 **پیروزی درخشان!**\n\n"
                f"شما {defender['username']} را شکست دادید!\n"
                f"💰 غنیمت: {int(loot)} طلا\n"
                f"💪 میزان پیروزی: {victory_margin:.1%}\n"
                f"🏆 بردهای شما: {attacker['wins'] + 1}"
            )
        else:
            # شکست
            defeat_margin = (defense_power - attack_power) / defense_power
            self.update_player(attacker_id, losses=attacker['losses'] + 1)
            self.update_player(defender_id, wins=defender['wins'] + 1)
            
            result_text = (
                f"💔 **شکست مایوس کننده!**\n\n"
                f"شما در برابر {defender['username']} شکست خوردید!\n"
                f"💪 میزان شکست: {defeat_margin:.1%}\n"
                f"🎯 ارتش خود را تقویت کنید و دوباره تلاش کنید!"
            )
        
        # آپدیت زمان آخرین حمله
        self.update_player(attacker_id, last_attack=datetime.now().isoformat())
        
        # ثبت نبرد
        self.cursor.execute('''
            INSERT INTO battles (attacker_id, defender_id, result, loot, battle_time)
            VALUES (?, ?, ?, ?, ?)
        ''', (attacker_id, defender_id, 'win' if attack_power > defense_power else 'loss', 
              loot if attack_power > defense_power else 0, datetime.now().isoformat()))
        self.conn.commit()
        
        await message.reply(result_text, reply_markup=self.get_pvp_keyboard())

    def calculate_attack_power(self, player):
        """محاسبه قدرت حمله"""
        return (player['soldiers'] * 10 + 
                player['archers'] * 15 + 
                player['cavalry'] * 25)

    def get_player_rank(self, user_id):
        """دریافت رتبه بازیکن"""
        self.cursor.execute('''
            SELECT COUNT(*) + 1 FROM players 
            WHERE wins > (SELECT wins FROM players WHERE user_id = ?)
        ''', (user_id,))
        return self.cursor.fetchone()[0]

# اجرای ربات
if __name__ == "__main__":
    # توکن ربات خود را اینجا قرار دهید
    bot = PVPStrategicGame(BOT_TOKEN)
    
    print("🤖 ربات بازی استراتژیک PVP در حال اجراست...")
    print("🎮 برای شروع، در تلگرام به ربات مراجعه و /start را ارسال کنید!")
    print("📱 منوها به صورت دکمه‌ای نمایش داده می‌شوند!")
    bot.client.run()