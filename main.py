import discord
from discord.ext import commands
import random

# Initialize the bot
intents = discord.Intents.default()
intents.message_content = True
bot = commands.Bot(command_prefix="!", intents=intents)

# Game state
game_active = False
user_score = 0
bot_score = 0
user_batting = True
overs = 0
wickets = 0
balls_remaining = 0
wickets_remaining = 0
game_message = None  # To store the bot's game message
last_user_choice = None  # To store the user's last choice
last_bot_choice = None  # To store the bot's last choice

# Cricket emojis
EMOJI_BAT = "🏏"
EMOJI_BALL = "🎾"
EMOJI_WICKET = "🎯"
EMOJI_TROPHY = "🏆"
EMOJI_SCORE = "📊"
EMOJI_CLOCK = "⏳"
EMOJI_WIN = "🎉"
EMOJI_LOSE = "😢"
EMOJI_TIE = "🤝"
EMOJI_BANG = "💥"

# Run emojis
RUN_EMOJIS = ["1️⃣", "2️⃣", "3️⃣", "4️⃣", "5️⃣", "6️⃣"]

@bot.event
async def on_ready():
    print(f"Bot is ready! Logged in as {bot.user}")

@bot.command(name="start", help="Start a new Hand Cricket game")
async def start(ctx):
    global game_active, user_score, bot_score, user_batting, overs, wickets, balls_remaining, wickets_remaining, game_message, last_user_choice, last_bot_choice

    if game_active:
        await ctx.send(embed=create_embed(
            "Game in Progress ⚠️",
            f"{EMOJI_BAT} A game is already in progress! Finish it first.",
            discord.Color.red()
        ))
        return

    # Ask for the number of overs
    await ctx.send(embed=create_embed(
        "Hand Cricket 🏏",
        f"{EMOJI_BALL} How many overs do you want to play?",
        discord.Color.blue()
    ))
    try:
        overs_msg = await bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.content.isdigit())
        overs = int(overs_msg.content)
    except:
        await ctx.send(embed=create_embed(
            "Timeout ⏰",
            f"{EMOJI_BALL} You took too long to respond. Game canceled.",
            discord.Color.red()
        ))
        return

    # Ask for the number of wickets
    await ctx.send(embed=create_embed(
        "Hand Cricket 🏏",
        f"{EMOJI_WICKET} How many wickets per inning?",
        discord.Color.blue()
    ))
    try:
        wickets_msg = await bot.wait_for("message", timeout=30, check=lambda m: m.author == ctx.author and m.content.isdigit())
        wickets = int(wickets_msg.content)
    except:
        await ctx.send(embed=create_embed(
            "Timeout ⏰",
            f"{EMOJI_BALL} You took too long to respond. Game canceled.",
            discord.Color.red()
        ))
        return

    # Initialize game state
    game_active = True
    user_score = 0
    bot_score = 0
    user_batting = True
    balls_remaining = overs * 6
    wickets_remaining = wickets
    last_user_choice = None
    last_bot_choice = None

    # Send the initial game embed
    game_message = await ctx.send(embed=create_game_embed())
    for emoji in RUN_EMOJIS:
        await game_message.add_reaction(emoji)

@bot.event
async def on_reaction_add(reaction, user):
    global game_active, user_score, bot_score, user_batting, balls_remaining, wickets_remaining, game_message, last_user_choice, last_bot_choice

    # Ignore reactions from the bot itself or if no game is active
    if user == bot.user or not game_active or reaction.message.id != game_message.id:
        return

    # Get the user's choice from the reaction emoji
    if reaction.emoji in RUN_EMOJIS:
        last_user_choice = RUN_EMOJIS.index(reaction.emoji) + 1
        last_bot_choice = random.randint(1, 6)  # Generate the bot's number

        if user_batting:
            await handle_user_batting()
        else:
            await handle_bot_batting()

        # Update the game embed
        await game_message.edit(embed=create_game_embed())

        # Check if the game is over
        if not game_active:
            await determine_winner(game_message.channel)

async def handle_user_batting():
    global user_score, user_batting, balls_remaining, wickets_remaining, last_user_choice, last_bot_choice

    if last_user_choice == last_bot_choice:
        # 50% chance of getting out
        if random.random() < 0.5:
            wickets_remaining -= 1
            if wickets_remaining == 0:
                user_batting = False
                balls_remaining = overs * 6
                wickets_remaining = wickets
    else:
        user_score += last_user_choice
        balls_remaining -= 1

    if balls_remaining == 0:
        user_batting = False
        balls_remaining = overs * 6
        wickets_remaining = wickets

async def handle_bot_batting():
    global bot_score, game_active, balls_remaining, wickets_remaining, last_user_choice, last_bot_choice

    if last_user_choice == last_bot_choice:
        wickets_remaining -= 1
        if wickets_remaining == 0:
            game_active = False
    else:
        bot_score += last_bot_choice
        balls_remaining -= 1

    if balls_remaining == 0:
        game_active = False

def create_game_embed():
    global user_score, bot_score, balls_remaining, wickets_remaining, user_batting, last_user_choice, last_bot_choice

    if user_batting:
        title = "Your Turn 🏏"
        description = f"{EMOJI_BAT} You are batting. React with a run emoji to play."
    else:
        title = "Bot's Turn 🏏"
        description = f"{EMOJI_BALL} You are bowling. React with a run emoji to play."

    embed = discord.Embed(title=title, description=description, color=discord.Color.blue())
    embed.add_field(name=f"{EMOJI_SCORE} Your Score", value=f"{user_score}", inline=True)
    embed.add_field(name=f"{EMOJI_SCORE} Bot's Score", value=f"{bot_score}", inline=True)
    embed.add_field(name=f"{EMOJI_CLOCK} Balls Remaining", value=f"{balls_remaining}", inline=True)
    embed.add_field(name=f"{EMOJI_WICKET} Wickets Remaining", value=f"{wickets_remaining}", inline=True)

    # Show the user's and bot's numbers after the user reacts
    if last_user_choice is not None and last_bot_choice is not None:
        embed.add_field(name=f"{EMOJI_BAT} Your Number", value=f"{last_user_choice}", inline=False)
        embed.add_field(name=f"{EMOJI_BALL} Bot's Number", value=f"{last_bot_choice}", inline=False)

        # Show "You are out! 💥" if the user is out
        if user_batting and last_user_choice == last_bot_choice and random.random() < 0.5:
            embed.add_field(name="Out! 💥", value="You are out! 💥", inline=False)

    return embed

async def determine_winner(channel):
    global user_score, bot_score
    embed = discord.Embed(
        title="Game Over 🏆",
        description=f"{EMOJI_SCORE} Final Scores:\n{EMOJI_BAT} Your score: {user_score}\n{EMOJI_BALL} Bot's score: {bot_score}",
        color=discord.Color.gold()
    )
    if user_score > bot_score:
        embed.add_field(name="Result 🎉", value=f"{EMOJI_WIN} Congratulations! You win!", inline=False)
    elif user_score < bot_score:
        embed.add_field(name="Result 😢", value=f"{EMOJI_LOSE} Sorry, the bot wins!", inline=False)
    else:
        embed.add_field(name="Result 🤝", value=f"{EMOJI_TIE} It's a tie!", inline=False)
    await channel.send(embed=embed)

@bot.command(name="end", help="End the current game")
async def end(ctx):
    global game_active
    if not game_active:
        await ctx.send(embed=create_embed(
            "No Game ❌",
            f"{EMOJI_BALL} No game is active.",
            discord.Color.red()
        ))
        return

    game_active = False
    await ctx.send(embed=create_embed(
        "Game Ended ⚡",
        f"{EMOJI_BALL} Game ended. Type `!start` to start a new game.",
        discord.Color.red()
    ))

def create_embed(title, description, color):
    embed = discord.Embed(title=title, description=description, color=color)
    return embed

# Run the bot
bot.run("MTExMzg3NjY3OTQ4ODcyMTAwNg.GNA_x4.iM5pZNiNynRCPqBqRK0Oi7Lj8Tp-fIzpuUDoxQ")  # Replace with your bot token
