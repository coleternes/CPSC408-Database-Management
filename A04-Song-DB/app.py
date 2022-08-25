from db_operations import db_operations
from helper import helper

db_ops = db_operations("chinook.db")
data = helper.data_cleaner("songs.csv")

def start_screen():
    print("Welcome to your playlist!")

def is_empty():
    query = '''
    SELECT COUNT(*)
    FROM songs;
    '''

    result = db_ops.single_record(query)
    return result == 0

def pre_process():
    # Fills table from songs.csv if empty
    if is_empty():
        attribute_count = len(data[0]) # Number of attributes
        placeholders = ("?," * attribute_count)[:-1]
        query = "INSERT INTO songs VALUES (" + placeholders + ")"
        db_ops.bulk_insert(query, data)

    # FEATURE 1
    # Prompt user for path to file that can add new songs
    print("Do you want to load new songs into your playlist?" \
    "\n1. Yes" \
    "\n2. No")
    user_choice = helper.get_choice([1,2])

    # Checks if the user wants to add new songs
    if user_choice == 1:
        path = input("Please provide the file path to the songs file: ")
        tmp_data = helper.data_cleaner(path) # Stores the songs from the file
        new_data = [] # Will store only the songs that do not currently exist in the playlist

        # BONUS 1
        # Before inserting each new song, check if that song already exists
        for record in tmp_data:
            query = '''
            SELECT *
            FROM songs
            WHERE songID = '%s';
            '''

            result = db_ops.cursor.execute(query % record[0])
            song_name = result.fetchone()
            if not song_name:
                new_data.append(record) # Only appends the song if it is not found in the playlist

        # Checks that new_data is not empty
        if new_data:
            attribute_count = len(new_data[0]) # Number of attributes
            placeholders = ("?," * attribute_count)[:-1]
            query = "INSERT INTO songs VALUES (" + placeholders + ")"
            db_ops.bulk_insert(query, new_data)

def options():
    print("Select from the following menu options:" \
    "\n1. Find songs by artist" \
    "\n2. Find songs by genre" \
    "\n3. Find songs by feature" \
    "\n4. Update song information" \
    "\n5. Delete song from playlist" \
    "\n6. Remove songs containing null" \
    "\n7. Exit")
    return helper.get_choice([1,2,3,4,5,6,7])

def search_by_artist():
    query = '''
    SELECT DISTINCT Artist
    FROM songs;
    '''

    print("Artists in playlist:")
    artists = db_ops.single_attribute(query)

    choices = {}
    for i in range(len(artists)):
        print(i, artists[i])
        choices[i] = artists[i]
    index = helper.get_choice(choices.keys())

    # User can ask to see 1, 5, or all songs
    print("How many songs do you want returned for", choices[index]+"?")
    print("Enter 1, 5, or 0 for all songs")
    num = helper.get_choice([1,5,0])

    query = "SELECT DISTINCT name FROM songs WHERE Artist=:artist ORDER BY RANDOM()"
    dictionary = {"artist":choices[index]}
    if num != 0:
        query += " LIMIT:lim;"
        dictionary["lim"] = num
    else:
        query += ";"
    helper.pretty_print(db_ops.name_placeholder_query(query, dictionary))

def search_by_genre():
    query = '''
    SELECT DISTINCT Genre
    FROM songs;
    '''

    print("Genres in playlist:")
    genres = db_ops.single_attribute(query)

    choices = {}
    for i in range(len(genres)):
        print(i, genres[i])
        choices[i] = genres[i]
    index = helper.get_choice(choices.keys())

    # User can ask to see 1, 5, or all songs
    print("How many songs do you want returned for", choices[index]+"?")
    print("Enter 1, 5, or 0 for all songs")
    num = helper.get_choice([1,5,0])

    query = "SELECT DISTINCT name FROM songs WHERE Genre=:genre ORDER BY RANDOM()"
    dictionary = {"genre":choices[index]}
    if num != 0:
        query += " LIMIT:lim;"
        dictionary["lim"] = num
    else:
        query += ";"
    helper.pretty_print(db_ops.name_placeholder_query(query, dictionary))

def search_by_feature():
    features = ['Danceability', 'Liveness', 'Loudness']
    choices = {}
    for i in range(len(features)):
        print(i, features[i])
        choices[i] = features[i]
    index = helper.get_choice(choices.keys())

    # User can ask to see 1, 5, or all songs
    print("How many songs do you want returned for", choices[index]+"?")
    print("Enter 1, 5, or 0 for all songs")
    num = helper.get_choice([1,5,0])

    print("Do you want results sorted by the feature in ascending or descending order?")
    order = input("ASC or DESC: ")

    query = "SELECT DISTINCT name FROM songs ORDER BY " + choices[index] + " " + order
    dictionary = {}
    if num != 0:
        query += " LIMIT:lim;"
        dictionary["lim"] = num
    else:
        query += ";"
    helper.pretty_print(db_ops.name_placeholder_query(query, dictionary))

# FEATURE 2
def update_information():
    print("What kind of update would you like to perform?" \
    "\n1. Single song update" \
    "\n2. Bulk update")

    user_choice = helper.get_choice([1,2])

    # Update only a single song
    if user_choice == 1:
        song_name = input("Please provide the name of the song you wish to update: ")

        select_query = '''
        SELECT *
        FROM songs
        WHERE Name = '%s';
        '''

        result = db_ops.cursor.execute(select_query % song_name)

        song = result.fetchone()

        # Checks if the song is in the playlist
        if song:
            new_name = song[1]
            new_artist = song[2]
            new_album = song[3]
            new_release_date = song[4]
            flip_explicit = song[6]

            print("You have selected:",
            "\nSong Name: ", new_name,
            "\nArtist: ", new_artist,
            "\nAlbum: ", new_album,
            "\nRelease Date:", new_release_date,
            "\nExplicit: ", flip_explicit)

            print("Which attribute would you like to update?" \
            "\n1. Song Name" \
            "\n2. Artist" \
            "\n3. Album" \
            "\n4. Release Date" \
            "\n5. Explicit")
            num = helper.get_choice([1,2,3,4,5])

            if num == 1:
                new_name = input("Enter the new name: ")
            elif num == 2:
                new_artist = input("Enter the new artist: ")
            elif num == 3:
                new_album = input("Enter the new album: ")
            elif num == 4:
                new_release_date = input("Enter the new release date: ")
            elif num == 5:
                flip_explicit = not flip_explicit
                print("The explicit attribute has been flipped")

            update_song = [(new_name, new_artist, new_album, new_release_date, flip_explicit, song[0])]

            update_query = '''
            UPDATE songs
            SET Name = ?, Artist = ?, Album = ?, releaseDate = ?, Explicit = ?
            WHERE songID = ?;
            '''

            db_ops.cursor.executemany(update_query, update_song)
            db_ops.connection.commit()
        else:
            print("The song with that name was not found")
    # Bonus 2
    # Update a group of songs by attribute
    elif user_choice == 2:
        print("Select which attribute you wish to update:" \
        "\n1. Album" \
        "\n2. Artist" \
        "\n3. Genre")
        attribute_choice = helper.get_choice([1,2,3])

        if attribute_choice == 1:
            old_album = input("Enter the album you wish to update: ")
            new_album = input("Enter the new album: ")
            update_list = [(new_album, old_album)]

            update_query = '''
            UPDATE songs
            SET Album = ?
            WHERE Album = ?;
            '''

            db_ops.cursor.executemany(update_query, update_list)
            db_ops.connection.commit()
        elif attribute_choice == 2:
            old_artist = input("Enter the artist you wish to update: ")
            new_artist = input("Enter the new artist: ")
            update_list = [(new_artist, old_artist)]

            update_query = '''
            UPDATE songs
            SET Artist = ?
            WHERE Artist = ?;
            '''

            db_ops.cursor.executemany(update_query, update_list)
            db_ops.connection.commit()
        elif attribute_choice == 3:
            old_genre = input("Enter the genre you wish to update: ")
            new_genre = input("Enter the new genre: ")
            update_list = [(new_genre, old_genre)]

            update_query = '''
            UPDATE songs
            SET Genre = ?
            WHERE Genre = ?;
            '''

            db_ops.cursor.executemany(update_query, update_list)
            db_ops.connection.commit()

# FEATURE 3
def delete_song():
    song_name = input("Please provide the name of the song to delete: ")

    query = '''
    DELETE FROM songs
    WHERE Name = '%s';
    '''

    db_ops.cursor.execute(query % song_name)
    db_ops.connection.commit()

# BONUS 3
def remove_null():
    select_query = '''
    SELECT songID
    FROM songs
    WHERE Name IS NULL
    OR Artist IS NULL
    OR Album IS NULL
    OR releaseDate IS NULL
    OR Genre IS NULL
    OR Explicit IS NULL
    OR Duration IS NULL
    OR Energy IS NULL
    OR Danceability IS NULL
    OR Acousticness IS NULL
    OR Liveness IS NULL
    OR Loudness IS NULL;
    '''

    select_result = db_ops.cursor.execute(select_query)

    for row in select_result:
        delete_query = '''
        DELETE FROM songs
        WHERE songID = '%s';
        '''

        db_ops.cursor.execute(delete_query % row)
        db_ops.connection.commit()

# Main program
def main():
    start_screen()
    pre_process()
    while True:
        user_choice = options()
        if user_choice == 1:
            search_by_artist()
        elif user_choice == 2:
            search_by_genre()
        elif user_choice == 3:
            search_by_feature()
        elif user_choice == 4:
            update_information()
        elif user_choice == 5:
            delete_song()
        elif user_choice == 6:
            remove_null()
        elif user_choice == 7:
            print("Goodbye!")
            break

    db_ops.destructor()

main()
