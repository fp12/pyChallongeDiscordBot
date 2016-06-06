PRAGMA foreign_keys=OFF;
BEGIN TRANSACTION;
CREATE TABLE "User" (
    "DiscordID" INTEGER PRIMARY KEY NOT NULL,
    "ChallongeUserName" TEXT,
    "ChallongeAPIKey" TEXT
);
CREATE TABLE "Server" (
    "DiscordID" INTEGER PRIMARY KEY NOT NULL,
    "OwnerID" INTEGER NOT NULL,
    "ManagementChannelID" INTEGER NOT NULL
);
CREATE TABLE "Tournament" (
    "ChallongeID" INTEGER PRIMARY KEY NOT NULL,
    "ServerID" INTEGER NOT NULL,
    "ChannelID" INTEGER NOT NULL,
    "RoleID" INTEGER NOT NULL
);
CREATE TABLE "TournamentUsers" (
    "TournamentID" INTEGER NOT NULL,
    "UserDiscordID" INTEGER NOT NULL,
    "UserChallongeID" INTEGER
);
COMMIT;
