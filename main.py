import os
import time
import datetime
import json
import urllib.request
from dotenv import load_dotenv

from discord.ext import commands

load_dotenv()
TOKEN = os.getenv('DISCORD_TOKEN')
URL = os.getenv('AOC_URL')
COOKIE = os.getenv('AOC_COOKIE')

POLL_MINS = 15

players_cache = ()
def get_players():
    global players_cache
    now = time.time()
    debug_msg = "Got Leaderboard From Cache"
    if not players_cache or (now - players_cache[0]) > (60*POLL_MINS):
        debug_msg = "Got Leaderboard Fresh"
        req = urllib.request.Request(URL)
        req.add_header("Cookie", "session=" + COOKIE)

        resp = urllib.request.urlopen(req)
        page = resp.read()

        data = json.loads(page)
        #print(json.dumps(data, indent=4, sort_keys=True))

        players = [(data['members'][member]['name'],
                    data['members'][member]['local_score'],
                    data['members'][member]['stars'],
                    int(data['members'][member]['last_star_ts'])) for member in data['members']]
        for i, player in enumerate(players):
            if not player[0]:
                players[i] = ("Anon", player[1], player[2], player[3])
        players.sort(key=lambda tup: tup[1], reverse=True)
        players_cache = (now, players)
    print(debug_msg)
    return players_cache[1]



str_format = "{rank:2}) {name:{name_pad}} ({points:{points_len}}) {stars}* ({star_time})\n"

bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and is in the following channels:')
    for guild in bot.guilds:
        print("  ", guild.name)

@bot.command(name='leaderboard', help='Responds with the current leaderboard')
async def leaderboard(context, num_players: int = 20):
    if context.channel.name != 'advent-of-code':
        return
    print("Leaderboard requested")
    players = get_players()[:num_players]
    max_name_len = len(max(players, key=lambda t: len(t[0]))[0])
    max_stars_len = max(players, key=lambda t: t[2])[2]
    max_points_len = len(str((max(players, key=lambda t: len(str(t[1])))[1])))

    result = '```'
    for i, player in enumerate(players):
        result += str_format.format(rank=i+1,
                                    name=player[0], name_pad=max_name_len,
                                    points=player[1], points_len=max_points_len,
                                    stars=player[2],
                                    star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
    result += '```'
    if len(result) > 2000: # Can fix this by splitting up the results into ~2000 char blocks (including the ```), then calling context.send many times
        result = 'Whoops, it looks like that leaderboard won\'t fit in one message, please reduce the number of rankings required'
    await context.send(result)


@bot.command(name='rank', help='Responds with the current ranking of the supplied player')
async def leaderboard(context, *name):
    if context.channel.name != 'advent-of-code':
        return
    player_name = ' '.join(name)

    print("Rank requested for: ", player_name)
    players = get_players()

    players = [(i, player) for i, player in enumerate(players) if player[0].upper() == player_name.upper()]
    if players:
        i, player = players[0]
        result = '```'
        result += str_format.format(rank=i+1,
                                    name=player[0], name_pad=len(player[0]),
                                    points=player[1], points_len=len(str(player[1])),
                                    stars=player[2],
                                    star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
        result += '```'
    else:
        result = 'Whoops, it looks like I can\'t find that player, are you sure they\'re playing?'
    await context.send(result)


@bot.command(name='keen', help='Responds with today\'s keenest bean')
async def keen(context):
    if context.channel.name != 'advent-of-code':
        return
    print("Keenest bean requested")

    # Get list of players with max stars
    all_players = get_players()
    max_stars = max(all_players, key=lambda t: t[2])[2]
    players = [(i, player) for i, player in enumerate(all_players) if player[2] == max_stars]

    # Get first person who got the max stars
    i, player = min(players, key=lambda t: t[1][3])

    result = 'Today\'s keenest bean is:\n```'
    result += str_format.format(rank=i+1,
                                name=player[0], name_pad=len(player[0]),
                                points=player[1], points_len=len(str(player[1])),
                                stars=player[2],
                                star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
    result += '```'
    await context.send(result)

bot.run(TOKEN)

