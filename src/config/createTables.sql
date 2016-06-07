CREATE TABLE "Server" (
    "DiscordID" TEXT NOT NULL,
    "OwnerID" TEXT NOT NULL,
    "ManagementChannelID" TEXT NOT NULL
);
CREATE TABLE "Tournament" (
    "ChallongeID" TEXT NOT NULL,
    "ServerID" TEXT NOT NULL,
    "ChannelID" TEXT NOT NULL,
    "RoleID" TEXT NOT NULL
);
CREATE TABLE "TournamentUsers" (
    "TournamentID" TEXT NOT NULL,
    "UserDiscordID" TEXT NOT NULL,
    "UserChallongeID" TEXT
);
CREATE TABLE "User" (
    "DiscordID" TEXT NOT NULL,
    "ChallongeUserName" TEXT,
    "ChallongeAPIKey" TEXT
);
CREATE TABLE "Profile" (
    "LoggedAt" TEXT NOT NULL,
    "Scope" TEXT NOT NULL,
    "Time" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Args" TEXT,
    "Server" TEXT
);
