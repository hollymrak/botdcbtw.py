import discord
from discord.ext import commands
import os
import re
from datetime import datetime, timedelta
from collections import defaultdict
import time

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
user_word_spam = defaultdict(list)
verify_running = False

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

@bot.event
async def on_ready():
    print(f'Bot {bot.user} is online')
    await bot.change_presence(status=discord.Status.dnd, activity=discord.Game(name="HollyScriptX"))

@bot.event
async def on_message(message):
    if message.author == bot.user:
        await bot.process_commands(message)
        return
    
    if message.guild is None or message.guild.id != SERVER_ID:
        await bot.process_commands(message)
        return
    
    if bot.user in message.mentions:
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
    
    user_id = message.author.id
    current_time = time.time()
    content_lower = message.content.lower()
    
    user_messages[user_id] = [t for t in user_messages[user_id] if current_time - t < 3]
    user_messages[user_id].append(current_time)
    
    user_word_spam[user_id] = [(word, t) for word, t in user_word_spam[user_id] if current_time - t < 3]
    
    words = re.findall(r'\b\w+\b', content_lower)
    for word in words:
        if len(word) > 2:
            user_word_spam[user_id].append((word, current_time))
    
    word_counts = defaultdict(int)
    for word, _ in user_word_spam[user_id]:
        word_counts[word] += 1
    
    is_word_spam = any(count >= 5 for count in word_counts.values())
    
    last_messages = []
    async for msg in message.channel.history(limit=10):
        if msg.author.id == user_id:
            last_messages.append(msg.content.lower())
    
    is_repeat_spam = False
    if len(last_messages) >= 3:
        if all(msg == last_messages[0] for msg in last_messages[:3]):
            is_repeat_spam = True
    
    has_mentions = len(message.mentions) > 3 or len(message.role_mentions) > 2
    
    if is_repeat_spam or has_mentions or is_word_spam:
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
            
            spam_channel = bot.get_channel(1513695339167617084)
            if spam_channel:
                embed = discord.Embed(
                    description=f"> {message.author.mention} Has been timed-out for spamming.",
                    color=discord.Color.from_rgb(200, 50, 50)
                )
                embed.add_field(name="Duration", value=f"{mute_duration} seconds", inline=True)
                embed.add_field(name="Warning Count", value=f"{user_warnings[user_id]}", inline=True)
                
                if is_word_spam:
                    spam_words = [word for word, count in word_counts.items() if count >= 5]
                    embed.add_field(name="Reason", value=f"Spamming words: {', '.join(spam_words[:3])}", inline=False)
                elif is_repeat_spam:
                    embed.add_field(name="Reason", value="Repeating same message", inline=False)
                elif has_mentions:
                    embed.add_field(name="Reason", value="Mass mentions", inline=False)
                
                await spam_channel.send(embed=embed)
            
            user_messages[user_id] = []
            user_word_spam[user_id] = []
            
            if user_warnings[user_id] >= 5:
                try:
                    await message.author.ban(reason="Repeated spamming (5+ warnings)")
                    embed = discord.Embed(
                        description=f"> {message.author.mention} has been permanently **banned** for repeated spamming.",
                        color=discord.Color.from_rgb(200, 50, 50)
                    )
                    await spam_channel.send(embed=embed)
                    user_warnings[user_id] = 0
                except:
                    pass
            
            await bot.process_commands(message)
            return
        except Exception as e:
            print(f'Spam timeout error: {e}')
    
    if "zalupa" in message.content.lower():
        await message.reply("**hi!**")
    
    await bot.process_commands(message)

async def auto_ban(message):
    try:
        member = message.author
        log_channel = bot.get_channel(1518832499122507786)
        
        if log_channel:
            embed = discord.Embed(
                description=f"> {member.mention} has been permanently **banned** from **HollyScriptX**\n> Reason: **Scammed Accounts detection 1.0**\n> Typed Message:\n> {message.content}",
                color=discord.Color.from_rgb(200, 50, 50)
            )
            await log_channel.send(embed=embed)
        
        try:
            embed = discord.Embed(
                description=f"> You have been permanently **banned** from **HollyScriptX**\n> Reason: Auto-ban. Typed in do not type channel (prob hacked account).\n\n> You still can get unbanned, type to @t3e6 on discord and explain what happened.",
                color=discord.Color.from_rgb(200, 50, 50)
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
    msg = await ctx.send(f"> Deleted {len(deleted) - 1} messages")
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
                description=f"> You have been **permanently banned** from **HollyScriptX**\n> Banned By: {ctx.author.mention}\n> Reason: **{reason}**",
                color=discord.Color.from_rgb(200, 50, 50)
            )
            await member.send(embed=embed)
        except:
            pass
        await ctx.send(f"> User {member.mention} has been banned. Reason: {reason}")
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
            description=f"> {user.mention} **has been unbanned!**",
            color=discord.Color.from_rgb(50, 200, 50)
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
            description=f"> {member.mention} **has been unmuted!**",
            color=discord.Color.from_rgb(50, 200, 50)
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
                description=f"> You have been **hard-banned** from **HollyScriptX**\n> Banned by: {ctx.author.mention}\n> Reason: **{reason}**",
                color=discord.Color.from_rgb(200, 50, 50)
            )
            await member.send(embed=embed)
        except:
            pass
        
        embed = discord.Embed(
            description=f"> {member.mention} **has been hard-banned!**",
            color=discord.Color.from_rgb(200, 50, 50)
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
            description=f"> {member.mention} **has been unhard-banned!**",
            color=discord.Color.from_rgb(50, 200, 50)
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
                description=f"> You have been **muted** in **HollyScriptX**\n> Muted By: {ctx.author.mention}\n> Reason: **{reason}**\n> Duration: 24 hours",
                color=discord.Color.from_rgb(200, 150, 50)
            )
            await member.send(embed=embed)
        except:
            pass
        
        await ctx.send(f"> User {member.mention} has been muted. Reason: {reason}")
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
            description=f"> You have received a warning in **HollyScriptX**\n> Warned By: {ctx.author.mention}\n> Reason: **{reason}**\n> Total Warnings: {warn_count}",
            color=discord.Color.from_rgb(200, 180, 50)
        )
        await member.send(embed=embed)
    except:
        pass
    
    await ctx.send(f"> User {member.mention} has been warned. Reason: {reason}. Total warnings: {warn_count}")
    
    if warn_count >= 3:
        try:
            log_channel = bot.get_channel(1518832499122507786)
            if log_channel:
                embed = discord.Embed(
                    description=f"> {member.mention} have been permanently banned because received 3 warns",
                    color=discord.Color.from_rgb(200, 50, 50)
                )
                await log_channel.send(embed=embed)
            
            try:
                embed = discord.Embed(
                    description=f"> You have been permanently banned from **HollyScriptX**\n> Reason: lil stupid nigga got 3 warns lmaoo",
                    color=discord.Color.from_rgb(200, 50, 50)
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
        await ctx.send("Verification process is not running")
        return
    verify_running = False
    await ctx.send("Verification process stopped")

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
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

@bot.command()
@commands.has_role(ADMIN_ROLE_ID)
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

@bot.command()
async def invite(ctx):
    view = discord.ui.View()
    view.add_item(discord.ui.Button(label="Join Discord", url=INVITE_LINK))
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
    embed.add_field(name=",unban (user)", value="Unban a user", inline=False)
    embed.add_field(name=",mute (@user) (reason)", value="Mute a user for 24 hours", inline=False)
    embed.add_field(name=",unmute (@user)", value="Unmute a user", inline=False)
    embed.add_field(name=",warn (@user) (reason)", value="Give a warning to a user", inline=False)
    embed.add_field(name=",hardban (@user) (reason)", value="Hard ban a user (remove all channel access)", inline=False)
    embed.add_field(name=",unhardban (user)", value="Remove hard ban from a user", inline=False)
    embed.add_field(name=",lockchats", value="Lock all specified channels", inline=False)
    embed.add_field(name=",unlockchats", value="Unlock all specified channels", inline=False)
    embed.add_field(name=",verifyall", value="Verifies all people with unverified role", inline=False)
    embed.add_field(name=",stopverify", value="Stop verification process", inline=False)
    embed.add_field(name=",giverole (role_name)", value="Give a role to replied user", inline=False)
    embed.add_field(name=",delrole (role_name)", value="Remove a role from replied user", inline=False)
    embed.add_field(name=",invite", value="Send invite to Discord server", inline=False)
    embed.add_field(name=",help_commands", value="Show this help message", inline=False)
    
    available_roles = ', '.join(role_map.keys())
    embed.add_field(name="Available Roles", value=available_roles, inline=False)
    embed.set_footer(text=f"Admin Role ID: {ADMIN_ROLE_ID}")
    
    await ctx.send(embed=embed)

if __name__ == "__main__":
    if TOKEN is None:
        print("ERROR: DISCORD_TOKEN environment variable is not set!")
    else:
        bot.run(TOKEN)
