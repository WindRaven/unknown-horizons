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

import os
import shutil
import tempfile
import unittest

import horizons.main
from horizons.util.uhdbaccessor import UhDbAccessor
from horizons.constants import PATHS


db = None
temp_dir = None

def setup_package():
	"""
	One-time database setup. Nose will call this function once for this package,
	so we can avoid to create a database for each test. Using TestCase, we can
	be sure that each test runs on an unmodified database.
	"""
	global db, temp_dir

	db = UhDbAccessor(':memory:')
	for i in PATHS.DB_FILES:
		db.execute_script( open(i, "r").read() )

	# Truncate all tables. We don't want to rely on existing data.
	for (table_name, ) in db("SELECT name FROM sqlite_master WHERE type = 'table'"):
		db('DELETE FROM %s' % table_name)


def teardown_package():
	"""
	Close database and remove the temporary directory.
	"""
	db.close()


class TestCase(unittest.TestCase):
	"""
	For each test, open a new transaction and roll it back afterwards. This
	way, the database will remain unmodified for each new test.
	"""
	def setUp(self):
		# Some code is still accessing the global database reference.
		horizons.main.db = db

		self.db = db
		self.db('BEGIN TRANSACTION')

	def tearDown(self):
		self.db('ROLLBACK TRANSACTION')
