from nextcord.ext import commands


class Authentication(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def auth(self, ctx: commands.Context, code: str):
        await ctx.message.reply(f"Your code: {code}")


def setup(bot):
    bot.add_cog(Authentication(bot))
