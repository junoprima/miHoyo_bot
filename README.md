
# miHoyo Bot

miHoyo Bot is a versatile, feature-rich Discord bot designed to automate game check-ins and enhance user interaction using modern slash commands. With its robust integration of Firebase Firestore and Docker containerization, this bot ensures a seamless, scalable, and efficient experience for managing in-game accounts.

---

## 🌟 Features

- **Interactive Slash Commands:**
  - Add, edit, and delete cookies for multiple games directly in Discord.
  - List user accounts with beautifully styled embedded messages.
  - Trigger manual check-ins and dynamically reload commands.

- **Automated Daily Check-Ins:**
  - Configured using `cron` within a Docker container to ensure precise scheduling.

- **Multi-Game Support:**
  - Supports games like Genshin Impact, Honkai Star Rail, and more.

- **Firestore Integration:**
  - Securely stores account cookies and retrieves them for processing.

- **Dockerized Architecture:**
  - Simplified deployment and scalability with Docker Compose.

---

## 📂 Project Structure

```plaintext
miHoyo_bot/
├── cogs/
│   ├── admin.py        # Admin-related commands (e.g., reload)
│   ├── accounts.py     # Account-related commands (e.g., list_accounts)
│   ├── checkin.py      # Commands related to check-in functionality
│   ├── cookies.py      # Cookie management commands (add/edit/delete)
├── discord_bot/
│   ├── bot.py
├── games/
│   ├── game.py
├── logs/
│   ├── cron.log
│   ├── log.log
├── utils/
│   ├── autocomplete.py
│   ├── discord.py
│   ├── firestore.py
│   ├── logger.py
├── .env
├── config.json
├── constants.json
├── crontab.txt
├── docker-compose.yml
├── Dockerfile
├── Dockerfile-cron
├── firebase_key.json
├── main.py
├── requirements.txt
```

---

## 🛠️ Prerequisites

1. **Python**: Version 3.12 or higher
2. **Docker**: Installed with Docker Compose
3. **Firebase**:
   - A `firebase_key.json` file for Firestore integration.

---

## 🚀 Installation

### 1. Clone the Repository

```bash
git clone https://github.com/junoprima/miHoyo_bot.git
cd miHoyo_bot
```

### 2. Configure Environment Variables

Create a `.env` file in the project root with the following content:

```env
FIREBASE_KEY=firebase_key.json
DISCORD_WEBHOOK=<Your Discord Webhook URL>
DISCORD_BOT_TOKEN=<Your Bot Token>
DISCORD_GUILD_ID=<Your Guild ID>
CONSTANTS=constants.json
```

### 3. Install Dependencies

For local testing, you can install dependencies using pip:

```bash
pip install -r requirements.txt
```

### 4. Build and Run Docker Containers

Use Docker Compose to build and start the services:

```bash
docker-compose up --build -d
```

---

## 🎮 Usage

### Run the Bot

```bash
docker-compose up -d
```

### Scheduled Daily Check-In

- `main.py` handles automatic check-ins and is triggered daily by the cron job.

---

## ✨ Slash Commands

1. `/add_cookie`: Add a new cookie for a game.
2. `/edit_cookie`: Edit an existing cookie.
3. `/delete_cookie`: Delete a cookie.
4. `/list_accounts`: List all accounts for a selected game with styled embeds.
5. `/reload`: Reload commands dynamically.
6. `/trigger_checkin`: Trigger the daily check-in manually.

---

## 📜 Logs

- **Cron Logs**: `logs/cron.log` (daily check-ins)
- **Bot Logs**: `logs/log.log` (slash command activity)

---

## 🧩 Advanced Features

### Health Checks

- The Docker setup includes health checks for the scheduler service to ensure `cron` is running.

### Dynamic Slash Commands

- Autocomplete suggestions for games and accounts improve user experience.

---

## 🤝 Contributing

Contributions are always welcome! If you have an idea or find a bug, feel free to open an issue or submit a pull request. Visit [GitHub Repository](https://github.com/junoprima/miHoyo_bot) to get started.

---

## 📄 License

This project is licensed under the MIT License. See the `LICENSE` file for more details.

---

## ❤️ Acknowledgments

- **Guide on Cookie Retrieval**: Special thanks to the author of [this guide](https://github.com/torikushiii/hoyolab-auto/tree/main/services/google-script) for inspiration and instructions. Full credit to the author for their work.
- Icons and assets are owned by Hoyoverse.

---

**Made with ❤️ by Junoprima**
