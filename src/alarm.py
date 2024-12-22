import discord
import api
import database
from datetime import datetime, timezone, timedelta
from discord import app_commands
from discord.ext import commands, tasks

class Alarm(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self.alarm.start()

    alarm_group = app_commands.Group(name="알람", description="알람 명령어입니다.")
    @alarm_group.command(name="등록")
    @app_commands.rename(time="시각")
    async def add_alarm(self, interaction: discord.Interaction, time: str) -> None:
        """스트릭 알람을 등록합니다. 봇이랑 같은 서버에 있어야 합니다.

        Parameters
        ----------
        time: str
            한국 표준시(KST)로 HH:MM 형식을 사용해 입력하세요.
        """

        await interaction.response.defer()

        try:
            time = datetime.strptime(time, "%H:%M").strftime("%H:%M")
        except:
            return await interaction.followup.send(f"**{time}**은 유효한 시각이 아닙니다. 올바른 형식은 HH:MM입니다.")
        
        data = await database.get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send("등록된 계정이 없습니다.")
        if time in data[id]['alarm']:
            return await interaction.followup.send(f"이미 **{time}**에 알람이 등록되어 있습니다.")
        
        data[id]['alarm'].append(time)
        data[id]['alarm'] = sorted(data[id]['alarm'])
        await database.write_accounts(data)

        await interaction.followup.send(f"**{time}**에 알람이 등록되었습니다.")

    @alarm_group.command(name="목록")
    async def show_alarm(self, interaction: discord.Interaction) -> None:
        """등록된 알람 목록을 보여줍니다."""

        await interaction.response.defer()

        data = await database.get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send("등록된 계정이 없습니다.")
        if not data[id]['alarm']:
            return await interaction.followup.send(f"등록된 알람이 없습니다.")

        alarm_list = ""
        for alarm in data[id]['alarm']:
            alarm_list += f"- {alarm}\n"

        embed = discord.Embed(
            colour=0x7FFFD4,
            description=alarm_list
        )
        embed.set_author(
            name=f"{interaction.user.name}님의 알람 목록",
            icon_url=f"{interaction.user.avatar}"
        )

        await interaction.followup.send(embed=embed)

    @alarm_group.command(name="초기화")
    async def reset_alarm(self, interaction: discord.Interaction) -> None:
        """등록된 알람을 초기화합니다."""

        await interaction.response.defer()
        
        data = await database.get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send("등록된 계정이 없습니다.")
        if not data[id]['alarm']:
            return await interaction.followup.send("등록된 알람이 없습니다.")
        
        data[id]['alarm'] = []
        await database.write_accounts(data)

        await interaction.followup.send("알람 목록이 초기화되었습니다.")

    @tasks.loop(minutes=1)
    async def alarm(self) -> None:
        data = await database.get_accounts()
        time = datetime.now(timezone(timedelta(hours=9))).strftime("%H:%M")
        if time == "06:00":
            for id in data:
                data[id]['today'] = False
            await database.write_accounts(data)
            await database.generate_backup()
            
        for id, account in data.items():
            if account['today'] == True:
                continue

            if time in account['alarm']:
                try:
                    streak = await api.get_streak(self.bot.session, account['account'])
                    streak_list = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
                    today = datetime.now(timezone(timedelta(hours=3))).date()
                    check = False
                    for entry in streak_list:
                        if isinstance(entry['value'], int):
                            date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
                            if date == today and entry['value'] >= 1:
                                check = True
                            break
                    
                    if check:
                        if account['today'] == False:
                            data[id]['today'] = True
                            await database.write_accounts(data)
                    else:
                        user = self.bot.get_user(int(id))
                        await user.send(f"오늘 문제를 안푸셨어요! 오늘 풀면 **{streak['currentStreak']+1}**일차!")

                except Exception as e:
                    print(f"알람 중 오류 발생: {e}")
                    continue
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Alarm(bot))