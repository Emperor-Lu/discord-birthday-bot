import discord

from discord.ext import commands, tasks

from discord import app_commands
import os
import json

from datetime import datetime, timezone



TOKEN = os.getenv("TOKEN")

ANNOUNCEMENT_CHANNEL_ID = 1511148697344544948
VENT_CHANNEL_ID = 1511049009425416354

BIRTHDAY_ROLE_NAME = "🎉 Birthday"



intents = discord.Intents.default()

intents.members = True



bot = commands.Bot(command_prefix="!", intents=intents)



BIRTHDAY_FILE = "birthdays.json"

ANNOUNCED_FILE = "announced.json"





# ---------------- FILE HELPERS ----------------



def load_birthdays():

    try:

        with open(BIRTHDAY_FILE, "r") as f:

            return json.load(f)

    except FileNotFoundError:

        return {}



def save_birthdays(data):

    with open(BIRTHDAY_FILE, "w") as f:

        json.dump(data, f, indent=4)



def load_announced():

    try:

        with open(ANNOUNCED_FILE, "r") as f:

            return json.load(f)

    except FileNotFoundError:

        return {}



def save_announced(data):

    with open(ANNOUNCED_FILE, "w") as f:

        json.dump(data, f, indent=4)





# ---------------- ROLE HELPERS ----------------



async def get_birthday_role(guild: discord.Guild):

    role = discord.utils.get(guild.roles, name=BIRTHDAY_ROLE_NAME)



    if role is None:

        role = await guild.create_role(name=BIRTHDAY_ROLE_NAME)

        print("Created Birthday role")



    return role





# ---------------- BOT READY ----------------



@bot.event

async def on_ready():

    print(f"Logged in as {bot.user}")



    try:

        synced = await bot.tree.sync()

        print(f"Synced {len(synced)} slash commands")

    except Exception as e:

        print(e)



    if not birthday_check.is_running():

        birthday_check.start()



    if not cleanup_roles.is_running():

        cleanup_roles.start()


class VentModal(discord.ui.Modal, title="Anonymous Vent"):

    vent_text = discord.ui.TextInput(
        label="What's on your mind?",
        style=discord.TextStyle.paragraph,
        placeholder="Type your vent here...",
        required=True,
        max_length=1000
    )

    async def on_submit(self, interaction: discord.Interaction):

        channel = bot.get_channel(VENT_CHANNEL_ID)

        if channel is None:
            await interaction.response.send_message(
                "Vent channel not found.",
                ephemeral=True
            )
            return

        embed = discord.Embed(
            title="💭 Anonymous Vent",
            description=self.vent_text.value,
            color=discord.Color.blurple()
        )

        await channel.send(embed=embed)

        await interaction.response.send_message(
            "Your anonymous vent has been posted.",
            ephemeral=True
        )


# ---------------- /birthday ----------------



@bot.tree.command(name="birthday", description="Register your birthday")

@app_commands.describe(month="Month (1-12)", day="Day (1-31)")

async def birthday(interaction: discord.Interaction, month: int, day: int):



    data = load_birthdays()



    data[str(interaction.user.id)] = {

        "month": month,

        "day": day,

        "name": interaction.user.display_name

    }



    save_birthdays(data)



    await interaction.response.send_message(

        f"🎂 Birthday saved as {month}/{day}!",

        ephemeral=True

    )

# ----------------    /vent     ----------------

@bot.tree.command(
    name="vent",
    description="Post an anonymous vent"
)
async def vent(interaction: discord.Interaction):
    await interaction.response.send_modal(VentModal())


# ---------------- /nextbirthday ----------------



@bot.tree.command(name="nextbirthday", description="Check your next birthday")

async def nextbirthday(interaction: discord.Interaction):



    data = load_birthdays()

    user = data.get(str(interaction.user.id))



    if not user:

        await interaction.response.send_message("You haven't set a birthday yet!", ephemeral=True)

        return



    now = datetime.now(timezone.utc)



    bday = datetime(now.year, user["month"], user["day"], tzinfo=timezone.utc)



    if bday < now:

        bday = datetime(now.year + 1, user["month"], user["day"], tzinfo=timezone.utc)



    days_left = (bday - now).days



    await interaction.response.send_message(

        f"🎂 Your next birthday is in **{days_left} days**!",

        ephemeral=True

    )





# ---------------- BIRTHDAY CHECK ----------------



@tasks.loop(minutes=1)

async def birthday_check():



    now = datetime.now(timezone.utc)

    today_key = f"{now.year}-{now.month}-{now.day}"



    birthdays = load_birthdays()

    announced = load_announced()



    if today_key not in announced:

        announced[today_key] = []



    for guild in bot.guilds:

        channel = guild.get_channel(ANNOUNCEMENT_CHANNEL_ID)

        if channel is None:

            continue



        role = await get_birthday_role(guild)



        for user_id, info in birthdays.items():



            if user_id in announced[today_key]:

                continue



            if info["month"] == now.month and info["day"] == now.day:



                member = guild.get_member(int(user_id))



                if member:

                    await channel.send(

                        f"🎉 Happy Birthday {member.mention}! 🎂"

                    )



                    try:

                        await member.add_roles(role)

                    except:

                        pass



                    announced[today_key].append(user_id)

                    save_announced(announced)





# ---------------- ROLE CLEANUP ----------------



@tasks.loop(hours=1)

async def cleanup_roles():



    role_name = BIRTHDAY_ROLE_NAME



    for guild in bot.guilds:

        role = discord.utils.get(guild.roles, name=role_name)



        if role is None:

            continue



        for member in role.members:

            try:

                await member.remove_roles(role)

            except:

                pass





# ---------------- RUN ----------------



bot.run(TOKEN)
