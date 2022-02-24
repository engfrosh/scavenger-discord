from nextcord.ext import commands
from nextcord import Interaction, SlashOption
import nextcord

GUILD_IDS = [731598642426675301]


class Scavenger(commands.Cog):

    def __init__(self, bot) -> None:
        self.bot = bot

    @commands.command()
    async def guess(self, ctx: commands.Context, guess: str):
        await ctx.message.reply(f"Your guess: {guess}")

    @commands.command()
    async def question(self, ctx: commands.Context):
        await ctx.channel.send("Here is your question")

    # @nextcord.slash_command(guild_ids=GUILD_IDS)
    # async def scav(
    #         interaction: Interaction,
    #         status: str = SlashOption(name="status", description="Enable or Disable Scav", choices={"Enable": "enable", "Disable": "disable"})):

    @nextcord.slash_command(guild_ids=GUILD_IDS)
    async def scav(self, interaction: Interaction):


        # if status:
        #     await interaction.response.send_message(f"You {status} Scav!")
        # else:
        await interaction.response.send_message("Scav!")

        # When working with slash commands you need to add the applications.commands scope to the oauth when getting the bot invite link


def setup(bot):
    bot.add_cog(Scavenger(bot))
