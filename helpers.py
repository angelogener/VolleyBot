import discord
def has_planner_role(ctx):
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(ctx.guild.roles, name="Planners")

    if role_access not in ctx.author.roles:
        print("User does not have permission to run this command.")
        return False
    return True

def has_planner_role_interaction(interaction: discord.Interaction):
    # Specifically add Planners as the sole role capable of using this command
    role_access = discord.utils.get(interaction.guild.roles, name="Planners")

    if role_access not in interaction.user.roles:
        print("User does not have permission to run this command.")
        return False
    return True
