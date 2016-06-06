class DBServer():
	def __init__(self, tup):
		if tup:
			self._tup = tup
		else:
			self._tup = (0, 0, 0)

	@property
	def server_id(self):
		return self._tup[0]

	@property
	def owner_id(self):
		return self._tup[1]

	@property
	def management_channel_id(self):
		return self._tup[2]

class DBTournament():
	def __init__(self, tup):
		if tup:
			self._tup = tup
		else:
			self._tup = (0, 0, 0, 0)

	@property
	def challonge_id(self):
		return self._tup[0]

	@property
	def server_id(self):
		return self._tup[1]

	@property
	def channel_id(self):
		return self._tup[2]

	@property
	def role_id(self):
		return self._tup[3]