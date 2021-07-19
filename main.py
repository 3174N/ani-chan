"""
Anilist discord bot.
"""

import json
import os
from dotenv import load_dotenv
import requests
import discord
import markdownify
from queries import *

DEFAULT_COLOR = discord.Color.teal()


users = {}


def string_to_hex(color):
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
    global users
    with open("./users.json", "r") as file:
        if file.read != "":
            users = json.loads(file.read())


def clear_users():
    open("./users.json", "w").close()


def get_user(name):
    try:
        response = requests.post(
            URL, json={"query": QUERY_USER_ID, "variables": {"id": int(name)}}
        )

        if response.json()["data"]["User"]:
            return response.json()["data"]["User"]
    except:
        pass

    response = requests.post(
        URL, json={"query": QUERY_USER, "variables": {"search": name}}
    )

    if response.json()["data"]["User"]:
        return response.json()["data"]["User"]

    return None


def add_user(id, name):
    user_data = get_user(name)

    if user_data is not None:
        users[str(id)] = {"name": user_data["name"], "id": user_data["id"]}

        with open("./users.json", "w") as file:
            file.write(json.dumps(users))

        load_users()

        return True
    return False


def get_media(name, type):
    try:
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

    response = requests.post(
        URL, json={"query": QUERY_MEDIA %
                   type.upper(), "variables": {"search": name}}
    )

    if response.json()["data"]["Media"] is not None:
        return response.json()["data"]["Media"]

    return None


def get_character(name):
    try:
        response = requests.post(
            URL, json={"query": QUERY_CHARACTER_ID,
                       "variables": {"id": int(name)}}
        )

        if response.json()["data"]["Character"] is not None:
            return response.json()["data"]["Character"]
    except:
        pass

    response = requests.post(
        URL, json={"query": QUERY_CHARACTER, "variables": {"search": name}}
    )

    if response.json()["data"]["Character"] is not None:
        return response.json()["data"]["Character"]

    return None


def search_media(name, media_type=None):
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
    variables = {
        "search": name,
        "page": 1,
        "perPage": 25,
    }

    response = requests.post(
        URL, json={"query": QUERY_SEARCH_CHARACTER, "variables": variables}
    )

    return response.json()["data"]["Page"]


def get_user_score(userId, mediaId):
    variables = {"userId": userId, "mediaId": mediaId}
    response = requests.post(
        URL, json={"query": QUERY_MEDIALIST, "variables": variables}
    )

    return response.json()["data"]["MediaList"]


client = discord.Client()

load_dotenv()
prefix = os.getenv("PREFIX")


@client.event
async def on_ready():
    print("We have logged in as {0.user}".format(client))
    load_users()


async def get_users_statuses(mediaId):
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


async def bot_get_media(msg):
    media_type = msg.content[1: msg.content.find(" ")]
    name = msg.content[msg.content.find(" "):]

    media = get_media(name, media_type)
    if media is None:
        embed = discord.Embed(
            title="Not Found", description="):", color=DEFAULT_COLOR)
    else:
        # user_scores = await get_users_statuses(media['id'])

        if len(media["description"]) >= 1024:
            media["description"] = media["description"][:1020] + "..."
        media["description"] = markdownify.markdownify(media["description"])

        if media["season"] is not None:
            media["season"] = f'{media["season"].capitalize()} {media["seasonYear"]}'

        for i in media:
            if media[i] is None:
                media[i] = "?"

        embed = discord.Embed(
            title=media["title"]["english"],
            url=media["siteUrl"],
            description=f'{media["title"]["native"]} - '
            + f'{media["title"]["romaji"]}\n\n',
            color=DEFAULT_COLOR,
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
        embed.add_field(name="Format", value=media["format"])  # .capitalize())
        embed.add_field(
            name="Genres", value=" - ".join(media["genres"]), inline=False)
        embed.add_field(name="Description",
                        value=media["description"], inline=False)

        embed.add_field(name="User Scores", value="Soon™")
        # for status in user_scores:
        #     embed.add_field(name=status, value=' | '.join(user_scores[status]),
        # inline=False)
    await msg.channel.send(embed=embed)


async def show_user(msg, name):
    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    if name is None:
        name = users[str(msg.author.id)]["name"]

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
            title="Not Found", description="):", color=DEFAULT_COLOR)

    await msg.channel.send(embed=embed)


async def link_user(msg):
    if add_user(msg.author.id, msg.content[6:]):
        await show_user(msg, msg.content[6:])
        await msg.channel.send("Linked successfully")
    else:
        await msg.channel.send("Not Found")


async def show_users(msg):
    result = []
    for i in users:
        result.append(users[i]["name"])
    await msg.channel.send(
        f'```Total linked users: {len(users)}\n{" | ".join(result)}```'
    )


async def show_top(msg, name):
    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    if name is None:
        try:
            name = users[str(msg.author.id)]["name"]
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
            title="Not Found", description="):", color=DEFAULT_COLOR)

    await msg.channel.send(embed=embed)


async def search(msg, params):
    try:
        search_type, search_string = params.split(" ", 1)
    except:
        search_type = "None"

    result = ""

    if search_type.lower() in ("media", "anime", "manga"):
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
    else:
        result = "Usage: `search [anime|manga|character|media] [name]'"

    await msg.channel.send(f"```{result}```")


async def user_score(msg, params):
    name, media_name = params.split(" ", 1)

    try:
        name = users[name.strip("<@!>")]["name"]
    except:
        pass

    user_data = get_user(name)
    media = get_media(media_name, "anime")
    media_manga = get_media(media_name, "manga")

    if user_data is not None:
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
                title="Not found.", description="):", color=DEFAULT_COLOR
            )
    else:
        embed = discord.Embed(title="Not found.",
                              description="):", color=DEFAULT_COLOR)
    await msg.channel.send(embed=embed)


async def show_character(msg, params):
    character = get_character(params)

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
            color=DEFAULT_COLOR,
        )
        embed.set_thumbnail(url=character["image"]["large"])
        relations = " "
        for i in character["media"]["edges"]:
            relations += f'• [{i["node"]["title"]["english"]}]({i["node"]["siteUrl"]}) [{i["characterRole"].capitalize()}]\n'
        embed.add_field(name="Relations", value=relations, inline=False)
        embed.add_field(
            name="Aliases",
            value=" - ".join(character["name"]["alternative"]),
            inline=False,
        )
        embed.add_field(name="Anilist ID", value=character["id"])
        embed.add_field(name="Favourites", value=character["favourites"])
    else:
        embed = discord.Embed(title="Not found.",
                              description="):", color=DEFAULT_COLOR)

    await msg.channel.send(embed=embed)


@client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(prefix):
        return
    if " " in message.content:
        command, params = message.content.split(" ", 1)
        command = command[1:].lower()
    else:
        command = message.content[1:]
        params = None

    if command in ("anime", "manga"):
        await bot_get_media(message)
    elif command == "link":
        await link_user(message)
    elif command == "user":
        await show_user(message, params)
    elif command == "users":
        await show_users(message)
    elif command == "top":
        await show_top(message, params)
    elif command == "score":
        await user_score(message, params)
    elif command == "search":
        await search(message, params)
    elif command == "character":
        await show_character(message, params)


client.run(os.getenv("TOKEN"))
