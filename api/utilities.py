import datetime
import re
"""### **1.3 Utility Functions**"""

"""# UTILITY FUNCTIONS"""
# Convert to lowercase
def string_to_slug(text):
    slug = text.lower()
    # Replace spaces with hyphens
    slug = slug.replace(' ', '-')
    # Remove non-alphanumeric characters except hyphens
    slug = re.sub(r'[^a-z0-9-]', '', slug)
    return slug

# Convert slug into title case
def slug_to_string(slug_text):
    # Split the slug text by '-'
    words = slug_text.split('-')

    # Capitalize each word and join them with a space
    title_case_text = ' '.join(word.capitalize() for word in words)

    return title_case_text

# Unix timestamp conversion
def unix_time_to_date(timestamp):
  # Convert Unix timestamp to datetime object
  dt_object = datetime.fromtimestamp(timestamp)

  # Format the datetime object as a string
  formatted_date = dt_object.strftime("%d-%b-%Y")

  return formatted_date

# Using poisson distribution to calculate probability fo home team and away team scoring x number of goals
def factorial(x):
  # When we get to x = 1 or 0, just return one as the thing to be multiplied by the other numbers
  if x == 0 or x == 1:
        return 1
  # Else return the multiplication of x and x-1
  return x * factorial(x - 1)

# Poisson Distribution Formula for likelihood of a team scoring x number of goals
def poisson_distribution(rate, x):
  E = 2.718
  return (rate ** x) * (E ** -rate)/ factorial(x)

# Convert strings into param strings, i.e. instead of 'Moises Caicedo', you'd have 'moises+caicedo'
def str_param(str):
  return '+'.join(str.split(' ')).lower()

# function to split the team_name in half because team_name concatenates onto itself when the dfs are added
def split_name_in_half(name):
  size = int(len(name)/2)
  return name[:size]
