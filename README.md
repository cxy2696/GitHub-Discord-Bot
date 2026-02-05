# GitHub-Discord Bot

Key Features:
- **Gamification**: Earn points (10/commit, 20/issue, 30/PR) and badges (when points > 100/500/1000 → Bronze/Silver/Gold Collaborator).
- **AI Challenges**: Personalized suggestions like "Review one PR to share your expertise" via Gemini AI.
- **Sentiment Analysis**: Analyze message tone for healthy communication.
- **Leaderboard**: Real-time ranking of top contributors.
- **Polling**: Automatic updates every 5 minutes.
- **Commands**: `!set_repo`, `!link_github`, `!my_challenge`, `!leaderboard`, `!sentiment <message_id>`,  `!update_stats`, `!shutdown`
- **Architecture**: Discord input → GitHub API fetch → Data processing → Gemini AI → Output/Leaderboard.

# Converting your Discord to developer mode:

https://github.com/user-attachments/assets/f07a655a-e819-476b-8b33-e9209bcaf7df



# Step-By-Step Setup Your Own APIs
see `.env.example`. If you already have all 3 APIs, Jump to see 2. New Terminal Installation

## 1 Obtain API Keys
### 1.1 Discord Bot Token:
- Go to the [Discord Developer Portal](https://discord.com/developers/applications).
- Create a new application, name it (e.g., "GitHubDiscordBot").
- In the "Bot" left tab, add a bot and copy the token.
- Enable "Message Content" intent in the bot settings.
- Invite the bot to your server using the OAuth2 URL generator (select bot permissions like "Send Messages" and "Read Message History").
- Why personal? Discord tokens are tied to your account; sharing violates terms and risks bans.
- Free; no costs.

<img width="1801" height="883" alt="image" src="https://github.com/user-attachments/assets/3b92b134-eae1-41b1-9698-7deaea56b32f" />


- *If want to save time*: Here is the [Example Bot Installation](https://discord.com/oauth2/authorize?client_id=1427839495516061786)
- Example Bot Token: you need to send me the request!
 
- *For your own Bot Token*: Install the discord bot through the Install Link in the "Installation" left tab.

<img width="1801" height="883" alt="image" src="https://github.com/user-attachments/assets/82f4db8e-7a3e-411e-9381-5d0b550ec34b" />


### 1.2 GitHub Personal Access Token:
- Log into GitHub, go to Settings > Developer settings > Personal access tokens > Tokens (classic).
- Generate a new token with scopes: repo (full access for commits/issues/PRs), read:user (for user data).
- Copy the token (it starts with ghp_ or github_pat_).
- Why personal? Allows access to private repos if needed; shared tokens can hit rate limits quickly.
- Free; GitHub provides 5,000 requests/hour per token.

https://github.com/user-attachments/assets/44258480-6591-4abb-9a80-b0f113b48b1a

### 1.3 Gemini API Key (for AI challenges and sentiment analysis):
- Go to [Google AI Studio](https://aistudio.google.com/api-keys).
- Sign in with a Google account (recommend your personal account since your organizational accounts might be blocked to use Google AI Studio), create a new project, and generate an API key.
- Note: Check pricing for heavier loads.
- Start with the free tier; upgrade to paid for more quota.

## 2. New Terminal Installation
[![Python 3.12+](https://img.shields.io/badge/python-3.12%2B-blue)](https://www.python.org/downloads/)
```bash
git clone https://github.com/cxy2696/GitHub-Discord-Bot.git
cd GitHub-Discord-Bot
python -m venv venv
source venv/bin/activate  # Windows: venv\Scripts\activate
pip install -r requirements.txt
```

Copy `.env.example` to `.env` and add your keys (Gemini, GitHub, Discord—generate personally for security).
In `.env` file in the root:

<img width="284" height="181" alt="image" src="https://github.com/user-attachments/assets/04fe8a4c-6f16-4b0b-b4a4-6be4362a33ba" />

```
GEMINI_API_KEY='your_gemini_key_here'
GITHUB_TOKEN='your_github_token_here'
DISCORD_BOT_TOKEN='your_discord_token_here'
```

Ensure .env file get your APIs ``Store these APIs in a .env file (never commit it to GitHub—add to .gitignore)`` before run the python script in the terminal:
```
python bot.py
```
The bot is successfully running:

<img width="708" height="445" alt="image" src="https://github.com/user-attachments/assets/7e840d7b-1030-4997-8c60-405bd9053bd8" />


## 3. Usage in Discord Channel (where you installed the bot):
- Set repository: `!set_repo` owner/repo
- Link GitHub: `!link_github` username
- Personalized Challenge: `!my_challenge`
- Display Leaderboard: `!leaderboard`
- Sentiment Analysis: `!sentiment` message_id
- Manual Refresh if want: `!update_stats`
- Close the Client: `!shutdown`

The testing example:

<img width="426" height="775" alt="image" src="https://github.com/user-attachments/assets/57605931-8c9c-451c-9b06-2927d03477ed" />


