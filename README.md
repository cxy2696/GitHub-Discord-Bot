# GitHub-Discord Bot

An AI-powered (gemini-2.5-flash) Discord bot to boost participation, motivation, and collaboration in remote GitHub teams using gamification.

Key Features:
- **Gamification**: Earn points (10/commit, 20/issue, 30/PR) and badges (Bronze/Silver/Gold Collaborator).
- **AI Challenges**: Personalized suggestions like "Review one PR to share your expertise" via Gemini AI.
- **Sentiment Analysis**: Analyze message tone for healthy communication.
- **Leaderboard**: Real-time ranking of top contributors.
- **Polling**: Automatic updates every 5 minutes.
- **Commands**: `!set_repo`, `!link_github`, `!my_challenge`, `!leaderboard`, `!sentiment <message_id>`
- **Architecture**: Discord input → GitHub API fetch → Data processing → Gemini AI → Output/Leaderboard.

## Setup Your Own APIs
Copy `.env.example` to `.env` and add your keys (Gemini, GitHub, Discord—generate personally for security).
In `.env` file in the root:
```
GEMINI_API_KEY='your_gemini_key_here'
GITHUB_TOKEN='your_github_token_here'
DISCORD_BOT_TOKEN='your_discord_token_here'
```

## Obtain API Keys
### Discord Bot:
- Go to the [Discord Developer Portal](https://discord.com/developers/applications).
- Create a new application, name it (e.g., "GitHubDiscordBot").
- In the "Bot" tab, add a bot and copy the token.
- Enable "Message Content" intent in the bot settings.
- Invite the bot to your server using the OAuth2 URL generator (select bot permissions like "Send Messages" and "Read Message History").
- Why personal? Discord tokens are tied to your account; sharing violates terms and risks bans.
- Free; no costs.

- *If want to save time*: Here is the [Example Bot Installation](https://discord.com/oauth2/authorize?client_id=1427839495516061786)
- Example Bot Token: you need to send me the request!
 
- *For your own Bot Token*: Install the discord bot through the Install Link from [Installation Page](https://discord.com/developers/applications/1427839495516061786/installation)

### GitHub Personal Access Token:
- Log into GitHub, go to Settings > Developer settings > Personal access tokens > Tokens (classic).
- Generate a new token with scopes: repo (full access for commits/issues/PRs), read:user (for user data).
- Copy the token (it starts with ghp_ or github_pat_).
- Why personal? Allows access to private repos if needed; shared tokens can hit rate limits quickly.
- Free; GitHub provides 5,000 requests/hour per token.

### Gemini API Key (for AI challenges and sentiment analysis):
- Go to [Google AI Studio](https://aistudio.google.com/api-keys).
- Sign in with a Google account, create a new project, and generate an API key.
- Note: Check pricing for heavier loads.
- Start with the free tier; upgrade to paid for more quota.



[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)

## New Terminal Installation
```bash
git clone https://github.com/cxy2696/GitHub-Discord-Bot.git
cd GitHub-Discord-Bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Ensure .env file get your APIs ``Store these APIs in a .env file (never commit it to GitHub—add to .gitignore)`` before run the python script in the terminal:
```
python bot.py
```

## Usage
- Set repo: !set_repo owner/repo
- Link GitHub: !link_github username
- Challenge: !my_challenge
- Leaderboard: !leaderboard
- Sentiment: !sentiment <message_id>

