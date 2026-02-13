# Endfield Deployment Guide

**Date**: 2026-02-13
**Status**: Ready to Deploy

---

## ✅ What Has Been Done (Local Changes)

All code changes have been implemented locally:

1. **✅ Created**: `games/endfield_adapter.py` (400+ lines)
   - OAuth flow implementation
   - v2 signature generation
   - Check-in and claim logic

2. **✅ Modified**: `games/game.py`
   - Added Endfield routing
   - Created `_sign_endfield()` method
   - Created `_process_endfield_account()` method

3. **✅ Modified**: `constants.json`
   - Added Endfield configuration
   - GameId: 10
   - API type: skport

4. **✅ Modified**: `utils/database.py`
   - Added "endfield" to autocomplete list

---

## 🚀 Deployment Steps to DigitalOcean Server

### Step 1: Upload Modified Files to Server

```bash
# From your local PC (d:\Relax\Coding\bot\miHoYo_bot)

# Upload new adapter file
scp games/endfield_adapter.py root@128.199.175.41:/root/projects/miHoYo_bot/games/

# Upload modified files
scp games/game.py root@128.199.175.41:/root/projects/miHoYo_bot/games/
scp constants.json root@128.199.175.41:/root/projects/miHoYo_bot/
scp utils/database.py root@128.199.175.41:/root/projects/miHoYo_bot/utils/
```

### Step 2: Add Endfield Game to Database

```bash
# SSH to server
ssh root@128.199.175.41

# Navigate to project directory
cd /root/projects/miHoYo_bot

# Add Endfield game to database
docker exec -it mihoyo_bot python -c "
import asyncio
from database.connection import init_database
from database.operations import db_ops

async def add_endfield():
    await init_database()

    # Check if Endfield already exists
    existing = await db_ops.get_game_config('endfield')
    if existing:
        print('Endfield game already exists in database!')
        return

    # Add Endfield game
    await db_ops.create_game(
        name='endfield',
        display_name='Arknights: Endfield',
        act_id='skport_endfield_attendance',
        sign_game_header='endfield',
        success_message='Attendance claimed successfully, Doctor~',
        signed_message=\"You've already checked in today, Doctor~\",
        game_id=10,
        author_name='Endfield Assistant',
        icon_url='https://play-lh.googleusercontent.com/IHJeGhqSpth4VzATp_afjsCnFRc-uYgGC1EV3b2tryjyZsVrbcaeN5L_m8VKwvOSpIu_Skc49mDpLsAzC6Jl3mM',
        info_url='https://zonai.skport.com/web/v1/game/endfield/attendance',
        home_url='https://zonai.skport.com/web/v1/game/endfield/attendance',
        sign_url='https://zonai.skport.com/web/v1/game/endfield/attendance'
    )
    print('✅ Endfield game added successfully!')

asyncio.run(add_endfield())
"
```

### Step 3: Restart Bot

```bash
# Still on server
cd /root/projects/miHoYo_bot
docker-compose restart bot

# Check if bot started successfully
docker logs mihoyo_bot --tail 20
```

### Step 4: Verify Deployment

```bash
# Check bot status
docker ps | grep mihoyo

# Verify Endfield in database
docker exec -it mihoyo_bot python -c "
import asyncio
from database.connection import init_database
from database.operations import db_ops

async def check():
    await init_database()
    game = await db_ops.get_game_config('endfield')
    if game:
        print('✅ Endfield found in database:')
        print(f'   Name: {game[\"game\"]}')
        print(f'   Game ID: {game[\"gameId\"]}')
        print(f'   API Type: {game.get(\"api_type\", \"N/A\")}')
    else:
        print('❌ Endfield not found in database')

asyncio.run(check())
"
```

---

## 🧪 Testing

### Step 1: Get Endfield Account Token

**Option A: Browser DevTools**
1. Go to https://www.skport.com/
2. Login to your account
3. Open DevTools (F12) → Application → Cookies
4. Find cookie named `account_token`
5. Copy the entire JWT token value

**Example token format**:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9.eyJzdWIiOiIxMjM0NTY3ODkwIiwibmFtZSI6IkRvY3RvciIsImlhdCI6MTUxNjIzOTAyMn0.SflKxwRJSMeKKF2QT4fwpMeJf36POk6yJV_adQssw5c
```

### Step 2: Add Account via Discord

```
1. In Discord, type: /add_cookie
2. Select game: endfield
3. Enter account name: MyDoctor (or any name)
4. Paste your account_token in the modal
5. Bot should respond: ✅ Account added successfully!
```

### Step 3: Test Manual Check-in

```bash
# On server
ssh root@128.199.175.41
cd /root/projects/miHoYo_bot

# Run manual check-in
docker exec mihoyo_bot python main.py

# Check logs
docker logs mihoyo_bot --tail 50 | grep -i endfield
```

### Step 4: Verify Discord Notification

After running manual check-in:
- Check your Discord channel (1417879161082613943)
- Should see Endfield check-in notification
- Notification should show:
  - Game: Arknights: Endfield
  - Account name
  - Reward received
  - Total check-ins

---

## 📝 Quick Deployment Commands (Copy-Paste)

### Full Deployment in One Go

```bash
# 1. Upload files from local PC
cd d:\Relax\Coding\bot\miHoYo_bot
scp games/endfield_adapter.py root@128.199.175.41:/root/projects/miHoYo_bot/games/
scp games/game.py root@128.199.175.41:/root/projects/miHoYo_bot/games/
scp constants.json root@128.199.175.41:/root/projects/miHoYo_bot/
scp utils/database.py root@128.199.175.41:/root/projects/miHoYo_bot/utils/

# 2. SSH to server and execute
ssh root@128.199.175.41 "cd /root/projects/miHoYo_bot && docker exec -it mihoyo_bot python -c \"import asyncio; from database.connection import init_database; from database.operations import db_ops; asyncio.run((lambda: db_ops.create_game(name='endfield', display_name='Arknights: Endfield', act_id='skport_endfield_attendance', sign_game_header='endfield', success_message='Attendance claimed successfully, Doctor~', signed_message='You\\\'ve already checked in today, Doctor~', game_id=10, author_name='Endfield Assistant', icon_url='https://play-lh.googleusercontent.com/IHJeGhqSpth4VzATp_afjsCnFRc-uYgGC1EV3b2tryjyZsVrbcaeN5L_m8VKwvOSpIu_Skc49mDpLsAzC6Jl3mM', info_url='https://zonai.skport.com/web/v1/game/endfield/attendance', home_url='https://zonai.skport.com/web/v1/game/endfield/attendance', sign_url='https://zonai.skport.com/web/v1/game/endfield/attendance'))()) && docker-compose restart bot\""

# 3. Verify
ssh root@128.199.175.41 "docker logs mihoyo_bot --tail 20"
```

---

## ⚠️ Important Notes

### 1. Account Token vs Cookie

**miHoYo games** use cookies like:
```
ltoken_v2=v2_xxx; ltuid_v2=123; ...
```

**Endfield** uses OAuth token:
```
eyJhbGciOiJSUzI1NiIsInR5cCI6IkpXVCJ9...
```

Both are stored in the same `encrypted_cookie` field in database!

### 2. Token Expiration

OAuth tokens expire after some time. If users see errors like:
- "OAuth authentication failed"
- "Invalid token"

They need to:
1. Get a new `account_token` from SKPort website
2. Update their account: `/add_cookie` (overwrites old token)

### 3. Error Handling

If check-in fails, check logs:
```bash
docker logs mihoyo_bot --tail 100 | grep -i error
```

Common errors:
- **"OAuth Step X failed"**: Token expired or invalid
- **"Missing valid credentials"**: Token format wrong
- **"Could not determine attendance status"**: API endpoint issue

---

## 🔍 Verification Checklist

After deployment:

- [ ] Files uploaded to server successfully
- [ ] Endfield game added to database (game_id=10)
- [ ] Bot restarted without errors
- [ ] `/add_cookie` shows "endfield" in dropdown
- [ ] Can add Endfield account via Discord
- [ ] Manual check-in works (`python main.py`)
- [ ] Discord notification appears
- [ ] Reward information displayed correctly
- [ ] No errors in logs

---

## 🎯 Expected Behavior

### When User Adds Endfield Account

```
User: /add_cookie
Bot: [Shows dropdown with games]
      - genshin
      - starrail
      - zenless
      - honkai
      - endfield ← NEW!

User: [Selects endfield, enters account name]
Bot: [Shows modal for token input]
User: [Pastes account_token]
Bot: ✅ Cookie added successfully for account 'MyDoctor' in game 'endfield'
```

### During Daily Check-in (23:05)

```
Bot processes all games...

Processing Endfield account: MyDoctor
OAuth flow successful
Checking Endfield attendance status...
Claiming Endfield attendance...
Attendance claimed successfully! Rewards: Credit Points x100

[Discord notification sent]
✅ Arknights: Endfield - MyDoctor
   Attendance claimed successfully, Doctor~
   Received: 100x Credit Points
   Total Check-Ins: 15
```

---

## 🐛 Troubleshooting

### Issue: "Module not found: endfield_adapter"

**Solution**: Ensure `endfield_adapter.py` is in `games/` directory on server
```bash
ls -la /root/projects/miHoYo_bot/games/endfield_adapter.py
```

### Issue: "Endfield not in dropdown"

**Solution**: Check if `utils/database.py` was updated
```bash
ssh root@128.199.175.41
cat /root/projects/miHoYo_bot/utils/database.py | grep endfield
# Should see: return ["genshin", "starrail", "zenless", "honkai", "endfield"]
```

### Issue: "OAuth authentication failed"

**Solution**:
1. Get fresh `account_token` from SKPort website
2. Re-add account via Discord
3. Verify token format (should be JWT: eyJ...)

### Issue: "Game not found in database"

**Solution**: Re-run database initialization script
```bash
docker exec -it mihoyo_bot python -c "[database script above]"
```

---

## 📊 Success Metrics

After successful deployment:

| Metric | Expected | How to Verify |
|--------|----------|---------------|
| **Files uploaded** | 4 files | `ls games/endfield_adapter.py` |
| **Database entry** | 1 game | Query database for game_id=10 |
| **Autocomplete** | 5 games | `/add_cookie` dropdown |
| **Check-in works** | ✅ Success | Run `python main.py` |
| **Notification** | Appears in Discord | Check channel |
| **No errors** | 0 errors | Check logs |

---

## 🎊 Post-Deployment

### For Users

Share this message in Discord:
```
🎮 NEW GAME AVAILABLE! 🎮

Arknights: Endfield is now supported for daily check-ins!

To add your account:
1. Go to https://www.skport.com/ and login
2. Open browser DevTools (F12) → Application → Cookies
3. Find `account_token` cookie and copy the value
4. In Discord: /add_cookie → Select "endfield"
5. Paste your account token

Daily check-ins will happen automatically at 23:05 Bangkok Time along with your other games!
```

### Monitoring

Add to your daily checks:
```bash
# Check Endfield accounts
docker exec mihoyo_bot python -c "
import asyncio
from database.connection import init_database
from database.operations import db_ops

async def check():
    await init_database()
    accounts = await db_ops.get_accounts_by_game(GUILD_ID, 'endfield')
    print(f'Total Endfield accounts: {len(accounts)}')

asyncio.run(check())
"
```

---

## ✅ Deployment Complete!

Once all steps are done:
- Endfield is integrated into miHoYo bot
- Users can add accounts via Discord
- Daily check-ins run automatically
- All games check-in together at 23:05

**Status**: 🟢 Ready for Production

---

**Created**: 2026-02-13
**Next**: Deploy to server and test with real account token
