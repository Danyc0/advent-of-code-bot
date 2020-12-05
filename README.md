# advent-of-code-bot
A simple Discord bot for Advent Of Code

## Dependencies
    pip install -U Discord.py python-dotenv

## Setup

You'll need to create a discord bot of your own in the [Discord Developer Portal](https://discord.com/developers/applications) with View Channels and Read Messages permissions. It's also handy if you have an empty server (or "guild") for you to test in. This section of [this guide](https://realpython.com/how-to-make-a-discord-bot-python/#how-to-make-a-discord-bot-in-the-developer-portal) may be helpful to set that up.

You'll need to set three environment variables:
* DISCORD TOKEN -> The Discord token for the bot you created (Available on your bot page in the developer portal)
* AOC_URL -> The JSON url for your or Advent Of Code private leaderboard (Available by clicking "API" then "JSON" on your private leaderboard page)
* AOC_COOKIE -> Your Advent Of Code session cookie so the bot has permission to view your private leaderboard (You can extract this from your web browser after signing in to AoC)

You can put these in a .env file in the repo directory as it uses dotenv (See [here](https://pypi.org/project/python-dotenv/) for usage) so you don't have to keep them in your environment
