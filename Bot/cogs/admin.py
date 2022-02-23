from nextcord.ext import commands
import sqlalchemy


class Admin(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def purge(self, ctx: commands.Context):
        await ctx.channel.purge()


def setup(bot):
    bot.add_cog(Admin(bot))
