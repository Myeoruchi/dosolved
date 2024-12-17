import os
import requests
import discord
from discord import app_commands
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
bot.tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

@bot.tree.command()
@app_commands.describe(account='등록할 계정을 입력하세요.')
async def register(interaction: discord.Interaction, user: str):
    """나의 계정을 등록합니다."""

@bot.tree.command()
@app_commands.describe(account='검색할 계정을 입력하세요.')
async def streak(interaction: discord.Interaction, account: str):
    """특정 유저의 스트릭을 조회합니다."""
    response = requests.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default")
    if response.status_code == 404:
        await interaction.response.send_message("해당 계정을 찾을 수 없습니다.")
    elif response.status_code != 200:
        await interaction.response.send_message("오류가 발생했습니다.")
    else:
        await interaction.response.defer()
        streak = response.json()
        streak['grass'] = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
        user = requests.get(f"https://solved.ac/api/v3/user/show?handle={account}").json()
        profile = user['profileImageUrl']
        background = requests.get(f"https://solved.ac/api/v3/background/show?backgroundId={user['backgroundId']}").json()['backgroundImageUrl']
        tier = user['tier']
        curStreak = streak['currentStreak']
        maxStreak = streak['longestStreak']

        today = datetime.now(timezone(timedelta(hours=3))).date()
        for entry in streak['grass']:
            if isinstance(entry['value'], int):
                date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
                if date == today and entry['value'] >= 1:
                    check = True
                    break
                else:
                    check = False
                    break
        
        file = discord.File(f"./tier/{tier}.png")
        embed = discord.Embed(title="Solved.ac Streak Status", description=f"Last Solved: {date}", colour=0x95a5a6)
        embed.set_author(name=account, url=f"https://solved.ac/profile/{account}", icon_url=f"attachment://{tier}.png")
        embed.set_image(url=background)
        embed.set_thumbnail(url=profile)
        embed.add_field(name="Today", value=f"{':white_check_mark:' if check else ':x:'}", inline=True)
        embed.add_field(name="Current", value=f"{curStreak} Days", inline=True)
        embed.add_field(name="Maximum", value=f"{maxStreak} Days", inline=True)
        await interaction.followup.send(file=file, embed=embed)

load_dotenv()
bot.run(os.environ.get('TOKEN'))