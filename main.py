'''
Anilist discord bot.
'''

import requests
import json

URL = 'https://graphql.anilist.co'
QUERY_USER = '''
query ($search: String) {
    User (search: $search) {
        name,
        id,
        about,
        siteUrl,
    },
}
'''
QUERY_MEDIA = '''
query ($search: String) {
    Media (search: $search, type: %s) {
        title {
            english,
            native,
        },
        id,
        meanScore,
    },
}
'''
QUERY_MEDIALIST = '''
query ($userId: Int, $mediaId: Int) {
    MediaList(userId: $userId, mediaId: $mediaId) {
        status,
        score,
        progress,
    },
}
'''

users = []


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
    return response.json()


def add_user(name):
    user_data = get_user(name)

    if user_data['data']['User'] is not None:
        user_data = user_data['data']['User']

        users.append({'name': user_data['name'], 'id': user_data['id']})

        with open('./users.json', 'w') as file:
            file.write(json.dumps(users))

        load_users()
    else:
        print(user_data['errors'][0]['message'])


def get_media(name, type):
    variables = {'search': name}
    response = requests.post(URL, json={'query': QUERY_MEDIA % type.upper(),
                                        'variables': variables})
    if response.json()['data']['Media'] is not None:
        return response.json()['data']['Media']

    print(response.json()['errors'][0]['message'])


def get_user_score(userId, mediaId):
    variables = {'userId': userId, 'mediaId': mediaId}
    response = requests.post(URL, json={'query': QUERY_MEDIALIST,
                                        'variables': variables})

    return response.json()['data']['MediaList']


def get_users_statuses(mediaId):
    result = {}
    for user in users:
        score = get_user_score(user['id'], mediaId)
        if score is not None:
            if score['status'] == 'COMPLETED':
                score = score['score']
            elif score['status'] == 'CURRENT':
                score = f'{score["status"]} [{score["progress"]}]'
            else:
                score = score['status']
        else:
            score = 'Not on List'
        result[user["name"]] = score
    print(result)
