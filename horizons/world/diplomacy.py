# ###################################################
# Copyright (C) 2011 The Unknown Horizons Team
# team@unknown-horizons.org
# This file is part of Unknown Horizons.
#
# Unknown Horizons is free software; you can redistribute it and/or modify
# it under the terms of the GNU General Public License as published by
# the Free Software Foundation; either version 2 of the License, or
# (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the
# Free Software Foundation, Inc.,
# 51 Franklin St, Fifth Floor, Boston, MA  02110-1301  USA
# ###################################################

from horizons.util.changelistener import metaChangeListenerDecorator

@metaChangeListenerDecorator("diplomacy_status_changed")
class Diplomacy(object):
	"""
	Diplomacy class
	handles diplomacy between players
	two players can be friends, neutral or enemies
		friends: set of (a,b) tuples of player instances meaning a and b are friends
		         for making the relationship symetrical a has a lower worldid than b
		enemies: set of (a,b) tuples of player instances meaning a and b are enemies
		if to players are not friends nore enemies, they are neutral

		for listeners that are not Callback instances, the arguments must be:
			caller, change_type, a, b
			change_type is a string that can be 'friend', 'neutral' or 'enemy'
			a is first player
			b is second player
	"""

	def __init__(self):
		self.friends = set()
		self.enemies = set()

	def add_friend_pair(self, a, b):
		tup = make_tup(a, b)
		if tup is None:
			return
		self.remove_enemy_pair(a, b)
		if tup not in self.friends:
			self.friends.add(tup)
		else:
			return
		self.on_diplomacy_status_changed(change_type='friend', a = a, b = b)

	def add_enemy_pair(self, a, b):
		tup = make_tup(a, b)
		if tup is None:
			return
		self.remove_friend_pair(a, b)
		if tup not in self.enemies:
			self.enemies.add(tup)
		else:
			return
		self.on_diplomacy_status_changed(change_type='enemy', a = a, b = b)

	def add_neutral_pair(self, a, b):
		tup = make_tup(a, b)
		if tup is None:
			return
		if tup not in self.friends and tup not in self.enemies:
			return
		self.remove_friend_pair(a,b)
		self.remove_enemy_pair(a,b)
		self.on_diplomacy_status_changed(change_type='neutral', a = a, b = b)

	def remove_enemy_pair(self, a, b):
		tup = make_tup(a,b)
		if tup is None:
			return
		if tup in self.enemies:
			self.enemies.remove(tup)

	def remove_friend_pair(self, a, b):
		tup = make_tup(a,b)
		if tup is None:
			return
		if tup in self.friends:
			self.friends.remove(tup)

	def are_friends(self, a, b):
		if a is b:
			return True
		tup = make_tup(a,b)
		return tup in self.friends

	def are_enemies(self, a, b):
		if a is b:
			return False
		tup = make_tup(a,b)
		return tup in self.enemies

	def are_neutral(self, a, b):
		if a is b:
			return False
		tup = make_tup(a,b)
		return tup not in self.friends and tup not in self.enemies

	def load(self, world, db):
		for a, b in db("SELECT player1, player2 FROM diplomacy_allies"):
			tup = world.get_object_by_id(a), world.get_object_by_id(b)
			self.friends.add(tup)
		for a, b in db("SELECT player1, player2 FROM diplomacy_enemies"):
			tup = world.get_object_by_id(a), world.get_object_by_id(b)
			self.enemies.add(tup)

	def save(self, db):
		for tup in self.friends:
			db("INSERT INTO diplomacy_allies(player1, player2) VALUES(?, ?)",
				tup[0].worldid, tup[1].worldid)
		for tup in self.enemies:
			db("INSERT INTO diplomacy_enemies(player1, player2) VALUES(?, ?)",
				tup[0].worldid, tup[1].worldid)

def make_tup(a, b):
	"""
	Utility function that returns x,y tuple with x.worldid < y.worldid
	"""
	if a is b:
		return None
	elif a.worldid < b.worldid:
		return a,b
	else:
		return b,a
