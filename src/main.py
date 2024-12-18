import os
import io
import json
import discord
import aiohttp
import aiofiles
import asyncio
from discord import app_commands
from discord.ext import tasks
from pathlib import Path
from dotenv import load_dotenv
from datetime import datetime, timezone, timedelta

load_dotenv()

DB_PATH = "./../db/user.json"
FILE_LOCK = asyncio.Lock()

intents = discord.Intents.default()
intents.members = True
bot = discord.Client(intents=intents)
bot.tree = discord.app_commands.CommandTree(bot)

@bot.event
async def on_ready():
    bot.tree.copy_global_to(guild=discord.Object(id=os.getenv('TEST_GUILD')))
    await bot.tree.sync()
    activity = discord.Game("오늘 문제 풀었나요?")
    await bot.change_presence(status=discord.Status.do_not_disturb, activity=activity)
    alarm.start()

@tasks.loop(minutes=1)
async def alarm():
    data = await get_accounts()
    time = datetime.now(timezone(timedelta(hours=9))).strftime("%H:%M")
    for id, account in data.items():
        if account['today'] == True:
            continue

        if time in account['alarm']:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f"https://solved.ac/api/v3/user/grass?handle={account['account']}&topic=default") as response:
                        streak = await response.json()
                
                streak['grass'] = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
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
                
                if check == True:
                    if account['today'] == False:
                        print("f")
                        data[id]['today'] = True
                        await write_accounts(data)
                else:
                    user = bot.get_user(int(id))
                    await user.send(f"오늘 문제를 안푸셨어요! 오늘 풀면 **{streak['currentStreak']}**일차!")
            except Exception as e:
                print(e)
                continue

async def get_accounts() -> dict:
    if not Path.exists(Path(DB_PATH)):
        return {}
    
    async with FILE_LOCK:
        async with aiofiles.open(DB_PATH, 'r', encoding='utf8') as f:
            data = await f.read()
            return json.loads(data)
        
async def write_accounts(accounts: dict) -> None:
    async with FILE_LOCK:
        async with aiofiles.open(DB_PATH, 'w', encoding='utf8') as f:
            await f.write(json.dumps(accounts, indent=4, ensure_ascii=False))

account_group = app_commands.Group(name="계정", description="계정 명령어")
@account_group.command(name="등록", description="나의 계정을 등록합니다.")
@app_commands.describe(account="등록할 계정을 입력하세요.")
@app_commands.rename(account="계정")
async def register(interaction: discord.Interaction, account: str):
    await interaction.response.defer()

    data = await get_accounts()
    id = str(interaction.user.id)

    if id in data:
        return await interaction.followup.send(f"이미 **{data[id]['account']}**로 계정이 등록되어 있습니다.")
    
    async with aiohttp.ClientSession() as session:
            async with session.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default") as response:
                if response.status == 404:
                    return await interaction.followup.send("해당 계정을 찾을 수 없습니다.")
                elif response.status != 200:
                    return await interaction.followup.send("오류가 발생했습니다.")

    new_data = {
        id: {
            "account": account,
            "alarm": [],
            "today": False,
        }
    }
    data.update(new_data)
    await write_accounts(data)

    await interaction.followup.send(f"**{account}**로 계정이 등록되었습니다.")

@account_group.command(name="해지", description="등록된 계정을 해지합니다.")
async def resign(interaction: discord.Interaction):
    await interaction.response.defer()

    data = await get_accounts()
    id = str(interaction.user.id)
    if id not in data:
        return await interaction.followup.send(f"등록된 계정이 없습니다.")
    
    account = data.pop(id)['account']
    await write_accounts(data)

    await interaction.followup.send(f"**{account}** 계정이 해지되었습니다.")

streak_group = app_commands.Group(name="스트릭", description="스트릭 명령어")
@streak_group.command(name="조회", description="스트릭을 조회합니다.")
@app_commands.describe(account="검색할 계정을 입력하세요.")
@app_commands.rename(account="계정")
async def streak(interaction: discord.Interaction, account: str = ""):
    await interaction.response.defer()

    if account == "":
        data = await get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send("등록된 계정이 없습니다.")
        
        account = data[id]['account']
    
    async with aiohttp.ClientSession() as session:
        async with session.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default") as response:
            if response.status == 404:
                return await interaction.followup.send("해당 계정을 찾을 수 없습니다.")
            elif response.status != 200:
                return await interaction.followup.send("오류가 발생했습니다.")
            streak = await response.json()

        async with session.get(f"https://solved.ac/api/v3/user/show?handle={account}") as response:
            user = await response.json()

        async with session.get(f"https://solved.ac/api/v3/background/show?backgroundId={user['backgroundId']}") as response:
            background = await response.json()
            background = background['backgroundImageUrl']

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
        
        if check == True:
            data = await get_accounts()
            id = str(interaction.user.id)
            if id in data and data[id]['today'] == False:
                data[id]['today'] = True
                await write_accounts(data)

        async with aiofiles.open(f"./../resource/tier/{tier}.png", 'rb') as f:
            data = await f.read()
        file = discord.File(io.BytesIO(data), str(tier))
        embed = discord.Embed(title="Solved.ac Streak Status", description=f"Last Solved: {date}", colour=0x95a5a6)
        embed.set_author(name=account, url=f"https://solved.ac/profile/{account}", icon_url=f"attachment://{tier}")
        embed.set_image(url=background)
        embed.set_thumbnail(url=profile)
        embed.add_field(name="Today", value=f"{':white_check_mark:' if check else ':x:'}", inline=True)
        embed.add_field(name="Current", value=f"{curStreak} Days", inline=True)
        embed.add_field(name="Maximum", value=f"{maxStreak} Days", inline=True)
        await interaction.followup.send(file=file, embed=embed)

alarm_group = app_commands.Group(name="알람", description="알람 명령어", parent=streak_group)
@alarm_group.command(name="설정", description="스트릭 알람을 설정합니다. 알람은 서버에 봇이 있을 경우에만 가능합니다.")
@app_commands.describe(time="한국 표준시(KST)로 HH:MM 형식을 사용해 입력하세요.")
@app_commands.rename(time="시각")
async def add_alarm(interaction: discord.Interaction, time: str):
    await interaction.response.defer()

    try:
        time = datetime.strptime(time, "%H:%M").strftime("%H:%M")
    except:
        return await interaction.followup.send(f"**{time}**은 유효한 시각이 아닙니다.")
    
    data = await get_accounts()
    id = str(interaction.user.id)
    if id not in data:
        return await interaction.followup.send("등록된 계정이 없습니다.")
    if time in data[id]['alarm']:
        return await interaction.followup.send(f"이미 **{time}**에 알람이 등록되어 있습니다.")
    
    data[id]['alarm'].append(time)
    await write_accounts(data)

    await interaction.followup.send(f"**{time}**에 알람이 등록되었습니다.")

@alarm_group.command(name="초기화", description="등록된 알람을 초기화합니다.")
async def reset_alarm(interaction: discord.Interaction):
    await interaction.response.defer()
    
    data = await get_accounts()
    id = str(interaction.user.id)
    if id not in data:
        return await interaction.followup.send("등록된 계정이 없습니다.")
    if not data[id]['alarm']:
        return await interaction.followup.send("등록된 알람이 없습니다.")
    
    data[id]['alarm'] = []
    await write_accounts(data)

    await interaction.followup.send("알림 목록이 초기화되었습니다.")

bot.tree.add_command(account_group)
bot.tree.add_command(alarm_group)

if __name__ == "__main__":
    bot.run(os.getenv('TOKEN'))