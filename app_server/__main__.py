import asyncio
import io
import os

import discord
from discord.ext import commands
from discord.ui import Button, View, Select

from table2ascii import table2ascii as t2a, PresetStyle

from app_server.backend.players import Player

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from plottable import ColumnDefinition, Table
from plottable.cmap import normed_cmap
import logging
from dotenv import load_dotenv

load_dotenv()

logger = logging.getLogger('bot_logger')
logger.setLevel(logging.DEBUG)

file_handler = logging.FileHandler('app.log', mode='a', encoding='utf-8')
file_handler.setLevel(logging.INFO) # Typically INFO or WARNING for file logs
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
file_handler.setFormatter(formatter)
logger.addHandler(file_handler)

# 2. Conditional Console Handler
# Check the deployment environment variable
deployment_env = os.getenv('DEPLOYMENT_ENV', 'development') # Default to 'development' if not set

if deployment_env == 'development':
    # Add a StreamHandler (for console output) only in development
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.DEBUG) # Typically DEBUG for local development
    # You might want a different, simpler format for the console
    console_formatter = logging.Formatter('%(levelname)s - %(name)s - %(message)s')
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)

token = os.getenv('DISCORD_TOKEN')

intents = discord.Intents.default()
intents.message_content = True  # Required to read message content

client = commands.Bot(command_prefix='!', intents=intents)
players = Player()


class Confirm(discord.ui.View):
    def __init__(self):
        super().__init__()
        self.value = None

    # When the confirm button is pressed, set the inner value to `True` and
    # stop the View from listening to more input.
    # We also send the user an ephemeral message that we're confirming their choice.
    @discord.ui.button(label='Confirm', style=discord.ButtonStyle.green)
    async def confirm(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Confirming', ephemeral=True)
        self.value = True
        self.stop()

    # This one is similar to the confirmation button except sets the inner value to `False`
    @discord.ui.button(label='Cancel', style=discord.ButtonStyle.grey)
    async def cancel(self, interaction: discord.Interaction, button: discord.ui.Button):
        await interaction.response.send_message('Cancelling', ephemeral=True)
        self.value = False
        self.stop()


class PlayerSelectView(View):
    def __init__(self, player_list: list[dict], quantity: int = None):
        super().__init__()
        self.value = None
        self.player_list = player_list

        # Create the Select component dynamically
        options = []
        for p in self.player_list:
            options.append(discord.SelectOption(label=f"{p['first_name']} {p['last_name'][0].upper()}.",
                                                value=p['player_id']))  # Assuming 'id' as a unique value

        select = Select(
            placeholder="Choose an option",
            options=options,
            min_values=quantity if quantity is not None else 1,
            max_values=quantity if quantity is not None else 2,
            custom_id="player_select"  # It's good practice to add a custom_id
        )
        self.add_item(select)

        # Assign the callback to the dynamically created select
        select.callback = self.select_callback

    async def select_callback(self, interaction: discord.Interaction):
        selected_values = interaction.data['values']
        self.value = selected_values  # Assign the list of selected values

        # You can now process multiple selected values
        selected_names = [
            f"{p['first_name']} {p['last_name'][0].upper()}." for p in self.player_list if
            str(p.get('player_id')) in selected_values
        ]

        await interaction.response.send_message(f"You selected: {', '.join(selected_names)}")
        self.stop()


class ScoreSelectView(View):
    def __init__(self):
        super().__init__()
        self.value = None
        options = [discord.SelectOption(label=i + 1, value=i + 1) for i in range(20)]

        select = Select(
            placeholder="Choose an option",
            options=options,
            min_values=1,
            max_values=1,
            custom_id="score_select"  # It's good practice to add a custom_id
        )
        self.add_item(select)

        # Assign the callback to the dynamically created select
        select.callback = self.select_callback

    async def select_callback(self, interaction: discord.Interaction):
        selected_values = interaction.data['values']
        self.value = selected_values[0]  # Assign the list of selected values
        await interaction.response.send_message(f"Team score set at: {selected_values[0]}")
        self.stop()


@client.command()
@commands.is_owner()
async def sync(ctx: commands.Context):
    synced = await client.tree.sync()  # Syncs globally

    await ctx.send(f"Synced {len(synced)} commands.")


@client.hybrid_command(name='listrank')
async def list_rank(ctx):
    player_list = players.get_all_current_ranking()
    # sorted_list = sorted(player_list, key=lambda x: (x['rating'], x['wins']), reverse=True)
    #
    # for i in range(len(sorted_list)):
    #     sorted_list[i]['rank'] = i + 1

    output = t2a(
        header=["Rank", "Name", "Games Played", "Wins", "Losses", "Win %"],
        body=[[player['rank'], player['name'], player['games'], player['wins'], player['losses'], player['percent']] for
              player in player_list],
        first_col_heading=True
    )

    user_id = ctx.author.id
    logger.debug(f"Your user ID is: {user_id}")
    # print(f"Your user ID is: {user_id}")

    bg_color = "#FFFFFF"
    text_color = "#000000"

    df = pd.DataFrame(player_list)
    new_order = ['rank', 'name', 'games', 'wins', 'losses', 'percent']
    df_reorderd = df[new_order]

    df['percent'] = df['percent'].map('{:,.2f}'.format).astype(str)
    df_reorderd.update(df[['percent']].astype(float))

    col_defs = [
        ColumnDefinition(name="rank",
                         title="Rank",
                         textprops={"ha": "left", "weight": "bold"},
                         group="Player", ),
        ColumnDefinition(name="name",
                         title="Name",
                         textprops={"ha": "left"},
                         group="Player"),
        ColumnDefinition(name="games",
                         title="Games Played",
                         textprops={"ha": "center"},
                         group="Stats"),
        ColumnDefinition(name="wins",
                         title="Wins",
                         textprops={"ha": "center"},
                         group="Stats"),
        ColumnDefinition(name="losses",
                         title="Losses",
                         textprops={"ha": "center"},
                         group="Stats"),
        ColumnDefinition(name="percent",
                         title="Win %",
                         textprops={"ha": "center", "color": text_color, "weight": "bold"},
                         group="Stats",
                         cmap=normed_cmap(df_reorderd['percent'], cmap=matplotlib.colormaps['RdYlGn'], num_stds=2))
    ]

    height = max(len(player_list) - 3, 4)

    fig, ax = plt.subplots(figsize=(10, height))
    ax.axis('off')  # Hide axes
    fig.set_facecolor(bg_color)
    ax.set_facecolor(bg_color)
    table = Table(
        df_reorderd,
        column_definitions=col_defs,
        index_col="rank",
        row_dividers=True,
        footer_divider=True,
        textprops={'fontsize': 14},
        ax=ax

    )

    buffer = io.BytesIO()
    fig.savefig(
        buffer,
        format='png',
        dpi=200,
        bbox_inches="tight"
    )
    buffer.seek(0)

    plt.close(fig)
    try:
        await ctx.send(file=discord.File(buffer, filename="rankings.png"))
        await ctx.send("Current rankings!")
    except Exception as e:
        await ctx.send(f"An error occurred while sending the plot: {e}")
        logger.error(f"Error sending plot: {e}")
        # print(f"Error sending plot: {e}")


@client.hybrid_command(name='addplayer')
async def add_player(ctx, first_name: str, last_name: str):
    created = players.create_new_player(first_name, last_name)
    await ctx.send(f"Added {first_name} {last_name[0].upper()}" if created else 'Error adding player')


@client.hybrid_command(name='savematch')
async def save_match(ctx) -> list:
    player_list = players.retrieve_player_list()
    player_list = sorted(player_list, key=lambda x: x['first_name'])

    # Select team 1 players
    view_1 = PlayerSelectView(player_list)
    await ctx.send("Select up to two players for team 1:", view=view_1)
    await view_1.wait()
    team_1 = view_1.value

    # Select team 1 score
    score_1_view = ScoreSelectView()
    await ctx.send("Select team 1 score:", view=score_1_view)
    await score_1_view.wait()
    team_1_score = int(score_1_view.value)

    # remove team 1 players from choices
    filtered_players = []
    for p in player_list:
        if str(p['player_id']) not in team_1:
            filtered_players.append(p)

    # Select team 2 players
    if len(filtered_players) == 0 or (len(filtered_players) == 1 and len(team_1) == 2):
        await ctx.send("Not enough remaining players to add to team 2...")
        return
    elif len(filtered_players) == 1:
        confirm_view = Confirm()
        await ctx.send(f"Is team 2 {filtered_players[0]['first_name']} {filtered_players[0]['last_name'][0].upper()}.?",
                       view=confirm_view)
        await confirm_view.wait()
        team_2 = [str(filtered_players[0]['player_id'])]
    else:
        view_2 = PlayerSelectView(filtered_players, len(team_1))
        quantity = "one" if len(team_1) == 1 else "two"
        await ctx.send(f"Select {quantity} player(s) for team 2:", view=view_2)
        await view_2.wait()
        team_2 = view_2.value

    # Select team 2 score
    score_2_view = ScoreSelectView()
    await ctx.send("Select team 2 score:", view=score_2_view)
    await score_2_view.wait()
    team_2_score = int(score_2_view.value)

    await ctx.send('Match successfully added' if players.add_match(team_1, team_2, team_1_score,
                                                                   team_2_score) else 'Error adding match...')


@client.command()
async def show_menu(ctx):
    await ctx.send("Here's your menu:", view=PlayerSelectView())


@client.hybrid_command()
async def ping(ctx, name: str):
    await ctx.send('Pong!')


async def send_keep_alive_message():
    await client.wait_until_ready()
    # Replace 'YOUR_CHANNEL_ID' with an actual channel ID your bot has access to
    # Consider sending to a private "log" channel, or just printing to console.
    log_channel_id = 1389746017892569100  # Replace with your channel ID
    try:
        channel = client.get_channel(log_channel_id)
        if channel:
            while not client.is_closed():
                # This could be a very light message, or just logging internally.
                # Sending a message to Discord every X minutes can be spammy.
                # A better "internal" heartbeat might just be logging.
                print(f"[{client.user}] Internal keep-alive check: Still running...")
                # await channel.send("Bot is still alive!", delete_after=60) # Sends and deletes after 60s
                await asyncio.sleep(300)  # Send every 5 minutes (adjust as needed)
        else:
            print(f"Warning: Log channel with ID {log_channel_id} not found for keep-alive.")
    except Exception as e:
        print(f"Error in send_keep_alive_message: {e}")


if __name__ == '__main__':
    print('starting discord server')
    client.run(
        token=os.getenv('DISCORD_TOKEN'),
        log_level=logging.DEBUG,
        log_handler=console_handler if deployment_env == 'development' else file_handler,
        log_formatter=formatter,
        reconnect=True
    )
