import discord
from discord.ext import commands

from table2ascii import table2ascii as t2a, PresetStyle

from app_server.backend.players import Player



token = 'MTM4NzgyNjg3OTI1MTIyMjY2OQ.GMHeg3.xY0g06occEWamvhWUqM3-QMH-Ck23nvTWa7EZM'

intents = discord.Intents.default()
intents.message_content = True # Required to read message content

client = commands.Bot(command_prefix='!', intents=intents)




@client.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    synced = await client.tree.sync() # Syncs globally

    await ctx.send(f"Synced {len(synced)} commands.")

@client.command()
async def members(ctx):
    for member in ctx.guild.members:
        print(member.name)
    await ctx.send(ctx.guild.members)



@client.hybrid_command(name='listrank')
async def list_rank(ctx):
    # In your command:
    output = t2a(
        header=["Rank", "Name", "Games Played", "Wins", "Losses", "Win %"],
        body=[[1, 'Nicholas', 12, 6, 6, 50.0],[2, 'Anallely', 12, 6, 6, 50.0]],
        first_col_heading=True
    )

    user_id = ctx.author.id
    print(f"Your user ID is: {user_id}")
    print(type(user_id))

    await ctx.send(f"```\n{output}\n```")


@client.hybrid_command()
async def ping(ctx):
  await ctx.send('Pong!')


client.run(token)