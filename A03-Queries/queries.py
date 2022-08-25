# Completed by Cole Ternes

# Import library
import sqlite3

# Add path to chinook.db for connection
connection = sqlite3.connect("chinook.db")

question_num = 1

# Cursor object - executes sql commands
cur_obj = connection.cursor()

def printQuestionNum():
    global question_num
    print("Question", question_num)
    question_num += 1

def prereq():
    # Query to create the table patient
    create_table_query = '''
    CREATE TABLE patient(
        patientID INTEGER NOT NULL PRIMARY KEY,
        Name VARCHAR(40) NOT NULL,
        DOB DATETIME,
        Phone VARCHAR(24)
    );
    '''

    # Execute the query using cursor object and commit to the database
    cur_obj.execute(create_table_query)
    connection.commit()

def selectPatient():
    # Select query
    select_query = '''
    SELECT *
    FROM patient;
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    for row in result:
        print(row)

def postreq():
    # Drops the patient table
    drop_table_query = '''
    DROP TABLE patient;
    '''

    # Execute the query using cursor object and commit to the database
    cur_obj.execute(drop_table_query)
    connection.commit()

def question1():
    # A list of tuple containing values to be inserted
    records = [
    (1, 'John Doe', '1960-01-01', '7142022222'),
    (2, 'Jane Doe', None, None),
    (3, 'Rick Grimes', '1980-06-01', None)
    ]

    # Insert query with question mark placeholders
    insert_query = '''
    INSERT INTO patient(patientID, Name, DOB, Phone)
    VALUES(?, ?, ?, ?);
    '''

    # Use execute many function for multiple records
    cur_obj.executemany(insert_query, records)
    connection.commit()

def question2():
    # New likes, new comments, new retweets for a given tweetID
    new_data = ('1984-12-20', 2)

    # Update query with placeholders for respectice values
    update_query = '''
    UPDATE patient
    SET DOB = ?
    WHERE patientID = ?;
    '''

    # Execute the query using cursor object and commit to the database
    cur_obj.execute(update_query, new_data)
    connection.commit()

def question3():
    # Remove query
    remove_query = '''
    DELETE FROM patient
    WHERE Phone IS NULL;
    '''

    # Execute the query using cursor object and commit to the database
    cur_obj.execute(remove_query)
    connection.commit()

def question4():
    # Select query
    select_query = '''
    SELECT *
    FROM invoices
    ORDER BY Total DESC
    LIMIT 1;
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    for row in result:
        print(row)

def question5():
    # Select query
    select_query = '''
    SELECT BillingCountry
    FROM invoices
    ORDER BY Total ASC
    LIMIT 1;
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    for row in result:
        print(row)

def question6():
    # Select query
    select_query = '''
    SELECT AVG(Total)
    FROM invoices
    WHERE BillingCountry = 'USA';
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    for row in result:
        print(row)

def question7():
    # Select query
    select_query = '''
    SELECT COUNT(*)
    FROM invoices
    WHERE InvoiceDate BETWEEN 2010-01-01 AND 2020-12-31;
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    for row in result:
        print(row)

def question8():
    # Select query
    select_query = '''
    SELECT a.Title, m.Name, t.Name
    FROM tracks AS t
    INNER JOIN albums AS a
    ON t.AlbumId = a.AlbumId
    INNER JOIN media_types AS m
    ON t.MediaTypeId = m.MediaTypeId;
    '''

    # Store returned records into a result object
    # Result is also a cursor object
    result = cur_obj.execute(select_query)

    # Records are returned as tuples
    # Uncomment this if you want to be spammed with tuples
    # for row in result:
    #     print(row)
    print("Query hidden for simplicity")


def main():
    # Prerequisite:
    prereq()

    # Question 1:
    printQuestionNum()
    question1()
    selectPatient()

    # Question 2:
    printQuestionNum()
    question2()
    selectPatient()

    # Question 3:
    printQuestionNum()
    question3()
    selectPatient()
    postreq()

    # Question 4:
    printQuestionNum()
    question4()

    # Question 5:
    printQuestionNum()
    question5()

    # Question 6:
    printQuestionNum()
    question6()

    # Question 7:
    printQuestionNum()
    question7()

    # Question 8:
    printQuestionNum()
    question8()

main()
