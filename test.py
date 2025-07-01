import math

import pandas as pd
import matplotlib
import matplotlib.pyplot as plt
from matplotlib.pyplot import title
from plottable import ColumnDefinition, Table
from plottable.cmap import normed_cmap

from plottable.plots import image

bg_color = "#FFFFFF"
text_color = "#000000"

sorted_list = [{'games': 7, 'losses': 5, 'name': 'Nicholas N.', 'percent': 28.5722342, 'rank': 1, 'rating': 1705,
                'wins': 2},
               {'games': 1, 'losses': 1, 'name': 'George S.', 'percent': 0.0, 'rank': 2, 'rating': 1641, 'wins': 0},
               {'games': 8, 'losses': 2, 'name': 'Anallely N.', 'percent': 75.0, 'rank': 3, 'rating': 1510, 'wins': 6},

               {'games': 2, 'losses': 1, 'name': 'Bob S.', 'percent': 50.0, 'rank': 4, 'rating': 1441, 'wins': 1}]
# print(sorted_list)
pd.set_option('display.precision', 2)
df = pd.DataFrame(sorted_list)
new_order = ['rank', 'name', 'games', 'wins', 'losses', 'percent']
df_reorderd = df[new_order]

df['percent'] = df['percent'].map('{:,.2f}'.format).astype(str)
df_reorderd.update(df[['percent']].astype(float))
# print(df)

col_defs = [
    ColumnDefinition(name="rank",
                     title="Rank",
                     textprops={"ha": "left", "weight": "bold"},
                     group="Player",),
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

height = max(len(sorted_list) - 3, 4)

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
fig.savefig(
    'fig.png',
    dpi=200,
    bbox_inches="tight"
)

