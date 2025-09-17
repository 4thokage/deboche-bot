# bot.py
import os, random, time
import discord
from discord.ext import commands

TOKEN = os.getenv("DISCORD_TOKEN")
bot = commands.Bot(command_prefix="/")

cooldowns = {}  # { (user_id, command): timestamp }

COOLDOWN_SECONDS = 30

def check_cd(user, cmd):
    now = time.time()
    key = (user, cmd)
    if key in cooldowns and now - cooldowns[key] < COOLDOWN_SECONDS:
        return False, COOLDOWN_SECONDS - (now - cooldowns[key])
    cooldowns[key] = now
    return True, 0

@bot.command()
async def hunt(ctx):
    ok, left = check_cd(ctx.author.id, "hunt")
    if not ok:
        return await ctx.send(f"⏳ Cooldown! Try again in {int(left)}s")
    monster = random.choice(["Slime", "Wolf", "Boar"])
    await ctx.send(f"{ctx.author.mention} went hunting and found a **{monster}**!")

@bot.command()
async def forage(ctx):
    ok, left = check_cd(ctx.author.id, "forage")
    if not ok:
        return await ctx.send(f"⏳ Cooldown! {int(left)}s left.")
    item = random.choice(["Herb", "Mushroom", "Stick"])
    await ctx.send(f"You foraged and found a {item} 🌱")

bot.run(TOKEN)