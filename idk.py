import discord
from discord.ext import commands
import asyncio
import aiohttp
from datetime import timedelta, datetime
import re
from collections import defaultdict
import time

TOKEN = "MTUxOTgwOTU2MDM3NzAzNjkyMQ.GOd4mX.VNTTHG3MhBuF-PDZFYy4j2lHiY6KQ9L7W-ZumU"
SERVER_ID = 1504482964661076098
VOICE_CHANNEL_ID = 1513692263010799716
OLD_ROLE_ID = 1508785745547235388
NEW_ROLE_ID = 1504503685328146585
ADMIN_ROLE_ID = 1516094850628587630
INVITE_LINK = "https://discord.gg/njxxTuMH"
AVATAR_URL = "https://cdn.discordapp.com/attachments/1472794232329605141/1520192243250495518/hsxalwaysbest.png"

BAN_CHANNEL_ID = 1518832499122507786
LOG_CHANNEL_ID = 1518832499122507786
SPAM_CHANNEL_ID = 1513695339167617084
STARTUP_CHANNEL_ID = 1504482964661076098

CHANNELS_TO_LOCK = [
    1513695339167617084,
    1513695434026254438,
    1514945294964359329
]

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=',', intents=intents)

verify_running = False
warnings = {}
user_messages = defaultdict(list)
user_warnings = defaultdict(int)
user_word_spam = defaultdict(list)
spam_cooldown = defaultdict(float)
last_startup_message = None

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
    'dev': 1504502883872411800
}

class DiscordInviteView(discord.ui.View):
    def __init__(self):
        super().__init__(timeout=None)
        button = discord.ui.Button(label="Join Discord", url=INVITE_LINK)
        self.add_item(button)

def has_admin_role():
    async def predicate(ctx):
        if ctx.guild is None:
            return False
        role = ctx.guild.get_role(ADMIN_ROLE_ID)
        if role is None:
            return False
        return role in ctx.author.roles
    return commands.check(predicate)

@bot.event
async def on_ready():
    global last_startup_message
    print(f'Bot {bot.user} is online')
    
    activity = discord.Game(name="HollyScriptX")
    await bot.change_presence(activity=activity)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(AVATAR_URL) as resp:
                if resp.status == 200:
                    image_data = await resp.read()
                    await bot.user.edit(avatar=image_data)
                    print('Avatar updated')
    except Exception as e:
        print(f'Avatar error: {e}')
    
    guild = bot.get_guild(SERVER_ID)
    if guild:
        print(f'On server: {guild.name}')
        
        try:
            await guild.me.edit(nick="Negrito faggoto")
            print('Nickname changed to Negrito faggoto')
        except Exception as e:
            print(f'Nickname change error: {e}')
        
        try:
            startup_channel = guild.get_channel(STARTUP_CHANNEL_ID)
            if startup_channel:
                last_startup_message = datetime.now()
                await startup_channel.send("I'm here again ✌️")
                print('Startup message sent')
        except Exception as e:
            print(f'Startup message error: {e}')
    
    bot.loop.create_task(daily_startup_message())
    bot.loop.create_task(voice_activity_loop())

async def daily_startup_message():
    global last_startup_message
    await bot.wait_until_ready()
    while True:
        try:
            if last_startup_message is None or (datetime.now() - last_startup_message).total_seconds() >= 86400:
                guild = bot.get_guild(SERVER_ID)
                if guild:
                    channel = guild.get_channel(STARTUP_CHANNEL_ID)
                    if channel:
                        await channel.send("I'm here again ✌️")
                        last_startup_message = datetime.now()
                        print('Daily startup message sent')
            await asyncio.sleep(3600)
        except Exception as e:
            print(f'Daily startup message error: {e}')
            await asyncio.sleep(3600)

async def voice_activity_loop():
    await bot.wait_until_ready()
    statuses = ["Join to our discord", "HollyScriptX", "Maked by @t3e6"]
    index = 0
    
    while True:
        try:
            guild = bot.get_guild(SERVER_ID)
            if guild:
                channel = guild.get_channel(VOICE_CHANNEL_ID)
                if channel:
                    connected = False
                    for vc in bot.voice_clients:
                        if vc.guild.id == SERVER_ID and vc.is_connected():
                            connected = True
                            break
                    
                    if not connected:
                        try:
                            await channel.connect()
                            print('CONNECTED TO VOICE')
                        except Exception as e:
                            print(f'CONNECT ERROR: {e}')
                
                if bot.voice_clients:
                    status = statuses[index % len(statuses)]
                    await bot.change_presence(activity=discord.Game(name=status))
                    index += 1
            
            await asyncio.sleep(10)
            
        except Exception as e:
            print(f'Voice loop error: {e}')
            await asyncio.sleep(5)

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    
    if message.guild and message.guild.id == SERVER_ID:
        if bot.user in message.mentions:
            await message.reply("u fucking piece of shit can you fucking shut the fuck up okay ✌️")
            return
        
        if message.channel.id == BAN_CHANNEL_ID:
            await auto_ban(message)
            return
        
        user_id = message.author.id
        current_time = time.time()
        content_lower = message.content.lower()
        
        user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 5]
        user_messages[user_id].append(current_time)
        
        user_word_spam[user_id] = [(word, t) for word, t in user_word_spam[user_id] if current_time - t < 5]
        
        words = re.findall(r'\b\w+\b', content_lower)
        for word in words:
            if len(word) > 2:
                user_word_spam[user_id].append((word, current_time))
        
        word_counts = defaultdict(int)
        for word, _ in user_word_spam[user_id]:
            word_counts[word] += 1
        
        is_word_spam = any(count >= 3 for count in word_counts.values())
        
        last_messages = []
        async for msg in message.channel.history(limit=10):
            if msg.author.id == user_id:
                last_messages.append(msg.content.lower())
        
        is_repeat_spam = False
        if len(last_messages) >= 3:
            if all(msg == last_messages[0] for msg in last_messages[:3]):
                is_repeat_spam = True
        
        is_character_spam = False
        if len(message.content) > 10:
            unique_chars = len(set(message.content))
            if unique_chars <= 3:
                is_character_spam = True
        
        has_mentions = len(message.mentions) > 3 or len(message.role_mentions) > 2
        
        caps_count = sum(1 for c in message.content if c.isupper())
        caps_percent = caps_count / len(message.content) * 100 if len(message.content) > 0 else 0
        is_caps_spam = caps_percent > 70 and len(message.content) > 10
        
        is_long_message = len(message.content) > 500
        
        if len(user_messages[user_id]) >= 3 or is_repeat_spam or is_character_spam or has_mentions or is_caps_spam or is_long_message or is_word_spam:
            user_warnings[user_id] += 1
            
            mute_duration = 60
            if user_warnings[user_id] >= 5:
                mute_duration = 3600
            elif user_warnings[user_id] >= 3:
                mute_duration = 600
            elif user_warnings[user_id] >= 2:
                mute_duration = 300
            
            try:
                timeout = discord.utils.utcnow() + timedelta(seconds=mute_duration)
                await message.author.timeout(timeout, reason=f"Spamming (Warning #{user_warnings[user_id]})")
                
                spam_channel = bot.get_channel(SPAM_CHANNEL_ID)
                if spam_channel:
                    embed = discord.Embed(
                        description=f"{message.author.mention} Has been timed-out for spamming.",
                        color=discord.Color.from_rgb(180, 60, 60)
                    )
                    embed.add_field(name="Duration", value=f"{mute_duration} seconds", inline=True)
                    embed.add_field(name="Warning Count", value=f"{user_warnings[user_id]}", inline=True)
                    
                    if is_word_spam:
                        spam_words = [word for word, count in word_counts.items() if count >= 3]
                        embed.add_field(name="Reason", value=f"Spamming words: {', '.join(spam_words[:3])}", inline=False)
                    elif is_repeat_spam:
                        embed.add_field(name="Reason", value="Repeating same message", inline=False)
                    elif is_character_spam:
                        embed.add_field(name="Reason", value="Spamming characters", inline=False)
                    elif has_mentions:
                        embed.add_field(name="Reason", value="Mass mentions", inline=False)
                    elif is_caps_spam:
                        embed.add_field(name="Reason", value="Caps spam", inline=False)
                    elif is_long_message:
                        embed.add_field(name="Reason", value="Extremely long message", inline=False)
                    elif len(user_messages[user_id]) >= 3:
                        embed.add_field(name="Reason", value="Too many messages", inline=False)
                    
                    await spam_channel.send(embed=embed)
                
                user_messages[user_id] = []
                user_word_spam[user_id] = []
                
                if user_warnings[user_id] >= 5:
                    try:
                        await message.author.ban(reason="Repeated spamming (5+ warnings)")
                        embed = discord.Embed(
                            description=f"{message.author.mention} has been permanently **banned** for repeated spamming.",
                            color=discord.Color.from_rgb(180, 60, 60)
                        )
                        await spam_channel.send(embed=embed)
                        user_warnings[user_id] = 0
                    except:
                        pass
                
                return
            except Exception as e:
                print(f'Spam timeout error: {e}')
        
        if len(user_messages[user_id]) >= 6:
            try:
                timeout = discord.utils.utcnow() + timedelta(seconds=300)
                await message.author.timeout(timeout, reason="Flood spam")
                
                spam_channel = bot.get_channel(SPAM_CHANNEL_ID)
                if spam_channel:
                    embed = discord.Embed(
                        description=f"{message.author.mention} Has been timed-out for flood spamming.",
                        color=discord.Color.from_rgb(180, 60, 60)
                    )
                    await spam_channel.send(embed=embed)
                
                user_messages[user_id] = []
                user_word_spam[user_id] = []
                return
            except:
                pass
        
        xeno_patterns = [
            r'x[e3]n[o0]',
            r'x[e3]no',
            r'x[e3]n[o0]',
            r'x[e3]n0',
            r'x[e3]н[o0]',
            r'x[e3]нo',
            r'x[e3]н0',
            r'x[e3]nо',
            r'x[e3]n[o0]',
            r'x[e3]no',
            r'x[e3]n0',
            r'x[e3]н[o0]',
            r'x[e3]нo',
            r'x[e3]н0',
        ]
        
        is_xeno = False
        for pattern in xeno_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                is_xeno = True
                break
        
        if is_xeno:
            await message.delete()
            await message.reply("Fuck you script doesn't support xeno and delete this rat")
            return
        
        nigger_patterns = [
            r'n[i1]gg[e3]r',
            r'n[i1]gg[a4]',
            r'n[i1]g[a4]',
            r'n[e3]g[r0]',
            r'n[i1]gg[e3]r',
            r'n[i1]gg[a4]',
            r'n[i1]g[a4]',
            r'n[e3]g[r0]',
        ]
        
        is_nigger = False
        for pattern in nigger_patterns:
            if re.search(pattern, content_lower, re.IGNORECASE):
                is_nigger = True
                break
        
        if is_nigger:
            await message.delete()
            await message.reply("Bad words detected")
            return
        
        if "zalupa" in message.content.lower():
            await message.reply("**hi!**")
    
    await bot.process_commands(message)

async def auto_ban(message):
    try:
        member = message.author
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(
                description=f"{member.mention} has been permanently **banned** from **HollyScriptX**\nReason: **Scammed Accounts detection 1.0**\nTyped Message:\n{message.content}",
                color=discord.Color.from_rgb(180, 60, 60)
            )
            await log_channel.send(embed=embed)
        
        try:
            embed = discord.Embed(
                description=f"You have been permanently **banned** from **HollyScriptX**\nReason: Auto-ban. Typed in do not type channel (prob hacked account).\n\nYou still can get unbanned, type to @t3e6 on discord and explain what happened.",
                color=discord.Color.from_rgb(180, 60, 60)
            )
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
        await ctx.send("Command not found!")
    else:
        raise error

@bot.command()
@has_admin_role()
async def clear(ctx, amount: int):
    if amount <= 0:
        await ctx.send("Please specify a positive number")
        return
    if amount > 100:
        await ctx.send("Cannot delete more than 100 messages at once")
        return
    deleted = await ctx.channel.purge(limit=amount + 1)
    msg = await ctx.send(f"Deleted {len(deleted) - 1} messages")
    await msg.delete(delay=3)

@clear.error
async def clear_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: ,clear (amount)")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("Please specify a number")

@bot.command()
@has_admin_role()
async def ban(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None:
        if ctx.message.reference:
            try:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = referenced_msg.author
            except:
                await ctx.send("Could not find the user")
                return
        else:
            await ctx.send("Usage: ,ban (@user) (reason) or reply to a message with ,ban")
            return
    
    try:
        await member.ban(reason=reason)
        try:
            embed = discord.Embed(
                description=f"You have been **permanently banned** from **HollyScriptX**\nBanned By: {ctx.author.mention}\nReason: **{reason}**",
                color=discord.Color.from_rgb(180, 60, 60)
            )
            await member.send(embed=embed)
        except:
            pass
        await ctx.send(f"User {member.mention} has been banned. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error banning user: {e}")

@ban.error
async def ban_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: ,ban (@user) (reason) or reply to a message with ,ban")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("User not found")

@bot.command()
@has_admin_role()
async def mute(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None:
        if ctx.message.reference:
            try:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = referenced_msg.author
            except:
                await ctx.send("Could not find the user")
                return
        else:
            await ctx.send("Usage: ,mute (@user) (reason) or reply to a message with ,mute")
            return
    
    try:
        timeout = discord.utils.utcnow() + timedelta(hours=24)
        await member.timeout(timeout, reason=reason)
        
        try:
            embed = discord.Embed(
                description=f"You have been **muted** in **HollyScriptX**\nMuted By: {ctx.author.mention}\nReason: **{reason}**\nDuration: 24 hours",
                color=discord.Color.from_rgb(200, 150, 50)
            )
            await member.send(embed=embed)
        except:
            pass
        
        await ctx.send(f"User {member.mention} has been muted. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to mute this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error muting user: {e}")

@mute.error
async def mute_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: ,mute (@user) (reason) or reply to a message with ,mute")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("User not found")

@bot.command()
@has_admin_role()
async def warn(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None:
        if ctx.message.reference:
            try:
                referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
                member = referenced_msg.author
            except:
                await ctx.send("Could not find the user")
                return
        else:
            await ctx.send("Usage: ,warn (@user) (reason) or reply to a message with ,warn")
            return
    
    if member.id not in warnings:
        warnings[member.id] = []
    
    warnings[member.id].append(reason)
    warn_count = len(warnings[member.id])
    
    try:
        embed = discord.Embed(
            description=f"You have received a warning in **HollyScriptX**\nWarned By: {ctx.author.mention}\nReason: **{reason}**\nTotal Warnings: {warn_count}",
            color=discord.Color.from_rgb(200, 180, 50)
        )
        await member.send(embed=embed)
    except:
        pass
    
    await ctx.send(f"User {member.mention} has been warned. Reason: {reason}. Total warnings: {warn_count}")
    
    if warn_count >= 3:
        await auto_ban_3_warns(member)

async def auto_ban_3_warns(member):
    try:
        log_channel = bot.get_channel(LOG_CHANNEL_ID)
        
        if log_channel:
            embed = discord.Embed(
                description=f"{member.mention} have been permanently banned because received 3 warns",
                color=discord.Color.from_rgb(180, 60, 60)
            )
            await log_channel.send(embed=embed)
        
        try:
            embed = discord.Embed(
                description=f"You have been permanently banned from **HollyScriptX**\nReason: lil stupid nigga got 3 warns lmaoo",
                color=discord.Color.from_rgb(180, 60, 60)
            )
            await member.send(embed=embed)
        except:
            pass
        
        await member.ban(reason="lil stupid nigga got 3 warns lmaoo")
        
    except Exception as e:
        print(f'Auto ban 3 warns error: {e}')

@warn.error
async def warn_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: ,warn (@user) (reason) or reply to a message with ,warn")
    elif isinstance(error, commands.BadArgument):
        await ctx.send("User not found")

@bot.command()
@has_admin_role()
async def lockchats(ctx):
    for channel_id in CHANNELS_TO_LOCK:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = False
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                await ctx.send(f"Locked {channel.mention}")
            except Exception as e:
                await ctx.send(f"Error locking {channel.mention}: {e}")
        else:
            await ctx.send(f"Channel {channel_id} not found")
    
    await ctx.send("All specified channels have been locked")

@bot.command()
@has_admin_role()
async def unlockchats(ctx):
    for channel_id in CHANNELS_TO_LOCK:
        channel = ctx.guild.get_channel(channel_id)
        if channel:
            try:
                overwrite = channel.overwrites_for(ctx.guild.default_role)
                overwrite.send_messages = None
                await channel.set_permissions(ctx.guild.default_role, overwrite=overwrite)
                await ctx.send(f"Unlocked {channel.mention}")
            except Exception as e:
                await ctx.send(f"Error unlocking {channel.mention}: {e}")
        else:
            await ctx.send(f"Channel {channel_id} not found")
    
    await ctx.send("All specified channels have been unlocked")

@bot.command()
@has_admin_role()
async def verifyall(ctx):
    global verify_running
    
    if verify_running:
        await ctx.send("Verification process is already running")
        return
    
    guild = ctx.guild
    old_role = guild.get_role(OLD_ROLE_ID)
    new_role = guild.get_role(NEW_ROLE_ID)
    
    if not old_role:
        await ctx.send(f"Role with ID {OLD_ROLE_ID} not found")
        return
    if not new_role:
        await ctx.send(f"Role with ID {NEW_ROLE_ID} not found")
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

@verifyall.error
async def verifyall_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")

@bot.command()
@has_admin_role()
async def stopverify(ctx):
    global verify_running
    if not verify_running:
        await ctx.send("Verification process is not running")
        return
    verify_running = False
    await ctx.send("Verification process stopped")

@bot.command()
@has_admin_role()
async def join(ctx):
    voice_channel = ctx.guild.get_channel(VOICE_CHANNEL_ID)
    if not voice_channel:
        await ctx.send(f"Voice channel with ID {VOICE_CHANNEL_ID} not found")
        return
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
    await voice_channel.connect()
    await ctx.send(f"Connected to {voice_channel.name}")

@bot.command()
@has_admin_role()
async def leave(ctx):
    if ctx.voice_client:
        await ctx.voice_client.disconnect()
        await ctx.send("Left voice channel")
    else:
        await ctx.send("Not in a voice channel")

@bot.command()
@has_admin_role()
async def giverole(ctx, role_name: str):
    if not ctx.message.reference:
        await ctx.send("You must reply to a message to give a role")
        return
    
    try:
        referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced_msg.author
    except:
        await ctx.send("Could not find the user")
        return
    
    role_name_lower = role_name.lower()
    if role_name_lower not in role_map:
        available_roles = ', '.join(role_map.keys())
        await ctx.send(f"Role '{role_name}' not found. Available roles: {available_roles}")
        return
    
    role_id = role_map[role_name_lower]
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send(f"Role not found on this server")
        return
    
    try:
        await member.add_roles(role)
        await ctx.send(f"Added role '{role.name}' to {member.mention}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to give this role")
    except discord.HTTPException as e:
        await ctx.send(f"Error giving role: {e}")

@giverole.error
async def giverole_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: Reply to a message with ,giverole (role_name)")

@bot.command()
@has_admin_role()
async def delrole(ctx, role_name: str):
    if not ctx.message.reference:
        await ctx.send("You must reply to a message to remove a role")
        return
    
    try:
        referenced_msg = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced_msg.author
    except:
        await ctx.send("Could not find the user")
        return
    
    role_name_lower = role_name.lower()
    if role_name_lower not in role_map:
        available_roles = ', '.join(role_map.keys())
        await ctx.send(f"Role '{role_name}' not found. Available roles: {available_roles}")
        return
    
    role_id = role_map[role_name_lower]
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send(f"Role not found on this server")
        return
    
    if role not in member.roles:
        await ctx.send(f"{member.mention} does not have the '{role.name}' role")
        return
    
    try:
        await member.remove_roles(role)
        await ctx.send(f"Removed role '{role.name}' from {member.mention}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to remove this role")
    except discord.HTTPException as e:
        await ctx.send(f"Error removing role: {e}")

@delrole.error
async def delrole_error(ctx, error):
    if isinstance(error, commands.CheckFailure):
        await ctx.send("You do not have permission to use this command")
    elif isinstance(error, commands.MissingRequiredArgument):
        await ctx.send("Usage: Reply to a message with ,delrole (role_name)")

@bot.command()
async def invite(ctx):
    view = DiscordInviteView()
    await ctx.send("Join to our discord!", view=view)

@bot.command()
async def help_commands(ctx):
    embed = discord.Embed(
        title="Bot Commands",
        description="Commands require the admin role to use",
        color=discord.Color.blue()
    )
    embed.add_field(name=",clear (amount)", value="Delete messages in the channel (max 100)", inline=False)
    embed.add_field(name=",ban (@user) (reason)", value="Ban a user permanently", inline=False)
    embed.add_field(name=",mute (@user) (reason)", value="Mute a user for 24 hours", inline=False)
    embed.add_field(name=",warn (@user) (reason)", value="Give a warning to a user", inline=False)
    embed.add_field(name=",lockchats", value="Lock all specified channels", inline=False)
    embed.add_field(name=",unlockchats", value="Unlock all specified channels", inline=False)
    embed.add_field(name=",verifyall", value="Verifies all people with unverified role", inline=False)
    embed.add_field(name=",stopverify", value="Stop verification process", inline=False)
    embed.add_field(name=",join", value="Connect bot to ink game voice channel", inline=False)
    embed.add_field(name=",leave", value="Disconnect bot from voice channel", inline=False)
    embed.add_field(name=",giverole (role_name)", value="Give a role to replied user", inline=False)
    embed.add_field(name=",delrole (role_name)", value="Remove a role from replied user", inline=False)
    embed.add_field(name=",invite", value="Send invite to Discord server", inline=False)
    embed.add_field(name=",help_commands", value="Show this help message", inline=False)
    
    available_roles = ', '.join(role_map.keys())
    embed.add_field(name="Available Roles", value=available_roles, inline=False)
    embed.set_footer(text=f"Admin Role ID: {ADMIN_ROLE_ID}")
    
    await ctx.send(embed=embed)

bot.run(TOKEN)
