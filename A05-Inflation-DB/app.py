# https://github.com/kivy/kivy/issues/7094
# https://github.com/kivy/kivy/pull/7299
# https://github.com/kivy/kivy/pull/7293
from ctypes import windll, c_int64
windll.user32.SetProcessDpiAwarenessContext(c_int64(-1))

# Red dot hot fix
from kivy.config import Config
Config.set('input', 'mouse', 'mouse,multitouch_on_demand')

# Import statements
import mysql.connector
import csv
import kivy
from kivymd.app import MDApp
from kivy.lang import Builder
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.properties import ObjectProperty
from kivymd.uix.dialog import MDDialog
from kivymd.uix.button import MDFlatButton
import matplotlib.pyplot as plt
from kivy.garden.matplotlib.backend_kivyagg import FigureCanvasKivyAgg
from kivy.uix.boxlayout import BoxLayout
import webbrowser
import pandas as pd
from kivy.core.window import Window
import requests
import os
from kivy.uix.image import Image
import threading
from kivy.clock import Clock

# ======================================DDL=====================================

# Checks that the database has been properly created
def checkDBConnection():
    # Try to establish a connection
    try:
        # Connect to rideshareDB
        inflationDB = mysql.connector.connect(host="localhost",
                                              user="root",
                                              password="RosaDev68!",
                                              auth_plugin='mysql_native_password',
                                              database="Inflation")

        # Try to create the tables, views, index and insert the govt data
        try:
            createTables(inflationDB)
            createViews(inflationDB)
            createIndex(inflationDB)
            all_dates = insertCPI(inflationDB)
            insertPCE(inflationDB, all_dates)
            insertPPI(inflationDB, all_dates)
            insertFED(inflationDB, all_dates)

            # Return the connection
            return inflationDB

        # If there is an error, then everything already exists
        except:
            pullLatestPCE(inflationDB)
            pullLatestCPI(inflationDB)
            pullLatestPPI(inflationDB)
            pullLatestFED(inflationDB)

            # Return the connection
            return inflationDB

    # If the initial connection fails, create the database and try again
    except:
        # Build the database
        tmp_connection = mysql.connector.connect(host="localhost",
                                              user="root",
                                              password="RosaDev68!",
                                              auth_plugin='mysql_native_password')

        # Connect the cursor
        tmp_cursor = tmp_connection.cursor()

        # Create the Inflation database
        tmp_cursor.execute("CREATE SCHEMA Inflation;")

        # Close the temporary variables
        tmp_cursor.close()
        tmp_connection.close()

        # Attempt the connection again
        inflationDB = checkDBConnection()

        # Return the connection
        return inflationDB

# Create the tables used in the database
def createTables(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Create PCE Table
    cursor.execute("CREATE TABLE PCE ( \
    pce_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    date DATE NOT NULL, \
    value FLOAT, \
    inflation FLOAT);")

    # Create CPI Table
    cursor.execute("CREATE TABLE CPI ( \
    cpi_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    date DATE NOT NULL, \
    value FLOAT, \
    inflation FLOAT);")

    # Create PPI Table
    cursor.execute("CREATE TABLE PPI ( \
    ppi_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    date DATE NOT NULL, \
    value FLOAT, \
    inflation FLOAT);")

    # Create FED Table
    cursor.execute("CREATE TABLE FED ( \
    fed_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    date DATE NOT NULL, \
    value FLOAT);")

    # Create User Table
    cursor.execute("CREATE TABLE User ( \
    user_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    username VARCHAR(40) NOT NULL, \
    password VARCHAR(40) NOT NULL, \
    data_view BOOLEAN NOT NULL DEFAULT 0, \
    deleted BOOLEAN NOT NULL DEFAULT 0);")

    # Create DBLogs Table
    cursor.execute("CREATE TABLE DBLogs ( \
    log_ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY, \
    user_ID INT NOT NULL, \
    old_username VARCHAR(40), \
    new_username VARCHAR(40), \
    old_password VARCHAR(40), \
    new_password VARCHAR(40));")

    # Close cursor
    cursor.close()

# Create the views used in the database
def createViews(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Create OriginalData View
    cursor.execute("CREATE VIEW OriginalData AS \
    SELECT CPI.date AS date, pce.inflation AS pce_inflation, CPI.inflation AS cpi_inflation, PPI.inflation AS ppi_inflation, FED.value AS fed_value \
    FROM CPI \
    INNER JOIN PCE ON CPI.date = PCE.date \
    INNER JOIN PPI ON CPI.date = PPI.date \
    INNER JOIN FED ON CPI.date = FED.date \
    GROUP BY date;")

    # Create CustomData View
    cursor.execute("CREATE VIEW CustomData AS \
    SELECT CPI.cpi_ID AS custom_ID, CPI.date AS date, PCE.inflation AS pce_inflation, CPI.inflation AS cpi_inflation, PPI.inflation AS ppi_inflation, FED.value AS fed_value \
    FROM CPI \
    INNER JOIN PCE ON CPI.date = PCE.date \
    INNER JOIN PPI ON CPI.date = PPI.date \
    INNER JOIN FED ON CPI.date = FED.date \
    GROUP BY date;")

    # Close cursor
    cursor.close()

# Create the index used for searching usernames in the User table
def createIndex(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    cursor.execute("CREATE INDEX usernameIndex ON User(username);")

    # Close cursor
    cursor.close()

# Inserts PCE data from FRED webiste
def insertPCE(inflationDB, all_dates):
    # Create cursor
    cursor = inflationDB.cursor()

    # Request data from FRED website
    pce_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=PCEPI&scale=left&cosd=1959-01-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1959-01-01")

    # Transfer request to pce.csv file
    with open('pce.csv', 'wb') as pce_file:
        pce_file.write(pce_req.content)

    # Re-open pce.csv
    pce_file = open('pce.csv')
    pce_csv_reader = csv.reader(pce_file)

    # Ignore column titles
    next(pce_csv_reader)

    # Transfer the contents of pce.csv to pce_records
    pce_records = []
    for record in pce_csv_reader:
        pce_records.append(record)

    # Close the file
    pce_file.close()

    # Delete the file from the directory
    os.remove('pce.csv')

    # Used to calculate yearly_inflation
    pce_values = []
    pce_values_index = 0

    # Used to differentiate between entering a blank date and a pce date
    adjustable_index = 0

    # Insert data into inflationDB
    for i in range(len(all_dates)-1):
        # Checks to see if the pce_record matches the current date
        if all_dates[i] == pce_records[adjustable_index][0]:
            # Increment the adjustable index to keep pace with
            adjustable_index += 1

            # Store the pce_record
            record = pce_records[adjustable_index]

            # Stores record[1] (value) in pce_values if it exists (used for calculating yearly_inflation)
            if record[1]:
                pce_values.append(record[1])

                # Record with date, value, and available inflation value
                if (len(pce_values) > 12):
                    # Calculate yearly inflation
                    yearly_inflation = (float(pce_values[pce_values_index]) - float(pce_values[pce_values_index-12])) / float(pce_values[pce_values_index-12]) * 100.0

                    query = "INSERT INTO PCE (date, value, inflation) \
                             VALUES (%s, %s, %s);"
                    cursor.execute(query, (record[0], record[1], yearly_inflation))
                    inflationDB.commit()

                # Record with date and value
                else:
                    query = "INSERT INTO PCE (date, value) \
                             VALUES (%s, %s);"
                    cursor.execute(query, (record[0], record[1]))
                    inflationDB.commit()

                pce_values_index += 1

            # Record with only date
            else:
                query = "INSERT INTO PCE (date) \
                         VALUES (%s);"
                cursor.execute(query, (record[0],))
                inflationDB.commit()

        # If the pce_record does not match the current date, insert just the date
        else:
            query = "INSERT INTO PCE (date) \
                     VALUES (%s);"
            cursor.execute(query, (all_dates[i],))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Inserts CPI data from FRED website
def insertCPI(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Request data from FRED website
    cpi_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CPIAUCSL&scale=left&cosd=1947-01-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1947-01-01")

    # Transfer request to cpi.csv file
    with open('cpi.csv', 'wb') as cpi_file:
        cpi_file.write(cpi_req.content)

    # Re-open cpi.csv
    cpi_file = open('cpi.csv')
    cpi_csv_reader = csv.reader(cpi_file)

    # Ignore column titles
    next(cpi_csv_reader)

    # Transfer the contents of cpi.csv to cpi_records
    cpi_records = []
    for record in cpi_csv_reader:
        cpi_records.append(record)

    # Close the file
    cpi_file.close()

    # Delete the file from the directory
    os.remove('cpi.csv')

    # Used to calculate yearly_inflation
    cpi_values = []
    cpi_values_index = 0

    # Stores every date in the database since cpi is the longest running price index
    all_dates = []

    # Insert data into inflationDB
    for record in cpi_records:
        # Track all of the dates in the entire database
        all_dates.append(record[0])

        # Stores record[1] (value) in cpi_values if it exists (used for calculating yearly_inflation)
        if record[1]:
            cpi_values.append(record[1])

            # Record with date, value, and available inflation value
            if (len(cpi_values) > 12):
                # Calculate yearly inflation
                yearly_inflation = (float(cpi_values[cpi_values_index]) - float(cpi_values[cpi_values_index-12])) / float(cpi_values[cpi_values_index-12]) * 100.0

                query = "INSERT INTO CPI (date, value, inflation) \
                         VALUES (%s, %s, %s);"
                cursor.execute(query, (record[0], record[1], yearly_inflation))
                inflationDB.commit()

            # Record with date and value
            else:
                query = "INSERT INTO CPI (date, value) \
                         VALUES (%s, %s);"
                cursor.execute(query, (record[0], record[1]))
                inflationDB.commit()

            cpi_values_index += 1

        # Record with only date
        else:
            query = "INSERT INTO CPI (date) \
                     VALUES (%s);"
            cursor.execute(query, (record[0],))
            inflationDB.commit()

    # Close cursor
    cursor.close()

    # Passes along the dates to be compared to with the other price indices
    return all_dates

# Inserts PPI data from FRED website
def insertPPI(inflationDB, all_dates):
    # Create cursor
    cursor = inflationDB.cursor()

    # Request data from FRED website
    ppi_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=PPIFIS&scale=left&cosd=2009-11-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=2009-11-01")

    # Transfer request to ppi.csv file
    with open('ppi.csv', 'wb') as ppi_file:
        ppi_file.write(ppi_req.content)

    # Re-open ppi.csv
    ppi_file = open('ppi.csv')
    ppi_csv_reader = csv.reader(ppi_file)

    # Ignore column titles
    next(ppi_csv_reader)

    # Transfer the contents of ppi.csv to ppi_records
    ppi_records = []
    for record in ppi_csv_reader:
        ppi_records.append(record)

    # Close the file
    ppi_file.close()

    # Delete the file from the directory
    os.remove('ppi.csv')

    # Used to calculate yearly_inflation
    ppi_values = []
    ppi_values_index = 0

    # Used to differentiate between entering a blank date and a ppi date
    adjustable_index = 0

    # Insert data into inflationDB
    for i in range(len(all_dates)-1):
        # Checks to see if the ppi_record matches the current date
        if all_dates[i] == ppi_records[adjustable_index][0]:
            # Increment the adjustable index to keep pace with
            adjustable_index += 1

            # Store the ppi_record
            record = ppi_records[adjustable_index]

            # Stores record[1] (value) in ppi_values if it exists (used for calculating yearly_inflation)
            if record[1]:
                ppi_values.append(record[1])

                # Record with date, value, and available inflation value
                if (len(ppi_values) > 12):
                    # Calculate yearly inflation
                    yearly_inflation = (float(ppi_values[ppi_values_index]) - float(ppi_values[ppi_values_index-12])) / float(ppi_values[ppi_values_index-12]) * 100.0

                    query = "INSERT INTO PPI (date, value, inflation) \
                             VALUES (%s, %s, %s);"
                    cursor.execute(query, (record[0], record[1], yearly_inflation))
                    inflationDB.commit()

                # Record with date and value
                else:
                    query = "INSERT INTO PPI (date, value) \
                             VALUES (%s, %s);"
                    cursor.execute(query, (record[0], record[1]))
                    inflationDB.commit()

                ppi_values_index += 1

            # Record with only date
            else:
                query = "INSERT INTO PPI (date) \
                         VALUES (%s);"
                cursor.execute(query, (record[0],))
                inflationDB.commit()

        # If the ppi_record does not match the current date, insert just the date
        else:
            query = "INSERT INTO PPI (date) \
                     VALUES (%s);"
            cursor.execute(query, (all_dates[i],))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Inserts FED data from FRED website
def insertFED(inflationDB, all_dates):
    # Create cursor
    cursor = inflationDB.cursor()

    # Request data from FRED website
    fed_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=748&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=FEDFUNDS&scale=left&cosd=1954-07-01&coed=2022-04-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1954-07-01")

    # Transfer request to fed.csv file
    with open('fed.csv', 'wb') as fed_file:
        fed_file.write(fed_req.content)

    # Re-open fed.csv
    fed_file = open('fed.csv')
    fed_csv_reader = csv.reader(fed_file)

    # Ignore column titles
    next(fed_csv_reader)

    # Transfer the contents of fed.csv to fed_records
    fed_records = []
    for record in fed_csv_reader:
        fed_records.append(record)

    # Close the file
    fed_file.close()

    # Delete the file from the directory
    os.remove('fed.csv')

    # Used to differentiate between entering a blank date and a fed date
    adjustable_index = 0

    # Insert data into inflationDB
    for i in range(len(all_dates)-1):
        # Checks to see if the fed_record matches the current date
        if all_dates[i] == fed_records[adjustable_index][0]:
            # Increment the adjustable index to keep pace with
            adjustable_index += 1

            # Store the fed_record
            record = fed_records[adjustable_index]

            # Record with date and value
            if record[1]:
                query = "INSERT INTO FED (date, value) \
                         VALUES (%s, %s);"
                cursor.execute(query, (record[0], record[1]))
                inflationDB.commit()
            # Record with just date
            else:
                query = "INSERT INTO FED (date) \
                         VALUES (%s);"
                cursor.execute(query, (record[0],))
                inflationDB.commit()

        # If the fed_record does not match the current date, insert just the date
        else:
            query = "INSERT INTO FED (date) \
                     VALUES (%s);"
            cursor.execute(query, (all_dates[i],))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Pulls the latest pce data from FRED
def pullLatestPCE(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Grab all of the stored dates from the PCE table
    cursor.execute("SELECT date FROM PCE;")
    response = cursor.fetchall()
    stored_pce_dates = []
    for date in response:
        stored_pce_dates.append(date[0])

    # Reverse the order so the most recent dates are at the start of the list
    stored_pce_dates.reverse()

    # Request data from FRED website
    pce_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=PCEPI&scale=left&cosd=1959-01-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1959-01-01")

    # Transfer request to pce.csv file
    with open('pce.csv', 'wb') as pce_file:
        pce_file.write(pce_req.content)

    # Re-open pce.csv
    pce_file = open('pce.csv')
    pce_csv_reader = csv.reader(pce_file)

    # Ignore column titles
    next(pce_csv_reader)

    # Transfer the contents of pce.csv to pce_records
    pce_records = []
    for record in pce_csv_reader:
        pce_records.append(record)

    # Close the file
    pce_file.close()

    # Delete the file from the directory
    os.remove('pce.csv')

    # Reverses the pulled PCE records
    pce_records.reverse()

    # Iterates through the newly pulled data
    for i in range(len(stored_pce_dates)):
        # If the pulled date matches an existing date, then we break to prevent duplicate data
        if str(pce_records[i][0]) == str(stored_pce_dates[0]):
            break
        # Otherwise, insert the new data
        else:
            # Calculate yearly inflation
            yearly_inflation = (float(pce_records[i][1]) - float(pce_records[i+12][1])) / float(pce_records[i+12][1]) * 100.0

            query = "INSERT INTO PCE (date, value, inflation) \
                     VALUES (%s, %s, %s);"
            cursor.execute(query, (pce_records[i][0], pce_records[i][1], yearly_inflation))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Pulls the latest cpi data from FRED
def pullLatestCPI(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Grab all of the stored dates from the CPI table
    cursor.execute("SELECT date FROM CPI;")
    response = cursor.fetchall()
    stored_cpi_dates = []
    for date in response:
        stored_cpi_dates.append(date[0])

    # Reverse the order so the most recent dates are at the start of the list
    stored_cpi_dates.reverse()

    # Request data from FRED website
    cpi_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=CPIAUCSL&scale=left&cosd=1947-01-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1947-01-01")

    # Transfer request to cpi.csv file
    with open('cpi.csv', 'wb') as cpi_file:
        cpi_file.write(cpi_req.content)

    # Re-open cpi.csv
    cpi_file = open('cpi.csv')
    cpi_csv_reader = csv.reader(cpi_file)

    # Ignore column titles
    next(cpi_csv_reader)

    # Transfer the contents of cpi.csv to cpi_records
    cpi_records = []
    for record in cpi_csv_reader:
        cpi_records.append(record)

    # Close the file
    cpi_file.close()

    # Delete the file from the directory
    os.remove('cpi.csv')

    # Reverses the pulled CPI records
    cpi_records.reverse()

    # Iterates through the newly pulled data
    for i in range(len(stored_cpi_dates)):
        # If the pulled date matches an existing date, then we break to prevent duplicate data
        if str(cpi_records[i][0]) == str(stored_cpi_dates[0]):
            break
        # Otherwise, insert the new data
        else:
            # Calculate yearly inflation
            yearly_inflation = (float(cpi_records[i][1]) - float(cpi_records[i+12][1])) / float(cpi_records[i+12][1]) * 100.0

            query = "INSERT INTO CPI (date, value, inflation) \
                     VALUES (%s, %s, %s);"
            cursor.execute(query, (cpi_records[i][0], cpi_records[i][1], yearly_inflation))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Pulls the latest ppi data from FRED
def pullLatestPPI(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Grab all of the stored dates from the PPI table
    cursor.execute("SELECT date FROM PPI;")
    response = cursor.fetchall()
    stored_ppi_dates = []
    for date in response:
        stored_ppi_dates.append(date[0])

    # Reverse the order so the most recent dates are at the start of the list
    stored_ppi_dates.reverse()

    # Request data from FRED website
    ppi_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=1168&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=PPIFIS&scale=left&cosd=2009-11-01&coed=2022-03-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=2009-11-01")

    # Transfer request to ppi.csv file
    with open('ppi.csv', 'wb') as ppi_file:
        ppi_file.write(ppi_req.content)

    # Re-open ppi.csv
    ppi_file = open('ppi.csv')
    ppi_csv_reader = csv.reader(ppi_file)

    # Ignore column titles
    next(ppi_csv_reader)

    # Transfer the contents of ppi.csv to ppi_records
    ppi_records = []
    for record in ppi_csv_reader:
        ppi_records.append(record)

    # Close the file
    ppi_file.close()

    # Delete the file from the directory
    os.remove('ppi.csv')

    # Reverses the pulled PPI records
    ppi_records.reverse()

    # Iterates through the newly pulled data
    for i in range(len(stored_ppi_dates)):
        # If the pulled date matches an existing date, then we break to prevent duplicate data
        if str(ppi_records[i][0]) == str(stored_ppi_dates[0]):
            break
        # Otherwise, insert the new data
        else:
            # Calculate yearly inflation
            yearly_inflation = (float(ppi_records[i][1]) - float(ppi_records[i+12][1])) / float(ppi_records[i+12][1]) * 100.0

            query = "INSERT INTO PPI (date, value, inflation) \
                     VALUES (%s, %s, %s);"
            cursor.execute(query, (ppi_records[i][0], ppi_records[i][1], yearly_inflation))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# Pulls the latest fed data from FRED
def pullLatestFED(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Grab all of the stored dates from the FED table
    cursor.execute("SELECT date FROM FED;")
    response = cursor.fetchall()
    stored_fed_dates = []
    for date in response:
        stored_fed_dates.append(date[0])

    # Reverse the order so the most recent dates are at the start of the list
    stored_fed_dates.reverse()

    # Request data from FRED website
    fed_req = requests.get("https://fred.stlouisfed.org/graph/fredgraph.csv?bgcolor=%23e1e9f0&chart_type=line&drp=0&fo=open%20sans&graph_bgcolor=%23ffffff&height=450&mode=fred&recession_bars=on&txtcolor=%23444444&ts=12&tts=12&width=748&nt=0&thu=0&trc=0&show_legend=yes&show_axis_titles=yes&show_tooltip=yes&id=FEDFUNDS&scale=left&cosd=1954-07-01&coed=2022-04-01&line_color=%234572a7&link_values=false&line_style=solid&mark_type=none&mw=3&lw=2&ost=-99999&oet=99999&mma=0&fml=a&fq=Monthly&fam=avg&fgst=lin&fgsnd=2020-02-01&line_index=1&transformation=lin&vintage_date=2022-05-10&revision_date=2022-05-10&nd=1954-07-01")

    # Transfer request to fed.csv file
    with open('fed.csv', 'wb') as fed_file:
        fed_file.write(fed_req.content)

    # Re-open fed.csv
    fed_file = open('fed.csv')
    fed_csv_reader = csv.reader(fed_file)

    # Ignore column titles
    next(fed_csv_reader)

    # Transfer the contents of fed.csv to fed_records
    fed_records = []
    for record in fed_csv_reader:
        fed_records.append(record)

    # Close the file
    fed_file.close()

    # Delete the file from the directory
    os.remove('fed.csv')

    # Reverses the pulled FED records
    fed_records.reverse()

    # Iterates through the newly pulled data
    for i in range(len(stored_fed_dates)):
        # If the pulled date matches an existing date, then we break to prevent duplicate data
        if str(fed_records[i][0]) == str(stored_fed_dates[0]):
            break
        # Otherwise, insert the new data
        else:
            query = "INSERT INTO FED (date, value) \
                     VALUES (%s, %s);"
            cursor.execute(query, (fed_records[i][0], fed_records[i][1]))
            inflationDB.commit()

    # Close cursor
    cursor.close()

# ======================================DQL=====================================

# Takes in username and password, outputs user_ID
def loginDB(inflationDB, username_input, password_input):
    # Create cursor
    cursor = inflationDB.cursor()

    # Query to find potential username in User table
    query = "SELECT password, user_ID \
             FROM User \
             WHERE username = %s AND deleted = 0;"
    cursor.execute(query, (username_input,))
    response = cursor.fetchone()

    # Close cursor
    cursor.close()

    # If the username exists, grab the password
    if response:
        # Check if the password is correct
        if password_input == response[0]:
            return response[1]
        # Otherwise, produce error message
        else:
            return -1

    # Otherwise, produce error message
    else:
        return -1

    return -1

# Takes in username and password, outputs user_ID
def createAccountDB(inflationDB, username_input, password_input):
    # Create cursor
    cursor = inflationDB.cursor()

    # Check if the username is already taken
    query = "SELECT user_ID \
             FROM User \
             WHERE username = %s;"
    cursor.execute(query, (username_input,))
    response = cursor.fetchall()

    # If the username already exists, return an error
    if response:
        return -1
    # Otherwise, return the newly generated user_ID
    else:
        # Insert the credentials into the User table
        query = "INSERT INTO User (username, password) \
                 VALUES (%s, %s);"
        cursor.execute(query, (username_input, password_input))
        inflationDB.commit()

        # Grab the newly generated user_ID using a subquery
        query = "SELECT user_ID \
                 FROM User \
                 WHERE user_ID = (SELECT LAST_INSERT_ID());"
        cursor.execute(query)
        response = cursor.fetchone()

        # Close cursor
        cursor.close()

        # Retrun the user_ID
        return response[0]

    return -1

# Returns all dates in the database
def getDatesDB(inflationDB, start_date, range_date):
    # Create cursor
    cursor = inflationDB.cursor()

    # List of dates from the database
    dates_x = []

    # List of dummy values to properly shift the graph around
    dummy_y = []

    # Query to count the number of records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Check if the user has modified the view of the graph
    if response[0] != range_date or start_date != 0:
        query = "SELECT date \
                 FROM CustomData \
                 WHERE custom_ID > %s \
                 LIMIT %s;"
        cursor.execute(query, (start_date, range_date))
        response = cursor.fetchall()
        for record in response:
            dates_x.append(record[0])
            dummy_y.append(0)

    # Otherwise, append all dates that exist
    else:
        cursor.execute("SELECT date FROM OriginalData;")
        response = cursor.fetchall()
        for record in response:
            dates_x.append(record[0])
            dummy_y.append(0)

    # Close cursor
    cursor.close()

    return (dates_x, dummy_y)

# Returns all PCE values in the database
def getPCEDB(inflationDB, start_date, range_date):
    # Create cursor
    cursor = inflationDB.cursor()

    # List of PCE values from the database
    pce_y = []

    # Query to count the number of records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Check if the user has modified the view of the graph
    if response[0] != range_date or start_date != 0:
        query = "SELECT pce_inflation \
                 FROM CustomData \
                 WHERE custom_ID > %s \
                 LIMIT %s;"
        cursor.execute(query, (start_date, range_date))
        response = cursor.fetchall()
        for record in response:
            pce_y.append(record[0])

    # Otherwise, append all PCE values that exist
    else:
        cursor.execute("SELECT pce_inflation FROM OriginalData;")
        response = cursor.fetchall()
        for record in response:
            pce_y.append(record[0])

    # Close cursor
    cursor.close()

    return pce_y

# Returns all CPI values in the database
def getCPIDB(inflationDB, start_date, range_date):
    # Create cursor
    cursor = inflationDB.cursor()

    # List of CPI values from the database
    cpi_y = []

    # Query to count the number of records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Check if the user has modified the view of the graph
    if response[0] != range_date or start_date != 0:
        query = "SELECT cpi_inflation \
                 FROM CustomData \
                 WHERE custom_ID > %s \
                 LIMIT %s;"
        cursor.execute(query, (start_date, range_date))
        response = cursor.fetchall()
        for record in response:
            cpi_y.append(record[0])

    # Otherwise, append all PCE values that exist
    else:
        cursor.execute("SELECT cpi_inflation FROM OriginalData;")
        response = cursor.fetchall()
        for record in response:
            cpi_y.append(record[0])

    # Close cursor
    cursor.close()

    return cpi_y

# Returns all PPI values in the database
def getPPIDB(inflationDB, start_date, range_date):
    # Create cursor
    cursor = inflationDB.cursor()

    # List of PPI values from the database
    ppi_y = []

    # Query to count the number of records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Check if the user has modified the view of the graph
    if response[0] != range_date or start_date != 0:
        query = "SELECT ppi_inflation \
                 FROM CustomData \
                 WHERE custom_ID > %s \
                 LIMIT %s;"
        cursor.execute(query, (start_date, range_date))
        response = cursor.fetchall()
        for record in response:
            ppi_y.append(record[0])

    # Otherwise, append all PCE values that exist
    else:
        cursor.execute("SELECT ppi_inflation FROM OriginalData;")
        response = cursor.fetchall()
        for record in response:
            ppi_y.append(record[0])

    # Close cursor
    cursor.close()

    return ppi_y

# Returns all FED values in the database
def getFEDDB(inflationDB, start_date, range_date):
    # Create cursor
    cursor = inflationDB.cursor()

    # List of FED values from the database
    fed_y = []

    # Query to count the number of records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Check if the user has modified the view of the graph
    if response[0] != range_date or start_date != 0:
        query = "SELECT fed_value \
                 FROM CustomData \
                 WHERE custom_ID > %s \
                 LIMIT %s;"
        cursor.execute(query, (start_date, range_date))
        response = cursor.fetchall()
        for record in response:
            fed_y.append(record[0])

    # Otherwise, append all PCE values that exist
    else:
        cursor.execute("SELECT fed_value FROM OriginalData;")
        response = cursor.fetchall()
        for record in response:
            fed_y.append(record[0])

    # Close cursor
    cursor.close()

    return fed_y

# Takes in a new username and user_ID
def changeUsernameDB(inflationDB, old_username, new_username, user_ID):
    # Int to be returned
    username_changed = 0

    # Temporary user id
    tmp_user_ID = -1

    # Create cursor
    cursor = inflationDB.cursor()

    # Verify that the user input is the same as the old username
    query = "SELECT username \
             FROM User \
             WHERE user_ID = %s;"
    cursor.execute(query, (user_ID,))
    response = cursor.fetchone()
    verify_username = response[0]

    # Check that the new username does not already exist
    query = "SELECT user_ID \
             FROM User \
             WHERE username = %s;"
    cursor.execute(query, (new_username,))
    response = cursor.fetchone()
    if response:
        tmp_user_ID = response[0]

    # Checks if the input old username is the same as the one in the database and that the new username does not already exist
    if verify_username == old_username and tmp_user_ID == -1:
        # Perform the transaction with the User and DBLogs tables
        cursor.execute("START TRANSACTION;")
        cursor.execute("UPDATE User SET username = %s WHERE user_ID = %s;", (new_username, user_ID))
        cursor.execute("INSERT INTO DBLogs (user_ID, old_username, new_username) VALUES (%s, %s, %s);", (user_ID, old_username, new_username))
        cursor.execute("COMMIT;")

        # Flag the int as correct
        username_changed = 1
    elif verify_username != old_username:
        # Flag the int as first incorrect option
        username_changed = -1
    elif tmp_user_ID != -1:
         # Flag the int as first incorrect option
         username_changed = -2

    # Close cursor
    cursor.close()

    return username_changed

# Takes in a new password and user_ID
def changePasswordDB(inflationDB, old_password, new_password, user_ID):
    # Boolean to be returned
    password_changed = False

    # Create cursor
    cursor = inflationDB.cursor()

    # Grab old username
    query = "SELECT password \
             FROM User \
             WHERE user_ID = %s;"
    cursor.execute(query, (user_ID,))
    response = cursor.fetchone()

    # Checks if the input old username is the same as the one in the database
    if response[0] == old_password:
        # Perform the transaction with the User and DBLogs tables
        cursor.execute("START TRANSACTION;")
        cursor.execute("UPDATE User SET password = %s WHERE user_ID = %s;", (new_password, user_ID))
        cursor.execute("INSERT INTO DBLogs (user_ID, old_password, new_password) VALUES (%s, %s, %s);", (user_ID, old_password, new_password))
        cursor.execute("COMMIT;")

        # Flag the boolean as true
        username_changed = True

    # Close cursor
    cursor.close()

    return username_changed

# Takes in user_ID, outputs username and password
def getCredentialsDB(inflationDB, user_ID):
    # Create cursor
    cursor = inflationDB.cursor()

    # Grab username
    query = "SELECT username \
             FROM User \
             WHERE user_ID = %s;"
    cursor.execute(query, (user_ID,))
    response = cursor.fetchone()
    username = response[0]

    # Grab password
    query = "SELECT password \
             FROM User \
             WHERE user_ID = %s;"
    cursor.execute(query, (user_ID,))
    response = cursor.fetchone()
    password = response[0]

    # Close cursor
    cursor.close()

    return (username, password)

# Takes in the user_ID
def deleteAccountDB(inflationDB, user_ID):
    # Create cursor
    cursor = inflationDB.cursor()

    # Query to flip the deleted value
    query = "UPDATE User \
             SET deleted = 1 \
             WHERE user_ID = %s;"
    cursor.execute(query, (user_ID,))
    inflationDB.commit()

    # Close cursor
    cursor.close()

# Returns the size of the database
def getDBSize(inflationDB):
    # Create cursor
    cursor = inflationDB.cursor()

    # Query to count the number of govt records in the database
    cursor.execute("SELECT COUNT(*) FROM CPI;")
    response = cursor.fetchone()

    # Close cursor
    cursor.close()

    return response[0]

# ======================================GUI=====================================

# Loading screen
class LoadingScreen(Screen):
    # Stores MySQL connection
    inflationDB = None

    # Upon loading the program, play a loading animation while the data is being loaded
    def on_enter(self, *args):

        # Creates separate thread to load data
        t = threading.Thread(target=self.connectToDB)
        t.start()

        # Plays the loading animation
        self.playAnimation()

        # Creates event to trigger when to move to the login screen
        self.event = Clock.create_trigger(self.finished)

    # Transitions to the login screen once the data has been loaded
    def connectToDB(self):
        self.inflationDB = checkDBConnection()
        self.event()

    # Plays the animation while loading the data
    def playAnimation(self):
        load_gif = Image(source='load.gif',
                    pos_hint={"center_x": 0.5, "center_y": 0.5},
                    size_hint=(0.1, 0.1),
                    anim_delay=0.03)
        self.add_widget(load_gif)

    # Called when the data is finished loading
    def finished(self, *args):
        sm.add_widget(LoginScreen(name="login"))
        self.clear_widgets()
        sm.transition.direction = "up"
        sm.current = "login"

# Login screen
class LoginScreen(Screen):
    # Text Fields
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    # Enter the app
    access_granted = False

    # Stores the user_ID from the entered credentials
    user_ID = -1

    # Stores MySQL connection
    inflationDB = None

    # Reset info upon entering the screen
    def on_enter(self, *args):
        self.user_ID = -1
        self.access_granted = False
        self.resetScreen()
        self.inflationDB = sm.get_screen(name="loading").inflationDB

    # Displays button for logging in
    def login(self):
        # Stores the user_ID upon logging in
        self.user_ID = loginDB(self.inflationDB, self.username.text, self.password.text)

        if self.user_ID == -1:
            self.dialog = MDDialog(title="Incorrect username/password",
                                   text="The credentials that were entered do not match any existing records", size_hint=(0.7, 0.5),
                                   buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
            self.dialog.open()
        else:
            self.resetScreen()
            self.access_granted = True

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

    # Resets the information on the screen
    def resetScreen(self):
        self.username.text = ""
        self.password.text = ""

# Create account screen
class CreateAccountScreen(Screen):
    # Text Fields
    username = ObjectProperty(None)
    password = ObjectProperty(None)

    # Enter the app
    access_granted = False

    # Stores the user_ID from the entered credentials
    user_ID = -1

    # Stores MySQL connection
    inflationDB = None

    # Reset info upon entering the screen
    def on_enter(self, *args):
        self.user_ID = -1
        self.access_granted = False
        self.resetScreen()
        self.inflationDB = sm.get_screen(name="loading").inflationDB

    # Displays button for submitting information to the database
    def createAccount(self):
        # If both textboxes are not blank, then create the account
        if self.username.text != "" and self.password.text != "":
            self.user_ID = createAccountDB(self.inflationDB, self.username.text, self.password.text)

            # If self.user_ID is -1, then the username has already been taken and a dialog box pops up
            if self.user_ID == -1:
                self.dialog = MDDialog(title="Username taken",
                                       text="The username that you have entered is already taken", size_hint=(0.7, 0.5),
                                       buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                self.dialog.open()
            # Otherwise, create the account
            else:
                self.resetScreen()
                self.access_granted = True
        # Otherwise, display error
        else:
            self.dialog = MDDialog(title="Blank username/password",
                                   text="Required fields were left blank", size_hint=(0.7, 0.5),
                                   buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
            self.dialog.open()

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

    # Resets the information on the screen
    def resetScreen(self):
        self.username.text = ""
        self.password.text = ""

# Menu screen
class MenuScreen(Screen):
    # Stores the user_ID from the entered credentials
    user_ID = -1

    # Stores the username and the password of the given user_ID
    username = ""
    password = ""

    # Stores MySQL connection
    inflationDB = None

    # Lists that contain the plotted data
    dates_x = []
    pce_y = []
    cpi_y = []
    ppi_y = []
    fed_y = []

    # Bools to disable / enable plots
    show_pce = True
    show_cpi = True
    show_ppi = True
    show_fed = True

    # Default date values
    start_date = 0
    range_date = 0

    # zoom_val determines how much of the x values are shown on the plot
    zoom_val = 1.0

    # loc_val determines what x values are shown on the plot
    range_val = 0.0

    # Display the graph upon entering the screen
    def on_enter(self, *args):
        self.inflationDB = sm.get_screen(name="loading").inflationDB
        self.range_date = getDBSize(self.inflationDB)
        self.updateCredentials()
        self.updateGraph()

    # Update the credentials
    def updateCredentials(self):
        # Get the user_ID
        if sm.get_screen(name="login").user_ID != -1:
            self.user_ID = sm.get_screen(name="login").user_ID
        else:
            self.user_ID = sm.get_screen(name="create").user_ID

        credentials = getCredentialsDB(self.inflationDB, self.user_ID)

        self.username = credentials[0]
        self.password = credentials[1]

    # Displays a dialog box that explains pce
    def pcePopup(self):
        self.dialog = MDDialog(title="What is PCE?",
                               text="The personal consumption expenditure price index is one measure of U.S. inflation, tracking the change in prices of goods and services purchased by consumers throughout the economy. Of all the measures of consumer price inflation, PCE includes the broadest set of goods and services.",
                               size_hint=(0.7, 0.5),
                               buttons=[MDFlatButton(text="Source Data", on_release=self.sourcePCE),
                                        MDFlatButton(text="Close", on_release=self.closeDialog)])
        self.dialog.open()

    # Toggle function for drawing the pce plot
    def togglePCE(self, switchVal):
        self.show_pce = switchVal
        self.updateGraph()

    # Open the website containing the PCE data
    def sourcePCE(self, obj):
        webbrowser.open('https://fred.stlouisfed.org/series/PCEPI', new=2)

    # Displays a dialog box that explains cpi
    def cpiPopup(self):
        self.dialog = MDDialog(title="What is CPI?",
                               text="The Consumer Price Index (CPI) is a measure that examines the weighted average of prices of a basket of consumer goods and services, such as transportation, food, and medical care. It is calculated by taking price changes for each item in the predetermined basket of goods and averaging them. Changes in the CPI are used to assess price changes associated with the cost of living.",
                               size_hint=(0.7, 0.5),
                               buttons=[MDFlatButton(text="Source Data", on_release=self.sourceCPI),
                                        MDFlatButton(text="Close", on_release=self.closeDialog)])
        self.dialog.open()

    # Toggle function for drawing the cpi plot
    def toggleCPI(self, switchVal):
        self.show_cpi = switchVal
        self.updateGraph()

    # Open the website containing the CPI data
    def sourceCPI(self, obj):
        webbrowser.open('https://fred.stlouisfed.org/series/CPIAUCSL', new=2)

    # Displays a dialog box that explains ppi
    def ppiPopup(self):
        self.dialog = MDDialog(title="What is PPI?",
                               text="The producer price index (PPI) is a group of indexes that calculates and represents the average movement in selling prices from domestic production over time. It is a measure of inflation based on input costs to producers.",
                               size_hint=(0.7, 0.5),
                               buttons=[MDFlatButton(text="Source Data", on_release=self.sourcePPI),
                                        MDFlatButton(text="Close", on_release=self.closeDialog)])
        self.dialog.open()

    # Toggle function for drawing the ppi plot
    def togglePPI(self, switchVal):
        self.show_ppi = switchVal
        self.updateGraph()

    # Open the website containing the PPI data
    def sourcePPI(self, obj):
        webbrowser.open('https://fred.stlouisfed.org/series/PPIFIS', new=2)

    # Displays a dialog box that explains fed
    def fedPopup(self):
        self.dialog = MDDialog(title="What is FED?",
                               text="The federal funds rate is the interest rate that banks charge each other to borrow or lend excess reserves overnight. The federal funds rate is the Federal Reserve's main benchmark interest rate that influences how much consumers pay to borrow and how much they’re paid to save.",
                               size_hint=(0.7, 0.5),
                               buttons=[MDFlatButton(text="Source Data", on_release=self.sourceFED),
                                        MDFlatButton(text="Close", on_release=self.closeDialog)])
        self.dialog.open()

    # Toggle function for drawing the fed plot
    def toggleFED(self, switchVal):
        self.show_fed = switchVal
        self.updateGraph()

    # Open the website containing the FED data
    def sourceFED(self, obj):
        webbrowser.open('https://fred.stlouisfed.org/series/FEDFUNDS', new=2)

    # Updates the graph
    def updateGraph(self):

        # Clear the widgets in the graph location
        sm.get_screen("menu").ids.graph_location.clear_widgets()

        # Clear the plot
        plt.clf()

        # Calculate the range of dates that are shown on the plot
        self.range_date = int(getDBSize(self.inflationDB) / self.zoom_val)

        # Calculate the starting date that is show on the plot
        self.start_date = int((getDBSize(self.inflationDB) - self.range_date) * self.range_val)

        # Grab dates
        pair_return = getDatesDB(self.inflationDB, self.start_date, self.range_date)
        self.dates_x = pair_return[0]
        dummy_y = pair_return[1]

        # Plot the dummy variables
        plt.plot(self.dates_x, dummy_y, color="black")

        # Checks if the pce plot is toggled on
        if self.show_pce:
            # Gets PCE inflation data points
            self.pce_y = getPCEDB(self.inflationDB, self.start_date, self.range_date)

            # Add PCE plot
            plt.plot(self.dates_x, self.pce_y, color="blue", label="PCE")

        # Checks if the cpi plot is toggled on
        if self.show_cpi:
            # Gets CPI inflation data points
            self.cpi_y = getCPIDB(self.inflationDB, self.start_date, self.range_date)

            # Add CPI plot
            plt.plot(self.dates_x, self.cpi_y, color="orange", label="CPI")

        # Checks if the ppi plot is toggled on
        if self.show_ppi:
            # Gets PPI inflation data points
            self.ppi_y = getPPIDB(self.inflationDB, self.start_date, self.range_date)

            # Add PPI plot
            plt.plot(self.dates_x, self.ppi_y, color="green", label="PPI")

        # Checks if the fed plot is toggled on
        if self.show_fed:
            # Gets FED inflation data points
            self.fed_y = getFEDDB(self.inflationDB, self.start_date, self.range_date)

            # Add FED plot
            plt.plot(self.dates_x, self.fed_y, color="red", label="FED")

        # Set constant y-axis values
        plt.ylim([-3, 20])

        # Insert the plot into the graph_location
        sm.get_screen("menu").ids.graph_location.add_widget(FigureCanvasKivyAgg(plt.gcf()))

    # Updates self.zoom_val based on the slider value
    def updateZoom(self, zoomVal):
        if self.zoom_val != round(zoomVal, 1):
            self.zoom_val = round(zoomVal, 1)
            self.updateGraph()

    # Updates self.range_val based on the slider value
    def updateRange(self, rangeVal):
        if self.range_val != rangeVal:
            self.range_val = rangeVal
            self.updateGraph()

    # Transitions to the settings screen
    def settings(self):
        sm.transition.direction = "left"
        sm.current = "settings"

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

    # Exports the current data in the graph to export.csv in the current directory of the application
    def exportData(self):
        try:
            # open the file in the write mode
            f = open('export.csv', 'w')

            # Check that data is being plotted on the graph
            if self.show_pce or self.show_cpi or self.show_ppi or self.show_fed:
                csv_dict = {"date": self.dates_x}

                # If the pce plot is toggled on, then append the data to the dictionary
                if self.show_pce:
                    csv_dict["pce"] = self.pce_y

                # If the cpi plot is toggled on, then append the data to the dictionary
                if self.show_cpi:
                    csv_dict["cpi"] = self.cpi_y

                # If the ppi plot is toggled on, then append the data to the dictionary
                if self.show_ppi:
                    csv_dict["ppi"] = self.ppi_y

                # If the fed plot is toggled on, then append the data to the dictionary
                if self.show_fed:
                    csv_dict["fed"] = self.fed_y

                # Save the dictionary to a dataframe and save the dataframe to the csv file
                df = pd.DataFrame(csv_dict)
                df.to_csv('export.csv')

                self.dialog = MDDialog(title="Data Exported",
                                       text="Successfully exported data!",
                                       size_hint=(0.7, 0.5),
                                       buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                self.dialog.open()


            # If not data is being plotted, then open an error dialog box
            else:
                self.dialog = MDDialog(title="No Graph Present",
                                       text="Please enable at least one of the trend lines before exporting data.",
                                       size_hint=(0.7, 0.5),
                                       buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                self.dialog.open()

            f.close()
        except:
            self.dialog = MDDialog(title="Unable to Export Data",
                                   text="Verify that you do not have 'export.csv' already open.",
                                   size_hint=(0.7, 0.5),
                                   buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
            self.dialog.open()

# Settings screen
class SettingsScreen(Screen):
    # Stores MySQL connection
    inflationDB = None

    # Grabs the inflationDB connection
    def on_enter(self, *args):
        self.inflationDB = sm.get_screen(name="loading").inflationDB

    # Returns to the menu screen
    def menu(self):
        sm.transition.direction = "right"
        sm.current = "menu"

    # Verifies that the user wants to delete their account
    def verifyPopup(self):

        self.dialog = MDDialog(title="Delete account?",
                               text="Are you sure you want to delete your account?", size_hint=(0.7, 0.5),
                               buttons=[MDFlatButton(text="Delete", on_release=self.deleteAccount),
                                        MDFlatButton(text="Close", on_release=self.closeDialog)])
        self.dialog.open()

    # Deletes the account
    def deleteAccount(self, obj):

        # Grabs the user_ID from the menu screen
        user_ID = sm.get_screen(name="menu").user_ID

        # Soft deletes the user
        deleteAccountDB(self.inflationDB, user_ID)

        # Transitions back to the login screen
        sm.transition.direction = "down"
        sm.current = "login"

        # Closes out of the dialog box
        self.dialog.dismiss()

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

# Change username screen
class UsernameScreen(Screen):
    # Text Fields
    old_username = ObjectProperty(None)
    new_username = ObjectProperty(None)

    # Stores MySQL connection
    inflationDB = None

    # Grabs the inflationDB connection
    def on_enter(self, *args):
        self.inflationDB = sm.get_screen(name="loading").inflationDB

    # Returns to the settings screen
    def settings(self):
        sm.transition.direction = "right"
        sm.current = "settings"

    # Returns the username in the database
    def changeUsername(self):
        # Boolean to check if the username was changed
        username_changed = 0

        # Grabs the user_ID from the menu screen
        user_ID = sm.get_screen(name="menu").user_ID

        # Check that the new username is not blank
        if self.new_username.text != "":
                username_changed = changeUsernameDB(self.inflationDB, self.old_username.text, self.new_username.text, user_ID)

                # Checks if the username was changed
                if username_changed == 1:
                    self.old_username.text = ""
                    self.new_username.text = ""
                    sm.transition.direction = "right"
                    sm.current = "settings"
                # If username_changed is -1, then the old username did not match
                elif username_changed == -1:
                    self.dialog = MDDialog(title="Username Error",
                                           text="The old username does not match any existing records", size_hint=(0.7, 0.5),
                                           buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                    self.dialog.open()
                # If username_changed is -2, then the new username already exists
                elif username_changed == -2:
                    self.dialog = MDDialog(title="Username Error",
                                           text="The new username already exists", size_hint=(0.7, 0.5),
                                           buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                    self.dialog.open()

        # Otherwise, dialog box
        else:
            self.dialog = MDDialog(title="Blank username",
                                   text="Required fields were left blank", size_hint=(0.7, 0.5),
                                   buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
            self.dialog.open()

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

# Change password screen
class PasswordScreen(Screen):
    # Text Fields
    old_password = ObjectProperty(None)
    new_password = ObjectProperty(None)

    # Stores MySQL connection
    inflationDB = None

    # Grabs the inflationDB connection
    def on_enter(self, *args):
        self.inflationDB = sm.get_screen(name="loading").inflationDB

    # Returns to the settings screen
    def settings(self):
        sm.transition.direction = "right"
        sm.current = "settings"

    # Returns the password in the database
    def changePassword(self):
        # Boolean to check if the password was changed
        password_changed = False

        # Grabs the user_ID from the menu screen
        user_ID = sm.get_screen(name="menu").user_ID

        # Check that the new password is not blank
        if self.new_password.text != "":
                password_changed = changePasswordDB(self.inflationDB, self.old_password.text, self.new_password.text, user_ID)

                # Checks if the password was changed
                if password_changed:
                    self.old_password.text = ""
                    self.new_password.text = ""
                    sm.transition.direction = "right"
                    sm.current = "settings"
                else:
                    self.dialog = MDDialog(title="Incorrect password",
                                           text="The password that was entered does not match any existing records", size_hint=(0.7, 0.5),
                                           buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
                    self.dialog.open()

        # Otherwise, dialog box
        else:
            self.dialog = MDDialog(title="Blank password",
                                   text="Required fields were left blank", size_hint=(0.7, 0.5),
                                   buttons=[MDFlatButton(text="Close", on_release=self.closeDialog)])
            self.dialog.open()

    # Closes the dialog box
    def closeDialog(self, obj):
        self.dialog.dismiss()

# ======================================RUN=====================================

# Define the screen manager
sm = ScreenManager()

class InflationTrackerApp(MDApp):
    # Build function
    def build(self):
        Window.bind(on_request_close=self.on_request_close)

        # Pass in gui file
        Builder.load_file("gui.kv")

        # Add screens to screen manager
        sm.add_widget(LoadingScreen(name="loading"))
        sm.add_widget(CreateAccountScreen(name="create"))
        sm.add_widget(MenuScreen(name="menu"))
        sm.add_widget(SettingsScreen(name="settings"))
        sm.add_widget(UsernameScreen(name="username"))
        sm.add_widget(PasswordScreen(name="password"))

        # App theme
        self.theme_cls.primary_palette = "Teal"
        self.theme_cls.primary_hue = "400"

        return sm

    # Closes the database connection upon closing the app
    def on_request_close(self, *args):
        sm.get_screen(name="loading").inflationDB.close()
        self.stop()
        return True

InflationTrackerApp().run()
