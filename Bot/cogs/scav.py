from nextcord.ext import commands


class Scavenger(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def guess(self, ctx: commands.Context, guess: str):
        await ctx.message.reply(f"Your guess: {guess}")


def setup(bot):
    bot.add_cog(Scavenger(bot))
