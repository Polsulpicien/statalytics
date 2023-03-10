import os
import sqlite3

def background(path, uuid, default):
    with sqlite3.connect(f'{os.getcwd()}/database/linkedaccounts.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM linkedaccounts WHERE uuid = '{uuid}'")
        linked_data = cursor.fetchone()

    if not linked_data:
        return f'{path}/{default}.png'
    discordid = linked_data[1]

    parent_dir = os.path.dirname(os.path.abspath(os.getcwd()))
    with sqlite3.connect(f'{parent_dir}/statalyticsWeb/subscriptions.db') as conn:
        cursor = conn.cursor()
        cursor.execute(f"SELECT * FROM subscriptions WHERE discordid = '{discordid}'")
        subscription = cursor.fetchone()
    if subscription and 'premium' in subscription[1] and os.path.exists(f'{path}/custom/{discordid}.png'):
        return f'{path}/custom/{discordid}.png'
    return f'{path}/{default}.png'