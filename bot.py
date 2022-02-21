import json
import nextcord
import nextcord.ext.commands

import logging
import os

CURRENT_DIRECTORY = os.path.dirname(__file__)
LOG_LEVEL = logging.DEBUG

# region Logging Setup
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
# endregion

# region Import Token

with open("credentials.json", "r") as f:
    json_data = json.load(f)
    api_token = json_data["api_token"]

client = nextcord.ext.commands.Bot("!")


@client.event
async def on_ready():

    logger.debug("Logged in.")
    channel = await client.fetch_channel(807100215651074109)
    await channel.send("Logged on and ready to go.")


client.run(api_token)
