import os
import json
import discord
import aiohttp
import aiofiles
from pathlib import Path
from discord import app_commands
from datetime import datetime, timezone, timedelta
from dotenv import load_dotenv

DB_PATH = "./db/user.json"

intents = discord.Intents.default()
bot = discord.Client(intents=intents)
bot.tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    await bot.tree.sync()
    print(f'Logged in as {bot.user} (ID: {bot.user.id})')

# async def get_data(id: int):
#     with open(DB_PATH, 'r', encoding='utf8') as f:
#         return json.load(f)

# @bot.tree.command(name="계정 등록", description="나의 계정을 등록합니다.")
# @app_commands.describe(account="등록할 계정을 입력하세요.")
# async def register(interaction: discord.Interaction, account: str):
#     await interaction.response.defer()

#     data = {}
#     if Path.exists(Path(DB_PATH)):
#         with open(DB_PATH, 'r', encoding='utf8') as f:
#             data = json.load(f)
#             if data['id'] == interaction.user.id:
#                 await interaction.followup.send("이미 계정이 등록되어 있습니다.")

#     new_data = {
#         interaction.user.id: {
#             "account": account,
#             "alarm": []
#         }
#     }

#     data.update(new_data)
#     with open(DB_PATH, "w", encoding='utf8') as f:
#         json.dump(data, f, indent=4)

#     await interaction.followup.send("계정이 등록되었습니다.")

@bot.tree.command(name="스트릭 검색", description="특정 계정의 스트릭을 조회합니다.")
@app_commands.describe(account="검색할 계정을 입력하세요.")
async def streak(interaction: discord.Interaction, account: str):
    await interaction.response.defer()
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default") as response:
            if response.status_code == 404:
                await interaction.followup.send("해당 계정을 찾을 수 없습니다.")
                return
            elif response.status_code != 200:
                await interaction.followup.send("오류가 발생했습니다.")
                return
            streak = await response.json()

        async with session.get(f"https://solved.ac/api/v3/user/show?handle={account}") as response:
            user = await response.json()

        async with session.get(f"https://solved.ac/api/v3/background/show?backgroundId={user['backgroundId']}") as response:
            background = await response.json()['backgroundImageUrl']

        streak['grass'] = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
        curStreak = streak['currentStreak']
        maxStreak = streak['longestStreak']
        profile = user['profileImageUrl']
        tier = user['tier']

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
        
        async with aiofiles.open(f"./tier/{tier}.png", 'rb') as f:
            file = discord.File(f)
        embed = discord.Embed(title="Solved.ac Streak Status", description=f"Last Solved: {date}", colour=0x95a5a6)
        embed.set_author(name=account, url=f"https://solved.ac/profile/{account}", icon_url=f"attachment://{tier}.png")
        embed.set_image(url=background)
        embed.set_thumbnail(url=profile)
        embed.add_field(name="Today", value=f"{':white_check_mark:' if check else ':x:'}", inline=True)
        embed.add_field(name="Current", value=f"{curStreak} Days", inline=True)
        embed.add_field(name="Maximum", value=f"{maxStreak} Days", inline=True)
        await interaction.followup.send(file=file, embed=embed)

load_dotenv()
bot.run(os.getenv('TOKEN'))