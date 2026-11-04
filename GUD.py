
import os
import asyncio
import requests
import discord
from discord.ext import tasks

# ==============================
# GUD PVP - TOP 10 ZABÓJSTW
# ==============================

DISCORD_TOKEN = os.getenv("DISCORD_TOKEN")
ROBLOX_API_KEY = os.getenv("ROBLOX_API_KEY")
DISCORD_CHANNEL_ID = os.getenv("DISCORD_CHANNEL_ID")

UNIVERSE_ID = "10774663567"
DATASTORE_NAME = "GUDPVP_KillsRanking_V1"
SCOPE = "global"

MARKER = "GUDPVP_KILLS_LEADERBOARD"

if not DISCORD_TOKEN or not ROBLOX_API_KEY or not DISCORD_CHANNEL_ID:
    raise RuntimeError(
        "Brakuje DISCORD_TOKEN, ROBLOX_API_KEY lub DISCORD_CHANNEL_ID!"
    )

DISCORD_CHANNEL_ID = int(DISCORD_CHANNEL_ID)

intents = discord.Intents.default()
bot = discord.Client(intents=intents)

username_cache = {}


def get_top_players():
    url = (
        "https://apis.roblox.com/cloud/v2/"
        f"universes/{UNIVERSE_ID}/ordered-data-stores/"
        f"{DATASTORE_NAME}/scopes/{SCOPE}/entries"
    )

    headers = {
        "x-api-key": ROBLOX_API_KEY
    }

    params = {
        "maxPageSize": 10,
        "orderBy": "value desc"
    }

    response = requests.get(
        url,
        headers=headers,
        params=params,
        timeout=20
    )

    response.raise_for_status()
    data = response.json()

    entries = (
        data.get("entries")
        or data.get("orderedDataStoreEntries")
        or data.get("data")
        or []
    )

    players = []

    for entry in entries:
        user_id = entry.get("id")

        if not user_id and entry.get("path"):
            user_id = entry["path"].split("/")[-1]

        value = entry.get("value", 0)

        if isinstance(value, dict):
            value = value.get("value", 0)

        try:
            user_id = int(user_id)
            kills = int(value)
        except (TypeError, ValueError):
            continue

        if kills < 0:
            continue

        players.append({
            "user_id": user_id,
            "kills": kills
        })

    return players[:10]


def get_username(user_id):
    if user_id in username_cache:
        return username_cache[user_id]

    try:
        response = requests.get(
            f"https://users.roblox.com/v1/users/{user_id}",
            timeout=15
        )

        response.raise_for_status()
        name = response.json().get("name", f"Gracz {user_id}")

    except Exception:
        name = f"Gracz {user_id}"

    username_cache[user_id] = name
    return name


async def create_leaderboard_embed():
    players = await asyncio.to_thread(get_top_players)

    embed = discord.Embed(
        title="GUD PVP | TOP 10 ZABÓJSTW",
        description="**Najlepsi gracze na serwerze!**",
        color=discord.Color.blurple()
    )

    if not players:
        embed.add_field(
            name="Ranking",
            value="Brak zapisanych wyników.",
            inline=False
        )
    else:
        lines = []

        medals = ["🥇", "🥈", "🥉"]

        for index, player in enumerate(players):
            name = await asyncio.to_thread(
                get_username,
                player["user_id"]
            )

            if index < 3:
                position = medals[index]
            else:
                position = f"`{index + 1}.`"

            lines.append(
                f"{position} **{name}** — "
                f"`{player['kills']}` zabójstw"
            )

        embed.add_field(
            name="🏆 Ranking graczy",
            value="\n".join(lines),
            inline=False
        )

    embed.set_footer(
        text=MARKER + " • Aktualizacja co 10 minut"
    )

    return embed


async def update_leaderboard():
    channel = bot.get_channel(DISCORD_CHANNEL_ID)

    if channel is None:
        channel = await bot.fetch_channel(DISCORD_CHANNEL_ID)

    embed = await create_leaderboard_embed()

    async for message in channel.history(limit=100):
        if (
            message.author.id == bot.user.id
            and message.embeds
            and message.embeds[0].footer.text
            and MARKER in message.embeds[0].footer.text
        ):
            await message.edit(embed=embed)
            print("Zaktualizowano istniejącą tabelę TOP 10!")
            return

    await channel.send(embed=embed)
    print("Utworzono wiadomość TOP 10!")


@tasks.loop(minutes=10)
async def leaderboard_loop():
    try:
        await update_leaderboard()
    except Exception as error:
        print("Błąd aktualizacji rankingu:", error)


@leaderboard_loop.before_loop
async def before_leaderboard():
    await bot.wait_until_ready()


@bot.event
async def on_ready():
    print(f"Zalogowano jako: {bot.user}")

    if not leaderboard_loop.is_running():
        try:
            await update_leaderboard()
        except Exception as error:
            print("Błąd pierwszej aktualizacji:", error)

        leaderboard_loop.start()


bot.run(MTU2NzU2ODQxNDc4MjkxODcwNg.GWOFH9._0jYTePgw-bps4f_wkeUdKEEV0h40Mdio51qdo)
