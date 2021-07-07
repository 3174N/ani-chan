'''
Anilist discord bot.
'''

import json
import os
from dotenv import load_dotenv
import requests
import discord
import markdownify

URL = 'https://graphql.anilist.co'
QUERY_USER = '''
query ($search: String) {
    User (search: $search) {
        name,
        id,
        about,
        siteUrl,
        avatar {
            large,
        },
        bannerImage,
        statistics {
            anime {
                count,
                meanScore,
                episodesWatched,
                minutesWatched,
                formats (limit: 3) {
                    format,
                },
                genres (limit: 3) {
                    genre,
                },
            },
            manga {
                count,
                meanScore,
                volumesRead,
                chaptersRead,
                formats (limit: 3) {
                    format,
                },
                genres (limit: 3) {
                    genre,
                },
            },

        },
    },
}
'''
QUERY_MEDIA = '''
query ($search: String) {
    Media (search: $search, type: %s) {
        title {
            english,
            native,
            romaji,
        },
        id,
        meanScore,
        description,
        coverImage {
            extraLarge,
        },
        siteUrl,
        genres,
    },
}
'''
QUERY_MEDIALIST = '''
query ($userId: Int, $mediaId: Int) {
    MediaList(userId: $userId, mediaId: $mediaId) {
        status,
        score (format: POINT_100),
        progress,
    },
}
'''

users = {}


def load_users():
    global users
    with open('./users.json', 'r') as file:
        users = json.loads(file.read())


def clear_users():
    open('./users.json', 'w').close()


def get_user(name):
    variables = {'search': name}
    response = requests.post(URL, json={'query': QUERY_USER,
                                        'variables': variables})
    return response.json()['data']['User']


def add_user(id, name):
    user_data = get_user(name)

    if user_data is not None:
        users[id] = {'name': user_data['name'], 'id': user_data['id']}

        with open('./users.json', 'w') as file:
            file.write(json.dumps(users))

        load_users()

        return True
    return False


def get_media(name, type):
    variables = {'search': name}
    response = requests.post(URL, json={'query': QUERY_MEDIA % type.upper(),
                                        'variables': variables})
    # print(response.text)
    return response.json()['data']['Media']


def get_user_score(userId, mediaId):
    variables = {'userId': userId, 'mediaId': mediaId}
    response = requests.post(URL, json={'query': QUERY_MEDIALIST,
                                        'variables': variables})

    return response.json()['data']['MediaList']


client = discord.Client()

load_dotenv()
prefix = os.getenv('PREFIX')


@ client.event
async def on_ready():
    print('We have logged in as {0.user}'.format(client))
    load_users()


async def get_users_statuses(mediaId):
    result = {}

    query = '''
query ($mediaId: Int) {
    %s
}'''
    media_query = '''
    %s: MediaList(userId: %s, mediaId: $mediaId) {
        status,
        score (format: POINT_100),
        progress,
    },'''
    media_query_combined = ''

    for user in users:
        for value in user:
            value = user[value]
            media_query_combined += media_query % (
                '_' + value['name'], str(value['id']))

    query = query % media_query_combined
    print(query)
    print(mediaId)

    variables = {'mediaId': mediaId}
    response = requests.post(URL, json={'query': query,
                                        'variables': variables})
    print(response.text)

    for user in users:
        for value in user:
            value = user[value]
            score = get_user_score(value['id'], mediaId)
            if score is not None:
                if score['status'] == 'PAUSED':
                    score['status'] = 'CURRENT'

                if score['status'] == 'COMPLETED':
                    status = f'{value["name"]} **({score["score"]})**'
                elif score['status'] == 'CURRENT':
                    status = f'{value["name"]} [{score["progress"]}]'
                else:
                    status = value["name"]

                if score['status'] in result:
                    result[score['status']].append(status)
                else:
                    result[score['status']] = [status]
            else:
                if 'NOT ON LIST' in result:
                    result['NOT ON LIST'].append(value['name'])
                else:
                    result['NOT ON LIST'] = [value['name']]

    result_sort = {}
    if 'COMPLETED' in result:
        result_sort['COMPLETED'] = result['COMPLETED']
    if 'CURRENT' in result:
        result_sort['CURRENT'] = result['CURRENT']
    if 'DROPPED' in result:
        result_sort['DROPPED'] = result['DROPPED']
    if 'PLANNING' in result:
        result_sort['PLANNING'] = result['PLANNING']
    if 'NOT ON LIST' in result:
        result_sort['NOT ON LIST'] = result['NOT ON LIST']
    return result_sort


async def bot_get_media(msg):
    media_type = msg.content[1:msg.content.find(' ')]
    name = msg.content[msg.content.find(' '):]

    media = get_media(name, media_type)
    if media is None:
        embed = discord.Embed(title='Not Found.', description='):')
    else:
        user_scores = await get_users_statuses(media['id'])

        if len(media['description']) >= 1024:
            media['description'] = media['description'][:1020] + '...'
        media['description'] = markdownify.markdownify(media['description'])

        embed = discord.Embed(title=media['title']['english'],
                              url=media['siteUrl'],
                              description=f'{media["title"]["native"]} - ' +
                              f'{media["title"]["romaji"]}\n\n')
        embed.set_thumbnail(url=media['coverImage']['extraLarge'])
        embed.add_field(name='Mean Score', value=media['meanScore'])
        embed.add_field(name='Description', value=media['description'],
                        inline=False)

        # embed.add_field(name='User Scores', value=' ')
        for status in user_scores:
            embed.add_field(name=status, value=' | '.join(user_scores[status]),
                            inline=False)
    await msg.channel.send(embed=embed)


async def show_user(msg, name):
    try:
        name = users[name.strip('<@!>')]['name']
    except:
        pass

    if name is None:
        name = users[str(msg.author.id)]['name']

    user_data = get_user(name)

    if user_data is not None:
        embed = discord.Embed(title=user_data['name'] + ' - Anilist Statistics',
                              url=user_data['siteUrl'])
        embed.set_thumbnail(url=user_data['avatar']['large'])
        if user_data['bannerImage'] is not None:
            embed.set_image(url=user_data['bannerImage'])
        if user_data['about'] is not None:
            embed.add_field(name='About', value=user_data['about'])

        stats_anime = user_data['statistics']['anime']
        if stats_anime['formats'] != []:
            stats_anime['format'] = stats_anime['formats'][0]['format']
        else:
            stats_anime['format'] = 'Unknown'
        if stats_anime['genres'] != []:
            genres = []
            for i in stats_anime['genres']:
                genres.append(i['genre'])
            stats_anime['genres'] = ' / '.join(genres)
        else:
            stats_anime['genres'] = 'Unknown'
        anime_stats_str = (
            f'- Total Entries: **{stats_anime["count"]}**\n' +
            f'- Mean Score: **{stats_anime["meanScore"]}**\n' +
            f'- Episodes Watched: **{stats_anime["episodesWatched"]}**\n' +
            f'- Minutes Watched: **{stats_anime["minutesWatched"]}**\n' +
            f'- Favorite Format: **{stats_anime["format"]}**\n' +
            f'- Favorite Genres: **{stats_anime["genres"]}**\n'
        )
        stats_manga = user_data['statistics']['manga']
        if stats_manga['formats'] != []:
            stats_manga['format'] = stats_manga['formats'][0]['format']
        else:
            stats_manga['format'] = 'Unknown'
        if stats_manga['genres'] != []:
            genres = []
            for i in stats_manga['genres']:
                genres.append(i['genre'])
            stats_manga['genres'] = ' / '.join(genres)
        else:
            stats_manga['genres'] = 'Unknown'
        manga_stats_str = (
            f'- Total Entries: **{stats_manga["count"]}**\n' +
            f'- Mean Score: **{stats_manga["meanScore"]}**\n' +
            f'- Volumes Read: **{stats_manga["volumesRead"]}**\n' +
            f'- Chapters Read: **{stats_manga["chaptersRead"]}**\n' +
            f'- Favorite Format: **{stats_manga["format"]}**\n' +
            f'- Favorite Genres: **{stats_manga["genres"]}**\n'
        )

        embed.add_field(name='Anime Statistics', value=anime_stats_str,
                        inline=False)
        embed.add_field(name='Manga Statistics', value=manga_stats_str,
                        inline=False)
    else:
        embed = discord.Embed(title='Not Found.', description='):')

    await msg.channel.send(embed=embed)


async def link_user(msg):
    if add_user(msg.author.id, msg.content[6:]):
        await msg.channel.send('Linked successfully')
    else:
        await msg.channel.send('Not Found.')


@ client.event
async def on_message(message):
    if message.author == client.user:
        return

    if not message.content.startswith(prefix):
        return
    if ' ' in message.content:
        command, params = message.content.split(' ', 1)
        command = command[1:].lower()
    else:
        command = message.content[1:]
        params = None
    if command == 'anime' or command == 'manga':
        await bot_get_media(message)
    elif command == 'link':
        await link_user(message)
    elif command == 'user':
        await show_user(message, params)


client.run(os.getenv('TOKEN'))
