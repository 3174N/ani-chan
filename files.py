#!/usr/bin/env python3

import json

USERS_FILE = "users.json"
SETTINGS_FILE = "config.json"

users_glob = {}
users = {}
settings = {}


def load_users():
    """Loads users from users file."""
    global users_glob

    with open(USERS_FILE, "r") as users_file:
        users_glob = json.loads(users_file.read())
    return users_glob


def update_users(users_dict):
    """Updates users file based on dictionary.

    Keyword arguments:
      users_dict -- Users dictionary.
    """
    with open(USERS_FILE, "w") as users_file:
        users_file.write(json.dumps(users_dict))


def load_settings():
    """Loads settings from settings file."""
    global settings

    with open(SETTINGS_FILE, "r") as settings_file:
        settings = json.loads(settings_file.read())
    return settings


def update_settings(settings_dict):
    """Updates settings file based on dictionary.

    Keyword arguments:
      settings_dict -- Settings dictionary.
    """
    with open(SETTINGS_FILE, "w") as settings_file:
        settings_file.write(json.dumps(settings_dict))
