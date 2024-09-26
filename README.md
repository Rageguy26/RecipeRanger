
# RecipeRanger Bot

## Introduction
RecipeRanger is a Discord bot designed to manage recipes and their ingredients within Discord communities. It supports various commands that allow users to add and manage recipes, list and edit ingredient details, and calculate the cost of recipes based on ingredients and their quantities.

## Features
- Add new recipes with a detailed description and ingredient list.
- List all recipes stored in the database with clickable buttons for details.
- Manage ingredient quantities and costs per unit for precise control over recipe data.
- Calculate the total cost of preparing a recipe based on ingredient costs.
- User-specific ingredient management to track individual ingredient quantities.

## Prerequisites
- Python 3.9 or higher
- `discord.py` library
- SQLite3

## Setup
1. **Install Dependencies**:
   Make sure Python 3.9 or later is installed on your system. You can install all required Python libraries with:
   \`\`\`bash
   pip install discord.py
   \`\`\`

2. **Database Setup**:
   The bot uses SQLite for data management. Ensure the database file is created and tables are set up by running the bot script once.

3. **Configuration**:
   - Set your bot token in a file named `bot_token.py` or directly in your script.
   - Adjust the database path as necessary in the bot script.

4. **Run the Bot**:
   Execute the script to run your bot:
   \`\`\`bash
   python bot_script.py
   \`\`\`

## Usage
- **Add a Recipe**:
  \`\`\`
  !add_item <item_name> | <description>
  \`\`\`
  Follow the prompts to add ingredients.

- **List All Recipes**:
  \`\`\`
  !list_items
  \`\`\`
  Click on a recipe name to view its details.

- **Calculate Recipe Cost**:
  \`\`\`
  !calculate_cost <item_name> <quantity>
  \`\`\`

- **Update Recipe Ingredients**:
  \`\`\`
  !update_item <item_name>
  \`\`\`
  Follow the prompts to update ingredients.

- **Delete a Recipe**:
  \`\`\`
  !delete_item <item_name>
  \`\`\`

- **Manage Ingredient Inventory**:
  \`\`\`
  !set_ingredient_quantity <ingredient_name> <quantity>
  \`\`\`
  \`\`\`
  !check_ingredient_quantity <ingredient_name>
  \`\`\`

## Contributing
Contributions to RecipeRanger are welcome! Feel free to fork the repository, make changes, and submit pull requests.
