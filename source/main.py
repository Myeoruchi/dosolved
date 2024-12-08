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
@app_commands.describe(user='검색할 ID를 입력하세요')
async def streak(interaction: discord.Interaction, user: str):
    """검색한 유저의 스트릭을 조회합니다."""
    response = requests.get(f"https://solved.ac/api/v3/user/grass?handle={user}&topic=default")
    if response.status_code == 404:
        await interaction.response.send_message("해당 유저를 찾을 수 없습니다.")
    elif response.status_code != 200:
        await interaction.response.send_message("오류가 발생했습니다.")
    else:
        streak = response.json()
        streak['grass'] = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
        account = requests.get(f"https://solved.ac/api/v3/user/show?handle={user}").json()
        profile = account['profileImageUrl']
        background = requests.get(f"https://solved.ac/api/v3/background/show?backgroundId={account['backgroundId']}").json()['backgroundImageUrl']
        tier = account['tier']
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
        
        file = discord.File(f"../resource/{tier}.png")
        embed = discord.Embed(title="Solved.ac Streak Status", description=f"Last Solved: {date}", colour=0x95a5a6)
        embed.set_author(name=user, url=f"https://solved.ac/profile/{user}", icon_url=f"attachment://{tier}.png")
        embed.set_image(url=background)
        embed.set_thumbnail(url=profile)
        embed.add_field(name="Today", value=f"{':white_check_mark:' if check else ':x:'}", inline=True)
        embed.add_field(name="Current", value=f"{curStreak} Days", inline=True)
        embed.add_field(name="Maximum", value=f"{maxStreak} Days", inline=True)
        await interaction.response.send_message(file=file, embed=embed)

load_dotenv()
bot.run(os.environ.get('TOKEN'))