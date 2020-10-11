import asyncio
import config
import asyncpg

async def connect():
    return await asyncpg.connect(user=config.DB_USER,
                                 password=config.DB_PASSWORD, database=config.DB,
                                 host=config.DB_HOST)

async def create_pool(db_name):
    return await asyncpg.create_pool(user=config.DB_USER, password=config.DB_PASSWORD, database=db_name, host=config.DB_HOST, min_size=10, max_size = 20)

async def insert_guild(guild_id, conn):
    guild_id = str(guild_id)
    q = f"""INSERT INTO guilds (guild_id, sound, roles, images, tags, logs) VALUES ({guild_id}, True, True, True, True, True);"""
    await conn.execute(q)

    q = f"insert into logs (guild_id, member_join, member_leave, channel_update, message_delete, member_ban, member_unban) " \
        f"VALUES ({guild_id}, False, False, False, False, False, False)"
    await conn.execute(q)

    q = f"""insert into roles (guild_id) VALUES ({guild_id});"""
    await conn.execute(q)

    q = f"""insert into sound (guild_id, cooldown_enabled) VALUES ({guild_id}, False);"""
    await conn.execute(q)

async def remove_guild(guild_id, conn):
    guild_id = str(guild_id)
    await conn.execute(f"""DELETE FROM guilds WHERE guild_id = '{guild_id}';""")
    await conn.execute(f"""DELETE FROM logs where guild_id = '{guild_id}';""")
    await conn.execute(f"""DELETE FROM roles where guild_id = '{guild_id}';""")
    await conn.execute(f"""DELETE FROM sound where guild_id = '{guild_id}';""")


async def add_remove_missing_guilds(discord_guilds, conn=None):
    if conn is None:
        conn = await connect()
    q = "select guild_id from guilds"
    db_guilds = await conn.fetch(q)

    db_ids = [guild['guild_id'] for guild in db_guilds]
    discord_ids = [str(guild.id) for guild in discord_guilds]

    added_guilds = 0
    removed_guilds = 0

    for guild_id in db_ids:
        if guild_id not in discord_ids:
            await remove_guild(guild_id, conn)
            removed_guilds += 1

    for guild_id in discord_ids:
        if guild_id not in db_ids:
            await insert_guild(guild_id, conn)
            added_guilds += 1

    await conn.close()    
    print(f'Guilds removed from Postgres: {removed_guilds}')
    print(f'Guilds added to Postgres: {added_guilds}')


async def add_missing_guilds(discord_guilds, conn, db_guilds=None, db_ids=None,discord_ids=None):
    if db_guilds is None:
        db_guilds = await conn.fetch("select guild_id from guilds")

    if db_ids is None:
        db_ids = [guild['guild_id'] for guild in db_guilds]
    if discord_ids is None:
        discord_ids = [str(guild.id) for guild in discord_guilds]

    added_guilds = 0
    for guild_id in discord_ids:
        if guild_id not in db_ids:
            await insert_guild(guild_id, conn)
            added_guilds += 1

    print(f'{added_guilds} guilds added to Postgres')
    return added_guilds