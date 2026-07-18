import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time
import asyncio
import random

TOKEN = os.getenv("DISCORD_TOKEN")
SERVER_ID = 1504482964661076098
ADMIN_ROLE_ID = 1516094850628587630
INVITE_LINK = "https://discord.gg/njxxTuMH"

intents = discord.Intents.all()
bot = commands.Bot(command_prefix=',', intents=intents)

hardbanned_users = set()
warnings = defaultdict(list)
user_messages = defaultdict(list)
user_warnings = defaultdict(int)
verify_running = False
banned_count = 0

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

CHANNELS_TO_LOCK = [
    1513695339167617084,
    1513695434026254438,
    1514945294964359329
]

GREETINGS = [
    "Hello! How can I help you today?",
    "Hey there! What's up?",
    "Hi! Nice to see you!",
    "Greetings! How's it going?",
    "Hey! What can I do for you?",
    "Hello! Need any help?",
    "Hi there! How are you doing?",
    "Hey! I'm here for you!"
]

@bot.event
async def on_ready():
    global banned_count
    print(f'Bot {bot.user} is online')
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="HollyScriptX"))
    
    channel = bot.get_channel(1518832499122507786)
    if channel:
        try:
            async for message in channel.history(limit=None):
                if message.author == bot.user:
                    continue
                banned_count += 1
        except:
            pass

@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    
    if message.guild is None or message.guild.id != SERVER_ID:
        await bot.process_commands(message)
        return
    
    if bot.user in message.mentions:
        if len(message.content) > 3:
            await message.reply(random.choice(GREETINGS))
        else:
            await message.reply(random.choice(GREETINGS))
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
    
    await check_spam(message)
    
    if "zalupa" in message.content.lower():
        await message.reply("**hi!**")
    
    await bot.process_commands(message)

async def check_spam(message):
    user_id = message.author.id
    current_time = time.time()
    
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 2]
    user_messages[user_id].append(current_time)
    
    if len(user_messages[user_id]) >= 5:
        user_warnings[user_id] += 1
        warn_count = user_warnings[user_id]
        
        if user_id not in warnings:
            warnings[user_id] = []
        warnings[user_id].append("Spamming (5 messages in 2 seconds)")
        
        try:
            embed = discord.Embed(
                description=f"You have received a warning in **HollyScriptX**\nWarned By: Auto-Mod\nReason: **Spamming (5 messages in 2 seconds)**\nTotal Warnings: {warn_count}",
                color=discord.Color.from_rgb(255, 215, 0)
            )
            await message.author.send(embed=embed)
        except:
            pass
        
        if message.channel:
            embed = discord.Embed(
                description=f"{message.author.mention} has been warned for spamming! (5 messages in 2 seconds)",
                color=discord.Color.from_rgb(255, 215, 0)
            )
            await message.channel.send(embed=embed)
        
        user_messages[user_id] = []
        
        if warn_count >= 3:
            try:
                log_channel = bot.get_channel(1518832499122507786)
                if log_channel:
                    embed = discord.Embed(
                        description=f"{message.author.mention} have been permanently banned because received 3 warns",
                        color=discord.Color.from_rgb(220, 20, 20)
                    )
                    await log_channel.send(embed=embed)
                
                try:
                    embed = discord.Embed(
                        description=f"You have been permanently banned from **HollyScriptX**\nReason: lil stupid nigga got 3 warns lmaoo",
                        color=discord.Color.from_rgb(220, 20, 20)
                    )
                    await message.author.send(embed=embed)
                except:
                    pass
                
                await message.author.ban(reason="lil stupid nigga got 3 warns lmaoo")
                user_warnings[user_id] = 0
            except Exception as e:
                print(f'Auto ban 3 warns error: {e}')

async def auto_ban(message):
    global banned_count
    try:
        member = message.author
        banned_count += 1
        
        log_channel = bot.get_channel(1518832499122507786)
        if log_channel:
            embed = discord.Embed(
                description=f"{member.mention} has been permanently **banned** from **HollyScriptX**\nReason: **Scammed Accounts detection 1.0**\nTyped Message:\n{message.content}",
                color=discord.Color.from_rgb(220, 20, 20)
            )
            await log_channel.send(embed=embed)
        
        try:
            embed = discord.Embed(
                description=f"You have been permanently **banned** from **HollyScriptX**\nReason: Auto-ban. Typed in do not type channel (prob hacked account).\n\nYou still can get unbanned, type to @t3e6 on discord and explain what happened.",
                color=discord.Color.from_rgb(220, 20, 20)
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

@bot.event
async def on_member_join(member):
    if member.id in hardbanned_users:
        try:
            for channel in member.guild.channels:
                try:
                    await channel.set_permissions(member, view_channel=False, send_messages=False)
                except:
                    pass
        except:
            pass

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
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

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def ban(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: ,ban (@user) (reason) or reply to a message with ,ban")
        return
    
    try:
        await member.ban(reason=reason)
        try:
            embed = discord.Embed(
                description=f"You have been **permanently banned** from **HollyScriptX**\nBanned By: {ctx.author.mention}\nReason: **{reason}**",
                color=discord.Color.from_rgb(220, 20, 20)
            )
            await member.send(embed=embed)
        except:
            pass
        await ctx.send(f"User {member.mention} has been banned. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error banning user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
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
                await ctx.send("Usage: ,unban (user_id/username) or reply to a message with ,unban")
                return
    
    try:
        await ctx.guild.unban(user)
        embed = discord.Embed(
            description=f"{user.mention} **has been unbanned!**",
            color=discord.Color.from_rgb(50, 255, 50)
        )
        await ctx.send(embed=embed)
    except discord.NotFound:
        await ctx.send("User is not banned or not found")
    except discord.Forbidden:
        await ctx.send("I do not have permission to unban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unbanning user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def unmute(ctx, member: discord.Member = None):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: ,unmute (@user) or reply to a message with ,unmute")
        return
    
    try:
        await member.remove_timeout()
        embed = discord.Embed(
            description=f"{member.mention} **has been unmuted!**",
            color=discord.Color.from_rgb(50, 255, 50)
        )
        await ctx.send(embed=embed)
    except discord.Forbidden:
        await ctx.send("I do not have permission to unmute this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unmuting user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def hardban(ctx, member: discord.Member = None, *, reason = "Not specified"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: ,hardban (@user) (reason) or reply to a message with ,hardban")
        return
    
    try:
        hardbanned_users.add(member.id)
        
        for channel in ctx.guild.channels:
            try:
                await channel.set_permissions(member, view_channel=False, send_messages=False)
            except:
                pass
        
        try:
            embed = discord.Embed(
                description=f"You have been **hard-banned** from **HollyScriptX**\nBanned by: {ctx.author.mention}\nReason: **{reason}**",
                color=discord.Color.from_rgb(220, 20, 20)
            )
            await member.send(embed=embed)
        except:
            pass
        
        embed = discord.Embed(
            description=f"{member.mention} **has been hard-banned!**",
            color=discord.Color.from_rgb(220, 20, 20)
        )
        embed.add_field(name="Reason", value=reason, inline=False)
        await ctx.send(embed=embed)
        
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
                await ctx.send("Usage: ,unhardban (user_id/username) or reply to a message with ,unhardban")
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
            color=discord.Color.from_rgb(50, 255, 50)
        )
        await ctx.send(embed=embed)
        
    except discord.Forbidden:
        await ctx.send("I do not have permission to unhard-ban this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error unhard-banning user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def mute(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: ,mute (@user) (reason) or reply to a message with ,mute")
        return
    
    try:
        timeout = discord.utils.utcnow() + timedelta(hours=24)
        await member.timeout(timeout, reason=reason)
        
        try:
            embed = discord.Embed(
                description=f"You have been **muted** in **HollyScriptX**\nMuted By: {ctx.author.mention}\nReason: **{reason}**\nDuration: 24 hours",
                color=discord.Color.from_rgb(255, 165, 0)
            )
            await member.send(embed=embed)
        except:
            pass
        
        await ctx.send(f"User {member.mention} has been muted. Reason: {reason}")
    except discord.Forbidden:
        await ctx.send("I do not have permission to mute this user")
    except discord.HTTPException as e:
        await ctx.send(f"Error muting user: {e}")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
async def warn(ctx, member: discord.Member = None, *, reason = "No Reason Provided"):
    if member is None and ctx.message.reference:
        referenced = await ctx.channel.fetch_message(ctx.message.reference.message_id)
        member = referenced.author
    if member is None:
        await ctx.send("Usage: ,warn (@user) (reason) or reply to a message with ,warn")
        return
    
    if member.id not in warnings:
        warnings[member.id] = []
    
    warnings[member.id].append(reason)
    warn_count = len(warnings[member.id])
    
    try:
        embed = discord.Embed(
            description=f"You have received a warning in **HollyScriptX**\nWarned By: {ctx.author.mention}\nReason: **{reason}**\nTotal Warnings: {warn_count}",
            color=discord.Color.from_rgb(255, 215, 0)
        )
        await member.send(embed=embed)
    except:
        pass
    
    await ctx.send(f"User {member.mention} has been warned. Reason: {reason}. Total warnings: {warn_count}")
    
    if warn_count >= 3:
        try:
            log_channel = bot.get_channel(1518832499122507786)
            if log_channel:
                embed = discord.Embed(
                    description=f"{member.mention} have been permanently banned because received 3 warns",
                    color=discord.Color.from_rgb(220, 20, 20)
                )
                await log_channel.send(embed=embed)
            
            try:
                embed = discord.Embed(
                    description=f"You have been permanently banned from **HollyScriptX**\nReason: lil stupid nigga got 3 warns lmaoo",
                    color=discord.Color.from_rgb(220, 20, 20)
                )
                await member.send(embed=embed)
            except:
                pass
            
            await member.ban(reason="lil stupid nigga got 3 warns lmaoo")
        except Exception as e:
            print(f'Auto ban 3 warns error: {e}')

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
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
@commands.has_role(ADMIN_ROLE_ID)
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
@commands.has_role(ADMIN_ROLE_ID)
async def verifyall(ctx):
    global verify_running
    
    if verify_running:
        await ctx.send("Verification process is already running")
        return
    
    guild = ctx.guild
    old_role = guild.get_role(1508785745547235388)
    new_role = guild.get_role(1504503685328146585)
    
    if not old_role:
        await ctx.send(f"Role with ID 1508785745547235388 not found")
        return
    if not new_role:
        await ctx.send(f"Role with ID 1504503685328146585 not found")
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
        await ctx.send("Verification process is not 
