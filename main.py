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

# Advent Of Code request that you don't poll their API more often than once every 15 minutes
POLL_MINS = 15

# Discord messages are limited to 2000 characters. This also includes space for 6 '`' characters for a code block
MAX_MESSAGE_LEN = 2000 - 6

PLAYER_STR_FORMAT = '{rank:2}) {name:{name_pad}} ({points:{points_pad}}) {stars:{stars_pad}}* ({star_time})\n'
PLAYER_STR_FORMAT_NOPOINTS = '{rank:2}) {name:{name_pad}} {stars:{stars_pad}}* ({star_time})\n'

CHANNEL_NAME = 'advent-of-code'

players_cache = ()


def get_players():
    global players_cache
    now = time.time()
    debug_msg = 'Got Leaderboard From Cache'

    # If the cache is more than POLL_MINS old, refresh the cache, else use the cache
    if not players_cache or (now - players_cache[0]) > (60*POLL_MINS):
        debug_msg = 'Got Leaderboard Fresh'

        req = urllib.request.Request(URL)
        req.add_header('Cookie', 'session=' + COOKIE)
        page = urllib.request.urlopen(req).read()

        data = json.loads(page)
        # print(json.dumps(data, indent=4, sort_keys=True))

        # Extract the data from the JSON, it's a mess
        players = [(member['name'],
                    member['local_score'],
                    member['stars'],
                    int(member['last_star_ts']),
                    member['completion_day_level'],
                    member['id']) for member in data['members'].values()]

        # Players that are anonymous have no name in the JSON, so give them a default name "Anon"
        for i, player in enumerate(players):
            if not player[0]:
                anon_name = "anon #" + player[5]
                players[i] = (anon_name, player[1], player[2], player[3], player[4], player[5])

        # Sort the table primarily by score, secondly by stars and finally by timestamp
        players.sort(key=lambda tup: tup[3])
        players.sort(key=lambda tup: tup[2], reverse=True)
        players.sort(key=lambda tup: tup[1], reverse=True)
        players_cache = (now, players)

    print(debug_msg)
    return players_cache[1]


async def output_leaderboard(context, leaderboard_lst):
    item_len = len(leaderboard_lst[0])
    block_size = MAX_MESSAGE_LEN // item_len

    tmp_leaderboard = leaderboard_lst

    while (len(tmp_leaderboard) * item_len) > MAX_MESSAGE_LEN:
        output_str = '```'
        output_str += ''.join(tmp_leaderboard[:block_size])
        output_str += '```'
        await context.send(output_str)
        tmp_leaderboard = tmp_leaderboard[block_size:]
    output_str = '```'
    output_str += ''.join(tmp_leaderboard)
    output_str += '```'
    await context.send(output_str)


# Create the bot and specify to only look for messages starting with '!'
bot = commands.Bot(command_prefix='!')


@bot.event
async def on_ready():
    print(f'{bot.user.name} has connected to Discord and is in the following channels:')
    for guild in bot.guilds:
        print('  ', guild.name)


@bot.command(name='leaderboard', help='Responds with the current leaderboard')
async def leaderboard(context, num_players: int = 20):
    # Only respond if used in a channel containing CHANNEL_NAME
    if CHANNEL_NAME not in context.channel.name:
        return

    print('Leaderboard requested')
    players = get_players()[:num_players]

    # Get string lengths for the format string
    max_name_len = len(max(players, key=lambda t: len(t[0]))[0])
    max_points_len = len(str(max(players, key=lambda t: t[1])[1]))
    max_stars_len = len(str(max(players, key=lambda t: t[2])[2]))

    leaderboard = []
    for i, player in enumerate(players):
        leaderboard.append(PLAYER_STR_FORMAT.format(rank=i+1,
                                                    name=player[0], name_pad=max_name_len,
                                                    points=player[1], points_pad=max_points_len,
                                                    stars=player[2], stars_pad=max_stars_len,
                                                    star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3]))))

    await output_leaderboard(context, leaderboard)


@bot.command(name='rank', help='Responds with the current ranking of the supplied player')
async def rank(context, *name):
    # Only respond if used in a channel containing CHANNEL_NAME
    if CHANNEL_NAME not in context.channel.name:
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
                                           stars=player[2], stars_pad=len(str(player[2])),
                                           star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
        result += '```'
    else:
        result = 'Whoops, it looks like I can\'t find that player, are you sure they\'re playing?'
    await context.send(result)


@bot.command(name='keen', help='Responds with today\'s keenest bean')
async def keen(context):
    # Only respond if used in a channel containing CHANNEL_NAME
    if CHANNEL_NAME not in context.channel.name:
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
                                       stars=player[2], stars_pad=len(str(player[2])),
                                       star_time=time.strftime('%H:%M %d/%m', time.localtime(player[3])))
    result += '```'
    await context.send(result)


@bot.command(name='daily', help='Will give the daily leaderboard for specified day')
async def daily(context, day: str = None):
    # The default day calculation cannot be in the function default value because the default
    # value is evaluated when the program is started, not when the function is called
    if day is None:
        # The default day is whatever day's challenge has just come out
        # So at 4.59AM UTC it will still show previous day's leaderboard
        day = str((datetime.datetime.today() - datetime.timedelta(hours=5)).day)

    # Only respond if used in a channel containing CHANNEL_NAME
    if CHANNEL_NAME not in context.channel.name:
        return

    print("Daily leaderboard requested for day:", day)
    players = get_players()

    # Goes through all the players checking if they have data for that day and if they do adding to players_days
    players_day = [player for player in players if day in player[4]]

    # Players_day has all people who have finished one star for that day
    first_star = []
    second_star = []

    # Adds all the players which has stars the into respective lists
    for player_day in players_day:
        if '1' in player_day[4][day]:
            first_star.append((player_day[0], int(player_day[4][day]['1']['get_star_ts'])))
        if '2' in player_day[4][day]:
            second_star.append((player_day[0], int(player_day[4][day]['2']['get_star_ts'])))

    # Sorts the two lists on timestamps
    first_star.sort(key=lambda data: data[1])
    second_star.sort(key=lambda data: data[1])

    final_table = []

    # Adds all the people from first list
    for i, player in enumerate(first_star):
        final_table.append((player[0], (len(players) - i), player[1], 1))

    # Updates the list with all the people who got the second star and their score
    for i, player in enumerate(second_star):
        index = [i for i, item in enumerate(final_table) if item[0] == player[0]][0]
        to_change = final_table[index]
        final_table[index] = (to_change[0], (to_change[1] + (len(players) - i)), player[1], 2)

    # Sorts the table primarily by score, and secondly by timestamp
    final_table.sort(key=lambda data: data[2])
    final_table.sort(reverse=True, key=lambda data: data[1])

    # Outputs data
    if not final_table:
        result = "```No Scores for this day yet```"
        await context.send(result)
    else:
        # Get string lengths for the format string
        max_name_len = len(max(final_table, key=lambda t: len(t[0]))[0])
        max_points_len = len(str(max(final_table, key=lambda t: t[1])[1]))
        max_stars_len = len(str(max(final_table, key=lambda t: t[3])[3]))
        leaderboard = []
        for place, player in enumerate(final_table):
            leaderboard.append(PLAYER_STR_FORMAT.format(rank=place+1,
                                                        name=player[0], name_pad=max_name_len,
                                                        points=player[1], points_pad=max_points_len,
                                                        stars=player[3], stars_pad=max_stars_len,
                                                        star_time=time.strftime('%H:%M %d/%m',
                                                                                time.localtime(player[2]))))
        await output_leaderboard(context, leaderboard)


@bot.command(name='stars', help='Will give the time of completion of each star for specified day')
async def daily(context, day: str = None):
    # The default day calculation cannot be in the function default value because the default
    # value is evaluated when the program is started, not when the function is called
    if day is None:
        # The default day is whatever day's challenge has just come out
        # So at 4.59AM UTC it will still show previous day's leaderboard
        day = str((datetime.datetime.today() - datetime.timedelta(hours=5)).day)

    # Only respond if used in a channel containing CHANNEL_NAME
    if CHANNEL_NAME not in context.channel.name:
        return

    print("Star time leaderboard requested for day:", day)
    players = get_players()

    # Goes through all the players checking if they have data for that day and if they do adding to players_days
    players_day = [player for player in players if day in player[4]]

    # Players_day has all people who have finished one star for that day
    stars = []

    # Adds all stars achieved to the stars list
    for player_day in players_day:
        if '1' in player_day[4][day]:
            stars.append((player_day[0], int(player_day[4][day]['1']['get_star_ts']), '1'))
        if '2' in player_day[4][day]:
            stars.append((player_day[0], int(player_day[4][day]['2']['get_star_ts']), '2'))

    # Sorts the list on timestamps
    stars.sort(key=lambda data: data[1])

    final_table = []

    # Adds all the stars to the final list
    for i, player in enumerate(stars):
        final_table.append((player[0], (len(stars) - i), player[1], player[2]))

    # Sorts the table by timestamp
    final_table.sort(key=lambda data: data[2])

    # Outputs data
    if not final_table:
        result = "```No Scores for this day yet```"
        await context.send(result)
    else:
        # Get string lengths for the format string
        max_name_len = len(max(final_table, key=lambda t: len(t[0]))[0])
        max_points_len = len(str(max(final_table, key=lambda t: t[1])[1]))
        max_stars_len = len(str(max(final_table, key=lambda t: t[3])[3]))
        leaderboard = []
        for place, player in enumerate(final_table):
            leaderboard.append(PLAYER_STR_FORMAT_NOPOINTS.format(rank=place+1,
                                                                 name=player[0], name_pad=max_name_len,
                                                                 points=player[1], points_pad=max_points_len,
                                                                 stars=player[3], stars_pad=max_stars_len,
                                                                 star_time=time.strftime('%H:%M %d/%m',
                                                                                         time.localtime(player[2]))))
        await output_leaderboard(context, leaderboard)


bot.run(TOKEN)
