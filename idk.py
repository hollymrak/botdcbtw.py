import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
import random
import string

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = 1504482964661076098
ADMIN_ROLE_ID = 1516094850628587630
INVITE_LINK = "https://discord.gg/njxxTuMH"
VERIFY_ROLE_ID = 1508785745547235388
VERIFIED_ROLE_ID = 1504503685328146585
VERIFY_MESSAGE_CHANNEL_ID = 1513696689536372736
VERIFY_LOG_CHANNEL_ID = 1513733733184831558
JAIL_ROLE_ID = 1512734205971398676

intents = discord.Intents.all()
bot = commands.Bot(command_prefix='.', intents=intents)

hardbanned_users = set()
warnings = defaultdict(list)
user_messages = defaultdict(list)
user_warnings = defaultdict(int)
user_message_times = defaultdict(list)
verify_running = False
banned_count = 0
verify_message_id = None
verify_channel_id = None
user_roles_backup = {}

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
    'dev': 1504502883872411800
}

CHANNELS_TO_LOCK = [1513695339167617084, 1513695434026254438, 1514945294964359329]
VOICE_CHANNELS_TO_LOCK = [1513692263010799716, 1513692362931703818, 1513692441281036348, 1513692510306963476, 1513692585682669618]
STAFF_ROLES = [1508782838600830996, 1504503460740202567, 1508793047230709932, 1504503217382232166, 1504502978374139977, 1508790828448092211, 1516192523691884816]

def generate_warn_code():
    return '#' + ''.join(random.choices(string.digits, k=4))

@bot.event
async def on_ready():
    global banned_count, verify_message_id, verify_channel_id
    print(f'Bot {bot.user} is online')
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="discord.gg/hsx"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    if message.guild is None or message.guild.id != SERVER_ID:
        await bot.process_commands(message)
        return
    if message.channel.id == 1518832499122507786:
        await auto_ban(message)
        await bot.process_commands(message)
        return
    if "key" in message.content.lower():
        await message.reply("HSX-7562-3194-0835-4981-2470-1488-1029-6967")
        await bot.process_commands(message)
        return
    await check_violations(message)
    if "zalupa" in message.content.lower():
        await message.reply("**hi!**")
    await bot.process_commands(message)

@bot.event
async def on_member_join(member):
    if member.id in MONITORED_USERS:
        for role_id in MONITORED_USERS[member.id]:
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
    if payload.user_id == bot.user.id or payload.message_id != verify_message_id or str(payload.emoji) != "✅":
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

async def warn_user(message, reason, moderator=None):
    warn_code = generate_warn_code()
    user_warnings[message.author.id] += 1
    warn_count = user_warnings[message.author.id]
    if message.author.id not in warnings:
        warnings[message.author.id] = []
    warnings[message.author.id].append({
        'code': warn_code,
        'reason': reason,
        'moderator': moderator or "Auto-Mod",
        'date': datetime.now().strftime('%m/%d/%Y %I:%M %p')
    })
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
        await message.author.send(embed=embed)
    except:
        pass
    embed_channel = discord.Embed(
        description=f"{message.author.mention} has been warned for {reason} #{warn_count}/5\nCode: {warn_code}",
        color=discord.Color.from_rgb(255, 180, 50)
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

async def check_violations(message):
    user_id = message.author.id
    current_time = time.time()
    content = message.content
    user_message_times[user_id] = [t for t in user_message_times[user_id] if current_time - t < 5]
    user_message_times[user_id].append(current_time)
    if len(user_message_times[user_id]) >= 5:
        await warn_user(message, "spamming (5 messages in 5 seconds)")
        user_message_times[user_id] = []
        return
    if len(content) > 5:
        caps_count = sum(1 for c in content if c.isupper())
        caps_percent = caps_count / len(content) * 100 if len(content) > 0 else 0
        if caps_percent > 70 and len(content) > 10:
            await warn_user(message, "caps spam")
            return
    if message.attachments:
        user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 3]
        user_messages[user_id].append(current_time)
        if len(user_messages[user_id]) >= 3:
            await warn_user(message, "spamming images/files")
            user_messages[user_id] = []
            return

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
        await ctx.send("Command not found!")
    else:
        raise error

# ===================== КОМАНДЫ =====================

@bot.command()
@commands.has_role(1504503460740202567)
async def warn(ctx, member: discord.Member = None, *, args=None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        embed = discord.Embed(
            description="Usage\n.warn <@Member | ID> [duration] [reason]\n┗ Member parameter may be replaced with the author of the replied message.\n\nExample 1\n.warn @Member\n┗ Gives empty warning.\n\nExample 2\n.warn @Member behaves provocatively\n┗ Gives warning with specified reason.\n\nExample 3\n.warn @Member 1d behaves provocatively\n┗ Gives warning with reason expiring in one day.",
            color=discord.Color.from_rgb(255, 255, 255)
        )
        await ctx.send(embed=embed)
        return
    reason = args or "No reason provided"
    await warn_user(member, reason, ctx.author.mention)

@bot.command()
@commands.has_role(1504503460740202567)
async def warn_remove(ctx, member: discord.Member = None, code: str = None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None or code is None:
        await ctx.send("Usage: .warn-remove @user #1234")
        return
    if member.id not in warnings or not warnings[member.id]:
        await ctx.send(f"{member.mention} has no warnings.")
        return
    removed = False
    for warn in warnings[member.id]:
        if warn['code'] == code:
            warnings[member.id].remove(warn)
            user_warnings[member.id] -= 1
            removed = True
            embed = discord.Embed(
                description=f"Removed warning {code} from {member.mention}",
                color=discord.Color.from_rgb(100, 220, 100)
            )
            await ctx.send(embed=embed)
            break
    if not removed:
        await ctx.send(f"Warning {code} not found for {member.mention}")

@bot.command()
@commands.has_role(1504503460740202567)
async def warns_list(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .warns-list @user")
        return
    if member.id not in warnings or not warnings[member.id]:
        await ctx.send(f"{member.mention} has no warnings.")
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
async def mute(ctx, member: discord.Member = None, *, reason="No Reason Provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: .mute (@user) (reason) or reply to a message with .mute")
        return
    try:
        timeout = discord.utils.utcnow() + timedelta(hours=24)
        await member.timeout(timeout, reason=reason)
        embed = discord.Embed(
            title="Muted",
            description=f"You have been **muted** in\n**HollyScriptX**",
            color=discord.Color.from_rgb(255, 180, 50)
        )
        embed.add_field(name="Moderator", value=ctx.author.mention, inline=False)
        embed.add_field(name="Reason", value=reason, inline=False)
        embed.add_field(name="Duration", value="24 hours", inline=False)
        embed.set_footer(text=f"{datetime.now().strftime('%m/%d/%Y %I:%M %p')}")
        try:
            await member.send(embed=embed)
        except:
            pass
        await ctx.send(f"User {member.mention} has been muted. Reason: {reason}")
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
async def showstafflist(ctx):
    guild = ctx.guild
    staff_members = {}
    for role_id in STAFF_ROLES:
        role = guild.get_role(role_id)
        if role:
            members = [member for member in guild.members if role in member.roles]
            staff_members[role.name] = members
    embed = discord.Embed(title="Staff List", color=discord.Color.from_rgb(255, 255, 255))
    for role_name, members in staff_members.items():
        embed.add_field(
            name=role_name,
            value="\n".join([f"{member.mention}" for member in members]) or "None",
            inline=False
        )
    await ctx.send(embed=embed)

@bot.command()
@commands.has_role(1504502978374139977)
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
        await ctx.send(f"Role {role_name} not found. Available roles: {available_roles}")
        return
    role_id = role_map[role_name_lower]
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send(f"Role not found on this server")
        return
    max_allowed = ['helper', 'support', 'mod', 'senior mod']
    if role_name_lower not in max_allowed:
        await ctx.send(f"You can only give roles up to **helper**")
        return
    try:
        await member.add_roles(role)
        await ctx.send(f"Added role {role.name} to {member.mention}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to give this role")
    except discord.HTTPException as e:
        await ctx.send(f"Error giving role: {e}")

@bot.command()
@commands.has_role(1504502978374139977)
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
        await ctx.send(f"Role {role_name} not found. Available roles: {available_roles}")
        return
    role_id = role_map[role_name_lower]
    role = ctx.guild.get_role(role_id)
    if not role:
        await ctx.send(f"Role not found on this server")
        return
    max_allowed = ['helper', 'support', 'mod', 'senior mod']
    if role_name_lower not in max_allowed:
        await ctx.send(f"You can only remove roles up to **helper**")
        return
    try:
        await member.remove_roles(role)
        await ctx.send(f"Removed role {role.name} from {member.mention}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to remove this role")
    except discord.HTTPException as e:
        await ctx.send(f"Error removing role: {e}")

@bot.command()
async def moderatorshelp(ctx):
    embed = discord.Embed(
        description="""# read this!! important for this discord server Staff.

this channel is maded to show your Permissions. ( USING OTHER BOTS FOR STAFF COMMANDS NOT ALLOWED )

<@&1516192523691884816> Role Permissions:
- You can fully control server even without using this bot.

<@&1508790828448092211> Role Permissions:
- Access to commands from the roles below

<@&1504502978374139977> Role Permissions:
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
- Access to .warn-remove
- Access to .warns-list
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
    embed = discord.Embed(
        title="Bot Commands",
        description="Commands require the admin role to use",
        color=discord.Color.from_rgb(255, 255, 255)
    )
    embed.add_field(name=".clear (amount)", value="Delete messages in the channel (max 1000)", inline=False)
    embed.add_field(name=".ban (@user) (reason)", value="Ban a user permanently", inline=False)
    embed.add_field(name=".unban (user)", value="Unban a user", inline=False)
    embed.add_field(name=".mute (@user) (reason)", value="Mute a user for 24 hours", inline=False)
    embed.add_field(name=".unmute (@user)", value="Unmute a user", inline=False)
    embed.add_field(name=".warn (@user) (reason)", value="Give a warning to a user", inline=False)
    embed.add_field(name=".warn-remove (@user) (code)", value="Remove a warning from user", inline=False)
    embed.add_field(name=".warns-list (@user)", value="Show all warnings of a user", inline=False)
    embed.add_field(name=".hardban (@user) (reason)", value="Hard ban a user (remove all channel access)", inline=False)
    embed.add_field(name=".unhardban (user)", value="Remove hard ban from a user", inline=False)
    embed.add_field(name=".jail (@user) (reason)", value="Jail a user", inline=False)
    embed.add_field(name=".unjail (@user)", value="Unjail a user", inline=False)
    embed.add_field(name=".kick (@user) (reason)", value="Kick a user", inline=False)
    embed.add_field(name=".join", value="Connect bot to voice channel", inline=False)
    embed.add_field(name=".unjoin", value="Disconnect bot from voice channel", inline=False)
    embed.add_field(name=".lockchats", value="Lock all specified channels", inline=False)
    embed.add_field(name=".unlockchats", value="Unlock all specified channels", inline=False)
    embed.add_field(name=".verifyall", value="Verifies all people with unverified role", inline=False)
    embed.add_field(name=".stopverify", value="Stop verification process", inline=False)
    embed.add_field(name=".giverole (role_name)", value="Give a role to replied user", inline=False)
    embed.add_field(name=".delrole (role_name)", value="Remove a role from replied user", inline=False)
    embed.add_field(name=".down (InkGame / MurderMystery2 / Doors)", value="Mark selected script as down.", inline=False)
    embed.add_field(name=".down ALL", value="Mark all scripts as down.", inline=False)
    embed.add_field(name=".undetected (InkGame / MurderMystery2 / Doors)", value="Mark selected script as undetected.", inline=False)
    embed.add_field(name=".undetected ALL", value="Mark all scripts as undetected.", inline=False)
    embed.add_field(name=".showstafflist", value="Show all staff members", inline=False)
    embed.add_field(name=".moderatorshelp", value="Show staff permissions", inline=False)
    embed.add_field(name=".invite", value="Send invite to Discord server", inline=False)
    embed.add_field(name=".help_commands", value="Show this help message", inline=False)
    await ctx.send(embed=embed)

# ============ АДМИН КОМАНДЫ ============

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def clear(ctx, amount: int):
    if amount <= 0 or amount > 1000:
        await ctx.send("Please specify a positive number (max 1000)")
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
    if not old_role or not new_role:
        await ctx.send("Role not found")
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
async def saysomething(ctx):
    try:
        await ctx.message.delete()
    except:
        pass
    channel = bot.get_channel(1513695339167617084)
    if channel:
        await channel.send("I'm here again ✌️")

@bot.command()
async def say(ctx, *, message: str):
    try:
        await ctx.message.delete()
    except:
        pass
    channel = bot.get_channel(1513695339167617084)
    if channel:
        await channel.send(message)

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

if __name__ == "__main__":
    if TOKEN is None:
        print("ERROR: DISCORD_TOKEN environment variable is not set!")
    else:
        bot.run(TOKEN)
