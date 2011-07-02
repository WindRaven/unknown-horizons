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

import copy
import math

from collections import deque

from areabuilder import AreaBuilder
from builder import Builder
from constants import BUILD_RESULT, BUILDING_PURPOSE

from horizons.constants import AI, BUILDINGS
from horizons.util import Point, Rect
from horizons.util.python import decorators
from horizons.entities import Entities

class VillageBuilder(AreaBuilder):
	def __init__(self, settlement_manager):
		super(VillageBuilder, self).__init__(settlement_manager)
		self.__init(settlement_manager)
		self._create_plan()

	def __init(self, settlement_manager):
		self.land_manager = settlement_manager.land_manager
		self.tents_to_build = 0
		self.tent_queue = deque()
		self._init_cache()

	def save(self, db):
		super(VillageBuilder, self).save(db, 'ai_village_builder_coords')
		db("INSERT INTO ai_village_builder(rowid, settlement_manager) VALUES(?, ?)", self.worldid, \
			self.settlement_manager.worldid)

	def _load(self, db, settlement_manager):
		worldid = db("SELECT rowid FROM ai_village_builder WHERE settlement_manager = ?", settlement_manager.worldid)[0][0]
		super(VillageBuilder, self).load(db, worldid)
		self.__init(settlement_manager)

		db_result = db("SELECT x, y, purpose, builder FROM ai_village_builder_coords WHERE village_builder = ?", worldid)
		for x, y, purpose, builder_id in db_result:
			coords = (x, y)
			builder = Builder.load(db, builder_id, self.land_manager) if builder_id else None
			self.register_change(x, y, purpose, builder)
			if purpose == BUILDING_PURPOSE.UNUSED_RESIDENCE or purpose == BUILDING_PURPOSE.RESIDENCE:
				self.tents_to_build += 1
		self._create_tent_queue()

	def _get_village_section_coordinates(self, start_x, start_y, width, height):
		result = set()
		for dx in xrange(width):
			for dy in xrange(height):
				coords = (start_x + dx, start_y + dy)
				if coords in self.land_manager.village and self.land_manager._coords_usable(coords):
					result.add(coords)
		return result

	def _create_plan(self):
		"""
		1. find a way to cut the village area into rectangular sections
		2. each section gets a plan with a main square, roads, and possible tent locations
		3. the plan is stitched together and other village buildings are added
		"""

		xs = set([x for (x, _) in self.land_manager.village])
		ys = set([y for (_, y) in self.land_manager.village])
		max_size = 22

		width = max(xs) - min(xs) + 1
		height = max(ys) - min(ys) + 1
		horizontal_sections = int(math.ceil(float(width) / max_size))
		vertical_sections = int(math.ceil(float(height) / max_size))

		sections = []
		vertical_roads = []
		horizontal_roads = []
		if horizontal_sections == 1 and vertical_sections == 1:
			# just one section, no extra roads needed
			section = self._create_section_plan(self.land_manager.village)
			sections.append(section[1])
		else:
			# partition with roads between the sections
			start_y = min(ys)
			section_width = width / horizontal_sections
			section_height = height / vertical_sections
			for i in xrange(vertical_sections):
				bottom_road = i + 1 < vertical_sections
				max_y = min(max(ys), start_y + section_height)
				current_height = max_y - start_y + 1
				start_x = min(xs)

				for j in xrange(horizontal_sections):
					right_road = j + 1 < horizontal_sections
					max_x = min(max(xs), start_x + section_width)
					current_width = max_x - start_x + 1
					section_coords_set = self._get_village_section_coordinates(start_x, start_y, current_width - right_road, current_height - bottom_road)
					section = self._create_section_plan(section_coords_set)
					sections.append(section[1])
					start_x += current_width
					if i == 0 and right_road:
						vertical_roads.append(start_x - 1)

				start_y += current_height
				if bottom_road:
					horizontal_roads.append(start_y - 1)

		self._compose_sections(sections, vertical_roads, horizontal_roads)

	def _compose_sections(self, sections, vertical_roads, horizontal_roads):
		self.plan = {}
		ys = set([y for (_, y) in self.land_manager.village])
		for road_x in vertical_roads:
			for road_y in ys:
				coords = (road_x, road_y)
				if self.land_manager._coords_usable(coords):
					self.plan[coords] = (BUILDING_PURPOSE.ROAD, None)

		xs = set([x for (x, _) in self.land_manager.village])
		for road_y in horizontal_roads:
			for road_x in xs:
				coords = (road_x, road_y)
				if self.land_manager._coords_usable(coords):
					self.plan[coords] = (BUILDING_PURPOSE.ROAD, None)

		for plan in sections:
			self._optimize_plan(plan)
			for coords in plan:
				if plan[coords][0] == BUILDING_PURPOSE.UNUSED_RESIDENCE:
					builder = Builder.create(BUILDINGS.RESIDENTIAL_CLASS, self.land_manager, Point(coords[0], coords[1]))
					plan[coords] = (BUILDING_PURPOSE.UNUSED_RESIDENCE, builder)
				elif plan[coords][0] == BUILDING_PURPOSE.MAIN_SQUARE:
					builder = Builder.create(BUILDINGS.MARKET_PLACE_CLASS, self.land_manager, Point(coords[0], coords[1]))
					plan[coords] = (BUILDING_PURPOSE.MAIN_SQUARE, builder)
			self._create_tent_queue(plan)
			for coords in plan:
				self.plan[coords] = plan[coords]
		self.num_sections = len(sections)
		self._reserve_other_buildings()

	@classmethod
	def _remove_unreachable_roads(cls, plan, main_square):
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		reachable = set()
		queue = deque()
		for (x, y) in main_square.tuple_iter():
			for (dx, dy) in moves:
				coords = (x + dx, y + dy)
				if coords in plan and plan[coords][0] == BUILDING_PURPOSE.ROAD:
					queue.append(coords)
					reachable.add(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in plan and plan[coords][0] == BUILDING_PURPOSE.ROAD and coords not in reachable:
					reachable.add(coords)
					queue.append(coords)

		to_remove = []
		for coords, (purpose, _) in plan.iteritems():
			if purpose == BUILDING_PURPOSE.ROAD and coords not in reachable:
				to_remove.append(coords)
		for coords in to_remove:
			plan[coords] = (BUILDING_PURPOSE.NONE, None)

	def _get_possible_building_positions(self, section_coords_set, size):
		result = {}
		for (x, y) in sorted(section_coords_set):
			ok = True
			for dx in xrange(size[0]):
				for dy in xrange(size[1]):
					coords = (x + dx, y + dy)
					if coords not in section_coords_set or not self.land_manager._coords_usable(coords):
						ok = False
						break
				if not ok:
					break
			if ok:
				result[(x, y)] = Rect.init_from_topleft_and_size(x, y, size[0] - 1, size[1] - 1)
		return result

	@classmethod
	def _get_main_square_position(cls, x, y):
		size = Entities.buildings[BUILDINGS.MARKET_PLACE_CLASS].size
		return Rect.init_from_topleft_and_size(x, y, size[0] - 1, size[1] - 1)

	def _create_section_plan(self, section_coords_set):
		"""
		The algorithm is as follows:
		Place the main square and then form a road grid to support the tents;
		prefer the one with maximum number of tent locations and minimum number of
		impossible road locations.
		"""

		best_plan = {}
		best_tents = 0
		best_value = -1
		xs = set([x for (x, _) in section_coords_set])
		ys = set([y for (_, y) in section_coords_set])
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]
		tent_radius = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].radius

		possible_road_positions = self._get_possible_building_positions(section_coords_set, (1, 1))
		possible_residence_positions = self._get_possible_building_positions(section_coords_set, Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].size)
		possible_main_square_positions = self._get_possible_building_positions(section_coords_set, Entities.buildings[BUILDINGS.MARKET_PLACE_CLASS].size)

		for (x, y), main_square in possible_main_square_positions.iteritems():
			plan = dict.fromkeys(section_coords_set, (BUILDING_PURPOSE.NONE, None))
			bad_roads = 0
			good_tents = 0

			# place the main square
			for coords in main_square.tuple_iter():
				plan[coords] = (BUILDING_PURPOSE.RESERVED, None)
			plan[(x, y)] = (BUILDING_PURPOSE.MAIN_SQUARE, None)

			# place the roads running parallel to the y-axis
			for road_y in ys:
				if road_y < y:
					if (y - road_y) % 5 != 1:
						continue
				else:
					if road_y < y + 6 or (road_y - y) % 5 != 1:
						continue
				for road_x in xs:
					coords = (road_x, road_y)
					if coords in possible_road_positions:
						plan[coords] = (BUILDING_PURPOSE.ROAD, None)
					else:
						bad_roads += 1

			# place the roads running parallel to the x-axis
			for road_x in xs:
				if road_x < x:
					if (x - road_x) % 5 != 1:
						continue
				else:
					if road_x < x + 6 or (road_x - x) % 5 != 1:
						continue
				for road_y in ys:
					coords = (road_x, road_y)
					if coords in possible_road_positions:
						plan[coords] = (BUILDING_PURPOSE.ROAD, None)
					else:
						bad_roads += 1

			if bad_roads > 0:
				self._remove_unreachable_roads(plan, main_square)

			# place the tents
			for coords, position in possible_residence_positions.iteritems():
				ok = True
				for dx, dy in tent_squares:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if plan[coords2][0] != BUILDING_PURPOSE.NONE:
						ok = False
						break
				if not ok:
					continue
				if main_square.distance(position) > tent_radius:
					continue # unable to build or out of main square range

				# is there a road connection?
				ok = False
				for dx, dy in road_connections:
					coords2 = (coords[0] + dx, coords[1] + dy)
					if coords2 in plan and plan[coords2][0] == BUILDING_PURPOSE.ROAD:
						ok = True
						break

				# connection to a road tile exists, build the tent
				if ok:
					for dx, dy in tent_squares:
						plan[(coords[0] + dx, coords[1] + dy)] = (BUILDING_PURPOSE.RESERVED, None)
					plan[coords] = (BUILDING_PURPOSE.UNUSED_RESIDENCE, None)
					good_tents += 1

			value = 10 * good_tents - bad_roads
			if best_value < value:
				best_plan = plan
				best_tents = good_tents
				best_value = value
		return (best_tents, best_plan)

	def _optimize_plan(self, plan):
		# calculate distance from the main square to every tile
		road_connections = [(-1, 0), (-1, 1), (0, -1), (0, 2), (1, -1), (1, 2), (2, 0), (2, 1)]
		tent_squares = [(0, 0), (0, 1), (1, 0), (1, 1)]
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		distance = {}
		queue = deque()

		for coords, (purpose, _) in plan.iteritems():
			if purpose == BUILDING_PURPOSE.MAIN_SQUARE:
				for coords in self._get_main_square_position(*coords).tuple_iter():
					distance[coords] = 0
					queue.append(coords)

		while queue:
			(x, y) = queue.popleft()
			for dx, dy in moves:
				coords = (x + dx, y + dy)
				if coords in plan and coords not in distance:
					distance[coords] = distance[(x, y)] + 1
					queue.append(coords)

		# remove planned tents from the plan
		for (x, y) in plan:
			coords = (x, y)
			if plan[coords][0] == BUILDING_PURPOSE.UNUSED_RESIDENCE:
				for dx, dy in tent_squares:
					plan[(x + dx, y + dy)] = (BUILDING_PURPOSE.NONE, None)

		# create new possible tent position list
		possible_tents = []
		for coords in plan:
			if coords in distance and plan[coords][0] == BUILDING_PURPOSE.NONE:
				possible_tents.append((distance[coords], coords))
		possible_tents.sort()

		# place the tents
		for _, (x, y) in possible_tents:
			ok = True
			for dx, dy in tent_squares:
				coords = (x + dx, y + dy)
				if coords not in plan or plan[coords][0] != BUILDING_PURPOSE.NONE:
					ok = False
					break
			if not ok:
				continue

			# is there a road connection?
			ok = False
			for dx, dy in road_connections:
				coords = (x + dx, y + dy)
				if coords in plan and plan[coords][0] == BUILDING_PURPOSE.ROAD:
					ok = True
					break

			# connection to a road tile exists, build the tent
			if ok:
				for dx, dy in tent_squares:
					plan[(x + dx, y + dy)] = (BUILDING_PURPOSE.RESERVED, None)
				plan[(x, y)] = (BUILDING_PURPOSE.UNUSED_RESIDENCE, None)

		self._return_unused_space(plan)

	def _return_unused_space(self, plan):
		not_needed = []
		for coords, (purpose, _) in plan.iteritems():
			if purpose == BUILDING_PURPOSE.NONE:
				not_needed.append(coords)
		for coords in not_needed:
			self.land_manager.add_to_production(coords)

	def _replace_planned_tent(self, building_id, new_purpose, max_buildings, capacity):
		""" replaces up to max_buildings planned tents with buildings of type building_id."""

		tent_range = Entities.buildings[BUILDINGS.RESIDENTIAL_CLASS].radius
		planned_tents = set([builder.position for (purpose, builder) in self.plan.itervalues() if purpose == BUILDING_PURPOSE.UNUSED_RESIDENCE])
		possible_positions = copy.copy(planned_tents)

		def get_centroid(planned, blocked):
			total_x, total_y = 0, 0
			for position in planned_tents:
				if position not in blocked:
					total_x += position.left
					total_y += position.top
			mid_x = total_x / float(len(planned) - len(blocked))
			mid_y = total_y / float(len(planned) - len(blocked))
			return (mid_x, mid_y)

		def get_centroid_distance_pairs(planned, blocked):
			centroid = get_centroid(planned_tents, blocked)
			positions = []
			for position in planned_tents:
				if position not in blocked:
					positions.append((-position.distance(centroid), position))
			positions.sort()
			return positions

		for _ in xrange(max_buildings):
			if len(planned_tents) <= 1:
				break
			best_score = None
			best_pos = None
			best_in_range = 0

			for replaced_pos in possible_positions:
				positions = get_centroid_distance_pairs(planned_tents, set([replaced_pos]))
				score = 0
				in_range = 0
				for negative_distance_to_centroid, position in positions:
					if in_range < capacity and replaced_pos.distance(position) <= tent_range:
						in_range += 1
					else:
						score -= negative_distance_to_centroid
				if best_score is None or best_score > score:
					best_score = score
					best_pos = replaced_pos
					best_in_range = in_range

			in_range = 0
			positions = get_centroid_distance_pairs(planned_tents, set([best_pos]))
			for _, position in positions:
				if in_range < capacity and best_pos.distance(position) <= tent_range:
					planned_tents.remove(position)
					in_range += 1

			possible_positions.remove(best_pos)
			builder = Builder.create(building_id, self.land_manager, best_pos.origin)
			(x, y) = best_pos.origin.to_tuple()
			self.register_change(x, y, new_purpose, builder)
			self.tents_to_build -= 1

	def _reserve_other_buildings(self):
		"""Replaces planned tents with a pavilion, school, and tavern."""
		# TODO: load these constants in a better way
		max_capacity = 22
		normal_capacity = 20
		num_other_buildings = 0
		tents = len(self.tent_queue)
		while tents > 0:
			num_other_buildings += 3
			tents -= 3 + normal_capacity
		self._replace_planned_tent(BUILDINGS.PAVILION_CLASS, BUILDING_PURPOSE.PAVILION, num_other_buildings, max_capacity)
		self._replace_planned_tent(BUILDINGS.VILLAGE_SCHOOL_CLASS, BUILDING_PURPOSE.VILLAGE_SCHOOL, num_other_buildings, max_capacity)
		self._replace_planned_tent(BUILDINGS.TAVERN_CLASS, BUILDING_PURPOSE.TAVERN, num_other_buildings, max_capacity)

	def _create_tent_queue(self, plan):
		""" This function takes the plan and orders all planned tents according to
		the distance from the main square to the block they belong to. """
		moves = [(-1, 0), (0, -1), (0, 1), (1, 0)]
		blocks = []
		block = {}

		# form blocks of tents
		main_square = None
		for coords, (purpose, _) in plan.iteritems():
			if purpose == BUILDING_PURPOSE.MAIN_SQUARE:
				main_square = self._get_main_square_position(*coords)
			if purpose != BUILDING_PURPOSE.UNUSED_RESIDENCE or coords in block:
				continue
			block[coords] = len(blocks)

			block_list = [coords]
			queue = deque()
			explored = set([coords])
			queue.append(coords)
			while queue:
				(x, y) = queue.popleft()
				for dx, dy in moves:
					coords = (x + dx, y + dy)
					if coords not in plan or coords in explored:
						continue
					if plan[coords][0] == BUILDING_PURPOSE.UNUSED_RESIDENCE or plan[coords][0] == BUILDING_PURPOSE.RESERVED:
						explored.add(coords)
						queue.append(coords)
						if plan[coords][0] == BUILDING_PURPOSE.UNUSED_RESIDENCE:
							block[coords] = len(blocks)
							block_list.append(coords)
			blocks.append(block_list)

		# calculate distance from the main square to the block
		block_distances = []
		for coords_list in blocks:
			distance = 0
			for coords in coords_list:
				distance += main_square.distance(coords)
			block_distances.append((distance / len(coords_list), coords_list))

		# form the sorted tent queue
		block_distances.sort()
		for _, block in block_distances:
			for coords in sorted(block):
				self.tent_queue.append(coords)

	def build_roads(self):
		for (x, y), (purpose, _) in self.plan.iteritems():
			if purpose == BUILDING_PURPOSE.ROAD:
				 Builder.create(BUILDINGS.TRAIL_CLASS, self.land_manager, Point(x, y)).execute()

	def build_tent(self):
		# the expected tents may have been replaced with omething else
		# TODO: fix it the right way
		while self.tent_queue:
			coords = self.tent_queue[0]
			if self.plan[coords][0] == BUILDING_PURPOSE.UNUSED_RESIDENCE:
				break
			self.tent_queue.popleft()

		if self.tent_queue:
			coords = self.tent_queue[0]
			builder = self.plan[coords][1]
			if not builder.have_resources():
				return BUILD_RESULT.NEED_RESOURCES
			if not builder.execute():
				return BUILD_RESULT.UNKNOWN_ERROR
			self.register_change(coords[0], coords[1], BUILDING_PURPOSE.RESIDENCE, builder)
			self.tent_queue.popleft()
			return BUILD_RESULT.OK
		return BUILD_RESULT.IMPOSSIBLE

	def count_tents(self):
		tents = 0
		for coords, (purpose, _) in self.plan.iteritems():
			if purpose != BUILDING_PURPOSE.RESIDENCE:
				continue
			object = self.island.ground_map[coords].object
			if object is not None and object.id == BUILDINGS.RESIDENTIAL_CLASS:
				tents += 1
		return tents

	def display(self):
		if not AI.HIGHLIGHT_PLANS:
			return

		road_colour = (30, 30, 30)
		tent_colour = (255, 255, 255)
		planned_tent_colour = (200, 200, 200)
		sq_colour = (255, 0, 255)
		pavilion_colour = (255, 128, 128)
		village_school_colour = (128, 128, 255)
		tavern_colour = (255, 255, 0)
		reserved_colour = (0, 0, 255)
		unknown_colour = (255, 0, 0)
		renderer = self.session.view.renderer['InstanceRenderer']

		for coords, (purpose, _) in self.plan.iteritems():
			tile = self.island.ground_map[coords]
			if purpose == BUILDING_PURPOSE.MAIN_SQUARE:
				renderer.addColored(tile._instance, *sq_colour)
			elif purpose == BUILDING_PURPOSE.RESIDENCE:
				renderer.addColored(tile._instance, *tent_colour)
			elif purpose == BUILDING_PURPOSE.UNUSED_RESIDENCE:
				renderer.addColored(tile._instance, *planned_tent_colour)
			elif purpose == BUILDING_PURPOSE.ROAD:
				renderer.addColored(tile._instance, *road_colour)
			elif purpose == BUILDING_PURPOSE.VILLAGE_SCHOOL:
				renderer.addColored(tile._instance, *village_school_colour)
			elif purpose == BUILDING_PURPOSE.PAVILION:
				renderer.addColored(tile._instance, *pavilion_colour)
			elif purpose == BUILDING_PURPOSE.TAVERN:
				renderer.addColored(tile._instance, *tavern_colour)
			elif purpose == BUILDING_PURPOSE.RESERVED:
				renderer.addColored(tile._instance, *reserved_colour)
			else:
				renderer.addColored(tile._instance, *unknown_colour)

decorators.bind_all(VillageBuilder)