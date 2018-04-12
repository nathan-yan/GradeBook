from flask import render_template
from bs4 import BeautifulSoup as bs

import requests
from requests import session
import random 

from . import db

def get_info_tables(soup, links = True):
    """Gets all info_tables in the HTML file

    Args:
        soup (BeautifulSoup): The soupified HTML content to parse
    
    Returns:
        list: A list of all info_tables
    """

    info_tables = soup.find_all(attrs = {
        "class" : "info_tbl"
    })

    tables = []
    for tbl in info_tables:
        tables.append([])

        rows = tbl.find_all("tr")

        for row in rows:
            tables[-1].append([])

            columns = row.find_all("td")

            for column in columns:
                # check for link first
                link = column.find('a')

                if link and links:
                    tables[-1][-1].append(str(link))
                
                else:
                    tables[-1][-1].append(column.text)
    
    return tables

def parse_info_tables(tables):
    """Parses a list of info_tables to an easy-to-manipulate dictionary format.

    Args:
        tables (list): A list of info_tables
    
    Returns:
        dict: A dictionary organized with the keys as first row categories, and the values being a list of values for the categories
    """

    new_tables = []
    for table in range (len(tables)):
        new_tables.append(parse_table(tables[table]))

    return new_tables

def parse_table(table):
    """Parses a single info_table into an easy-to-manipulate dictionary format.

    Args:
        table (list): A list of info_table contents
    
    Returns:
        dict: A dictionary organized with the keys as first row categories, and the values being a list of values for the categories
    """
    
    dictionary = { category : [] for category in table[0] }
    print(len(table[0]))
    # The first row of the table defines the seperate categories, so we'll skip the first row
    for row in table[1:]:
        print(len(row))
        for column in range (len(row)):
            print(column, end = ' ')
            dictionary[table[0][column]].append(row[column])     # Append the column value to its appropriate category
    
    return dictionary

def filter_parsed_by_category(dictionary, whitelist = [], blacklist = []):
    """Filters a parsed info_table by a whitelist or blacklist, so that you can eliminate categories you don't want

    Args:
        dictionary (dict): A parsed info_table
        whitelist (list): A list of categories you want included in the dictionary
        blacklist (list): A list of categories you don't want included in the dictionary

    Returns:
        dict: The parsed info_table but filtered
    """

    for category in dictionary:
        if category in blacklist:
            del dictionary[category]

    return dictionary

def filter_table_by_category(table, whitelist = [], blacklist = []):
    """Filters a info_table by a whitelist or blacklist, so that you can eliminate categories you don't want

    Args:
        table (list): An unparsed info_table
        whitelist (list): A list of categories you want included in the dictionary
        blacklist (list): A list of categories you don't want included in the dictionary

    Returns:
        list: The info_table but filtered
    """

    for category in range(len(table[0]) - 1, -1, -1):
        if blacklist:
            if table[0][category] in blacklist:
                for row in range(len(table) - 1, -1, -1):
                    del table[row][category]
        elif whitelist: 
            if table[0][category] not in whitelist:
                for row in range (len(table) - 1, -1, -1):
                    del table[row][category]

    return table

def salt(length):
    """Returns a token/salt of length `length`

    Args:
        length (int): The length of the salt
    
    Returns:
        string: The salt
    """

    alpha = 'abcdefghijklmnopqrstuvwxyzABCDEFGHIJKLMNOPQRSTUVWXYZ0123456789'
    s = ""
    for l in range (length):
        s += alpha[random.randint(0, len(alpha) - 1)]
    
    return s

if __name__ == "__main__":
    table = [
        ['c1', 'c2', 'c3'],
        ['test11', 'test12', 'test13'],
        ['test21', 'test22', 'test23'],
        ['test31', 'test32', 'test33']
    ]

    print(filter_table_by_category(table, whitelist = ['c1', 'c3']))