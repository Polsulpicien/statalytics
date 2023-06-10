import os
import sqlite3
import traceback
import asyncio
from datetime import datetime, timedelta, timezone

import discord
from discord import app_commands
from discord.ext import commands, tasks

from render.historical import render_historical
from helper.functions import (username_autocompletion,
                       get_command_cooldown,
                       get_hypixel_data,
                       update_command_stats,
                       authenticate_user,
                       start_historical,
                       uuid_to_discord_id,
                       get_time_config,
                       fetch_skin_model,
                       get_lookback_eligiblility,
                       message_invalid_lookback,
                       ordinal, loading_message,
                       send_generic_renders,
                       reset_historical,
                       log_error_msg)


class Weekly(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client
        self.LOADING_MSG = loading_message()


    @tasks.loop(hours=1)
    async def reset_weekly(self):
        utc_now = datetime.utcnow()
        if not utc_now.weekday() in (5, 6, 0):
            return

        reset_historical(
            method='weekly',
            table_format='weekly_%Y_%U',
            condition='timezone.weekday() == 6'
        )


    def cog_load(self):
        self.reset_weekly.start()


    def cog_unload(self):
        self.reset_weekly.cancel()


    @reset_weekly.before_loop
    async def before_reset_weekly(self):
        now = datetime.now()
        sleep_seconds = (60 - now.minute) * 60 - now.second
        await asyncio.sleep(sleep_seconds)


    @reset_weekly.error
    async def on_reset_weekly_error(self, error):
        await log_error_msg(self.client, error)


    @app_commands.command(name = "weekly", description = "View the weekly stats of a player")
    @app_commands.autocomplete(username=username_autocompletion)
    @app_commands.describe(username='The player you want to view')
    @app_commands.checks.dynamic_cooldown(get_command_cooldown)
    async def weekly(self, interaction: discord.Interaction, username: str=None):
        try: name, uuid = await authenticate_user(username, interaction)
        except TypeError: return
        refined = name.replace("_", "\_")

        discord_id = uuid_to_discord_id(uuid=uuid)
        gmt_offset, hour = get_time_config(discord_id=discord_id)

        with sqlite3.connect('./database/historical.db') as conn:
            cursor = conn.cursor()
            cursor.execute(f"SELECT uuid FROM weekly WHERE uuid = '{uuid}'")
            historical_data = cursor.fetchone()

        if not historical_data:
            await interaction.response.defer()
            start_historical(uuid=uuid)
            await interaction.followup.send(f'Historical stats for {refined} will now be tracked.')
            return

        await interaction.response.send_message(self.LOADING_MSG)
        os.makedirs(f'./database/activerenders/{interaction.id}')
        skin_res = fetch_skin_model(uuid, 144)
        hypixel_data = get_hypixel_data(uuid)

        now = datetime.now(timezone(timedelta(hours=gmt_offset)))
        formatted_date = now.strftime(f"%b {now.day}{ordinal(now.day)}, %Y")

        next_occurrence = now.replace(hour=hour, minute=0, second=0, microsecond=0)
        while now >= next_occurrence or next_occurrence.weekday() != 6:
            next_occurrence += timedelta(days=1)
        utc_next_occurrence = next_occurrence.astimezone(timezone.utc)
        timestamp = int(utc_next_occurrence.timestamp())

        kwargs = {
            "name": name,
            "uuid": uuid,
            "method": "weekly",
            "relative_date": formatted_date,
            "title": "Weekly BW Stats",
            "hypixel_data": hypixel_data,
            "skin_res": skin_res,
            "save_dir": interaction.id
        }

        await send_generic_renders(
            interaction=interaction,
            func=render_historical,
            kwargs=kwargs, 
            message=f':alarm_clock: Resets <t:{timestamp}:R>'
        )
        update_command_stats(interaction.user.id, 'weekly')


    @app_commands.command(name = "lastweek", description = "View last weeks stats of a player")
    @app_commands.autocomplete(username=username_autocompletion)
    @app_commands.describe(username='The player you want to view', weeks='The lookback amount in weeks')
    @app_commands.checks.dynamic_cooldown(get_command_cooldown)
    async def lastweek(self, interaction: discord.Interaction, username: str=None, weeks: int=1):
        try: name, uuid = await authenticate_user(username, interaction)
        except TypeError: return

        refined = name.replace("_", "\_")
        discord_id = uuid_to_discord_id(uuid)

        max_lookback = await get_lookback_eligiblility(interaction=interaction, discord_id=discord_id)
        if -1 != max_lookback < (weeks * 7):
            await message_invalid_lookback(interaction=interaction, max_lookback=max_lookback)
            return
        if weeks < 1: weeks = 1

        gmt_offset = get_time_config(discord_id=discord_id)[0]

        now = datetime.now(timezone(timedelta(hours=gmt_offset)))
        relative_date = now - timedelta(weeks=weeks)
        formatted_date = relative_date.strftime("Week %U, %Y")

        try:
            table_name = relative_date.strftime("weekly_%Y_%U")
        except OverflowError:
            await interaction.response.send_message('Big, big number... too big number...')
            return

        with sqlite3.connect('./database/historical.db') as conn:
            cursor = conn.cursor()
            try:
                cursor.execute(f"SELECT uuid FROM {table_name} WHERE uuid = '{uuid}'")
                historical_data = cursor.fetchone()
            except sqlite3.OperationalError:
                historical_data = ()

        if not historical_data:
            await interaction.response.send_message(f'{refined} has no tracked data for {weeks} week(s) ago!')
            return

        await interaction.response.send_message(self.LOADING_MSG)
        os.makedirs(f'./database/activerenders/{interaction.id}')
        skin_res = fetch_skin_model(uuid, 144)
        hypixel_data = get_hypixel_data(uuid)

        kwargs = {
            "name": name,
            "uuid": uuid,
            "method": "lastweek",
            "relative_date": formatted_date,
            "title": f"{weeks} Weeks Ago",
            "table_name": table_name,
            "hypixel_data": hypixel_data,
            "skin_res": skin_res,
            "save_dir": interaction.id
        }

        await send_generic_renders(interaction, render_historical, kwargs)
        update_command_stats(interaction.user.id, 'lastweek')


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Weekly(client))
