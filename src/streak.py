import io
import discord
import aiofiles
import asyncio
import database
import api
from datetime import datetime, timezone, timedelta
from discord import app_commands
from discord.ext import commands

class Streak(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    streak_group = app_commands.Group(name="스트릭", description="스트릭 명령어 그룹입니다.")
    @streak_group.command(name="조회", description="계정의 스트릭 상태를 조회합니다.")
    @app_commands.rename(account="계정")
    async def streak(self, interaction: discord.Interaction, account: str | None) -> None:
        """계정의 스트릭 상태를 조회합니다.
        
        Parameters
        ----------
        account: str | None
            조회할 계정을 입력하세요.
        """

        await interaction.response.defer()

        if account == None:
            data = await database.get_accounts()
            id = str(interaction.user.id)
            if id not in data:
                return await interaction.followup.send("등록된 계정이 없습니다.")
            
            account = data[id]['account']

        responses = await asyncio.gather(
            api.get_streak(self.bot.session, account),
            api.get_user(self.bot.session, account)
        )
        
        if isinstance(responses[0], str) or isinstance(responses[1], str):
            if responses[0] == "NOT_EXIST":
                return await interaction.followup.send("해당 계정을 찾을 수 없습니다.")
            return await interaction.followup.send("오류가 발생했습니다. 다시 시도해주세요.")
        
        streak = responses[0]
        user = responses[1]

        response = api.get_background(self.bot.session, user['backgroundId'])
        if isinstance(response, str):
            return await interaction.followup.send("오류가 발생했습니다. 다시 시도해주세요.")
        
        background = await response['backgroundImageUrl']
        streak_list = sorted(streak['grass'], key=lambda x: datetime.strptime(x['date'], '%Y-%m-%d').date(), reverse=True)
        curStreak = streak['currentStreak']
        maxStreak = streak['longestStreak']
        profile = user['profileImageUrl']
        tier = user['tier']

        today = datetime.now(timezone(timedelta(hours=3))).date()
        check = False
        for entry in streak_list:
            if isinstance(entry['value'], int):
                date = datetime.strptime(entry['date'], '%Y-%m-%d').date()
                if date == today:
                    check = True
                break

        async with aiofiles.open(f"./../resource/tier/{tier}.png", 'rb') as f:
            data = await f.read()
            file = discord.File(io.BytesIO(data), str(tier))

        embed = discord.Embed(
            title="Solved.ac Streak Status",
            description=f"Last Solved: {date}",
            colour=0x7FFFD4)
        embed.set_author(name=account, url=f"https://solved.ac/profile/{account}", icon_url=f"attachment://{tier}")
        embed.set_image(url=background)
        embed.set_thumbnail(url=profile)
        embed.add_field(name="Today", value=f"{':white_check_mark:' if check else ':x:'}", inline=True)
        embed.add_field(name="Current", value=f"{curStreak} Days", inline=True)
        embed.add_field(name="Maximum", value=f"{maxStreak} Days", inline=True)
        
        await interaction.followup.send(file=file, embed=embed)
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Streak(bot))