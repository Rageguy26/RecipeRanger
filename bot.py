import discord
from discord.ext import commands
from discord.ui import View, Button  # Combine these into a single line
import sqlite3
import os

from bot_token import TOKEN  # Import the token from bot_token.py

# Define the necessary intents
intents = discord.Intents.default()
intents.messages = True          # Enables the bot to receive message events
intents.guilds = True            # Enables the bot to interact with guild (server) related events
intents.message_content = True   # Required to access the content of messages
intents.reactions = True         # Enables the bot to handle reactions

# Initialize the bot with the specified intents
bot = commands.Bot(command_prefix="!", intents=intents, help_command=None)

# Path to the directory where the database will be stored
directory = r'C:\RecipeRanger'
if not os.path.exists(directory):
    os.makedirs(directory)  # Create the directory if it doesn't exist

# Path for the database file
db_path = '/app/data/crafting.db'

# Connect to the database
conn = sqlite3.connect(db_path)
c = conn.cursor()

# Create the table for storing item ingredients and descriptions
c.execute('''
CREATE TABLE IF NOT EXISTS items
(name TEXT UNIQUE, ingredients TEXT, description TEXT)
''')

# Create the table for storing ingredient costs
c.execute('''
CREATE TABLE IF NOT EXISTS ingredient_costs
(ingredient TEXT UNIQUE, cost_per_unit REAL)
''')

c.execute('''
CREATE TABLE IF NOT EXISTS user_ingredients
(user_id INTEGER, ingredient TEXT, quantity REAL, PRIMARY KEY (user_id, ingredient))
''')
conn.commit()

@bot.event
async def on_ready():
    print(f'Logged in as {bot.user.name}')

# Command to add new items and their ingredients
@bot.command()
async def add_item(ctx, *, args: str = None):
    if args is None:
        await ctx.send("Please specify an item name and description. Usage: `!add_item <item_name> | <description>`")
        return

    parts = args.split(' | ')
    if len(parts) < 2:
        await ctx.send("Please provide both an item name and a description separated by ' | '. Usage: `!add_item <item_name> | <description>`")
        return

    item_name = parts[0].strip().lower()  # Convert to lowercase
    description = parts[1].strip()

    await ctx.send("Please type the ingredients (e.g., '5 sugar') followed by 'done' when finished.")
    ingredients = []

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    embed = discord.Embed(title=f"Adding Ingredients for {item_name.title()}", description="Type ingredients and quantities.", color=discord.Color.blue())
    message = await ctx.send(embed=embed)

    while True:
        ingredient_input = await bot.wait_for('message', check=check)
        content = ingredient_input.content.lower()
        if content == 'done':
            break
        parts = content.split()
        if len(parts) < 2 or not parts[0].isdigit():
            await ctx.send("Incorrect format. Please enter the ingredient in the format 'quantity ingredient_name'. Example: '5 sugar'")
            continue
        ingredients.append(content)
        embed.description = f"Current ingredients for {item_name.title()}:\n" + '\n'.join(ingredients) + "\n\nType 'done' when finished or add another ingredient."
        await message.edit(embed=embed)

    ingredients_str = ', '.join(ingredients)
    try:
        c.execute('INSERT INTO items (name, ingredients, description) VALUES (?, ?, ?)', (item_name, ingredients_str, description))
        conn.commit()
        embed = discord.Embed(title="Item Added", description=f"{item_name.title()} added with ingredients: {ingredients_str}\nDescription: {description}", color=discord.Color.green())
        await message.edit(embed=embed)
    except sqlite3.IntegrityError:
        embed = discord.Embed(title="Error", description="Item already exists. Try updating it instead.", color=discord.Color.red())
        await message.edit(embed=embed)
    except sqlite3.Error as e:
        await ctx.send(f"Database error: {e}")

@bot.command()
async def list_items(ctx):
    c.execute('SELECT name, description FROM items')
    items = c.fetchall()
    
    if items:
        embed = discord.Embed(title="Items List", color=discord.Color.blue())
        view = View()

        for item in items:
            item_name = item[0]
            item_description = item[1]
            
            # Create a button for each item
            button = Button(label=item_name, style=discord.ButtonStyle.primary)

            async def button_callback(interaction, item_name=item_name):
                await list_item_details(ctx, item_name)  # Function to show item details
                await interaction.response.defer()  # Acknowledge the interaction

            button.callback = button_callback
            view.add_item(button)

        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("No items found in the database.")

async def list_item_details(ctx, item_name):
    c.execute('SELECT ingredients, description FROM items WHERE name = ?', (item_name,))
    item = c.fetchone()
    
    if item:
        ingredients, description = item
        embed = discord.Embed(title=item_name, description=description, color=discord.Color.green())
        embed.add_field(name="Ingredients", value=ingredients, inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No details found for {item_name}.")

# Command to list ingredients for a specific item
@bot.command()
async def list_ingredients(ctx, item_name: str = None):
    if item_name is None:
        await ctx.send("Please specify an item name. Usage: `!list_ingredients <item_name>`")
        return
    
    item_name = item_name.lower()  # Ensure the input is in lowercase
    c.execute('SELECT ingredients FROM items WHERE lower(name) = ?', (item_name,))  # Use lower() to ensure case-insensitive comparison
    ingredients = c.fetchone()
    
    if ingredients:
        embed = discord.Embed(title=f"Ingredients for {item_name}", description=ingredients[0], color=discord.Color.blue())
        await ctx.send(embed=embed)
    else:
        await ctx.send(f"No ingredients found for {item_name}.")

# Custom help command
@bot.command()
async def help(ctx):
    embed = discord.Embed(title="Help", description="List of available commands", color=discord.Color.green())

    embed.add_field(name="!add_item <item_name>", value="Add a new item and its ingredients.", inline=False)
    embed.add_field(name="!list_items", value="List all items in the database.", inline=False)
    embed.add_field(name="!list_ingredients <item_name>", value="List the ingredients of a specific item.", inline=False)
    embed.add_field(name="!calculate_ingredients <item_name> <quantity>", value="Calculate the required ingredients for a given quantity.", inline=False)
    embed.add_field(name="!calculate_cost <item_name> <quantity>", value="Calculate the total cost to craft an item.", inline=False)
    embed.add_field(name="!update_item <item_name>", value="Update the ingredients of an item.", inline=False)
    embed.add_field(name="!delete_item <item_name>", value="Delete an item from the database.", inline=False)
    embed.add_field(name="!add_ingredient <ingredient> <cost>", value="Add a new ingredient with its cost.", inline=False)
    embed.add_field(name="!search_item <item_name>", value="SELECT name, description FROM items WHERE name LIKE ? OR description LIKE?", inline=False)
    embed.add_field(name="!set_ingredient_quantity <ingredient_name> <quantity>", value="Set or update the quantity of an ingredient you have.", inline=False)
    embed.add_field(name="!check_ingredient_quantity <ingredient_name>", value="Check how much of a specific ingredient you have.", inline=False)
    embed.add_field(name="!list_my_ingredients", value="List all ingredients you currently have.", inline=False)
    embed.add_field(name="!list_ingredients_prices", value="SELECT ingredient, cost_per_unit FROM ingredient_costs", inline=False)

    await ctx.send(embed=embed)

# Command to calculate required ingredients for a given quantity
@bot.command()
async def calculate_ingredients(ctx, item_name: str, quantity: int):
    c.execute('SELECT ingredients FROM items WHERE name = ?', (item_name,))
    ingredients = c.fetchone()
    if not ingredients:
        await ctx.send("Item not found.")
        return

    ingredients_list = ingredients[0].split(', ')
    total_cost = 0
    response_lines = []

    for ingredient in ingredients_list:
        parts = ingredient.split(' ')
        ingredient_name = ' '.join(parts[1:])
        ingredient_quantity = int(parts[0]) * quantity

        c.execute('SELECT cost_per_unit FROM ingredient_costs WHERE ingredient = ?', (ingredient_name,))
        cost_info = c.fetchone()
        if cost_info:
            cost_per_unit = cost_info[0]
            cost = ingredient_quantity * cost_per_unit
            total_cost += cost
            response_lines.append(f"{ingredient_quantity}x {ingredient_name} at ${cost:.2f}")
        else:
            response_lines.append(f"{ingredient_quantity}x {ingredient_name} (cost not set)")

    embed = discord.Embed(title=f"Total cost to craft {quantity} of {item_name}", description='\n'.join(response_lines) + f"\n\n**Total Cost: ${total_cost:.2f}**", color=discord.Color.green())
    await ctx.send(embed=embed)

@bot.command()
async def update_item(ctx, item_name: str):
    item_name = item_name.lower()  # Convert to lowercase
    await ctx.send("Please enter the new ingredients list for this item, or type 'cancel' to stop.")

    def check(m):
        return m.author == ctx.author and m.channel == ctx.channel

    new_ingredients_msg = await bot.wait_for('message', check=check)
    if new_ingredients_msg.content.lower() == 'cancel':
        await ctx.send("Update canceled.")
        return

    new_ingredients = new_ingredients_msg.content
    c.execute('UPDATE items SET ingredients = ? WHERE lower(name) = ?', (new_ingredients, item_name))
    conn.commit()
    await ctx.send(f"Ingredients updated for {item_name}.")

@bot.command()
async def delete_item(ctx, item_name: str):
    item_name = item_name.lower()  # Convert to lowercase
    # Confirm deletion
    confirm_message = await ctx.send(f"Are you sure you want to delete {item_name}? React with ✅ to confirm or ❌ to cancel.")
    await confirm_message.add_reaction('✅')
    await confirm_message.add_reaction('❌')

    def check(reaction, user):
        return user == ctx.author and str(reaction.emoji) in ['✅', '❌']

    reaction, user = await bot.wait_for('reaction_add', check=check)
    if str(reaction.emoji) == '✅':
        c.execute('DELETE FROM items WHERE lower(name) = ?', (item_name,))
        conn.commit()
        await ctx.send(f"{item_name} has been deleted.")
    else:
        await ctx.send("Deletion canceled.")

@bot.command()
async def calculate_cost(ctx, item_name: str, quantity: int):
    item_name = item_name.lower()  # Ensure case insensitivity
    c.execute('SELECT ingredients FROM items WHERE lower(name) = ?', (item_name,))
    result = c.fetchone()

    if not result:
        await ctx.send("Item not found.")
        return

    ingredients_list = result[0].split(', ')
    total_cost = 0
    response_lines = []

    for ingredient_info in ingredients_list:
        parts = ingredient_info.split(' ')
        if len(parts) < 2:
            await ctx.send(f"Error in ingredient format: '{ingredient_info}'. Expected format: 'quantity ingredient_name'.")
            return
        quantity_needed = int(parts[0]) * quantity
        ingredient_name = ' '.join(parts[1:])  # Get the ingredient name

        c.execute('SELECT cost_per_unit FROM ingredient_costs WHERE ingredient = ?', (ingredient_name,))
        cost_info = c.fetchone()
        if cost_info:
            cost_per_unit = cost_info[0]
            cost = quantity_needed * cost_per_unit
            total_cost += cost
            response_lines.append(f"{quantity_needed}x {ingredient_name} at ${cost:.2f}")
        else:
            response_lines.append(f"{quantity_needed}x {ingredient_name} (cost not set)")

    if response_lines:
        embed = discord.Embed(title=f"Total cost to craft {quantity} of {item_name}", description='\n'.join(response_lines) + f"\n\n**Total Cost: ${total_cost:.2f}**", color=discord.Color.green())
        await ctx.send(embed=embed)
    else:
        await ctx.send("No cost data available for ingredients.")

@bot.command()
async def add_ingredient(ctx, *, args: str):
    parts = args.rsplit(' ', 1)  # Split from the right to separate the cost
    if len(parts) != 2:
        await ctx.send("Please provide the ingredient name and cost. Usage: `!add_ingredient <ingredient_name> <cost>`")
        return

    ingredient_name = parts[0]  # All but the last part is the ingredient name
    try:
        cost = float(parts[1])  # Convert the last part to float
    except ValueError:
        await ctx.send("Invalid cost. Please provide a numeric value for the cost.")
        return

    # Check if the ingredient already exists and update or insert accordingly
    c.execute('SELECT cost_per_unit FROM ingredient_costs WHERE ingredient = ?', (ingredient_name,))
    if c.fetchone():
        c.execute('UPDATE ingredient_costs SET cost_per_unit = ? WHERE ingredient = ?', (cost, ingredient_name))
        await ctx.send(f"Updated the cost of {ingredient_name} to ${cost:.2f} per unit.")
    else:
        c.execute('INSERT INTO ingredient_costs (ingredient, cost_per_unit) VALUES (?, ?)', (ingredient_name, cost))
        await ctx.send(f"Added {ingredient_name} with a cost of ${cost:.2f} per unit.")
    conn.commit()

@bot.command()
async def set_ingredient_quantity(ctx, *, args: str):
    parts = args.rsplit(' ', 1)
    if len(parts) != 2:
        await ctx.send("Usage: `!set_ingredient_quantity <ingredient_name> <quantity>`")
        return

    ingredient_name = parts[0]
    try:
        quantity = float(parts[1])
    except ValueError:
        await ctx.send("Invalid quantity. Please provide a numeric value.")
        return

    user_id = ctx.author.id

    c.execute('''
    INSERT INTO user_ingredients (user_id, ingredient, quantity)
    VALUES (?, ?, ?)
    ON CONFLICT(user_id, ingredient) DO UPDATE SET quantity = ?
    ''', (user_id, ingredient_name, quantity, quantity))

    conn.commit()
    await ctx.send(f"Set {quantity} of {ingredient_name} for <@{user_id}>.")

@bot.command()
async def check_ingredient_quantity(ctx, *, ingredient_name: str):
    user_id = ctx.author.id
    c.execute('SELECT quantity FROM user_ingredients WHERE user_id = ? AND ingredient = ?', (user_id, ingredient_name))
    result = c.fetchone()
    
    if result:
        await ctx.send(f"You have {result[0]} of {ingredient_name}.")
    else:
        await ctx.send(f"You do not have any {ingredient_name} recorded.")

@bot.command()
async def list_my_ingredients(ctx):
    user_id = ctx.author.id
    c.execute('SELECT ingredient, quantity FROM user_ingredients WHERE user_id = ?', (user_id,))
    ingredients = c.fetchall()

    if ingredients:
        embed = discord.Embed(title="Your Ingredients", color=discord.Color.blue())
        for ingredient, quantity in ingredients:
            embed.add_field(name=ingredient, value=f"Quantity: {quantity}", inline=False)
        await ctx.send(embed=embed)
    else:
        await ctx.send("You don't have any ingredients recorded.")

class PaginatedIngredientsView(View):
    def __init__(self, ctx, ingredients, start=0, per_page=5):
        super().__init__()
        self.ctx = ctx
        self.ingredients = ingredients
        self.start = start
        self.per_page = per_page
        self.end = start + per_page
        self.max = len(ingredients)
        self.populate_buttons()

    def populate_buttons(self):
        self.clear_items()
        for ingredient, price in self.ingredients[self.start:self.end]:
            button = Button(label=f"{ingredient}: ${price:.2f}", style=discord.ButtonStyle.secondary)
            button.callback = lambda interaction, button=button: self.edit_price_callback(interaction, button)
            self.add_item(button)
        
        # Add navigation buttons
        if self.start > 0:
            prev_button = Button(label="Previous", style=discord.ButtonStyle.primary)
            prev_button.callback = self.show_previous
            self.add_item(prev_button)

        if self.end < self.max:
            next_button = Button(label="Next", style=discord.ButtonStyle.primary)
            next_button.callback = self.show_next
            self.add_item(next_button)

    async def edit_price_callback(self, interaction, button):
        await interaction.response.send_message(f"Enter the new price for {button.label.split(':')[0]}:", ephemeral=True)
        message = await self.ctx.bot.wait_for('message', check=lambda m: m.author == interaction.user and m.channel == interaction.channel)
        try:
            new_price = float(message.content)
            c.execute('UPDATE ingredient_costs SET cost_per_unit = ? WHERE ingredient = ?', (new_price, button.label.split(':')[0]))
            conn.commit()
            await interaction.followup.send(f"Updated the price of {button.label.split(':')[0]} to ${new_price:.2f}")
        except ValueError:
            await interaction.followup.send("Invalid price. Please enter a numeric value.")

    async def show_previous(self, interaction):
        new_start = max(0, self.start - self.per_page)
        new_view = PaginatedIngredientsView(self.ctx, self.ingredients, start=new_start, per_page=self.per_page)
        await interaction.response.edit_message(view=new_view)

    async def show_next(self, interaction):
        new_start = min(self.max, self.end)
        new_view = PaginatedIngredientsView(self.ctx, self.ingredients, start=new_start, per_page=self.per_page)
        await interaction.response.edit_message(view=new_view)

@bot.command()
async def list_ingredients_prices(ctx):
    c.execute('SELECT ingredient, cost_per_unit FROM ingredient_costs')
    ingredients = c.fetchall()
    
    if ingredients:
        view = PaginatedIngredientsView(ctx, ingredients, per_page=5)
        embed = discord.Embed(title="Ingredient Prices", description="Click an ingredient to edit its price.", color=discord.Color.blue())
        await ctx.send(embed=embed, view=view)
    else:
        await ctx.send("No ingredients found.")

# Run the bot
bot.run(TOKEN)
