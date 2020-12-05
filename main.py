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
PLAYER_STR_FORMAT = '{rank:2}) {name:{name_pad}} ({points:{points_pad}}) {stars}* ({star_time})\n'


players_cache = ()
def get_players():
    global players_cache
    now = time.time()
    debug_msg = 'Got Leaderboard From Cache'

    # If the cache is more than POLL_MINS old, get refresh the cache, else use the cache
    if not players_cache or (now - players_cache[0]) > (60*POLL_MINS):
        debug_msg = 'Got Leaderboard Fresh'

        req = urllib.request.Request(URL)
        req.add_header('Cookie', 'session=' + COOKIE)
        page = urllib.request.urlopen(req).read()

        data = json.loads(page)
        #print(json.dumps(data, indent=4, sort_keys=True))

        # Extract the data from the JSON, it's a mess
        players = [(data['members'][member]['name'],
                    data['members'][member]['local_score'],
                    data['members'][member]['stars'],
                    int(data['members'][member]['last_star_ts'])) for member in data['members']]

        # Players that are anonymous have no name in the JSON, so give them a default name "Anon"
        for i, player in enumerate(players):
            if not player[0]:
                players[i] = ('Anon', player[1], player[2], player[3])

        players.sort(key=lambda tup: tup[1], reverse=True)
        players_cache = (now, players)

    print(debug_msg)
    return players_cache[1]


# Create the bot and specify to only look for messages starting with '!'
bot = commands.Bot(command_prefix='!')

@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and is in the following channels:')
    for guild in bot.guilds:
        print('  ', guild.name)


@bot.command(name='leaderboard', help='Responds with the current leaderboard')
async def leaderboard(context, num_players: int = 20):
    # Only respond if used in a channel called 'advent-of-code'
    if context.channel.name != 'advent-of-code':
        return

    print('Leaderboard requested')
    players = get_players()[:num_players]

    # Get string lengths for the format string
    max_name_len = len(max(players, key=lambda t: len(t[0]))[0])
    max_stars_len = max(players, key=lambda t: t[2])[2]
    max_points_len = len(str((max(players, key=lambda t: len(str(t[1])))[1])))

    # Create the leaderboard string
    result = '```'
    for i, player in enumerate(players):
        result += PLAYER_STR_FORMAT.format(rank=i+1,
                                           name=player[0], name_pad=max_name_len,
                                           points=player[1], points_pad=max_points_len,
                                           stars=player[2],
                                           star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
    result += '```'

    # Discord messages can't be over 2000 characters, so put a limit in for that
    if len(result) > 2000: # Can fix this by splitting up the results into ~2000 char blocks (including the ```), then calling context.send many times
        result = 'Whoops, it looks like that leaderboard won\'t fit in one message, please reduce the number of rankings required'
    await context.send(result)


@bot.command(name='rank', help='Responds with the current ranking of the supplied player')
async def rank(context, *name):
    # Only respond if used in a channel called 'advent-of-code'
    if context.channel.name != 'advent-of-code':
        return

    # Join together all passed parameters with a space, this allows users to enter names with spaces
    player_name = ' '.join(name)

    print('Rank requested for: ', player_name)
    players = get_players()
    
    # Get the player with the matching name (case insensitive)
    players = [(i, player) for i, player in enumerate(players) if player[0].upper() == player_name.upper()]
    if players:
        # Assume there was only one match
        i, player = players[0]
        result = '```'
        result += PLAYER_STR_FORMAT.format(rank=i+1,
                                           name=player[0], name_pad=len(player[0]),
                                           points=player[1], points_pad=len(str(player[1])),
                                           stars=player[2],
                                           star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
        result += '```'
    else:
        result = 'Whoops, it looks like I can\'t find that player, are you sure they\'re playing?'
    await context.send(result)


@bot.command(name='keen', help='Responds with today\'s keenest bean')
async def keen(context):
    # Only respond if used in a channel called 'advent-of-code'
    if context.channel.name != 'advent-of-code':
        return
    print('Keenest bean requested')

    all_players = get_players()
    # Calculate the highest number of stars gained by anyone in the leaderboard
    max_stars = max(all_players, key=lambda t: t[2])[2]
    # Get list of players with max stars
    players = [(i, player) for i, player in enumerate(all_players) if player[2] == max_stars]

    # Find the first person who got the max stars
    i, player = min(players, key=lambda t: t[1][3])

    result = 'Today\'s keenest bean is:\n```'
    result += PLAYER_STR_FORMAT.format(rank=i+1,
                                       name=player[0], name_pad=len(player[0]),
                                       points=player[1], points_pad=len(str(player[1])),
                                       stars=player[2],
                                       star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
    result += '```'
    await context.send(result)


bot.run(TOKEN)

