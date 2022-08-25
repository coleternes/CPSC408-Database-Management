
CREATE TABLE songs(
    songID VARCHAR(22) NOT NULL PRIMARY KEY,
    Name VARCHAR(20),
    Artist VARCHAR(20),
    Album VARCHAR(20),
    releaseDate DATETIME,
    Genre VARCHAR(20),
    Explicit BOOLEAN,
    Duration DOUBLE,
    Energy DOUBLE,
    Danceability DOUBLE,
    Acousticness DOUBLE,
    Liveness DOUBLE,
    Loudness DOUBLE
);
