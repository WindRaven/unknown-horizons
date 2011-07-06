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

from mission.domestictrade import DomesticTrade

from building import AbstractBuilding
from horizons.util import WorldObject
from horizons.util.python import decorators
from horizons.constants import RES

class TradeManager(WorldObject):
	"""
	An object of this class manages the trade routes of one settlement.
	"""

	legal_resources = [RES.FOOD_ID, RES.BRICKS_ID, RES.TOOLS_ID]

	def __init__(self, settlement_manager):
		super(TradeManager, self).__init__()
		self.__init(settlement_manager)

	def __init(self, settlement_manager):
		self.settlement_manager = settlement_manager
		self.data = {} # (resource_id, building_id): SingleResourceManager
		self.ship = None

	def save(self, db):
		super(ResourceManager, self).save(db)
		pass # TODO: save

	def _load(self, db, settlement_manager):
		#worldid = db("SELECT rowid FROM ai_resource_manager WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		#super(ResourceManager, self).load(db, worldid)
		#self.__init()
		pass # TODO: load

	@classmethod
	def load(cls, db, settlement_manager):
		self = cls.__new__(cls)
		self._load(db, settlement_manager)
		return self

	def refresh(self):
		for resource_manager in self.data.itervalues():
			resource_manager.refresh()

	def finalize_requests(self):
		for resource_manager in self.data.itervalues():
			resource_manager.finalize_requests()

	def request_quota_change(self, quota_holder, resource_id, amount):
		if resource_id not in self.legal_resources:
			return
		if resource_id not in self.data:
			self.data[resource_id] = SingleResourceTradeManager(self.settlement_manager, resource_id)
		self.data[resource_id].request_quota_change(quota_holder, amount)

	def get_quota(self, quota_holder, resource_id):
		if resource_id not in self.legal_resources:
			return 0.0
		if resource_id not in self.data:
			self.data[resource_id] = SingleResourceTradeManager(self.settlement_manager, resource_id)
		return self.data[resource_id].get_quota(quota_holder)

	def load_resources(self, source_settlement_manager, ship):
		""" the given ship has arrived at the source settlement to pick up the resources required by this trade manager """
		total_amount = {}
		for resource_manager in source_settlement_manager.trade_manager.data.itervalues():
			for settlement_manager, amount in resource_manager.partners.iteritems():
				if settlement_manager != self.settlement_manager:
					continue # not the right one
				if resource_manager.resource_id not in total_amount:
					total_amount[resource_manager.resource_id] = 0.0
				total_amount[resource_manager.resource_id] += amount

		any_transferred = False
		for resource_id, amount in total_amount.iteritems():
			actual_amount = int(round(5000 * amount)) # take resources for 5000 ticks
			if actual_amount > 0:
				any_transferred = True
			self.settlement_manager.owner.complete_inventory.move(ship, source_settlement_manager.settlement, resource_id, -actual_amount)
		return any_transferred

	def _get_source_settlement_manager(self):
		total_amount = {}
		for resource_manager in self.data.itervalues():
			for settlement_manager, amount in resource_manager.partners.iteritems():
				if settlement_manager not in total_amount:
					total_amount[settlement_manager] = 0.0
				total_amount[settlement_manager] += amount
		options = [(amount, settlement_manager.worldid, settlement_manager) for settlement_manager, amount in total_amount.iteritems()]
		options.sort(reverse = True)
		return options[0][2] if options else None

	def organize_shipping(self):
		source_settlement_manager = self._get_source_settlement_manager()
		if source_settlement_manager is None:
			return # no trade ships needed

		player = self.settlement_manager.owner
		if self.ship is not None:
			if player.ships[self.ship] == player.shipStates.idle:
				self.ship = None
		if self.ship is not None:
			return # already using a ship

		# need to get a ship
		for ship, ship_state in player.ships.iteritems():
			if ship_state == player.shipStates.idle:
				self.ship = ship
				break
		if self.ship is None:
			return # no available ships

		player.ships[self.ship] = player.shipStates.on_a_mission
		mission = DomesticTrade(source_settlement_manager, self.settlement_manager, self.ship, player.report_success, player.report_failure)
		player.missions.add(mission)
		mission.start()

	def __str__(self):
		result = 'TradeManager(%d)' % self.worldid
		for resource_manager in self.data.itervalues():
			result += '\n' + resource_manager.__str__()
		return result

class SingleResourceTradeManager(WorldObject):
	def __init__(self, settlement_manager, resource_id):
		super(SingleResourceTradeManager, self).__init__()
		self.__init(settlement_manager, resource_id)
		self.available = 0.0 # unused resource production available per tick
		self.total = 0.0 # total resource production imported per tick
		self.partners = {}

	def __init(self, settlement_manager, resource_id):
		self.settlement_manager = settlement_manager
		self.resource_id = resource_id
		self.quotas = {} # {quota_holder: amount, ...}
		self.identifier = '/%d,%d/trade' % (self.worldid, self.resource_id)
		self.building_ids = []
		for abstract_building in AbstractBuilding.buildings.itervalues():
			if self.resource_id in abstract_building.lines:
				self.building_ids.append(abstract_building.id)

	def save(self, db, resource_manager, building_id):
		pass # TODO: save

	def _load(self, db, worldid):
		super(SingleResourceManager, self).load(db, worldid)
		self.__init(resource_id)
		pass # TODO: load

	@classmethod
	def load(cls, db, worldid):
		self = cls.__new__(cls)
		self._load(db, worldid)
		return self

	def _refresh_current_production(self):
		total = 0.0
		for settlement_manager in self.settlement_manager.owner.settlement_managers:
			if self.settlement_manager != settlement_manager:
				resource_manager = settlement_manager.resource_manager
				for building_id in self.building_ids:
					resource_manager.request_quota_change(self.identifier, self.resource_id, building_id, 100)
					total += resource_manager.get_quota(self.identifier, self.resource_id, building_id)
		return total

	def refresh(self):
		production = self._refresh_current_production()
		if production >= self.total:
			self.available += production - self.total
		else:
			change = self.total - production
			if change > self.available and self.total - self.available > 1e-7:
				# unable to honour current quota assignments, decreasing all equally
				multiplier = 0.0 if abs(production) < 1e-7 else (self.total - self.available) / production
				for quota_holder in self.quotas:
					amount = self.quotas[quota_holder]
					if amount > 1e-7:
						amount *= multiplier
				self.available = 0.0
			else:
				self.available -= change
		self.total = production

	def finalize_requests(self):
		options = []
		for settlement_manager in self.settlement_manager.owner.settlement_managers:
			if self.settlement_manager != settlement_manager:
				resource_manager = settlement_manager.resource_manager
				for building_id in self.building_ids:
					amount = resource_manager.get_quota(self.identifier, self.resource_id, building_id)
					options.append((amount, building_id, resource_manager.worldid, resource_manager, settlement_manager))
		options.sort(reverse = True)

		self.partners = {}
		needed_amount = self.total - self.available
		for amount, building_id, _, resource_manager, settlement_manager in options:
			if amount > needed_amount:
				resource_manager.request_quota_change(self.identifier, self.resource_id, building_id, needed_amount)
				#print resource_manager.data[(self.resource_id, building_id)]
				self.partners[settlement_manager] = needed_amount
				needed_amount = 0
			else:
				self.partners[settlement_manager] = amount
				needed_amount -= amount
			if needed_amount < 1e-9:
				break
		self.total -= self.available
		self.available = 0.0

	def get_quota(self, quota_holder):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		return self.quotas[quota_holder]

	def request_quota_change(self, quota_holder, amount):
		if quota_holder not in self.quotas:
			self.quotas[quota_holder] = 0.0
		amount = max(amount, 0.0)

		if amount <= self.quotas[quota_holder]:
			# lower the amount of reserved import
			change = self.quotas[quota_holder] - amount
			self.available += change
			self.quotas[quota_holder] -= change
		else:
			# raise the amount of reserved import
			change = min(amount - self.quotas[quota_holder], self.available)
			self.available -= change
			self.quotas[quota_holder] += change

	def __str__(self):
		result = 'Resource %d import %.5f/%.5f' % (self.resource_id, self.available, self.total)
		for quota in self.quotas.itervalues():
			result += '\n  quota assignment %.5f' % quota
		for settlement_manager, amount in self.partners.iteritems():
			result += '\n  import %.5f from %s' % (amount, settlement_manager.settlement.name)
		return result

decorators.bind_all(TradeManager)
decorators.bind_all(SingleResourceTradeManager)