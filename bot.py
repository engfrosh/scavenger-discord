from typing import Union
from nextcord import SlashOption
import nextcord
from nextcord.ext import commands

import logging
import os

import json

import datetime as dt

from math import ceil, floor

import string
import random

# TODO settings.guild_id should be deprecated

LOG_LEVEL = logging.DEBUG
SCAV_QUESTIONS_FILE = "scav_questions.json"
SETTINGS_FILE = "settings.json"
SCAV_TEAM_FILENAME = "scav_teams.json"
USER_REGISTRATION_FILE = "registrations.json"

BLANK_TEAM_CSV = {
    "role": 0,
    "team_name": "",
    "current_question": 0,
    "locked_out_until": "",
    "last_hint": -1,
    "members": [],
    "finished": False,
    "finish_time": "",
    "question_completion_time": {}
}

# region Logging Setup
SCRIPT_NAME = os.path.splitext(os.path.basename(__file__))[0]

logger = logging.getLogger(SCRIPT_NAME)

if __name__ == "__main__":
    LOG_FILE = "{}.log".format(SCRIPT_NAME)
    if os.path.exists(LOG_FILE):
        try:
            os.remove(LOG_FILE)
        except PermissionError:
            pass
    logging.basicConfig(level=LOG_LEVEL, filename=LOG_FILE)
    logger.debug("Module started.")
    logger.debug("Log file set as: %s", LOG_FILE)

# endregion

client = commands.Bot("!")

# region Variable Declerations
quick_settings = {}
guild = None
guild_channels = None
channels = {}
scav_game = None
user_registrations = {}
# endregion


# region SCAV Classes
class ScavTeam():
    def __init__(self, team_info: dict, channel_id: int):
        self.team_info = dict(team_info)
        self.channel_id = channel_id

    async def init_channel(self):
        self.channel = await client.fetch_channel(self.channel_id)

    async def _send_message(self, content: str):
        await self.channel.send(content)

    def get_team_info(self):
        return self.team_info

    def is_team_member(self, author_id: int):
        return author_id in self.team_info["members"]

    def is_team_locked_out(self):
        """Returns number of seconds if still locked out, otherwise returns 0"""
        if not self.team_info["locked_out_until"]:
            return False
        locked_out_time = dt.datetime.fromisoformat(
            self.team_info["locked_out_until"])
        now = dt.datetime.now()
        delta = locked_out_time - now
        if delta > dt.timedelta(0):
            return ceil(delta.total_seconds())
        else:
            return 0

    async def check_answer(self, guess):
        if self.team_info["finished"]:
            await self.channel.send("You're already finished!")
            return
        if guess.lower() == scav_questions[self.team_info["current_question"]]["answer"].lower():
            await self.correct_answer()
            return True
        else:
            await self.wrong_answer()
        return False

    async def wrong_answer(self):
        await self.channel.send("Sorry, that is incorrect.")

    async def correct_answer(self):
        await self.channel.send("That is correct!")
        self.team_info["question_completion_time"][self.team_info["current_question"]
                                                   ] = dt.datetime.now().isoformat()
        self.team_info["current_question"] += 1
        scav_game.save_team_info()
        if self.team_info["current_question"] >= len(scav_questions):
            await self.channel.send("CONGRATS!! You have completed SCAV")
            self.team_info["finished"] = True
            self.team_info["finish_time"] = dt.datetime.now().isoformat()
            scav_game.save_team_info()
        else:
            await self.ask_question()
        await scav_game.leaderboard()
        return

    async def lockout(self, minutes):
        now = dt.datetime.now()
        delta = dt.timedelta(minutes=minutes)
        lockout_end_time = now + delta
        self.team_info["locked_out_until"] = lockout_end_time.isoformat()
        scav_game.save_team_info()
        await self.channel.send("You are locked out for {} minutes".format(minutes))
        return

    async def unlock(self):
        self.team_info["locked_out_until"] = ""
        await self.channel.send("Your team is now unlocked")
        return

    async def ask_question(self):
        if self.team_info["finished"]:
            await self.channel.send("You're already finished!")
            return
        if "file" in scav_questions[self.team_info["current_question"]]:
            if "file_display_name" in scav_questions[self.team_info["current_question"]]:
                filename = scav_questions[self.team_info["current_question"]
                                          ]["file_display_name"]
            else:
                filename = None
            f = nextcord.File(
                scav_questions[self.team_info["current_question"]]["file"], filename=filename)
        else:
            f = None
        await self.channel.send(scav_questions[self.team_info["current_question"]]["clue"], file=f)
        if self.team_info["current_question"] == self.team_info["last_hint"]:
            if "hint_file" in scav_questions[self.team_info["current_question"]]:
                if "hint_file_display" in scav_questions[self.team_info["current_question"]]:
                    filename = scav_questions[self.team_info["current_question"]
                                              ]["file_display_name"]
                else:
                    filename = None
                f = nextcord.File(
                    scav_questions[self.team_info["current_question"]]["hint_file"], filename=filename)
            else:
                f = None
            await self.channel.send(scav_questions[self.team_info["current_question"]]["hint"], file=f)

    async def introduction(self):
        await self.channel.send(settings["help_text"])

    async def send_hint(self):
        if self.team_info["finished"]:
            await self.channel.send("You're already finished!")
            return
        if "hint_file" in scav_questions[self.team_info["current_question"]]:
            if "hint_file_display" in scav_questions[self.team_info["current_question"]]:
                filename = scav_questions[self.team_info["current_question"]
                                          ]["file_display_name"]
            else:
                filename = None
            f = nextcord.File(
                scav_questions[self.team_info["current_question"]]["hint_file"], filename=filename)
        else:
            f = None
        if "hint" in scav_questions[self.team_info["current_question"]]:
            if self.team_info["last_hint"] == self.team_info["current_question"]:
                await self.ask_question()
                return
            else:
                self.team_info["last_hint"] = self.team_info["current_question"]
                scav_game.save_team_info()
                await self.lockout(settings["scav"]["default_lockout_time"])
                await self.channel.send(scav_questions[self.team_info["current_question"]]["hint"], file=f)
        else:
            await self.channel.send("Sorry, no hint available")

    async def reset_team(self):
        self.team_info["finished"] = False
        self.team_info["finish_time"] = ""
        self.team_info["question_completion_time"] = {}
        self.team_info["current_question"] = 0
        self.team_info["locked_out_until"] = ""
        self.team_info["last_hint"] = -1
        scav_game.save_team_info()
        await self.channel.send("Your team has been reset")

    async def add_player(self, author):
        self.team_info["members"].append(author.id)
        scav_game.save_team_info()
        # member = guild.get_member(author.id)
        # member = await client.fetch_user(author.id)
        role = guild.get_role(self.team_info["role"])
        await author.add_roles(role)

    def create_registration_code(self, name="", nickname=""):
        code = "$" + "".join(random.choice(string.ascii_lowercase +
                                           string.digits) for i in range(8))
        global user_registrations
        user_registrations[code] = {
            "name": "",
            "nickname": "",
            "account_type": "scav_player",
            "user_id": 0,
            "scav_team": self.channel_id,
            "team_name": self.team_info["team_name"]
        }
        save_user_registrations()
        return code


class ScavGame():
    def __init__(self, all_team_info_fp: str):
        logger.debug("Team info to load is a filepath, attempting to load...")
        with open(all_team_info_fp, "r") as f:
            all_team_info = json.load(f)
        self.teams = {}
        for key, value in all_team_info.items():
            key = int(key)
            self.teams[key] = ScavTeam(value, key)
            logger.debug("Scav team with id %i loaded", key)
        logger.info("All Scav teams loaded")
        return

    async def init_channels(self):
        for team in self.teams.values():
            await team.init_channel()

    def save_team_info(self, filename: str = None, indent=4):
        if filename is None:
            filename = SCAV_TEAM_FILENAME
        export_dict = {}
        for key, value in self.teams.items():
            export_dict[str(key)] = value.get_team_info()
        with open(filename, "w") as f:
            json.dump(export_dict, f, indent=indent)

    def is_scav_channel(self, channel_id: int):
        if channel_id in self.teams:
            return self.teams[channel_id]
        else:
            return False

    async def new_scav_team(self, team_name=None):
        global guild
        logger.debug("Create new team")
        if team_name == None:
            team_name = "Team {}".format(len(self.teams))
        logger.debug("Team name: %s", team_name)
        # role = await guild.create_role(name=team_name, colour=nextcord.Colour.gold)
        new_role = await guild.create_role(name=team_name)
        scav_manager_role = guild.get_role(settings["scav_manager_role"])
        overwrites = {
            guild.default_role: nextcord.PermissionOverwrite(read_messages=False),
            new_role: nextcord.PermissionOverwrite(read_messages=True),
            scav_manager_role: nextcord.PermissionOverwrite(read_messages=True)
        }
        channel = await guild.create_text_channel(team_name, overwrites=overwrites)
        team_details = BLANK_TEAM_CSV
        team_details["role"] = new_role.id
        team_details["team_name"] = team_name
        self.teams[channel.id] = (ScavTeam(team_details, channel.id))
        await self.teams[channel.id].init_channel()
        self.save_team_info()
        await channels["bot_status_channel"].send("{} Created".format(team_name))
        reg_codes = []
        for i in range(settings["scav"]["default_team_size"]):
            reg_codes.append(self.teams[channel.id].create_registration_code())
        await self.leaderboard()

        guild = await client.fetch_guild(settings["guild_id"])
        return reg_codes

    async def leaderboard(self):
        await channels["leaderboard_channel"].purge()
        finished_teams = []
        inprogress_teams = []
        for key, team in self.teams.items():
            if team.team_info["finished"]:
                finished_teams.append(team)
            else:
                inprogress_teams.append(team)
        finished_teams = sorted(
            finished_teams, key=lambda team: team.team_info["finish_time"])
        inprogress_teams = sorted(
            inprogress_teams, key=lambda team: team.team_info["current_question"], reverse=True)
        leaderboard_str = "Standings\n============\n"
        position = 1
        for team in finished_teams:
            leaderboard_str += "{position}: {team}\n".format(
                position=position, team=team.team_info["team_name"])
            position += 1
        for team in inprogress_teams:
            leaderboard_str += "\*{position}: {team}\n".format(
                position=position, team=team.team_info["team_name"],)
            position += 1
        await channels["leaderboard_channel"].send(leaderboard_str)

    async def send_introductions(self):
        for team in self.teams.values():
            await team.introduction()

# endregion


# region Function Definitions


def load_all_settings():
    global settings
    with open(SETTINGS_FILE, "r") as f:
        settings = json.load(f)
    global quick_settings
    quick_settings["admin_ids"] = set(settings["admin_users"])
    quick_settings["scav_manager_ids"] = set(settings["scav_manager_users"])

    if "bot_status_channel" in settings["channels"]:
        settings["bot_status_channel_active"] = True
        settings["bot_status_channel_id"] = settings["channels"]["bot_status_channel"]
    return settings


def load_scav_questions():
    with open(SCAV_QUESTIONS_FILE, "r") as f:
        return json.load(f)


def load_user_registrations():
    with open(USER_REGISTRATION_FILE, "r") as f:
        global user_registrations
        user_registrations = json.load(f)


def save_user_registrations(indent=4):
    with open(USER_REGISTRATION_FILE, "w") as f:
        json.dump(user_registrations, f, indent=indent)


async def reload_files():
    load_all_settings()
    global scav_questions
    scav_questions = load_scav_questions()
    load_user_registrations()
    await load_scav_teams()


def save_settings(fp=None, indent=4):
    if fp == None:
        fp = SETTINGS_FILE
    with open(fp, "w") as f:
        json.dump(settings, f, indent=4)
    logger.debug("Settings saved to %s", fp)


def is_admin(user_id):
    return user_id in quick_settings["admin_ids"]


def is_scav_manager(user_id):
    return user_id in quick_settings["scav_manager_ids"]


async def load_scav_teams():
    global scav_game
    scav_game = ScavGame(SCAV_TEAM_FILENAME)
    await scav_game.init_channels()
    return


# endregion


@client.event
async def on_ready():
    logger.info("Successfully Logged In")
    print("Connected")
    global guild
    guild = await client.fetch_guild(settings["guild_id"])
    channels["bot_status_channel"] = await client.fetch_channel(settings["channels"]["bot_status_channel"])
    channels["leaderboard_channel"] = await client.fetch_channel(settings["channels"]["leaderboard_channel"])
    await channels["bot_status_channel"].send("Hello, I am now working! It is currently {datetime}".format(datetime=dt.datetime.now().isoformat()))
    await reload_files()
    if "profile_picture" in settings and not settings["profile_picture_set"]:
        with open(settings["profile_picture"], "rb") as f:
            await client.user.edit(avatar=f.read())
        settings["profile_picture_set"] = True
        save_settings()


@client.event
async def on_message(message):
    if message.author == client.user:
        return
    if message.guild.id != settings["guild_id"]:
        return
    message_array = message.content.lower().strip().split()

    # * NEW TEAM
    if settings["scav"]["self_registration_allowed"] and message_array[0] == "\\newteam":
        if len(message_array) > 1:
            team_name = " ".join(message_array[1:])
        else:
            team_name = "Team {}".format(len(scav_game.teams))
        logger.debug("Creating team %s", team_name)
        reg_codes = await scav_game.new_scav_team(team_name=team_name)
        code_msg = "Here are your scav team registration codes for team {team_name}\n".format(team_name=team_name)
        code_msg += "```\n"
        for code in reg_codes:
            code_msg += code + "\n"
        code_msg += "```"
        code_msg += "Send one of these codes in a channel in the discord server. Send these to your teammates and have them do the same."
        await message.author.send(code_msg)
        await message.delete()
        return

    # * Lock / Unlock
    if (
            message_array[0] == "\\lockout" or message_array[0] == "\\unlock") and (
            is_admin(message.author.id) or is_scav_manager(message.author.id)):
        active_scav_team = scav_game.is_scav_channel(message.channel.id)
        if active_scav_team is not False:
            if message_array[0] == "\\unlock":
                await active_scav_team.unlock()
            else:
                if len(message_array) == 2:
                    minutes = int(message_array[1])
                else:
                    minutes = settings["scav"]["default_lockout_time"]
                await active_scav_team.lockout(minutes)
            scav_game.save_team_info()
        else:
            await message.channel.send("Not a SCAV channel")
        await message.delete()
        return

    # * Get Question
    if (message_array[0] == "\\question" or message_array[0] == "?"):
        active_scav_team = scav_game.is_scav_channel(message.channel.id)
        if active_scav_team is not False:
            if settings["scav"]["enabled"]:
                await active_scav_team.ask_question()
            else:
                await message.channel.send("SCAV is not enabled")
        else:
            await message.channel.send("This is not a SCAV channel!")
        return

    # * Get Hing
    if (message_array[0] == "\\hint"):
        active_scav_team = scav_game.is_scav_channel(message.channel.id)
        if active_scav_team is not False:
            if active_scav_team.is_team_member(message.author.id):
                if settings["scav"]["enabled"]:
                    await active_scav_team.send_hint()
                else:
                    await message.channel.send("SCAV is not enabled")
            else:
                await message.channel.send("You are not allowed to ask for hints in this channel!")
                return
        else:
            await message.channel.send("This is not a SCAV channel!")
        return

    # * Get Help
    if message_array[0] == "\\help":
        if scav_game.is_scav_channel(message.channel.id):
            await message.channel.send(settings["help_text"])
            return
        else:
            await message.channel.send("Please `@Grant` for help")

    # * Authenticate New User
    if message_array[0][0] == "$":
        await message.delete()
        if message_array[0] in user_registrations:
            if user_registrations[message_array[0]]["user_id"] == 0:
                if user_registrations[message_array[0]]["account_type"] == "admin":
                    if message.author.id not in settings["admin_users"]:
                        user_registrations[message_array[0]
                                           ]["user_id"] = message.author.id
                        save_user_registrations()
                        settings["admin_users"].append(message.author.id)
                        save_settings()
                        quick_settings["admin_ids"].add(message.author.id)
                        role = guild.get_role(settings["admin_role"])
                        await message.author.add_roles(role)
                        await message.channel.send("Welcome Admin!")
                    else:
                        await message.channel.send("Already an Admin")
                elif user_registrations[message_array[0]]["account_type"] == "scav_manager":
                    if message.author.id not in settings["scav_manager_users"] and message.author.id not in settings["admin_users"]:
                        user_registrations[message_array[0]
                                           ]["user_id"] = message.author.id
                        save_user_registrations()
                        settings["scav_manager_users"].append(
                            message.author.id)
                        save_settings()
                        quick_settings["scav_manager_ids"].add(
                            message.author.id)
                        role = guild.get_role(settings["scav_manager_role"])
                        await message.author.add_roles(role)
                        await message.channel.send("Welcome Scav Manager!")
                    else:
                        await message.channel.send("Already a Scav Manager or Higher")
                elif user_registrations[message_array[0]]["account_type"] == "scav_player":
                    if message.author.id not in settings["scav_manager_users"] and message.author.id not in settings["admin_users"]:
                        user_registrations[message_array[0]
                                           ]["user_id"] = message.author.id
                        save_user_registrations()
                        await scav_game.teams[user_registrations[message_array[0]]["scav_team"]].add_player(
                            message.author)
                        await message.channel.send("Welcome Scav Player!")
                    else:
                        await message.channel.send("Already a Scav Manager or Higher")
            else:
                await message.channel.send("Activation code already used")
        else:
            await message.channel.send("Invalid activation code")
        return

    # * Admin Commands
    if is_admin(message.author.id):
        if message_array[0] == "\\reset_team":
            team_id = int(message_array[1])
            if team_id in scav_game.teams:
                await scav_game.teams[team_id].reset_team()
        elif message_array[0] == "\\remove_scav_manager":
            user_id = int(message_array[1])
            if user_id in settings["scav_manager_users"]:
                settings["scav_manager_users"].remove(user_id)
                save_settings()
            if user_id in quick_settings["scav_manager_ids"]:
                quick_settings["scav_manager_ids"].remove(user_id)
            await message.delete()
        elif message_array[0] == "\\create_team":
            if len(message_array) > 1:
                team_name = message_array[1]
            else:
                team_name = None
            await scav_game.new_scav_team(team_name)
        elif message_array[0] == "\\leaderboard":
            await scav_game.leaderboard()
        elif message_array[0] == "\\welcome":
            await scav_game.send_introductions()
        else:
            return
    else:
        return

load_all_settings()


@client.slash_command(guild_ids=settings["guild_ids"], description="Reload bot settings")
async def reload(interaction: nextcord.Interaction):
    if is_admin(interaction.user.id):
        await reload_files()
        await interaction.response.send_message("Reloaded Files", ephemeral=True)
    else:
        await interaction.response.send_message("You do not have permission to reload", ephemeral=True)


@client.slash_command(guild_ids=settings["guild_ids"], description="Guess an answer for Scav")
async def guess(interaction: nextcord.Interaction, answer: str = SlashOption(name="answer", description="Your guess", required=True)):
    active_scav_team: Union[False, ScavTeam] = scav_game.is_scav_channel(interaction.channel_id)

    if active_scav_team is False:
        await interaction.response.send_message("This is not a scav channel.", ephemeral=True)
        return

    if not active_scav_team.is_team_member(interaction.user.id):
        await interaction.response.send_message("You are not allowed to guess in this channel!", ephemeral=True)
        return

    if not settings["scav"]["enabled"]:
        await interaction.response.send_message("SCAV is currently disabled")
        return

    lockout_time = active_scav_team.is_team_locked_out()
    if lockout_time == 0:
        await interaction.response.send_message(f"Checking your answer: {answer}")
        await active_scav_team.check_answer(answer)

    else:
        # TODO Update the way lockout times are displayed
        await interaction.response.send_message("You are locked out for {}:{}".format(floor(lockout_time / 60), lockout_time % 60))
    return


@client.slash_command(guild_ids=settings["guild_ids"], description="Enable / disable scav game")
async def scav(interaction: nextcord.Interaction,
               action: str = SlashOption(name="action",
                                         description="The action to manage the scav game.", required=True, choices={
                                             "enable": "enable",
                                             "disable": "disable"
                                         })):

    if not is_admin(interaction.user.id):
        await interaction.response.send_message("You do not have permission to use this command.", ephemeral=True)
        return

    if action == "enable":
        settings["scav"]["enabled"] = True
        save_settings()
        await interaction.response.send_message("Scav is now enabled.")
        return
    elif action == "disable":
        settings["scav"]["enabled"] = False
        save_settings()
        await interaction.response.send_message("Scav is now disabled.")
        return
    else:
        logger.error(f"Invalid action {action}")
        return

    # region Load Credentials
with open(settings["credentials_file"], "r") as f:
    credentials = json.load(f)

bot_token = credentials["api_token"]
# endregion


client.run(bot_token)
