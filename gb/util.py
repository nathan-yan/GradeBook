from flask import render_template
from bs4 import BeautifulSoup as bs

import requests
from requests import session

from . import db

def get_info_tables(soup):
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

                if link:
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

    # The first row of the table defines the seperate categories, so we'll skip the first row
    for row in table[1:]:
        for column in range (len(row)):
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
        if 

def filter_table_by_category(table, whitelist = [], blacklist = []):
    """Filters a info_table by a whitelist or blacklist, so that you can eliminate categories you don't want

    Args:
        table (list): An unparsed info_table
        whitelist (list): A list of categories you want included in the dictionary
        blacklist (list): A list of categories you don't want included in the dictionary

    Returns:
        list: The info_table but filtered
    """

    for category in table[0]:
        if category in blacklist:
            