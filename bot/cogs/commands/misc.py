import sqlite3
from json import load as load_json

import discord
from discord import app_commands
from discord.ext import commands

from helper.functions import update_command_stats, get_embed_color, get_config


class SubmitSuggestion(discord.ui.Modal, title='Submit Suggestion'):
    def __init__(self, channel, **kwargs):
        self.channel = channel
        super().__init__(**kwargs)

    suggestion = discord.ui.TextInput(label='Suggestion:', placeholder='You should add...', style=discord.TextStyle.long)

    async def on_submit(self, interaction: discord.Interaction):
        await interaction.response.defer()
        embed_color = get_embed_color('primary')
        submit_embed = discord.Embed(
            title=f'Suggestion by {interaction.user} ({interaction.user.id})',
            description=f'**Suggestion:**\n{self.suggestion}', color=embed_color
        )

        await self.channel.send(embed=submit_embed)
        await interaction.followup.send('Successfully submitted suggestion!', ephemeral=True)


class Misc(commands.Cog):
    def __init__(self, client):
        self.client: discord.Client = client


    @app_commands.command(name="help", description="Help Page")
    async def get_help(self, interaction: discord.Interaction):
        with open('./assets/help.json', 'r') as datafile:
            embed_data = load_json(datafile)

        embeds = [discord.Embed.from_dict(embed) for embed in embed_data['embeds']]
        await interaction.response.send_message(embeds=embeds, ephemeral=True)

        update_command_stats(interaction.user.id, 'help')


    @app_commands.command(name='invite', description=f'Invite Statalytics to your server')
    async def invite(self, interaction: discord.Interaction):
        invite_url = get_config()['links']['invite_url']
        await interaction.response.send_message(f'To add Statalytics to your server, click [here]({invite_url})')

        update_command_stats(interaction.user.id, 'invite')


    @app_commands.command(name='suggest', description='Suggest a feature you would like to see added!')
    async def suggest(self, interaction: discord.Interaction):
        channel = self.client.get_channel(1065918528236040232)
        await interaction.response.send_modal(SubmitSuggestion(channel))

        update_command_stats(interaction.user.id, 'suggest')


    @app_commands.command(name="usage", description="View Command Usage")
    async def usage_stats(self, interaction: discord.Interaction):
        await interaction.response.defer()
        with open('./assets/command_map.json', 'r') as datafile:
            command_map: dict = load_json(datafile)['commands']

        with sqlite3.connect('./database/command_usage.db') as conn:
            cursor = conn.cursor()
            cursor.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = [table[0] for table in cursor.fetchall()]

            cursor.execute(f'SELECT * FROM overall WHERE discord_id = {interaction.user.id}')
            table_data = cursor.fetchone()
            if not table_data: table_data = (0, 0)
            overall = f'**Overall - {table_data[1]}**'
            description = []

            usage_values = {}
            for table in tables:
                cursor.execute(f'SELECT * FROM {table} WHERE discord_id = {interaction.user.id}')
                table_data = cursor.fetchone()
                if not table_data or table == "overall": continue
                usage_values[command_map.get(table)] = table_data[1]

        for key, value in sorted(usage_values.items(), key=lambda x: x[1], reverse=True):
            description.append(f'`{key}` - `{value}`')

        embed_color = get_embed_color('primary')
        embed = discord.Embed(title="Your Command Usage", description=overall, color=embed_color)
        for i in range(0, len(description), 10):
            sublist = description[i:i+10]
            embed.add_field(name='', value='\n'.join(sublist))
        await interaction.followup.send(embed=embed)

        update_command_stats(interaction.user.id, 'usage')


    @app_commands.command(name="credits", description="The people who made Statalytics possible")
    async def credits(self, interaction: discord.Interaction):
        with open('./assets/credits.json', 'r') as datafile:
            credits = load_json(datafile)

        embed = discord.Embed.from_dict(credits['credits'])
        await interaction.response.send_message(embed=embed)

        update_command_stats(interaction.user.id, 'credits')


async def setup(client: commands.Bot) -> None:
    await client.add_cog(Misc(client))
