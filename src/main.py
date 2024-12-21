import os
import aiohttp
import discord
from discord.ext import commands
from dotenv import load_dotenv

class StreakBot(commands.AutoShardedBot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.members = True  # DM을 보내기 위해서 필요
        super().__init__(
            command_prefix="!",
            intents=intents
        )
        self.session = None

    async def setup_hook(self):
        self.session = aiohttp.ClientSession()
        await self.load_extension("default")
        await self.load_extension("account")
        await self.load_extension("streak")
        await self.load_extension("alarm")

        self.tree.copy_global_to(guild=discord.Object(id=os.getenv('TEST_GUILD')))
        await self.tree.sync()
    
    async def on_ready(self):
        print("Bot is ready")
        activity = discord.Game("오늘 문제 풀었나요?")
        await self.change_presence(status=discord.Status.online, activity=activity)

    async def close(self):
        await super().close()
        if self.session:
            await self.session.close()
            
if __name__=="__main__":
    load_dotenv()
    bot = StreakBot()
    bot.run(os.getenv('TOKEN'))