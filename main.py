import discord
from discord.ext import commands
from supabase import create_client, Client
import aiohttp
import os
from dotenv import load_dotenv
load_dotenv()
SUPABASE_URL = os.getenv('SUPABASE_API_URL')
SUPABASE_KEY = os.getenv('SUPABASE_KEY')
BUCKET_NAME = 'cdn'
DISCORD_TOKEN = os.getenv('TOKEN')
# specify the channel id where the bot should check for images
TARGET_CHANNEL_ID = 1315895347825868881 

supabase: Client = create_client(SUPABASE_URL, SUPABASE_KEY)

intents = discord.Intents.default()
intents.messages = True
intents.message_content = True
bot = commands.Bot(command_prefix='!', intents=intents)

@bot.event
async def on_ready():
    print(f'IN AS {bot.user}')

@bot.event
async def on_message(message):
    if message.author == bot.user:
        return
    if message.channel.id == TARGET_CHANNEL_ID:
        if message.attachments:
            for attachment in message.attachments:
                if attachment.content_type and 'image' in attachment.content_type:
                    uploading_message = await message.channel.send('Beep boop beep... Uploading image... Be patient!')
                    async with aiohttp.ClientSession() as session:
                        async with session.get(attachment.url) as img:
                            if img.status == 200:
                                image_data = await img.read()
                                file_name = attachment.filename
                                # Upload to bucket
                                                           
                                try:
                                    uploaded = supabase.storage.from_(BUCKET_NAME).upload(file_name, image_data)
                                    if uploaded:
                                        # Generate the url of the uploaded image
                                        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
                                        await uploading_message.delete()
                                        await message.channel.send(f'Here is your image URL: {image_url}')
                                    else:
                                        await uploading_message.delete()
                                        await message.channel.send('Failed to upload image.')
                                except Exception as e:
                                    if 'already exists' in str(e):
                                        # Get url of existing image
                                        image_url = f"{SUPABASE_URL}/storage/v1/object/public/{BUCKET_NAME}/{file_name}"
                                        await uploading_message.delete()
                                        await message.channel.send(f'Already existing image - URL: {image_url}')
                                    else:
                                        await uploading_message.delete()
                                        await message.channel.send(f'Failed to upload: {e}')     
                    return
            await message.channel.send('No valid images found to upload.')
        else:
            # Delete messages without images
            await message.delete()
            await message.channel.send('Only images are allowed in this channel!', delete_after=5)
    else:
        #Can be used to process commands...
        await bot.process_commands(message)

bot.run(DISCORD_TOKEN)