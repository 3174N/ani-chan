"""
Anilist discord bot.
"""

###########
# IMPORTS #
###########

import json
import os
from dotenv import load_dotenv
import requests
from discord.ext import commands
import discord
import markdownify
from queries import *

#############
# VARIABLES #
#############

COLOR_DEFAULT = discord.Color.teal()
COLOR_ERROR = discord.Color.red()


users = {}


#############
# FUNCTIONS #
#############


def string_to_hex(color):
    """Converts a color name to color string.

    Keyword arguments:
      color -- Color name.
    """
    if color == "blue":
        return discord.Color.blue()
    if color == "purple":
        return discord.Color.purple()
    if color == "pink":
        return discord.Color.magenta()
    if color == "orange":
        return discord.Color.orange()
    if color == "red":
        return discord.Color.red()
    if color == "green":
        return discord.Color.green()
    if color == "gray":
        return discord.Color.light_gray()


def load_users():
    """Loads users from users file."""
    global users
    with open("./users.json", "r") as file:
        if file.read != "":
            users = json.loads(file.read())


def clear_users():
    """Deletes all users."""
    open("./users.json", "w").close()  # Clear file
    load_users()


def get_user(name):
    """Gets a user from AniList.

    Keyword arguments:
      name -- User's name.
    """
    try:
        # Try to find user by id.
        response = requests.post(
            URL, json={"query": QUERY_USER_ID, "variables": {"id": int(name)}}
        )

        if response.json()["data"]["User"]:
            return response.json()["data"]["User"]
    except:
        pass

    # Find user by name.
    response = requests.post(
        URL, json={"query": QUERY_USER, "variables": {"search": name}}
    )

    if response.json()["data"]["User"]:
        return response.json()["data"]["User"]

    return None


def add_user(id, name):
    """Adds a user to the user list.

    Keyword arguments:
      id -- User's ID.
      name -- AniList user name.
    """
    user_data = get_user(name)

    if user_data is not None:
        users[str(id)] = {"name": user_data["name"], "id": user_data["id"]}

        with open("./users.json", "w") as file:
            file.write(json.dumps(users))

        load_users()

        return True
    return False


def get_media(name, type):
    """Gets a media from AniList.

    Keyword arguments:
      name -- Media name.
      type -- Media type.
    """
    try:
        # Find media by ID.
        response = requests.post(
            URL,
            json={
                "query": QUERY_MEDIA_ID % type.upper(),
                "variables": {"id": int(name)},
            },
        )

        if response.json()["data"]["Media"] is not None:
            return response.json()["data"]["Media"]
    except:
        pass

    # Find media by name.
    response = requests.post(
        URL, json={"query": QUERY_MEDIA %
                   type.upper(), "variables": {"search": name}}
    )

    if response.json()["data"]["Media"] is not None:
        return response.json()["data"]["Media"]

    return None


def get_character(name):
    """Gets a character from AniList.

    Keyword arguments:
      name -- Character name.
    """
    try:
        # Find character by ID.
        response = requests.post(
            URL, json={"query": QUERY_CHARACTER_ID,
                       "variables": {"id": int(name)}}
        )

        if response.json()["data"]["Character"] is not None:
            return response.json()["data"]["Character"]
    except:
        pass

    # Find character by name.
    response = requests.post(
        URL, json={"query": QUERY_CHARACTER, "variables": {"search": name}}
    )

    if response.json()["data"]["Character"] is not None:
        return response.json()["data"]["Character"]

    return None


def search_media(name, media_type=None):
    """Searches a media on AniList.

    Keyword arguments:
      name -- Search query.
      media_type -- Media type.
    """
    variables = {
        "search": name,
        "page": 1,
        "perPage": 25,
    }
    if media_type is not None:
        response = requests.post(
            URL,
            json={
                "query": QUERY_SEARCH_MEDIA_TYPE % media_type.upper(),
                "variables": variables,
            },
        )
    else:
        response = requests.post(
            URL, json={"query": QUERY_SEARCH_MEDIA, "variables": variables}
        )

    return response.json()["data"]["Page"]


def search_character(name):
    """Searches a character on AniList.

    Keyword arguments:
      name -- Search query.
    """
    variables = {
        "search": name,
        "page": 1,
        "perPage": 25,
    }

    response = requests.post(
        URL, json={"query": QUERY_SEARCH_CHARACTER, "variables": variables}
    )

    return response.json()["data"]["Page"]


def search_user(name):
    """Searches a user on AniList.

    Keyword arguments:
      name -- Search query.
    """
    variables = {
        "search": name,
        "page": 1,
        "perPage": 25,
    }

    response = requests.post(
        URL, json={"query": QUERY_SEARCH_USER, "variables": variables}
    )

    return response.json()["data"]["Page"]


def get_user_score(userId, mediaId):
    """Gets a user score on a specific media.

    Keyword arguments:
      userId -- User ID.
      mediaId -- Media ID.
    """
    variables = {"userId": userId, "mediaId": mediaId}
    response = requests.post(
        URL, json={"query": QUERY_MEDIALIST, "variables": variables}
    )

    return response.json()["data"]["MediaList"]


def get_users_statuses(mediaId):
    """Gets the statuses / scores of all the connected users on a specific media.

    Keyword arguments:
    mediaId -- Media ID.
    """
    # FIXME: Find a way to speed up queries.
    result = {}

    query = """
query ($mediaId: Int) {
    %s
}"""
    media_query = """
    %s: MediaList(userId: %s, mediaId: $mediaId) {
        status,
        score (format: POINT_100),
        progress,
    },"""
    media_query_combined = ""

    for user in users:
        value = users[user]
        media_query_combined += media_query % ("_" +
                                               value["name"], str(value["id"]))

    query = query % media_query_combined
    print(query)
    print(mediaId)

    variables = {"mediaId": mediaId}
    response = requests.post(
        URL, json={"query": query, "variables": variables})
    print(response.text)

    for user in users:
        value = users[user]
        score = get_user_score(value["id"], mediaId)
        if score is not None:
            if score["status"] == "PAUSED":
                score["status"] = "CURRENT"

            if score["status"] == "COMPLETED":
                status = f'{value["name"]} **({score["score"]})**'
            elif score["status"] == "CURRENT":
                status = f'{value["name"]} [{score["progress"]}]'
            else:
                status = value["name"]

            if score["status"] in result:
                result[score["status"]].append(status)
            else:
                result[score["status"]] = [status]
        else:
            if "NOT ON LIST" in result:
                result["NOT ON LIST"].append(value["name"])
            else:
                result["NOT ON LIST"] = [value["name"]]

    result_sort = {}
    if "COMPLETED" in result:
        result_sort["COMPLETED"] = result["COMPLETED"]
    if "CURRENT" in result:
        result_sort["CURRENT"] = result["CURRENT"]
    if "DROPPED" in result:
        result_sort["DROPPED"] = result["DROPPED"]
    if "PLANNING" in result:
        result_sort["PLANNING"] = result["PLANNING"]
    if "NOT ON LIST" in result:
        result_sort["NOT ON LIST"] = result["NOT ON LIST"]
    return result_sort


def bot_get_media(media_type, name):
    """Gets a media from AniList and generates an embeded message.

    Keyword arguments:
      media_type -- Media type.
      name -- Media name.
    """
    media = get_media(name, media_type)
    if media is None:
        embed = discord.Embed(
            title="Not Found", description="):", color=COLOR_DEFAULT)
    else:
        # user_scores = await get_users_statuses(media['id'])

        if media["season"] is not None:
            media["season"] = f'{media["season"].capitalize()} {media["seasonYear"]}'

        # Replace 'None' with '?'
        for i in media:
            if media[i] is None:
                media[i] = "?"

        if media["title"]["english"] is None:
            media["title"]["english"] = media["title"]["romaji"]

        if not media["genres"]:
            media["genres"] = ["?"]

        # Shorten description
        if len(media["description"]) >= 1024:
            media["description"] = media["description"][:1020] + "..."
        media["description"] = markdownify.markdownify(media["description"])

        embed = discord.Embed(
            title=media["title"]["english"],
            url=media["siteUrl"],
            description=f'{media["title"]["native"]} - '
            + f'{media["title"]["romaji"]}\n\n',
            color=COLOR_DEFAULT,
        )
        embed.set_thumbnail(url=media["coverImage"]["extraLarge"])
        embed.add_field(name="Mean Score", value=media["meanScore"])
        embed.add_field(name="Type", value=media["type"].capitalize())
        embed.add_field(name="Status", value=media["status"].capitalize())
        embed.add_field(name="Season", value=media["season"])
        embed.add_field(name="Popularity", value=media["popularity"])
        embed.add_field(name="Favourited",
                        value=f'{media["favourites"]} times')
        if media_type.lower() == "anime":
            embed.add_field(name="Episodes", value=media["episodes"])
            embed.add_field(
                name="Duration", value=f'{media["duration"]} minutes per episode'
            )
        else:
            embed.add_field(name="Chapters", value=media["chapters"])
            embed.add_field(name="Volumes", value=media["volumes"])
        embed.add_field(name="Format", value=media["format"])
        embed.add_field(
            name="Genres", value=" - ".join(media["genres"]), inline=False)
        embed.add_field(name="Description",
                        value=media["description"], inline=False)

        embed.add_field(name="User Scores", value="Soon™")
        # for status in user_scores:
        #     embed.add_field(name=status, value=' | '.join(user_scores[status]),
        # inline=False)
    return embed


load_dotenv()
prefix = os.getenv("PREFIX")
bot_channel = int(os.getenv("CHANNEL"))

bot = commands.Bot(command_prefix=prefix, help_command=None)


@bot.event
async def on_ready():
    """Gets called when the bot goes online."""
    print("We have logged in as {0.user}".format(bot))
    load_users()


@bot.command(
    name="help", description="Displays this message.", help=prefix + "help (command)"
)
async def help(ctx, help_command=""):
    """Shows help.

    Keyword arguments:
      ctx -- context.
      help_command -- Command to show help of.
    """
    if ctx.channel.id != bot_channel:
        return

    help_text = {}

    if help_command == "":
        embed = discord.Embed(title="Help", color=COLOR_DEFAULT)
        categories = []
        for command in bot.commands:
            if command.cog.__class__.__name__ not in categories:
                categories.append(command.cog.__class__.__name__)

        for category in categories:
            help_text[category] = ""
            for command in bot.commands:
                if command.cog.__class__.__name__ == category:
                    help_text[category] += f"`{command}` - {command.description}\n"

        for category in categories:
            if category == "NoneType":
                embed.add_field(
                    name="Commands", value=help_text[category], inline=False
                )
            else:
                embed.add_field(
                    name=category, value=help_text[category], inline=False)

        help_text = f"\nPrefix: `{prefix}`"
        help_text += f"\nUse `{prefix}help [command]` to get more info on the command."
        embed.add_field(name="Info", value=help_text, inline=False)
    else:
        is_command = False
        for command in bot.commands:
            if command.name == help_command:
                embed = discord.Embed(
                    title=command.name,
                    description=command.description,
                    color=COLOR_DEFAULT,
                )
                embed.add_field(name="Usage", value=f"```{command.help}```")
                is_command = True
                break

        if not is_command:
            embed = discord.Embed(
                title=help_command,
                description=f"`{help_command}` is not a command.",
                color=COLOR_DEFAULT,
            )

    await ctx.send(embed=embed)


@bot.command(
    name="anime",
    description="Search for a specific anime using its name.",
    help=prefix + "anime [name]",
)
async def anime(ctx, *name):
    """Shows an anime from AniList.

    Keyword arguments:
      ctx -- Context.
      *name -- Anime name.
    """
    if ctx.channel.id != bot_channel:
        return

    if not name:
        embed = discord.Embed(
            title="Incorrect usage",
            description=f"Usage: `{prefix}anime [name]`",
            color=COLOR_ERROR,
        )
    else:
        embed = bot_get_media("anime", " ".join(name))
    await ctx.send(embed=embed)


@bot.command(
    name="manga",
    description="Search for a specific manga using its name.",
    help=prefix + "manga [name]",
)
async def manga(ctx, *name):
    """Shows a manga from AniList.

    Keyword arguments:
      ctx -- Context
      *name -- Manga name.
    """
    if ctx.channel.id != bot_channel:
        return

    if not name:
        embed = discord.Embed(
            title="Incorrect usage",
            description=f"Usage: `{prefix}manga [name]`",
            color=COLOR_ERROR,
        )
    else:
        embed = bot_get_media("manga", " ".join(name))
    await ctx.send(embed=embed)


@bot.command(
    name="user",
    description="Search for a specific username.",
    help=prefix + "user <user|mention>",
)
async def user(ctx, name=None):
    """Shows a user from AniList.

    Keyword arguments:
      ctx -- Context.
      name -- User's name.
    """
    if ctx.channel.id != bot_channel:
        return

    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    if name is None:
        name = users[str(ctx.message.author.id)]["name"]

    user_data = get_user(name)

    if user_data is not None:
        embed = discord.Embed(
            title=user_data["name"] + " - Anilist Statistics",
            url=user_data["siteUrl"],
            color=string_to_hex(user_data["options"]["profileColor"]),
        )
        embed.set_thumbnail(url=user_data["avatar"]["large"])
        if user_data["bannerImage"] is not None:
            embed.set_image(url=user_data["bannerImage"])
        if user_data["about"] is not None:
            embed.add_field(name="About", value=user_data["about"])

        stats_anime = user_data["statistics"]["anime"]
        if stats_anime["formats"] != []:
            stats_anime["format"] = stats_anime["formats"][0]["format"]
        else:
            stats_anime["format"] = "Unknown"
        if stats_anime["genres"] != []:
            genres = []
            for i in stats_anime["genres"]:
                genres.append(i["genre"])
            stats_anime["genres"] = " / ".join(genres)
        else:
            stats_anime["genres"] = "Unknown"
        anime_stats_str = (
            f'- Total Entries: **{stats_anime["count"]}**\n'
            + f'- Mean Score: **{stats_anime["meanScore"]}**\n'
            + f'- Episodes Watched: **{stats_anime["episodesWatched"]}**\n'
            + f'- Minutes Watched: **{stats_anime["minutesWatched"]}**\n'
            + f'- Favorite Format: **{stats_anime["format"]}**\n'
            + f'- Favorite Genres: **{stats_anime["genres"]}**\n'
        )
        stats_manga = user_data["statistics"]["manga"]
        if stats_manga["formats"] != []:
            stats_manga["format"] = stats_manga["formats"][0]["format"]
        else:
            stats_manga["format"] = "Unknown"
        if stats_manga["genres"] != []:
            genres = []
            for i in stats_manga["genres"]:
                genres.append(i["genre"])
            stats_manga["genres"] = " / ".join(genres)
        else:
            stats_manga["genres"] = "Unknown"
        manga_stats_str = (
            f'- Total Entries: **{stats_manga["count"]}**\n'
            + f'- Mean Score: **{stats_manga["meanScore"]}**\n'
            + f'- Volumes Read: **{stats_manga["volumesRead"]}**\n'
            + f'- Chapters Read: **{stats_manga["chaptersRead"]}**\n'
            + f'- Favorite Format: **{stats_manga["format"]}**\n'
            + f'- Favorite Genres: **{stats_manga["genres"]}**\n'
        )

        embed.add_field(name="Anime Statistics",
                        value=anime_stats_str, inline=False)
        embed.add_field(name="Manga Statistics",
                        value=manga_stats_str, inline=False)
    else:
        embed = discord.Embed(
            title="Not Found", description="):", color=COLOR_DEFAULT)

    await ctx.send(embed=embed)


@bot.command(
    name="link",
    description="Links your discord account to an anilist user.",
    help=prefix + "link [name]",
)
async def link(ctx, name=None):
    """Links a user to AniList account.

    Keyword arguments:
      ctx -- Context.
      name -- AniList user's name.
    """
    if ctx.channel.id != bot_channel:
        return

    if name is None:
        embed = discord.Embed(
            title="Incorrect usage",
            description=f"Usage: `{prefix}link [name]`",
            color=COLOR_ERROR,
        )
        await ctx.send(embed=embed)
        return

    found_user = get_user(name)
    for _user in users:
        if users[_user]["name"] == found_user["name"]:
            await ctx.send("User taken.")
            return

    if add_user(ctx.message.author.id, name):
        await user(ctx, name)
        await ctx.send("Linked successfully")
    else:
        await ctx.channel.send("Not Found")


@bot.command(
    name="unlink",
    description="Removes the link between your discord account and an anilist user.",
    help=prefix + "unlink",
)
async def unlink(ctx):
    """Unlikes a user from linked AniList account.

    Keyword arguments:
      ctx -- Context.
    """
    if ctx.channel.id != bot_channel:
        return

    del users[str(ctx.message.author.id)]

    with open("./users.json", "w") as file:
        file.write(json.dumps(users))

    load_users()

    embed = discord.Embed(
        title="User unlinked successfuly", description="Hurrah!", color=COLOR_DEFAULT
    )
    await ctx.send(embed=embed)


@bot.command(
    name="users", description="Shows all users currently linked.", help=prefix + "users"
)
async def show_users(ctx):
    """Show all connected users.

    Keyword arguments:
      ctx -- Context.
    """
    if ctx.channel.id != bot_channel:
        return

    result = []
    for i in users:
        result.append(users[i]["name"])
    await ctx.send(f'```Total linked users: {len(users)}\n{" | ".join(result)}```')


@bot.command(
    name="top",
    description="Shows the top 10 of another user.",
    help=prefix + "top [name|mention]",
)
async def top(ctx, name=None):
    """Shows a user's top media.

    Keyword arguments:
      ctx -- Context.
      name -- User's name.
    """
    if ctx.channel.id != bot_channel:
        return

    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    if name is None:
        try:
            name = users[str(ctx.message.author.id)]["name"]
        except:
            name = " "

    user_data = get_user(name)
    if user_data is not None:
        variables = {"userId": user_data["id"], "page": 1, "perPage": 10}

        response = requests.post(
            URL, json={"query": QUERY_TOP_MEDIA, "variables": variables}
        )
        media_list = response.json()["data"]["Page"]["mediaList"]

        description = ""
        for media in media_list:
            if media["media"]["title"]["english"] is None:
                media["media"]["title"]["english"] = media["media"]["title"]["romaji"]
            description += (
                f'{media["media"]["title"]["english"]} - ' +
                f'**{media["score"]}**\n'
            )

        embed = discord.Embed(
            title=f"{name}'s top 10",
            description=description,
            color=string_to_hex(user_data["options"]["profileColor"]),
        )
        embed.set_thumbnail(url=user_data["avatar"]["large"])
    else:
        embed = discord.Embed(
            title="Not Found", description="):", color=COLOR_DEFAULT)

    await ctx.send(embed=embed)


@bot.command(
    name="search",
    description="Search for specific information. shows all results.",
    help=prefix + "search [media|anime|manga|character|user] [name]",
)
async def search(ctx, search_type=None, *search_string):
    """Searches for media/character/user on AniList.

    Keyword arguments:
      ctx -- Context.
      search_type -- Search type.
      *search_string -- Search query.
    """
    if ctx.channel.id != bot_channel:
        return

    search_string = " ".join(search_string)

    result = ""
    if search_type is None or not search_string:
        result = "Usage: 'search [anime|manga|character|media|user] [name]'"

    elif search_type.lower() in ("media", "anime", "manga"):
        if search_type.lower() == "media":
            medias = search_media(search_string)
        elif search_type.lower() in ("anime", "manga"):
            medias = search_media(search_string, search_type)

        for media in medias["media"]:
            result += f'{media["type"].capitalize()} {media["id"]} - '

            if media["title"]["english"] is not None:
                result += media["title"]["english"]
            elif media["title"]["romaji"] is not None:
                result += media["title"]["romaji"]
            else:
                result += media["title"]["native"]

            result += "\n"
    elif search_type.lower() == "character":
        characters = search_character(search_string)

        for character in characters["characters"]:
            result += f'Character {character["id"]} - '

            if character["name"]["full"] is not None:
                result += character["name"]["full"]
            else:
                result += character["name"]["native"]

            result += "\n"
    elif search_type.lower() == "user":
        found_users = search_user(search_string)

        for user in found_users["users"]:
            result += f'User {user["id"]} - {user["name"]}\n'
    else:
        result = "Usage: 'search [anime|manga|character|media|user] [name]'"

    await ctx.send(f"```{result}```")


@bot.command(
    name="score",
    description="Shows a user's score for a specific media.",
    help=prefix + "score [user|mention] [name]",
)
async def score(ctx, name, *media_name):
    """Shows a user score/status for a specific media.

    Keyword arguments:
      ctx -- Context.
      name -- User's name.
      *media_name -- Media name.
    """
    if ctx.channel.id != bot_channel:
        return

    media_name = " ".join(media_name)

    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    user_data = get_user(name)
    media = get_media(media_name, "anime")
    media_manga = get_media(media_name, "manga")

    if user_data is not None and media is not None:
        score = get_user_score(user_data["id"], media["id"])
        if score is None:
            score = get_user_score(user_data["id"], media_manga["id"])
            media = media_manga
        if score is not None:
            embed = discord.Embed(
                title=f'{user_data["name"]}\'s score for {media["title"]["english"]}',
                color=string_to_hex(user_data["options"]["profileColor"]),
            )
            if score["status"] == "COMPLETED":
                embed.add_field(name="Score", value=score["score"])
                embed.add_field(name="Notes", value=score["notes"])
            else:
                if score["status"] == "CURRENT":
                    score["status"] = (
                        "Watching" if media["type"] == "ANIME" else "Reading"
                    )
                embed.add_field(
                    name="Status", value=score["status"].capitalize())
                embed.add_field(name="Progress", value=score["progress"])
            embed.set_thumbnail(url=user_data["avatar"]["large"])
        else:
            embed = discord.Embed(
                title="Not found.", description="):", color=COLOR_DEFAULT
            )
    else:
        embed = discord.Embed(title="Not found.",
                              description="):", color=COLOR_DEFAULT)
    await ctx.send(embed=embed)


@bot.command(
    name="character",
    description="Search for a specific character using its name.",
    help=prefix + "character [name]",
)
async def show_character(ctx, *name):
    """Shows a character from AniList.

    Keyword arguments:
      ctx -- Context.
      *name -- Character's name.
    """
    if ctx.channel.id != bot_channel:
        return

    character = get_character(" ".join(name))

    if character is not None:
        if len(character["description"]) >= 1024:
            character["description"] = character["description"][:1020] + "..."
        character["description"] = character["description"].replace("~!", "||")
        character["description"] = character["description"].replace("!~", "||")
        character["name"]["alternative"].append(character["name"]["native"])

        embed = discord.Embed(
            title=character["name"]["full"],
            description=character["description"],
            url=character["siteUrl"],
            color=COLOR_DEFAULT,
        )
        embed.set_thumbnail(url=character["image"]["large"])
        relations = " "
        for i in character["media"]["edges"]:
            if i["node"]["title"]["english"] is not None:
                relation = f'• [{i["node"]["title"]["english"]}]({i["node"]["siteUrl"]}) [{i["characterRole"].capitalize()}]\n'
            else:
                relation = f'• [{i["node"]["title"]["native"]}]({i["node"]["siteUrl"]}) [{i["characterRole"].capitalize()}]\n'

            if len(relations) + len(relation) >= 1024:
                break

            relations += relation

        embed.add_field(name="Relations", value=relations, inline=False)
        embed.add_field(
            name="Aliases",
            value=" - ".join(character["name"]["alternative"]),
            inline=False,
        )
        embed.add_field(name="Anilist ID", value=character["id"])
        embed.add_field(name="Favourites", value=character["favourites"])
    else:
        embed = discord.Embed(
            title="Incorrect usage",
            description=f"Usage: `{prefix}character [name]`",
            color=COLOR_ERROR,
        )

    await ctx.send(embed=embed)


bot.run(os.getenv("TOKEN"))
