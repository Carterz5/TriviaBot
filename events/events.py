import discord
import logging




def register_events(client: discord.Client, tree: discord.app_commands.CommandTree):

    @client.event
    async def on_ready():


        for connected_guild in client.guilds:
            logging.info(f"Connected to guild: {connected_guild.name}")


        try:
            await tree.sync()
            logging.info(f"Synced slash commands.")
        except Exception as e:
            logging.error(f"Error syncing commands: {e}")
        logging.info(f"{client.user} is connected and ready.")

    @client.event
    async def on_message(message):
        if message.author == client.user:
            return

        elif message.content == '69':
            await message.channel.send("Hehe funny number")