import discord
from data import get_accounts, write_accounts
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

        data = await get_accounts()
        id = str(interaction.user.id)
        if id in data:
            return await interaction.followup.send(f"이미 **{data[id]['account']}**로 계정이 등록되어 있습니다.")
        
        async with self.bot.session.get(f"https://solved.ac/api/v3/user/grass?handle={account}&topic=default") as response:
            if response.status == 404:
                return await interaction.followup.send("해당 계정을 찾을 수 없습니다.")
            elif response.status != 200:
                print(f"계정 등록 중 오류 발생 : Response Status {response.status}")
                return await interaction.followup.send("알 수 없는 오류가 발생했습니다.")

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

    @account_group.command(name="해지")
    async def resign(self, interaction: discord.Interaction):
        """등록된 계정을 해지합니다."""
        
        await interaction.response.defer()

        data = await get_accounts()
        id = str(interaction.user.id)
        if id not in data:
            return await interaction.followup.send(f"등록된 계정이 없습니다.")
        
        account = data.pop(id)['account']
        await write_accounts(data)

        await interaction.followup.send(f"등록된 **{account}** 계정이 해지되었습니다.")
    
async def setup(bot: commands.Bot):
    await bot.add_cog(Account(bot))