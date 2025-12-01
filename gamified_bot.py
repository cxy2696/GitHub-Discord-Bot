import os
import json
import time
import asyncio
import certifi
import ssl
import sqlite3
import logging
from datetime import datetime, timezone, timedelta
from github import Github, Auth
import discord
from discord.ext import commands
from aiohttp import ClientSession, TCPConnector
from itertools import islice
import concurrent.futures  # For executor

'''
Bot Installation: 
https://discord.com/oauth2/authorize?client_id=1427839495516061786
'''

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s %(levelname)s: %(message)s',
    handlers=[
        logging.FileHandler('bot.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# Environment variables (set these externally, e.g., via .env or system environment)
os.environ['GEMINI_API_KEY'] = ''
os.environ['GITHUB_TOKEN'] = ''
os.environ['DISCORD_BOT_TOKEN'] = ''

GEMINI_API_KEY = os.getenv('GEMINI_API_KEY')
GITHUB_TOKEN = os.getenv('GITHUB_TOKEN')
DISCORD_BOT_TOKEN = os.getenv('DISCORD_BOT_TOKEN')

class GamifiedGitHubDiscordBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        intents.members = True
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)
        super().__init__(command_prefix='!', intents=intents, connector=connector)
        self.github = Github(auth=Auth.Token(GITHUB_TOKEN))
        self.repo = None
        self.init_db()
        self.user_data = self.load_user_data()
        self.last_global_check = datetime.now(timezone.utc) - timedelta(days=30)
        self.add_commands()
        self.validate_environment()
        self.executor = concurrent.futures.ThreadPoolExecutor(max_workers=50)  # For sync tasks

    def init_db(self):
        try:
            with sqlite3.connect('user_data.db') as conn:
                c = conn.cursor()
                c.execute('''CREATE TABLE IF NOT EXISTS users
                            (discord_id TEXT PRIMARY KEY, github_user TEXT, points INTEGER,
                             badges TEXT, current_challenge TEXT, last_activity_check TEXT)''')
                conn.commit()
                logger.info("Database initialized successfully")
        except Exception as e:
            logger.error(f"Failed to initialize database: {str(e)}")

    def load_user_data(self):
        user_data = {}
        try:
            with sqlite3.connect('user_data.db') as conn:
                c = conn.cursor()
                c.execute("SELECT * FROM users")
                for row in c.fetchall():
                    discord_id, github_user, points, badges, challenge, last_check = row
                    user_data[int(discord_id)] = {
                        'github_user': github_user,
                        'points': points,
                        'badges': json.loads(badges) if badges else [],
                        'current_challenge': challenge,
                        'last_activity_check': datetime.fromisoformat(last_check) if last_check else datetime(1970,1,1, tzinfo=timezone.utc)
                    }
            logger.info("User data loaded from database")
        except Exception as e:
            logger.error(f"Failed to load user data: {str(e)}")
        return user_data

    def save_user_data(self, discord_id, data):
        try:
            with sqlite3.connect('user_data.db') as conn:
                c = conn.cursor()
                c.execute('''INSERT OR REPLACE INTO users
                            (discord_id, github_user, points, badges, current_challenge, last_activity_check)
                            VALUES (?, ?, ?, ?, ?, ?)''',
                          (str(discord_id), data['github_user'], data['points'], json.dumps(data['badges']),
                           data['current_challenge'], data['last_activity_check'].isoformat()))
                conn.commit()
                logger.info(f"Saved data for Discord ID {discord_id}")
        except Exception as e:
            logger.error(f"Failed to save user data for {discord_id}: {str(e)}")

    def validate_environment(self):
        if not all([GEMINI_API_KEY, GITHUB_TOKEN, DISCORD_BOT_TOKEN]):
            logger.error("Missing one or more environment variables")
            raise ValueError("Please set GEMINI_API_KEY, GITHUB_TOKEN, and DISCORD_BOT_TOKEN")
        try:
            self.github.get_user().login
            logger.info("GitHub API connection validated")
        except Exception as e:
            logger.error(f"Invalid GitHub token: {str(e)}")
            raise

    def graphql_query(self, query):
        """Execute GraphQL query for exact totals (no 1-year limit)."""
        return self.github._requester.requestGraphql(query)['data']
    
    def get_user_total_activity(self, gh_user):
        """Get EXACT total commits/issues/PRs via GraphQL + commits API."""
        owner = self.repo.owner.login
        name = self.repo.name
        query = f"""
        {{
          repository(owner:"{owner}", name:"{name}") {{
            issues(first:0, filterBy:{{createdBy:"{gh_user}"}}, states:[OPEN,CLOSED]) {{ totalCount }}
            pullRequests(first:0, filterBy:{{createdBy:"{gh_user}"}}, states:[OPEN,CLOSED]) {{ totalCount }}
          }}
        }}
        """
        data = self.graphql_query(query)
        issues = data['repository']['issues']['totalCount']
        prs = data['repository']['pullRequests']['totalCount']
        commits = self.repo.get_commits(author=gh_user).totalCount
        return commits, issues, prs

    async def get_user_activity(self, gh_user):
        """Async total activity for leaderboard."""
        commits, issues, prs = await self.loop.run_in_executor(
            None, self.get_user_total_activity, gh_user
        )
        return f"Commits={commits}, Issues={issues}, PRs={prs}"


    def add_commands(self):
        @self.command(name='set_repo')
        async def set_repo(ctx, repo_name: str):
            repo_name = repo_name.strip(' .')
            try:
                self.repo = await self.loop.run_in_executor(None, self.github.get_repo, repo_name)
                await ctx.send(f"Repository set to {repo_name}.")
                logger.info(f"Set repository to {repo_name}")
            except Exception as e:
                await ctx.send(f"Error setting repository: {str(e)}. Check if the repo exists and spelling is correct.")
                logger.error(f"Error setting repository {repo_name}: {str(e)}")

        @self.command(name='link_github')
        async def link_github(ctx, github_username: str):
            github_username = github_username.strip()
            if ctx.author.id in self.user_data and self.user_data[ctx.author.id]['github_user'] == github_username:
                await ctx.send(f"You are already linked!")
                return
            now = datetime.now(timezone.utc)
            # **FIX: Award ALL historical points on link**
            commits, issues, prs = await self.loop.run_in_executor(
                None, self.get_user_total_activity, github_username
            )
            points = commits * 10 + issues * 20 + prs * 30
            self.user_data[ctx.author.id] = {
                'github_user': github_username,
                'points': points,
                'badges': [],
                'current_challenge': None,
                'last_activity_check': now
            }
            self.update_badges(self.user_data[ctx.author.id])
            self.save_user_data(ctx.author.id, self.user_data[ctx.author.id])
            await ctx.send(f"✅ Linked @{github_username}! **{points} points** awarded for {commits}c/{issues}i/{prs}p!")
            logger.info(f"Linked {ctx.author.name} → {github_username}: {points} pts")

        @self.command(name='my_challenge')
        async def my_challenge(ctx):
            if self.repo is None or ctx.author.id not in self.user_data:
                await ctx.send("Please set the repository and link your GitHub account first.")
                return
            user_info = self.user_data[ctx.author.id]
            activity = await self.loop.run_in_executor(None, self.get_user_activity, user_info['github_user'])
            challenge = await self.generate_challenge(activity)
            user_info['current_challenge'] = challenge
            self.save_user_data(ctx.author.id, user_info)
            await ctx.send(f"Your personalized challenge: {challenge}")
            logger.info(f"Generated challenge for {ctx.author.name}: {challenge}")

        @self.command(name='leaderboard')
        @commands.cooldown(1, 30, commands.BucketType.channel)  # **FIX: Prevent spam**
        async def leaderboard(ctx):
            await self.poll_github_once()
            sorted_users = sorted(self.user_data.items(), key=lambda x: x[1]['points'], reverse=True)[:10]
            lb_text = "**Leaderboard**\n"
            for idx, (disc_id, data) in enumerate(sorted_users, 1):
                # **FIX: Safe user fetch**
                member = ctx.guild.get_member(disc_id)
                if member:
                    display = member.display_name
                else:
                    try:
                        user = await self.fetch_user(disc_id)
                        display = user.name
                    except:
                        display = "Unknown"
                activity = await self.get_user_activity(data['github_user'])
                badges = ', '.join(data['badges']) or 'None'
                lb_text += f"{idx}. **{display}** (@{data['github_user']}) - **{data['points']} pts** | {badges}\n*{activity}*\n\n"
            await ctx.send(lb_text)

        @self.command(name='sentiment')
        async def sentiment(ctx, message_id: int):
            try:
                msg = await ctx.channel.fetch_message(message_id)
                sent = await self.analyze_sentiment(msg.content)
                await ctx.send(f"Sentiment analysis: {sent}")
                logger.info(f"Sentiment analysis for message {message_id}: {sent}")
            except Exception as e:
                await ctx.send(f"Error: {str(e)}")
                logger.error(f"Error in sentiment analysis for message {message_id}: {str(e)}")

        @self.command(name='update_stats')
        async def update_stats(ctx):
            await self.poll_github_once()
            await ctx.send("Stats updated.")
            logger.info("Manually updated stats")

        @self.command(name='shutdown')
        @commands.has_permissions(administrator=True)
        async def shutdown(ctx):
            await ctx.send("Shutting down the bot...")
            logger.info(f"Shutdown initiated by {ctx.author.name}")
            await self.close()

    async def on_message(self, message):
        if message.author == self.user:
            return  # Ignore own messages to prevent self-loops
        await self.process_commands(message)

    async def setup_hook(self):
        self.bg_task = self.loop.create_task(self.poll_github_periodic())

    async def poll_github_once(self):
        # **FIX: Delta only (recent → search OK)**
        if not self.repo: return
        now = datetime.now(timezone.utc)
        repo_name = self.repo.full_name
        for disc_id, data in list(self.user_data.items()):
            gh_user = data['github_user']
            last_check = data['last_activity_check']
            try:
                def fetch_delta():
                    # Commits: full history support
                    commits = self.repo.get_commits(author=gh_user, since=last_check).totalCount
                    # Issues/PRs: search (delta recent <1y)
                    date_str = last_check.strftime('%Y-%m-%d')
                    issues_q = f"repo:{repo_name} is:issue author:{gh_user} created:>{date_str}"
                    prs_q = f"repo:{repo_name} is:pr author:{gh_user} created:>{date_str}"
                    issues = self.github.search_issues(issues_q).totalCount
                    prs = self.github.search_issues(prs_q).totalCount
                    return commits, issues, prs

                commits_d, issues_d, prs_d = await self.loop.run_in_executor(self.executor, fetch_delta)
                new_points = commits_d * 10 + issues_d * 20 + prs_d * 30
                if new_points > 0:
                    data['points'] += new_points
                    self.update_badges(data)
                    logger.info(f"{gh_user}: +{new_points} pts")
            except Exception as e:
                logger.error(f"Poll error {gh_user}: {e}")
            data['last_activity_check'] = now
            self.save_user_data(disc_id, data)
        self.last_global_check = now

    async def poll_github_periodic(self):
        await self.wait_until_ready()
        while not self.is_closed():
            if self.repo:
                await self.poll_github_once()
            await asyncio.sleep(300)  # Poll every 5 minutes

    def get_user_activity(self, gh_user):
        try:
            repo_name = self.repo.full_name
            commits = self.repo.get_commits(author=gh_user).totalCount
            issues_search = self.github.search_issues(query=f'repo:{repo_name} is:issue author:{gh_user}')
            issues_count = issues_search.totalCount
            prs_search = self.github.search_issues(query=f'repo:{repo_name} is:pr author:{gh_user}')
            prs_count = prs_search.totalCount
            logger.info(f"Fetched activity for {gh_user}: Commits={commits}, Issues={issues_count}, PRs={prs_count}")
            return f"has done Commits={commits}, Issues={issues_count}, PRs={prs_count}"
        except Exception as e:
            logger.error(f"Error fetching activity for {gh_user}: {str(e)}")
            return f"Error fetching activity: {str(e)}"

    async def generate_challenge(self, activity):
        prompt = f"Based on this GitHub user activity: {activity}. Generate a personalized, engaging challenge to boost collaboration, e.g., 'Review one PR to earn a collaborator badge'. Keep it short."
        return await self.call_gemini(prompt)

    async def analyze_sentiment(self, text):
        prompt = f"Analyze the sentiment of this discussion text: '{text}'. Provide a summary like 'Positive: encouraging collaboration' or 'Negative: frustration detected'. Consider biases and be neutral and give the explanation."
        return await self.call_gemini(prompt)

    async def call_gemini(self, prompt):
        url = f"https://generativelanguage.googleapis.com/v1/models/gemini-2.5-flash:generateContent?key={GEMINI_API_KEY}"
        data = {"contents": [{"parts": [{"text": prompt}]}]}
        headers = {'Content-Type': 'application/json'}
        ssl_context = ssl.create_default_context(cafile=certifi.where())
        connector = TCPConnector(ssl=ssl_context)
        async with ClientSession(connector=connector) as session:
            for attempt in range(3):
                try:
                    async with session.post(url, json=data, headers=headers) as response:
                        if response.status == 200:
                            result = await response.json()
                            response_text = result['candidates'][0]['content']['parts'][0]['text'].strip()
                            logger.info(f"Gemini API call successful: {response_text[:50]}...")
                            return response_text
                        elif response.status == 429:
                            logger.warning(f"Gemini rate limit hit, retrying in {2 ** attempt}s")
                            await asyncio.sleep(2 ** attempt)
                            continue
                        else:
                            error = await response.text()
                            logger.error(f"Gemini API error: {response.status} {error}")
                            return f"Error calling AI: {response.status} {error}"
                except Exception as e:
                    logger.error(f"Gemini API exception: {str(e)}")
                    return f"Error calling AI: {str(e)}"
        logger.error("Gemini API rate limit exceeded after retries")
        return "Error: Gemini API rate limit exceeded."

    def update_badges(self, user_data):
        points = user_data['points']
        badges = user_data['badges']
        if points >= 100 and 'Bronze Collaborator' not in badges:
            badges.append('Bronze Collaborator')
        if points >= 500 and 'Silver Collaborator' not in badges:
            badges.append('Silver Collaborator')
        if points >= 1000 and 'Gold Collaborator' not in badges:
            badges.append('Gold Collaborator')

    async def on_ready(self):
        logger.info(f'Logged in as {self.user} (ID: {self.user.id})')
        print(f'Logged in as {self.user} (ID: {self.user.id})')
        print('------')

async def main():
    try:
        bot = GamifiedGitHubDiscordBot()
        await bot.start(DISCORD_BOT_TOKEN)
    except Exception as e:
        logger.error(f"Failed to start bot: {str(e)}")
        print(f"Error: {str(e)}")

if __name__ == "__main__":
    try:
        loop = asyncio.get_running_loop()
        loop.create_task(main())
    except RuntimeError:
        asyncio.run(main())
