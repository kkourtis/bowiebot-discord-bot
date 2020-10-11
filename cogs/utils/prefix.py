from tinydb import TinyDB, Query
import config

db = TinyDB('files/json/bowiebot.json')
table = db.table('prefix')
guild = Query()

def calculate(bot, msg):
    user_id = bot.user.id
    base = [f'<@!{user_id}> ', f'<@{user_id}> ']
    if msg.guild is None:
        base.append(config.PREFIX) 
    else:
        base.append(get(msg.guild.id))
        #base.append(config.PREFIX) 
    return base

def view(id):
    value = table.get(guild.id == id)
    return value

def all():
    result = table.all()
    return result

def get(id):
    value = table.get(guild.id == id)
    if value is None:
        return None
    return value['prefix']

def update(id, new):
    table.update({'prefix': new}, guild.id == id)

def insert(id, prefix):
    table.insert({'id': id, 'prefix': prefix})

def remove(id):
    table.remove(guild.id == id)

def add_missing_guilds(guilds):
    result = table.all()
    missing_guilds = []
    flat_results = []

    for entry in result:
        flat_results.append(entry['id'])

    for guild in guilds:
        if guild.id not in flat_results:
            missing_guilds.append(guild.id)

    if len(missing_guilds) > 0:
        for id in missing_guilds:
            insert(id, 'bb$')

    missing_guilds = len(missing_guilds)

    if missing_guilds == 1:
        print(f'{missing_guilds} guild added to prefix')
    else:
        print(f'{missing_guilds} guilds added to prefix')


def remove_missing_guilds(guilds):
    result = table.all()
    missing_guilds = []
    flat_guilds = []

    for guild in guilds:
        flat_guilds.append(guild.id)

    for entry in result:
        if entry['id'] not in flat_guilds:
            missing_guilds.append(entry['id'])

    if len(missing_guilds) > 0:
        for id in missing_guilds:
            remove(id)

    missing_guilds = len(missing_guilds)

    if missing_guilds == 1:
        print(f'{missing_guilds} guild removed from prefix')
    else:
        print(f'{missing_guilds} guilds removed from prefix')

async def remove_prefix_from_message(bot, message):
    content = None
    prefixes = calculate(bot, message)
    for pref in prefixes:
        if pref is None:
            continue
        if pref in message.content:
            content = message.content[len(pref):]
    return content

