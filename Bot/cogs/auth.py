import logging
from nextcord.ext import commands
import sqlalchemy
import sqlalchemy.orm
from sqlalchemy.orm import Session
from sqlalchemy import Table, Column

from database.auth_database import UserInvite, UserInviteRole

from DatabaseBot import DatabaseBot

import logging
import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

#region Logging Setup
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

logger = logging.getLogger(SCRIPT_NAME)

if __name__ == "__main__":
    LOG_FILE = CURRENT_DIRECTORY + "/{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    logger.debug("Module started.")
    logger.debug("Log file set as: %s", LOG_FILE)

logger.debug("Set current directory as: %s", CURRENT_DIRECTORY)
#endregion

class Authentication(commands.Cog):

    def __init__(self, bot: DatabaseBot) -> None:
        self.bot = bot
        self.engine = bot.db_engine

    @commands.command()
    async def auth(self, ctx: commands.Context, code: str):
        await ctx.message.reply(f"Your code: {code}")

    @commands.command()
    async def list(self, ctx: commands.Context):
        with Session(self.engine) as session:
            logger.debug("Listing user invites...")
            stmt = sqlalchemy.select(UserInvite)
            result = session.execute(stmt)
            await ctx.message.reply(f"Result: {result.scalars().first().nickname}")

    @commands.command()
    async def add(self, ctx:commands.Context, nickname: str):
        with Session(self.engine) as session:
            logger.debug(f"Adding user invite [{nickname}] ...")
            user_invite = UserInvite(invite_code="bob", nickname=nickname)
            session.add(user_invite)
            session.commit()
        await ctx.message.reply(f"User invite with nickname [{nickname}] added")


def setup(bot):
    bot.add_cog(Authentication(bot))
