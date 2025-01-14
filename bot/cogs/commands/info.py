import os
import psutil
import sys
import time
import datetime
import sqlite3
from json import load as load_json

import discord
from discord import app_commands
from discord.ext import commands

from helper.functions import (
    update_command_stats,
    get_command_users,
    get_embed_color,
    get_config
)


class Info(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client


    @app_commands.command(name="info", description="View information and stats for Statalytics")
    async def info(self, interaction: discord.Interaction):
        await interaction.response.defer()

        # Usage metrics
        with sqlite3.connect('./database/command_usage.db') as conn:
            cursor = conn.cursor()
            cursor.execute(
                f'SELECT commands_ran FROM overall WHERE discord_id = 0')
            total_commands_ran = cursor.fetchone()[0]

        with sqlite3.connect('./database/linked_accounts.db') as conn:
            cursor = conn.cursor()
            cursor.execute('SELECT COUNT(discord_id) FROM linked_accounts')
            total_linked_accounts = cursor.fetchone()[0]

        # Other shit
        total_guilds = len(self.client.guilds)
        total_members = get_command_users()

        with open('./database/uptime.json') as datafile:
            start_time = load_json(datafile)['start_time']

        uptime = str(datetime.timedelta(seconds=int(round(time.time()-start_time))))
        config = get_config()

        ping = round(self.client.latency * 1000)
        total_commands = len(list(self.client.tree.walk_commands()))

        # Embed
        embed = discord.Embed(
            title='Statalytics Info',
            description=None,
            color=get_embed_color('primary')
        )

        embed.add_field(name='Key Metrics', value=f"""
            `┌` **Uptime:** `{uptime}`
            `├` **Ping:** `{ping:,}ms`
            `├` **Commands:** `{total_commands:,}`
            `└` **Version:** `{config['version']}`
        """.replace('   ', ''))

        embed.add_field(name='', value='')

        embed.add_field(name='Bot Usage Stats', value=f"""
            `┌` **Servers:** `{total_guilds:,}`
            `├` **Users:** `{total_members:,}`
            `├` **Commands Ran:** `{total_commands_ran:,}`
            `└` **Linked Users**: `{total_linked_accounts:,}`
            ​
        """.replace('   ', ''))

        python_version = '.'.join((str(sys.version_info[0]), str(sys.version_info[1]), str(sys.version_info[2])))
        ram_usage = round(psutil.Process(os.getpid()).memory_info().rss / 1024 ** 2, 2)
        embed.add_field(name='Specifications', value=f"""
            `┌` **Devs:** `{', '.join(config['developers'])}`
            `├` **Library:** `discord.py`
            `├` **Python:** `{python_version}`
            `└` **Used RAM:** `{ram_usage:,}mb`
        """.replace('   ', ''))

        embed.add_field(name='', value='')

        embed.add_field(name='Links', value=f"""
            `┌` [Invite]({config['links']['invite_url']})
            `├` [Website]({config['links']['website']})
            `├` [Support]({config['links']['support_server']})
            `└` [Github]({config['links']['github']})
        """.replace('   ', ''))

        embed.set_thumbnail(url='https://statalytics.net/image/logo.png?v=2')
        await interaction.followup.send(embed=embed)

        update_command_stats(discord_id=interaction.user.id, command='info')


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Info(client))
