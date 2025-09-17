async def fetch_all_games():
    return ["genshin", "starrail", "zenless", "honkai"]

async def get_guild_accounts(guild_id, game):
    from database.operations import db_ops
    try:
        accounts = await db_ops.get_accounts_by_game(guild_id, game)
        return accounts
    except:
        return []

async def get_account_names_for_game(guild_id, game):
    from database.operations import db_ops
    try:
        accounts = await db_ops.get_accounts_by_game(guild_id, game)
        return [acc['name'] for acc in accounts]
    except:
        return []

async def update_cookie_in_database(guild_id, user_id, game_name, account_name, cookie):
    from database.operations import db_ops
    try:
        await db_ops.add_account(guild_id, user_id, game_name, account_name, cookie)
        return True
    except:
        return False

async def delete_cookie_in_database(guild_id, user_id, game_name, account_name):
    from database.operations import db_ops
    try:
        await db_ops.delete_account(guild_id, user_id, game_name, account_name)
        return True
    except:
        return False

async def edit_cookie_in_database(guild_id, user_id, game_name, account_name, new_cookie):
    from database.operations import db_ops
    try:
        await db_ops.update_account_cookie(guild_id, user_id, game_name, account_name, new_cookie)
        return True
    except:
        return False

async def fetch_cookies_from_database(guild_id):
    from database.operations import db_ops
    try:
        accounts = await db_ops.get_all_accounts(guild_id)
        return accounts
    except:
        return []