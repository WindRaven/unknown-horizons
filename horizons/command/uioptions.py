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

from horizons.command import GenericCommand

class SetTaxSetting(GenericCommand):
	"""Sets the taxes for a settlement."""
	def __init__(self, settlement, level, new_taxes):
		super(SetTaxSetting, self).__init__(settlement, 'set_tax_setting', level, new_taxes)

GenericCommand.allow_network(SetTaxSetting)

class SetSettlementUpgradePermissions(GenericCommand):
	"""Sets the new upgrade permissions for a level in a settlement."""
	def __init__(self, settlement, level, allowed):
		super(SetSettlementUpgradePermissions, self).__init__(settlement, 'set_upgrade_permissions', level, allowed)

GenericCommand.allow_network(SetSettlementUpgradePermissions)

class AddToBuyList(GenericCommand):
	"""Adds a Resource to buy_list of TradePost"""
	def __init__(self, tradepost, res_id, limit):
		super(AddToBuyList, self).__init__(tradepost, 'add_to_buy_list', res_id, limit)

GenericCommand.allow_network(AddToBuyList)

class RemoveFromBuyList(GenericCommand):
	"""Removes a Resource from buy_list of TradePost"""
	def __init__(self, tradepost, res_id):
		super(RemoveFromBuyList, self).__init__(tradepost, 'remove_from_buy_list', res_id)

GenericCommand.allow_network(RemoveFromBuyList)

class AddToSellList(GenericCommand):
	"""Adds a Resource to sell_list of TradePost"""
	def __init__(self, tradepost, res_id, limit):
		super(AddToSellList, self).__init__(tradepost, 'add_to_sell_list', res_id, limit)

GenericCommand.allow_network(AddToSellList)

class RemoveFromSellList(GenericCommand):
	"""Removes a Resource from sell_list of TradePost"""
	def __init__(self, tradepost, res_id):
		super(RemoveFromSellList, self).__init__(tradepost, 'remove_from_sell_list', res_id)

GenericCommand.allow_network(RemoveFromSellList)

class TransferResource(GenericCommand):
	"""Transfers an amount of a resource from one Storage to another"""
	def __init__(self, amount, res_id, transfer_from, transfer_to):
		super(TransferResource, self).__init__(transfer_from, 'transfer_to_storageholder', amount, res_id, transfer_to.worldid)

GenericCommand.allow_network(TransferResource)

class SellResource(GenericCommand):
	"""The given settlement attempts to sell the given amount of resource to the ship"""
	def __init__(self, settlement, ship, resource_id, amount):
		super(SellResource, self).__init__(settlement, 'sell_resource', ship.worldid, resource_id, amount)

GenericCommand.allow_network(SellResource)

class BuyResource(GenericCommand):
	"""The given settlement attempts to buy the given amount of resource from the ship"""
	def __init__(self, settlement, ship, resource_id, amount):
		super(BuyResource, self).__init__(settlement, 'buy_resource', ship.worldid, resource_id, amount)

GenericCommand.allow_network(BuyResource)

class RenameObject(GenericCommand):
	"""Rename a NamedObject"""
	def __init__(self, obj, new_name):
		super(RenameObject, self).__init__(obj, "set_name", new_name)

GenericCommand.allow_network(RenameObject)

class EquipWeaponFromInventory(GenericCommand):
	"""Equips a weapon to weapon storage from resource inventory"""
	def __init__(self, obj, weapon_id, number):
		super(EquipWeaponFromInventory, self).__init__(obj, "equip_from_inventory", weapon_id, number)

GenericCommand.allow_network(EquipWeaponFromInventory)

class UnequipWeaponToInventory(GenericCommand):
	"""Equips a weapon to weapon storage from resource inventory"""
	def __init__(self, obj, weapon_id, number):
		super(UnequipWeaponToInventory, self).__init__(obj, "unequip_to_inventory", weapon_id, number)

GenericCommand.allow_network(UnequipWeaponToInventory)
