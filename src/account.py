import discord
import api
import database
from discord import app_commands
from discord.ext import commands

class Account(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot

    account_group = app_commands.Group(name="계정", description="계정 명령어 그룹입니다.")
    @account_group.command(name="등록")
    @app_commands.rename(account="계정")
    async def register(self, interaction: discord.Interaction, account: str) -> None:
        """Solved.ac 계정을 등록합니다.
        
        Parameters
        ----------
        account: str
            등록할 계정을 입력하세요.
        """
        
        await interaction.response.defer()

        data = await database.get_accounts()
        id = str(interaction.user.id)
        if id in data:
            return await interaction.followup.send(f"이미 **{data[id]['account']}**로 계정이 등록되어 있습니다.")
        
        response = api.get_user(self.bot.session, account)
        if isinstance(response, str):
            if response == "NOT_EXIST":
                return await interaction.followup.send("해당 계정을 찾을 수 없습니다")
            return await interaction.followup.send("오류가 발생했습니다. 다시 시도해주세요.")

        new_data = {
            id: {
                "account": account,
                "alarm": [],
                "today": False,
            }
        }
        data.update(new_data)
        await database.write_accounts(data)

        await interaction.followup.send(f"**{account}**로 계정이 등록되었습니다.")

    @account_group.command(name="해지")
    async def resign(self, interaction: discord.Interaction) -> None:
        """등록된 계정을 해지합니다."""
        
        await interaction.response.defer()

        data = await database.get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send(f"등록된 계정이 없습니다.")
        
        account = data.pop(id)['account']
        await database.write_accounts(data)

        await interaction.followup.send(f"등록된 **{account}** 계정이 해지되었습니다.")
    
async def setup(bot: commands.Bot) -> None:
    await bot.add_cog(Account(bot))