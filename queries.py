#!/usr/bin/env python3

URL = "https://graphql.anilist.co"
QUERY_USER = """
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
        options {
            profileColor,
        },
    },
}
"""
QUERY_USER_ID = """
query ($id: Int) {
    User (id: $id) {
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
        options {
            profileColor,
        },
    },
}
"""
QUERY_MEDIA = """
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
        type,
        status,
        format,
        season,
        seasonYear,
        episodes,
        popularity,
        duration,
        favourites,
        chapters,
        volumes,
    },
}
"""
QUERY_MEDIA_ID = """
query ($id: Int) {
    Media (id: $id, type: %s) {
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
        type,
        status,
        format,
        season,
        seasonYear,
        episodes,
        popularity,
        duration,
        favourites,
        chapters,
        volumes,
    },
}
"""
QUERY_CHARACTER = """
query ($search: String) {
    Character (search: $search) {
        id,
        name {
            full,
            native,
            alternative,
        },
        image {
            large,
        },
        description,
        gender,
        dateOfBirth {
            year,
            month,
            day,
        },
        age,
        siteUrl,
        media {
            edges {
                relationType,
                characterRole,
                node {
                    title {
                        english,
                        native,
                        romaji,
                    },
                    siteUrl,
                },
            },
        },
        favourites,
    },
}
"""
QUERY_CHARACTER_ID = """
query ($id: Int) {
    Character (id: $id) {
        id,
        name {
            full,
            native,
            alternative,
        },
        image {
            large,
        },
        description,
        gender,
        dateOfBirth {
            year,
            month,
            day,
        },
        age,
        siteUrl,
        media {
            edges {
                relationType,
                characterRole,
                node {
                    title {
                        english,
                        native,
                        romaji,
                    },
                    siteUrl,
                },
            },
        },
        favourites,
    },
}
"""
QUERY_MEDIALIST = """
query ($userId: Int, $mediaId: Int) {
    MediaList(userId: $userId, mediaId: $mediaId) {
        status,
        score (format: POINT_100),
        progress,
        notes,
    },
}
"""

QUERY_TOP_MEDIA = """
query ($userId: Int, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        mediaList (userId: $userId, sort: SCORE_DESC) {
            media {
                title {
                    english,
                    romaji,
                    native,
                },
            },
            score (format: POINT_100),
        },
    },
}
"""
QUERY_SEARCH_MEDIA = """
query ($search: String, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        media (search: $search) {
            id,
            title {
                english,
                native,
                romaji,
            },
            type,
        },
    },
}
"""
QUERY_SEARCH_MEDIA_TYPE = """
query ($search: String, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        media (search: $search, type: %s) {
            id,
            title {
                english,
                native,
                romaji,
            },
            type,
        },
    },
}
"""
QUERY_SEARCH_CHARACTER = """
query ($search: String, $page: Int, $perPage: Int) {
    Page (page: $page, perPage: $perPage) {
        characters(search: $search) {
            id,
            name {
                full,
                native,
            },
        },
    },
}
"""
