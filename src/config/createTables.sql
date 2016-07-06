BEGIN TRANSACTION;
CREATE TABLE "User" (
	`DiscordID`	TEXT NOT NULL UNIQUE,
	`ChallongeUserName`	TEXT,
	`ChallongeAPIKey`	TEXT,
	PRIMARY KEY(DiscordID)
);
CREATE TABLE "TournamentUsers" (
    "TournamentID" TEXT NOT NULL,
    "UserDiscordID" TEXT NOT NULL,
    "UserChallongeID" TEXT
);
CREATE TABLE "Tournament" (
	`ChallongeID`	TEXT NOT NULL UNIQUE,
	`ServerID`	TEXT NOT NULL,
	`ChannelID`	TEXT NOT NULL UNIQUE,
	`RoleID`	TEXT NOT NULL UNIQUE,
	PRIMARY KEY(ChallongeID)
);
CREATE TABLE "Server" (
	`DiscordID`	TEXT NOT NULL UNIQUE,
	`OwnerID`	TEXT NOT NULL,
	`ManagementChannelID`	TEXT NOT NULL,
	`Trigger` TEXT,
	PRIMARY KEY(DiscordID)
);
CREATE TABLE "Profile" (
    "LoggedAt" TEXT NOT NULL,
    "Scope" TEXT NOT NULL,
    "Time" TEXT NOT NULL,
    "Name" TEXT NOT NULL,
    "Args" TEXT,
    "Server" TEXT
);
CREATE TABLE "Modules" (
    "ServerID" TEXT NOT NULL,
    "ModuleName" TEXT NOT NULL,
    "ModuleDef" TEXT NOT NULL,
    UNIQUE(ServerID, ModuleName)
);

COMMIT;
