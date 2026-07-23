import discord
from discord.ext import commands
from discord.ui import Button, View, Select
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
import random
import string
import json

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = 1504482964661076098
ADMIN_ROLE_ID = 1516094850628587630
INVITE_LINK = "https://discord.gg/njxxTuMH"
VERIFY_ROLE_ID = 1508785745547235388
VERIFIED_ROLE_ID = 1504503685328146585
VERIFY_MESSAGE_CHANNEL_ID = 1513696689536372736
VERIFY_LOG_CHANNEL_ID = 1513733733184831558
JAIL_ROLE_ID = 1512734205971398676
IMMUNITY_ROLE_ID = 1514879604270305291
TICKET_CATEGORY_ID = 1529642272118014073

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

hardbanned_users = set()
warnings = defaultdict(list)
user_messages = defaultdict(list)
user_warnings = defaultdict(int)
user_message_times = defaultdict(list)
user_violations = defaultdict(list)
verify_running = False
banned_count = 0
verify_message_id = None
verify_channel_id = None
user_roles_backup = {}
afk_users = {}

# Система кулдаунов
command_cooldowns = defaultdict(dict)
COOLDOWN_BAN = 7200
COOLDOWN_MUTE = 7200
COOLDOWN_JAIL = 7200
COOLDOWN_WARN = 7200

ban_usage = defaultdict(list)
mute_usage = defaultdict(list)
warn_usage = defaultdict(list)
jail_usage = defaultdict(list)

BAN_LIMIT = 3
MUTE_LIMIT = 3
WARN_LIMIT = 3
JAIL_LIMIT = 1
TIME_WINDOW = 300

MONITORED_USERS = {
    1220374053416599604: [1516094850628587630, 1527291269330505759],
    903474440564801627: [1515363972180869282, 1516192523691884816],
    1430922990706491546: [1508842712542089498]
}

role_map = {
    'retard': 1513440439766876180,
    'tester': 1504503576653856868,
    'known': 1504503401059324055,
    'vip': 1508798935991320767,
    'coolguy': 1508842712542089498,
    'ticketssupport': 1509149262334791791,
    'contentcreator': 1508793047230709932,
    'ticketsadmin': 1509149263123320874,
    'helper': 1504503460740202567,
    'support': 1508782838600830996,
    'mod': 1504503217382232166,
    'senior mod': 1504502978374139977,
    'manager': 1508790828448092211,
    'co-owner': 1508790026518003713,
    'dev': 1504502883872411800,
    'imageperms': 1514869583738175508
}

CHANNELS_TO_LOCK = [
    1513695339167617084,
    1513695434026254438,
    1514945294964359329
]

VOICE_CHANNELS_TO_LOCK = [
    1513692263010799716,
    1513692362931703818,
    1513692441281036348,
    1513692510306963476,
    1513692585682669618
]

STAFF_ROLES = [
    1508782838600830996,
    1504503460740202567,
    1508793047230709932,
    1504503217382232166,
    1504502978374139977,
    1508790828448092211,
    1516192523691884816
]

ADMIN_ROLES = [
    1504502759922077776,
    1516192523691884816,
    1508790828448092211,
    1504502978374139977
]

ALL_STAFF_ROLES = [
    1504502759922077776,
    1504502883872411800,
    1516192523691884816,
    1508790828448092211,
    1504502978374139977,
    1504503217382232166,
    1508782838600830996,
    1504503460740202567
]

def generate_warn_code():
    return '#' + ''.join(random.choices(string.digits, k=4))

def has_permission(ctx):
    if ctx.author.guild_permissions.administrator:
        return True
    return False

def has_immunity(member):
    if member is None:
        return False
    for role in member.roles:
        if role.id == IMMUNITY_ROLE_ID:
            return True
    return False

def check_cooldown(user_id, command_type, limit, time_window, cooldown_duration):
    current_time = time.time()
    
    if command_type == 'ban':
        usages = ban_usage[user_id]
    elif command_type == 'mute':
        usages = mute_usage[user_id]
    elif command_type == 'warn':
        usages = warn_usage[user_id]
    elif command_type == 'jail':
        usages = jail_usage[user_id]
    else:
        return True, None
    
    usages = [t for t in usages if current_time - t < time_window]
    
    if len(usages) >= limit:
        if command_type in command_cooldowns[user_id]:
            cooldown_end = command_cooldowns[user_id][command_type]
            if current_time < cooldown_end:
                remaining = int(cooldown_end - current_time)
                return False, remaining
        usages = []
    
    if command_type == 'ban':
        ban_usage[user_id] = usages
    elif command_type == 'mute':
        mute_usage[user_id] = usages
    elif command_type == 'warn':
        warn_usage[user_id] = usages
    elif command_type == 'jail':
        jail_usage[user_id] = usages
    
    return True, None

def add_cooldown(user_id, command_type, cooldown_duration):
    current_time = time.time()
    if user_id not in command_cooldowns:
        command_cooldowns[user_id] = {}
    command_cooldowns[user_id][command_type] = current_time + cooldown_duration

def record_usage(user_id, command_type):
    current_time = time.time()
    if command_type == 'ban':
        ban_usage[user_id].append(current_time)
    elif command_type == 'mute':
        mute_usage[user_id].append(current_time)
    elif command_type == 'warn':
        warn_usage[user_id].append(current_time)
    elif command_type == 'jail':
        jail_usage[user_id].append(current_time)

def format_time(seconds):
    hours = seconds // 3600
    minutes = (seconds % 3600) // 60
    if hours > 0:
        return f"{hours} hour{'s' if hours > 1 else ''} and {minutes} minute{'s' if minutes != 1 else ''}"
    return f"{minutes} minute{'s' if minutes != 1 else ''}"

def format_afk_time(start_time):
    elapsed = int(time.time() - start_time)
    hours = elapsed // 3600
    minutes = (elapsed % 3600) // 60
    seconds = elapsed % 60
    if hours > 0:
        return f"{hours}h {minutes}m {seconds}s"
    elif minutes > 0:
        return f"{minutes}m {seconds}s"
    else:
        return f"{seconds}s"

def save_warnings():
    try:
        warnings_dict = {}
        for key, value in warnings.items():
            warnings_dict[str(key)] = value
        with open('warnings.json', 'w') as f:
            json.dump(warnings_dict, f)
    except Exception as e:
        print(f"Error saving warnings: {e}")

def load_warnings():
    global warnings, user_warnings
    try:
        with open('warnings.json', 'r') as f:
            data = json.load(f)
            for user_id, warns in data.items():
                warnings[int(user_id)] = warns
                user_warnings[int(user_id)] = len(warns)
    except FileNotFoundError:
        pass
    except Exception as e:
        print(f"Error loading warnings: {e}")

# Кнопка для удаления тикета
class DeleteTicketButton(Button):
    def __init__(self):
        super().__init__(label="🗑️ Delete Ticket", style=discord.ButtonStyle.danger)
    
    async def callback(self, interaction: discord.Interaction):
        if not interaction.user.guild_permissions.administrator:
            embed = discord.Embed(
                description="You don't have permission to delete this ticket!",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            await interaction.response.send_message(embed=embed, ephemeral=True)
            return
        
        await interaction.response.send_message("Deleting ticket...", ephemeral=True)
        await asyncio.sleep(1)
        await interaction.channel.delete()

# Ticket Views
class TicketView(View):
    def __init__(self):
        super().__init__(timeout=None)
    
    @discord.ui.select(
        placeholder="Choose an option...",
        options=[
            discord.SelectOption(label="I want to be staff", description="Apply for staff position", emoji="🛡️"),
            discord.SelectOption(label="I want to be developer", description="Apply for developer position", emoji="💻"),
            discord.SelectOption(label="I found a issue in script", description="Report a script issue", emoji="🐛")
        ]
    )
    async def select_callback(self, interaction: discord.Interaction, select: discord.ui.Select):
        await interaction.response.defer()
        choice = select.values[0]
        
        category = interaction.guild.get_channel(TICKET_CATEGORY_ID)
        if not category:
            await interaction.followup.send("Ticket category not found!", ephemeral=True)
            return
        
        ticket_id = ''.join(random.choices(string.digits, k=3))
        channel_name = f"ticket-{ticket_id}"
        
        overwrites = {
            interaction.guild.default_role: discord.PermissionOverwrite(view_channel=False),
            interaction.user: discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        }
        
        for role_id in ALL_STAFF_ROLES:
            role = interaction.guild.get_role(role_id)
            if role:
                overwrites[role] = discord.PermissionOverwrite(view_channel=True, send_messages=True, attach_files=True, embed_links=True)
        
        channel = await interaction.guild.create_text_channel(
            channel_name,
            category=category,
            overwrites=overwrites
        )
        
        embed = discord.Embed(
            description=f"{interaction.user.mention}, hello. This is your ticket.",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        
        if choice == "I want to be staff":
            embed.description += f"\n\nThis is ur ticket to be staff. Answer the questions below:\n\n#1 how much u can be active in one day\n#2 are u mobile/pc user\n#3 have you read the staff-info?\n#4 was there any experience in this field?"
            mention = " ".join([f"<@&{role_id}>" for role_id in ADMIN_ROLES])
            await channel.send(f"{mention}")
        elif choice == "I want to be developer":
            embed.description += f'\n\nThis is ur ticket. "I want to be a new dev". Explain ur experience with lua coding below. Show screenshots/videos of your work to get admins respond faster.'
            mention = " ".join([f"<@&{role_id}>" for role_id in [1504502759922077776, 1504502883872411800, 1516192523691884816, 1508790828448092211]])
            await channel.send(f"{mention}")
        else:
            embed.description += f'\n\nThis is ur ticket. "I found a issue in script". Explain it below and wait when moderators answer to u. You can send screenshot or video to get ur problem resolved faster.'
            mention = " ".join([f"<@&{role_id}>" for role_id in ALL_STAFF_ROLES])
            await channel.send(f"{mention}")
        
        embed.color = discord.Color.from_rgb(255, 255, 255)
        await channel.send(embed=embed)
        
        view = View()
        view.add_item(DeleteTicketButton())
        await channel.send("Click the button below to delete this ticket.", view=view)
        
        await interaction.followup.send(f"Ticket created: {channel.mention}", ephemeral=True)

@bot.event
async def on_ready():
    global banned_count, verify_message_id, verify_channel_id
    print(f'Bot {bot.user} is online')
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="discord.gg/hsx"))
    
    load_warnings()
    
    channel = bot.get_channel(1518832499122507786)
    if channel:
        try:
            async for message in channel.history(limit=None):
                if message.author == bot.user:
                    continue
                banned_count += 1
        except:
            pass
    
    guild = bot.get_guild(SERVER_ID)
    if guild:
        verify_channel = guild.get_channel(VERIFY_MESSAGE_CHANNEL_ID)
        if verify_channel:
            async for message in verify_channel.history(limit=50):
                if message.author == bot.user and message.embeds:
                    verify_message_id = message.id
                    verify_channel_id = message.channel.id
                    print(f'Verification message restored: {verify_message_id}')
                    break

@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    
    if message.guild is None or message.guild.id != SERVER_ID:
        await bot.process_commands(message)
        return
    
    # AFK check
    if message.author.id in afk_users:
        afk_data = afk_users[message.author.id]
        afk_time = format_afk_time(afk_data['time'])
        embed = discord.Embed(
            description=f"{message.author.mention}, u was afk for: {afk_data['reason']} ({afk_time})",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await message.channel.send(embed=embed)
        del afk_users[message.author.id]
    
    # Проверка на # (если начинается с #)
    if message.content and message.content.startswith('#'):
        await message.delete()
        await warn_user_auto(message, "sending messages starting with #")
        await bot.process_commands(message)
        return
    
    # Проверка на спам (4 сообщения за 10 секунд)
    current_time = time.time()
    user_id = message.author.id
    
    # Очищаем старые сообщения
    if user_id not in user_message_times:
        user_message_times[user_id] = []
    user_message_times[user_id] = [t for t in user_message_times[user_id] if current_time - t < 10]
    user_message_times[user_id].append(current_time)
    
    # Проверка на 4 сообщения за 10 секунд
    if len(user_message_times[user_id]) >= 4:
        await message.delete()
        await warn_user_auto(message, "spamming (4 messages in 10 seconds)")
        user_message_times[user_id] = []
        await bot.process_commands(message)
        return
    
    # Проверка на одинаковые сообщения (4 за 5 секунд)
    if message.content and len(message.content) > 0:
        if user_id not in user_messages:
            user_messages[user_id] = []
        
        # Очищаем старые сообщения
        user_messages[user_id] = [msg for msg in user_messages[user_id] if current_time - msg['time'] < 5]
        
        # Проверяем одинаковые сообщения
        similar_count = 0
        for msg in user_messages[user_id]:
            if msg['content'] == message.content:
                similar_count += 1
        
        if similar_count >= 3:  # 3 одинаковых + текущее = 4
            await message.delete()
            await warn_user_auto(message, "spamming (4 identical messages in 5 seconds)")
            user_messages[user_id] = []
            await bot.process_commands(message)
            return
        
        user_messages[user_id].append({
            'content': message.content,
            'time': current_time
        })
    
    # Check for porn/loadstring links
    if "porn" in message.content.lower() or "loadstring" in message.content.lower():
        allowed_loadstring = 'loadstring(game:HttpGet("https://raw.githubusercontent.com/saosdkjiqwdjuqjudidw/HollyScriptX/refs/heads/main/main.lua"))()'
        if allowed_loadstring not in message.content:
            await message.delete()
            await warn_user_auto(message, "sending something stupid, prn links, random scripts")
            await bot.process_commands(message)
            return
    
    if message.channel.id == 1518832499122507786:
        await auto_ban(message)
        await bot.process_commands(message)
        return
    
    if "zalupa" in message.content.lower():
        await message.reply("**hi!**")
    
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.id in MONITORED_USERS:
        roles_to_add = MONITORED_USERS[member.id]
        for role_id in roles_to_add:
            role = member.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
        
        channel = bot.get_channel(1513695339167617084)
        if channel:
            embed = discord.Embed(
                description=f"{member.mention} i detected ur joining, so added ur roles back.",
                color=discord.Color.from_rgb(100, 220, 100)
            )
            await channel.send(embed=embed)

@bot.event
async def on_raw_reaction_add(payload):
    if payload.user_id == bot.user.id:
        return
    
    if payload.message_id != verify_message_id:
        return
    
    if str(payload.emoji) != "✅":
        return
    
    guild = bot.get_guild(SERVER_ID)
    if not guild:
        return
    
    member = guild.get_member(payload.user_id)
    if not member:
        return
    
    old_role = guild.get_role(VERIFY_ROLE_ID)
    new_role = guild.get_role(VERIFIED_ROLE_ID)
    
    if not old_role or not new_role:
        return
    
    try:
        await member.remove_roles(old_role)
        await member.add_roles(new_role)
        
        log_channel = bot.get_channel(VERIFY_LOG_CHANNEL_ID)
        if log_channel:
            embed = discord.Embed(
                description=f"HollyScriptX\n{member.mention} Just successfully verified!",
                color=discord.Color.from_rgb(100, 220, 100)
            )
            await log_channel.send(embed=embed)
    except Exception as e:
        print(f'Verify error: {e}')

async def warn_user_auto(message, reason, moderator="Auto-Mod"):
    # Check if user has admin perms
    if message.author.guild_permissions.administrator:
        return
    
    # Check immunity
    if has_immunity(message.author):
        return
    
    warn_code = generate_warn_code()
    user_warnings[message.author.id] += 1
    warn_count = user_warnings[message.author.id]
    
    if message.author.id not in warnings:
        warnings[message.author.id] = []
    
    warnings[message.author.id].append({
        'code': warn_code,
        'reason': reason,
        'moderator': moderator,
        'date': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    })
    
    save_warnings()
    
    embed = discord.Embed(
        title="Warned",
        description=f"You have been warned in\n**HollyScriptX**",
        color=discord.Color.from_rgb(255, 180, 50)
    )
    embed.add_field(name="Moderator", value=moderator, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Warning", value=f"{warn_count}/5", inline=False)
    embed.add_field(name="Code", value=warn_code, inline=False)
    embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
    
    try:
        await message.author.send(embed=embed)
    except:
        pass
    
    embed_channel = discord.Embed(
        description=f"{message.author.mention} you have been warned for {reason} #{warn_count}/5\nCode: {warn_code}",
        color=discord.Color.from_rgb(220, 80, 80)
    )
    await message.channel.send(embed=embed_channel)
    
    if warn_count >= 5:
        try:
            await message.author.ban(reason="5 warnings - automatic ban")
            
            embed_ban = discord.Embed(
                title="Banned",
                description=f"You have been **banned** from\n**HollyScriptX**",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            embed_ban.add_field(name="Moderator", value="Auto-Mod", inline=False)
            embed_ban.add_field(name="Reason", value="5 warnings", inline=False)
            embed_ban.add_field(name="Duration", value="Permanent", inline=False)
            embed_ban.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
            
            try:
                await message.author.send(embed=embed_ban)
            except:
                pass
            
            embed_channel_ban = discord.Embed(
                description=f"{message.author.mention} has been banned for violating rules. #5/5",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            await message.channel.send(embed=embed_channel_ban)
        except Exception as e:
            print(f'Ban error: {e}')
    
    return warn_code

async def warn_user(target, reason, moderator=None, ctx=None):
    if hasattr(target, 'author'):
        member = target.author
        channel = target.channel
    else:
        member = target
        channel = ctx.channel if ctx else None
    
    if has_immunity(member):
        if channel:
            embed = discord.Embed(
                description=f"{member.mention} has immunity from punishments.",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            await channel.send(embed=embed)
        return None
    
    if member.guild_permissions.administrator:
        if channel:
            embed = discord.Embed(
                description=f"{member.mention} has administrator permissions and cannot be warned.",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            await channel.send(embed=embed)
        return None
    
    warn_code = generate_warn_code()
    user_warnings[member.id] += 1
    warn_count = user_warnings[member.id]
    
    if member.id not in warnings:
        warnings[member.id] = []
    
    warnings[member.id].append({
        'code': warn_code,
        'reason': reason,
        'moderator': moderator or "Auto-Mod",
        'date': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    })
    
    save_warnings()
    
    embed = discord.Embed(
        title="Warned",
        description=f"You have been warned in\n**HollyScriptX**",
        color=discord.Color.from_rgb(255, 180, 50)
    )
    embed.add_field(name="Moderator", value=moderator or "Auto-Mod", inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Warning", value=f"{warn_count}/5", inline=False)
    embed.add_field(name="Code", value=warn_code, inline=False)
    embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
    
    try:
        await member.send(embed=embed)
    except:
        pass
    
    if channel:
        embed_channel = discord.Embed(
            description=f"{member.mention} has been warned for {reason} #{warn_count}/5\nCode: {warn_code}",
            color=discord.Color.from_rgb(255, 180, 50)
        )
        await channel.send(embed=embed_channel)
    
    if warn_count >= 5:
        try:
            await member.ban(reason="5 warnings - automatic ban")
            
            embed_ban = discord.Embed(
                title="Banned",
                description=f"You have been **banned** from\n**HollyScriptX**",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            embed_ban.add_field(name="Moderator", value="Auto-Mod", inline=False)
            embed_ban.add_field(name="Reason", value="5 warnings", inline=False)
            embed_ban.add_field(name="Duration", value="Permanent", inline=False)
            embed_ban.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
            
            try:
                await member.send(embed=embed_ban)
            except:
                pass
            
            if channel:
                embed_channel_ban = discord.Embed(
                    description=f"{member.mention} has been banned for violating rules. #5/5",
                    color=discord.Color.from_rgb(220, 80, 80)
                )
                await channel.send(embed=embed_channel_ban)
        except Exception as e:
            print(f'Ban error: {e}')
    
    return warn_code

async def auto_ban(message):
    global banned_count
    try:
        member = message.author
        banned_count += 1
        
        log_channel = bot.get_channel(1518832499122507786)
        if log_channel:
            embed = discord.Embed(
                description=f"{member.mention} has been permanently **banned** from **HollyScriptX**\nReason: **Scammed Accounts detection 1.0**\nTyped Message:\n{message.content}",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            await log_channel.send(embed=embed)
        
        try:
            embed = discord.Embed(
                title="Banned",
                description=f"You have been **banned** from\n**HollyScriptX**",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            embed.add_field(name="Moderator", value="Auto-Mod", inline=False)
            embed.add_field(name="Reason", value="Auto-ban. Typed in do not type channel (prob hacked account).", inline=False)
            embed.add_field(name="Duration", value="Permanent", inline=False)
            embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
            await member.send(embed=embed)
        except:
            pass
        
        await member.ban(reason="Auto-ban. Typed in do not type channel (prob hacked account).")
        await message.delete()
    except Exception as e:
        print(f'Auto ban error: {e}')

@bot.event
async def on_command_error(ctx, error):
    if isinstance(error, commands.CommandNotFound):
        embed = discord.Embed(
            description="Command not found!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingRole):
        if has_permission(ctx):
            await ctx.reinvoke()
        else:
            embed = discord.Embed(
                description="You don't have permissions.",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            await ctx.send(embed=embed)
    elif isinstance(error, commands.MissingAnyRole):
        if has_permission(ctx):
            await ctx.reinvoke()
        else:
            embed = discord.Embed(
                description="You don't have permissions.",
                color=discord.Color.from_rgb(255, 200, 0)
            )
            await ctx.send(embed=embed)
    elif isinstance(error, commands.MemberNotFound):
        embed = discord.Embed(
            description="User not found! Make sure to ping or use correct ID.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
    elif isinstance(error, commands.BadArgument):
        embed = discord.Embed(
            description=f"Invalid argument: {error}",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
    else:
        print(f"Error: {error}")
        embed = discord.Embed(
            description=f"An error occurred: {error}",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_role(1504503460740202567)
async def warn(ctx, member: discord.Member = None, *, args=None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    
    if member is None:
        embed = discord.Embed(
            description="Usage\n.warn <@Member | ID> [reason]\n┗ Member parameter may be replaced with the author of the replied message.\n\nExample 1\n.warn @Member\n┗ Gives empty warning.\n\nExample 2\n.warn @Member behaves provocatively\n┗ Gives warning with specified reason.",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        await ctx.send(embed=embed)
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot warn yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be warned.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    can_use, remaining = check_cooldown(ctx.author.id, 'warn', WARN_LIMIT, TIME_WINDOW, COOLDOWN_WARN)
    if not can_use:
        embed = discord.Embed(
            description=f"You have reached the warn limit ({WARN_LIMIT} warns in 5 minutes). Please wait {format_time(remaining)} before using this command again.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    record_usage(ctx.author.id, 'warn')
    
    if len(warn_usage[ctx.author.id]) >= WARN_LIMIT:
        add_cooldown(ctx.author.id, 'warn', COOLDOWN_WARN)
    
    reason = args or "No reason provided"
    await warn_user(member, reason, ctx.author.mention, ctx)

@bot.command(name="warn-remove", aliases=["warnremove"])
async def warn_remove(ctx, member: discord.Member = None, code: str = None):
    if not (has_permission(ctx) or any(role.id == 1504503460740202567 for role in ctx.author.roles)):
        embed = discord.Embed(
            description="You don't have permissions.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return

    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author

    if member is None or code is None:
        embed = discord.Embed(
            description="Usage: .warn-remove @user #1234",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.id not in warnings or not warnings[member.id]:
        embed = discord.Embed(
            description=f"{member.mention} has no warnings.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    removed = False
    for warn in list(warnings[member.id]):
        if warn['code'] == code:
            warnings[member.id].remove(warn)
            user_warnings[member.id] = max(0, user_warnings[member.id] - 1)
            removed = True
            save_warnings()
            embed = discord.Embed(
                description=f"Removed warning {code} from {member.mention}",
                color=discord.Color.from_rgb(100, 220, 100)
            )
            await ctx.send(embed=embed)
            break
    
    if not removed:
        embed = discord.Embed(
            description=f"Warning {code} not found for {member.mention}",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)

@bot.command(name="warn-list", aliases=["warns-list", "warnlist", "warnslist"])
async def warn_list(ctx, member: discord.Member = None):
    if not (has_permission(ctx) or any(role.id == 1504503460740202567 for role in ctx.author.roles)):
        embed = discord.Embed(
            description="You don't have permissions.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return

    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author

    if member is None:
        member = ctx.author
    
    if member.id not in warnings or not warnings[member.id]:
        embed = discord.Embed(
            description=f"{member.mention} has no warnings.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    embed = discord.Embed(
        title=f"Warnings for {member.display_name}",
        color=discord.Color.from_rgb(255, 180, 50)
    )
    
    for i, warn in enumerate(warnings[member.id], 1):
        embed.add_field(
            name=f"{i}. {warn['code']}",
            value=f"Reason: {warn['reason']}\nModerator: {warn['moderator']}\nDate: {warn['date']}",
            inline=False
        )
    
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(1504503460740202567)
async def jail(ctx, member: discord.Member = None, *, reason="No reason provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .jail @user (reason)")
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot jail yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be jailed.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    can_use, remaining = check_cooldown(ctx.author.id, 'jail', JAIL_LIMIT, TIME_WINDOW, COOLDOWN_JAIL)
    if not can_use:
        embed = discord.Embed(
            description=f"You have reached the jail limit ({JAIL_LIMIT} jail in 5 minutes). Please wait {format_time(remaining)} before using this command again.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    record_usage(ctx.author.id, 'jail')
    
    if len(jail_usage[ctx.author.id]) >= JAIL_LIMIT:
        add_cooldown(ctx.author.id, 'jail', COOLDOWN_JAIL)
    
    jail_role = ctx.guild.get_role(JAIL_ROLE_ID)
    if not jail_role:
        await ctx.send("Jail role not found!")
        return
    
    user_roles_backup[member.id] = [role.id for role in member.roles if role.id != JAIL_ROLE_ID]
    
    for role in member.roles:
        if role.id != JAIL_ROLE_ID:
            try:
                await member.remove_roles(role)
            except:
                pass
    
    try:
        await member.add_roles(jail_role)
    except:
        pass
    
    embed = discord.Embed(
        title="Jailed",
        description=f"You have been jailed in\n**HollyScriptX**",
        color=discord.Color.from_rgb(220, 80, 80)
    )
    embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
    embed.add_field(name="Reason", value=reason, inline=False)
    embed.add_field(name="Duration", value="Indefinite", inline=False)
    embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
    
    try:
        await member.send(embed=embed)
    except:
        pass
    
    embed_channel = discord.Embed(
        description=f"{member.mention} has been jailed. Reason: {reason}",
        color=discord.Color.from_rgb(220, 80, 80)
    )
    await ctx.send(embed=embed_channel)

@bot.command()
@commands.has_role(1504503460740202567)
async def unjail(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .unjail @user")
        return
    
    jail_role = ctx.guild.get_role(JAIL_ROLE_ID)
    if jail_role:
        try:
            await member.remove_roles(jail_role)
        except:
            pass
    
    if member.id in user_roles_backup:
        for role_id in user_roles_backup[member.id]:
            role = ctx.guild.get_role(role_id)
            if role:
                try:
                    await member.add_roles(role)
                except:
                    pass
        del user_roles_backup[member.id]
    
    embed = discord.Embed(
        description=f"{member.mention} has been unjailed!",
        color=discord.Color.from_rgb(100, 220, 100)
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(1508782838600830996)
async def kick(ctx, member: discord.Member = None, *, reason="No reason provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .kick @user (reason) or reply to a message with .kick")
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot kick yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be kicked.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        await member.kick(reason=reason)
        embed = discord.Embed(
            description=f"{member.mention} has been kicked. Reason: {reason}",
            color=discord.Color.from_rgb(220, 80, 80)
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I do not have permission to kick this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error kicking user: {e}")

@bot.command()
@commands.has_role(1508782838600830996)
async def ban(ctx, member: discord.Member = None, *, reason="No Reason Provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .ban (@user) (reason) or reply to a message with .ban")
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot ban yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be banned.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    can_use, remaining = check_cooldown(ctx.author.id, 'ban', BAN_LIMIT, TIME_WINDOW, COOLDOWN_BAN)
    if not can_use:
        embed = discord.Embed(
            description=f"You have reached the ban limit ({BAN_LIMIT} bans in 5 minutes). Please wait {format_time(remaining)} before using this command again.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    record_usage(ctx.author.id, 'ban')
    
    if len(ban_usage[ctx.author.id]) >= BAN_LIMIT:
        add_cooldown(ctx.author.id, 'ban', COOLDOWN_BAN)
    
    try:
        await member.ban(reason=reason)
        
        embed = discord.Embed(
            title="Banned",
            description=f"You have been **banned** from\n**HollyScriptX**",
            color=discord.Color.from_rgb(220, 80, 80)
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Duration", value="Permanent", inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
        
        try:
            await member.send(embed=embed)
        except:
            pass
        
        await ctx.send(f"User {member.mention} has been banned. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error banning user: {e}")

@bot.command()
@commands.has_role(1508782838600830996)
async def unban(ctx, *, user_input):
    try:
        user_id = int(user_input)
        user = await bot.fetch_user(user_id)
    except:
        if ctx.message.reference:
            referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            user = referenced.author
        else:
            try:
                user = await commands.UserConverter().convert(ctx, user_input)
            except:
                await ctx.send("Usage: .unban (user_id/username) or reply to a message with .unban")
                return
    
    try:
        await ctx.guild.unban(user)
        embed = discord.Embed(
            description=f"{user.mention} **has been unbanned!**",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except discord.NotFound:
        await ctx.send("User is not banned or not found")
    except discord.Forbidden:
        await ctx.send("I do not have permission to unban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unbanning user: {e}")

@bot.command()
@commands.has_role(1504503460740202567)
async def mute(ctx, member: discord.Member = None, duration: str = None, *, reason="Reason not specified"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .mute (@user) (duration) (reason)\nExample: .mute @user 1h Spamming\nDurations: 1h, 2h, 1d, 2d, 1w, 2w")
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot mute yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be muted.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if duration is None:
        duration = "1h"
    
    duration_map = {
        '1h': 1, '2h': 2, '3h': 3, '4h': 4, '6h': 6, '8h': 8, '12h': 12,
        '1d': 24, '2d': 48, '3d': 72, '4d': 96, '5d': 120, '6d': 144, '1w': 168, '2w': 336
    }
    
    duration_lower = duration.lower()
    if duration_lower not in duration_map:
        await ctx.send("Invalid duration! Use: 1h, 2h, 1d, 2d, 1w, 2w")
        return
    
    hours = duration_map[duration_lower]
    if hours > 336:
        await ctx.send("Maximum mute duration is 2 weeks!")
        return
    
    can_use, remaining = check_cooldown(ctx.author.id, 'mute', MUTE_LIMIT, TIME_WINDOW, COOLDOWN_MUTE)
    if not can_use:
        embed = discord.Embed(
            description=f"You have reached the mute limit ({MUTE_LIMIT} mutes in 5 minutes). Please wait {format_time(remaining)} before using this command again.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    record_usage(ctx.author.id, 'mute')
    
    if len(mute_usage[ctx.author.id]) >= MUTE_LIMIT:
        add_cooldown(ctx.author.id, 'mute', COOLDOWN_MUTE)
    
    try:
        timeout = discord.utils.utcnow() + timedelta(hours=hours)
        await member.timeout(timeout, reason=reason)
        
        embed = discord.Embed(
            title="Muted",
            description=f"You have been **muted** in\n**HollyScriptX**",
            color=discord.Color.from_rgb(255, 180, 50)
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Duration", value=f"{duration}", inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
        
        try:
            await member.send(embed=embed)
        except:
            pass
        
        await ctx.send(f"User {member.mention} has been muted for {duration}. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to mute this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error muting user: {e}")

@bot.command()
@commands.has_role(1508782838600830996)
async def unmute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .unmute (@user) or reply to a message with .unmute")
        return
    
    try:
        await member.remove_timeout()
        embed = discord.Embed(
            description=f"{member.mention} **has been unmuted!**",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I do not have permission to unmute this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unmuting user: {e}")

@bot.command()
async def afk(ctx, *, reason="No reason provided"):
    afk_users[ctx.author.id] = {
        'reason': reason,
        'time': time.time()
    }
    embed = discord.Embed(
        description=f"{ctx.author.mention}, your status now: AFK. ✅",
        color=discord.Color.from_rgb(100, 220, 100)
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def rename(ctx, *, name: str):
    try:
        await ctx.guild.edit(name=name)
        embed = discord.Embed(
            description=f"Server renamed to: {name}",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"Error renaming server: {e}")

@bot.command()
@commands.has_any_role(1504502978374139977, 1508790828448092211, 1504503217382232166, 1508782838600830996, 1504503460740202567)
async def giverole(ctx, role: discord.Role = None):
    if not ctx.message.reference:
        embed = discord.Embed(
            description="❌ You must reply to a message to give a role!\nUsage: .giverole @role (reply to a message)",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if role is None:
        embed = discord.Embed(
            description="❌ Usage: .giverole @role (reply to a message)\nExample: .giverole @helper",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced_msg.author
    except:
        embed = discord.Embed(
            description="❌ Could not find the user you replied to!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="❌ You cannot give roles to yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"❌ {member.mention} has immunity from role changes.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    author_top_role = ctx.author.top_role.position
    role_position = role.position
    bot_top_role = ctx.guild.me.top_role.position
    
    if role_position >= bot_top_role:
        embed = discord.Embed(
            description="❌ I cannot give this role because it's above my highest role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if role_position >= author_top_role:
        embed = discord.Embed(
            description="❌ You cannot give this role because it's above your highest role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        await member.add_roles(role, reason=f"Given by {ctx.author}")
        embed = discord.Embed(
            description=f"✅ Added role {role.mention} to {member.mention}",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            description="❌ I do not have permission to give this role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            description=f"❌ Error giving role: {e}",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_any_role(1504502978374139977, 1508790828448092211, 1504503217382232166, 1508782838600830996, 1504503460740202567)
async def delrole(ctx, role: discord.Role = None):
    if not ctx.message.reference:
        embed = discord.Embed(
            description="❌ You must reply to a message to remove a role!\nUsage: .delrole @role (reply to a message)",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if role is None:
        embed = discord.Embed(
            description="❌ Usage: .delrole @role (reply to a message)\nExample: .delrole @helper",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced_msg.author
    except:
        embed = discord.Embed(
            description="❌ Could not find the user you replied to!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"❌ {member.mention} has immunity from role changes.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    author_top_role = ctx.author.top_role.position
    role_position = role.position
    bot_top_role = ctx.guild.me.top_role.position
    
    if role_position >= bot_top_role:
        embed = discord.Embed(
            description="❌ I cannot remove this role because it's above my highest role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if role_position >= author_top_role:
        embed = discord.Embed(
            description="❌ You cannot remove this role because it's above your highest role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        await member.remove_roles(role, reason=f"Removed by {ctx.author}")
        embed = discord.Embed(
            description=f"✅ Removed role {role.mention} from {member.mention}",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        embed = discord.Embed(
            description="❌ I do not have permission to remove this role!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
    except discord.HTTPException as e:
        embed = discord.Embed(
            description=f"❌ Error removing role: {e}",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def createnewsupportedgame(ctx, *, name: str):
    category = ctx.guild.get_channel(1529642272118014073)
    if not category:
        category = ctx.channel.category
    
    try:
        channel = await ctx.guild.create_voice_channel(
            f"{name}: 🔵",
            category=category
        )
        embed = discord.Embed(
            description=f"✅ Created voice channel: {channel.mention}",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
    except Exception as e:
        await ctx.send(f"❌ Error creating channel: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def ticketcreatestaff(ctx):
    embed = discord.Embed(
        description="Press button below to create your ticket.",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    await ctx.send(embed=embed, view=TicketView())

@bot.command()
async def showstafflist(ctx):
    guild = ctx.guild
    staff_members = {}
    
    for role_id in STAFF_ROLES:
        role = guild.get_role(role_id)
        if role:
            members = [member for member in guild.members if role in member.roles]
            staff_members[role.name] = members
    
    embed = discord.Embed(
        title="Staff List",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    
    for role_name, members in staff_members.items():
        if members:
            embed.add_field(
                name=role_name,
                value="\n".join([f"{member.mention}" for member in members]) or "None",
                inline=False
            )
        else:
            embed.add_field(name=role_name, value="None", inline=False)
    
    await ctx.send(embed=embed)

@bot.command()
async def moderatorshelp(ctx):
    embed = discord.Embed(
        description="""# read this!! important for this discord server Staff.

this channel is maded to show your Permissions. ( USING OTHER BOTS FOR STAFF COMMANDS NOT ALLOWED )

<@&1516192523691884816> Role Permissions:
- You can fully control server even without using this bot.

<@&1508790828448092211> Role Permissions:
- Access to .giverole (maximum u can give is: **seniormod**)
- Access to commands from the roles below

<@&1504502978374139977> Role Permissions:
- Access to .giverole or .delrole (maximum u can give is: **helper**
- Access to audit logs & echo-logs and execution-logs.

<@&1504503217382232166> Role Permissions:
- The same commands with <@&1508782838600830996>

<@&1508782838600830996> Role Permissions:
- Access to .ban
- Access to .unban
- Access to audit logs & echo-logs.

<@&1504503460740202567>
- Access to .jail
- Access to .warn
- Access to .warn_remove
- Access to .warns_list
- Access to audit logs.

# Commands tooltips:
- .warn (userid/ping) (reason) - warns a user. If user gets 5 warns, hes automatically gets banned from server.
- .warn-remove (userid/ping) (warn code - u can see it if u type .warns-list) - removes a warning from user.
- .warns-list (userid/ping) - shows total count of user warnings.
- .ban (userid/ping) (reason) or reply to a message - bans a user from server permanently.
- .unban (userid/ping) - unban user from server.
- .kick (userid/ping) (reason) - kick user from server.
- .jail (userid) (reason) - jail a user
- .unjail (userid) (reason) - unjail a user""",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def down(ctx, game: str = None):
    if game is None:
        await ctx.send("Usage: .down (InkGame / MurderMystery2 / Doors / ALL)")
        return
    
    if game.lower() == "all":
        await down(ctx, "InkGame")
        await down(ctx, "MurderMystery2")
        await down(ctx, "Doors")
        return
    
    channel_map = {
        "inkgame": {"id": 1513692263010799716, "name": "Ink Game: 🔴"},
        "murder mystery 2": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🔴"},
        "murder mystery2": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🔴"},
        "murder": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🔴"},
        "doors": {"id": 1513692441281036348, "name": "Doors: 🔴"}
    }
    
    game_lower = game.lower()
    if game_lower not in channel_map:
        await ctx.send("Invalid game. Options: InkGame, MurderMystery2, Doors, ALL")
        return
    
    channel_id = channel_map[game_lower]["id"]
    new_name = channel_map[game_lower]["name"]
    
    channel = ctx.guild.get_channel(channel_id)
    if channel:
        try:
            await channel.edit(name=new_name)
            embed = discord.Embed(
                description=f"{game} marked as down.",
                color=discord.Color.from_rgb(220, 80, 80)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error changing channel name: {e}")
    else:
        await ctx.send("Channel not found")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def undetected(ctx, game: str = None):
    if game is None:
        await ctx.send("Usage: .undetected (InkGame / MurderMystery2 / Doors / ALL)")
        return
    
    if game.lower() == "all":
        await undetected(ctx, "InkGame")
        await undetected(ctx, "MurderMystery2")
        await undetected(ctx, "Doors")
        return
    
    channel_map = {
        "inkgame": {"id": 1513692263010799716, "name": "Ink Game: 🟢"},
        "murder mystery 2": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🟢"},
        "murder mystery2": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🟢"},
        "murder": {"id": 1513692362931703818, "name": "Murder Mystery 2: 🟢"},
        "doors": {"id": 1513692441281036348, "name": "Doors: 🟢"}
    }
    
    game_lower = game.lower()
    if game_lower not in channel_map:
        await ctx.send("Invalid game. Options: InkGame, MurderMystery2, Doors, ALL")
        return
    
    channel_id = channel_map[game_lower]["id"]
    new_name = channel_map[game_lower]["name"]
    
    channel = ctx.guild.get_channel(channel_id)
    if channel:
        try:
            await channel.edit(name=new_name)
            embed = discord.Embed(
                description=f"{game} marked as undetected.",
                color=discord.Color.from_rgb(100, 220, 100)
            )
            await ctx.send(embed=embed)
        except Exception as e:
            await ctx.send(f"Error changing channel name: {e}")
    else:
        await ctx.send("Channel not found")

@bot.command()
async def help_commands(ctx):
    embed1 = discord.Embed(
        title="Bot Commands (1/3)",
        description="Commands require the admin role to use",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    embed1.add_field(name=".clear (amount)", value="Delete messages in the channel (max 1000)", inline=False)
    embed1.add_field(name=".ban (@user) (reason)", value="Ban a user permanently", inline=False)
    embed1.add_field(name=".unban (user)", value="Unban a user", inline=False)
    embed1.add_field(name=".mute (@user) (duration) (reason)", value="Mute a user (1h, 2h, 1d, 2d, 1w, 2w)", inline=False)
    embed1.add_field(name=".unmute (@user)", value="Unmute a user", inline=False)
    embed1.add_field(name=".warn (@user) (reason)", value="Give a warning to a user", inline=False)
    embed1.add_field(name=".warn-remove (@user) (code)", value="Remove a warning from user", inline=False)
    embed1.add_field(name=".warns-list (@user)", value="Show all warnings of a user", inline=False)
    embed1.add_field(name=".hardban (@user) (reason)", value="Hard ban a user (remove all channel access)", inline=False)
    embed1.add_field(name=".unhardban (user)", value="Remove hard ban from a user", inline=False)
    embed1.add_field(name=".jail (@user) (reason)", value="Jail a user", inline=False)
    embed1.add_field(name=".unjail (@user)", value="Unjail a user", inline=False)
    embed1.add_field(name=".kick (@user) (reason)", value="Kick a user", inline=False)
    embed1.add_field(name=".join", value="Connect bot to voice channel", inline=False)
    embed1.add_field(name=".unjoin", value="Disconnect bot from voice channel", inline=False)
    embed1.add_field(name=".lockchats", value="Lock all specified channels", inline=False)
    
    embed2 = discord.Embed(
        title="Bot Commands (2/3)",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    embed2.add_field(name=".unlockchats", value="Unlock all specified channels", inline=False)
    embed2.add_field(name=".verifyall", value="Verifies all people with unverified role", inline=False)
    embed2.add_field(name=".stopverify", value="Stop verification process", inline=False)
    embed2.add_field(name=".giverole @role", value="Give a role to replied user (reply to message)", inline=False)
    embed2.add_field(name=".delrole @role", value="Remove a role from replied user (reply to message)", inline=False)
    embed2.add_field(name=".down (InkGame / MurderMystery2 / Doors)", value="Mark selected script as down.", inline=False)
    embed2.add_field(name=".down ALL", value="Mark all scripts as down.", inline=False)
    embed2.add_field(name=".undetected (InkGame / MurderMystery2 / Doors)", value="Mark selected script as undetected.", inline=False)
    embed2.add_field(name=".undetected ALL", value="Mark all scripts as undetected.", inline=False)
    embed2.add_field(name=".rename (name)", value="Rename the server", inline=False)
    embed2.add_field(name=".afk (reason)", value="Set AFK status", inline=False)
    embed2.add_field(name=".say (message)", value="Send a message in current channel", inline=False)
    embed2.add_field(name=".saysomething (message)", value="Send a message in specified channel", inline=False)
    embed2.add_field(name=".createnewsupportedgame (name)", value="Create a new voice channel for game", inline=False)
    embed2.add_field(name=".ticketcreatestaff", value="Create staff ticket system", inline=False)
    
    embed3 = discord.Embed(
        title="Bot Commands (3/3)",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    embed3.add_field(name=".showstafflist", value="Show all staff members", inline=False)
    embed3.add_field(name=".moderatorshelp", value="Show staff permissions", inline=False)
    embed3.add_field(name=".invite", value="Send invite to Discord server", inline=False)
    embed3.add_field(name=".help_commands", value="Show this help message", inline=False)
    embed3.add_field(name=".typeinchannel", value="Send warning about no typing channel", inline=False)
    embed3.add_field(name=".sendverifyshit", value="Send verification message", inline=False)
    
    await ctx.send(embed=embed1)
    await ctx.send(embed=embed2)
    await ctx.send(embed=embed3)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Please specify a positive number")
        return
    if amount > 1000:
        await ctx.send("Cannot delete more than 1000 messages at once")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"Deleted {len(deleted) - 1} messages")
    await msg.delete(delay=3)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def hardban(ctx, member: discord.Member = None, *, reason="Not specified"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .hardban (@user) (reason) or reply to a message with .hardban")
        return
    
    if member.id == ctx.author.id:
        embed = discord.Embed(
            description="You cannot hardban yourself!",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if has_immunity(member):
        embed = discord.Embed(
            description=f"{member.mention} has immunity from punishments.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    if member.guild_permissions.administrator:
        embed = discord.Embed(
            description=f"{member.mention} has administrator permissions and cannot be hardbanned.",
            color=discord.Color.from_rgb(255, 200, 0)
        )
        await ctx.send(embed=embed)
        return
    
    try:
        hardbanned_users.add(member.id)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(member, view_channel=False, send_messages=False)
            except:
                pass
        
        embed = discord.Embed(
            title="Hard Banned",
            description=f"You have been **hard-banned** from\n**HollyScriptX**",
            color=discord.Color.from_rgb(220, 80, 80)
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Duration", value="Permanent", inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
        
        try:
            await member.send(embed=embed)
        except:
            pass
        
        embed_channel = discord.Embed(
            description=f"{member.mention} **has been hard-banned!**",
            color=discord.Color.from_rgb(220, 80, 80)
        )
        embed_channel.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed_channel)
        
    except discord.Forbidden:
        await ctx.send("I do not have permission to hard-ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error hard-banning user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def unhardban(ctx, *, user_input):
    try:
        user_id = int(user_input)
        member = ctx.guild.get_member(user_id)
        if member is None:
            member = await bot.fetch_user(user_id)
    except:
        if ctx.message.reference:
            referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
            member = referenced.author
        else:
            try:
                member = await commands.UserConverter().convert(ctx, user_input)
            except:
                await ctx.send("Usage: .unhardban (user_id/username) or reply to a message with .unhardban")
                return
    
    try:
        if member.id in hardbanned_users:
            hardbanned_users.remove(member.id)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(member, overwrite=None)
            except:
                pass
        
        embed = discord.Embed(
            description=f"{member.mention} **has been unhard-banned!**",
            color=discord.Color.from_rgb(100, 220, 100)
        )
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("I do not have permission to unhard-ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unhard-banning user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def lockchats(ctx):
    guild = ctx.guild
    locked_channels = []
    
    for channel_id in CHANNELS_TO_LOCK:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(guild.default_role, overwrite=overwrite)
                locked_channels.append(channel.mention)
            except:
                pass
    
    for channel_id in VOICE_CHANNELS_TO_LOCK:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                overwrite = channel.overwrites_for(guild.default_role)
                overwrite.connect = False
                await channel.set_permissions(guild.default_role, overwrite=overwrite)
                locked_channels.append(channel.mention)
            except:
                pass
    
    if locked_channels:
        progress_msg = await ctx.send(f"Locking channels: {len(locked_channels)} channels...")
        await asyncio.sleep(1)
        await progress_msg.edit(content=f"Locked channels: {', '.join(locked_channels[:5])}" + (f" and {len(locked_channels)-5} more" if len(locked_channels) > 5 else ""))
    else:
        await ctx.send("No channels found to lock")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def unlockchats(ctx):
    guild = ctx.guild
    unlocked_channels = []
    
    for channel_id in CHANNELS_TO_LOCK:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.set_permissions(guild.default_role, overwrite=None)
                unlocked_channels.append(channel.mention)
            except:
                pass
    
    for channel_id in VOICE_CHANNELS_TO_LOCK:
        channel = guild.get_channel(channel_id)
        if channel:
            try:
                await channel.set_permissions(guild.default_role, overwrite=None)
                unlocked_channels.append(channel.mention)
            except:
                pass
    
    if unlocked_channels:
        progress_msg = await ctx.send(f"Unlocking channels: {len(unlocked_channels)} channels...")
        await asyncio.sleep(1)
        await progress_msg.edit(content=f"Unlocked channels: {', '.join(unlocked_channels[:5])}" + (f" and {len(unlocked_channels)-5} more" if len(unlocked_channels) > 5 else ""))
    else:
        await ctx.send("No channels found to unlock")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def verifyall(ctx):
    global verify_running
    
    if verify_running:
        await ctx.send("Verification process is already running")
        return
    
    guild = ctx.guild
    old_role = guild.get_role(VERIFY_ROLE_ID)
    new_role = guild.get_role(VERIFIED_ROLE_ID)
    
    if not old_role:
        await ctx.send(f"Role with ID {VERIFY_ROLE_ID} not found")
        return
    if not new_role:
        await ctx.send(f"Role with ID {VERIFIED_ROLE_ID} not found")
        return
    
    members = [member for member in guild.members if old_role in member.roles]
    if not members:
        await ctx.send("No members found with the specified role")
        return
    
    verify_running = True
    unverified_msg = await ctx.send(f"Unverified Users: {len(members)}")
    progress_msg = await ctx.send("Starting verification...")
    
    success = 0
    fail = 0
    total = len(members)
    
    for index, member in enumerate(members, 1):
        if not verify_running:
            break
        try:
            await member.remove_roles(old_role)
            await member.add_roles(new_role)
            success += 1
            await progress_msg.edit(content=f"Success Verified user: {member.mention} ({index}/{total})")
        except:
            fail += 1
        await asyncio.sleep(0.5)
    
    verify_running = False
    await unverified_msg.edit(content=f"Unverified Users: {total - success - fail}")
    await progress_msg.edit(content=f"Verification completed. Success: {success}, Failed: {fail}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def stopverify(ctx):
    global verify_running
    if not verify_running:
        await ctx.send("Verification process is not running")
        return
    verify_running = False
    await ctx.send("Verification process stopped")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def join(ctx):
    voice_channel = ctx.guild.get_channel(1513692263010799716)
    if not voice_channel:
        await ctx.send("Voice channel not found")
        return
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await voice_channel.connect()
    await ctx.send("Connected to voice channel")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def unjoin(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left voice channel")
    else:
        await ctx.send("Not in a voice channel")

@bot.command()
async def invite(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Join Discord", url=INVITE_LINK))
    await ctx.send("Join to our discord!", view=view)

@bot.command()
async def saysomething(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    channel = bot.get_channel(1513695339167617084)
    if channel:
        await channel.send(message)

@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except:
        pass
    
    await ctx.send(message)

@bot.command()
async def typeinchannel(ctx):
    global banned_count
    channel = bot.get_channel(1518832499122507786)
    if channel:
        embed = discord.Embed(
            description="⚠️ DON'T SEND ANY MESSAGES IN THIS CHANNEL ⚠️\n\n⚠️ This channel only used to catch spam bots and hacked accounts, don't send anything in this channel or you will be immediately banned from HollyScriptX ⚠️\n\nBanned users: " + str(banned_count),
            color=discord.Color.from_rgb(255, 255, 255)
        )
        await channel.send(embed=embed)
        await ctx.send("Message sent to the channel!", delete_after=3)

@bot.command()
async def sendverifyshit(ctx):
    global verify_message_id, verify_channel_id
    try:
        await ctx.message.delete()
    except:
        pass
    
    channel = bot.get_channel(VERIFY_MESSAGE_CHANNEL_ID)
    if not channel:
        await ctx.send("Verify channel not found!", delete_after=3)
        return
    
    embed = discord.Embed(
        description="HollyScriptX\nClick the button below to verify",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    
    message = await channel.send(embed=embed)
    await message.add_reaction("✅")
    
    verify_message_id = message.id
    verify_channel_id = channel.id
    
    await ctx.send("Verification message sent!", delete_after=3)

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def setstatus(ctx, status: str = None, *, game: str = None):
    if status is None:
        await ctx.send("Usage: .setstatus (online/idle/dnd/invisible) [game]")
        return
    
    status_map = {
        "online": discord.Status.online,
        "idle": discord.Status.idle,
        "dnd": discord.Status.dnd,
        "invisible": discord.Status.invisible
    }
    
    if status.lower() not in status_map:
        await ctx.send("Invalid status. Use: online, idle, dnd, invisible")
        return
    
    activity = None
    if game:
        activity = discord.Game(name=game)
    
    await bot.change_presence(status=status_map[status.lower()], activity=activity)
    await ctx.send(f"Status changed to: {status}")

if __name__ == "__main__":
    if TOKEN is None:
        print("ERROR: DISCORD_TOKEN environment variable is not set!")
    else:
        bot.run(TOKEN)
