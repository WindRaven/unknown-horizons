# ###################################################
# Copyright (C) 2008 The OpenAnno Team
# team@openanno.org
# This file is part of OpenAnno.
#
# OpenAnno is free software; you can redistribute it and/or modify
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

import game.main
import fife


class MessageWidget(object):
	"""Class that organises the messages in the top right of the screen.
	It uses Message Class instances to store messages and manages the
	archive.
	@param x,y: int position where the widget ist placed on the screen."""
	def __init__(self, x, y):
		self.x, self.y = x, y
		self.active_messages = []
		self.archive = []
		self.widget = game.main.fife.pychan.loadXML('content/gui/hud_messages.xml')
		self.widget.position = (x,y)
		self.widget.show()
		self.current_tick = None
		self.position = 0

	def add_message(self, x, y, id):
		"""Adds a message to the MessageWidget.
		@param x, y: int coordinates where the action took place.
		@param id: message id, needed to retrieve the message from the database.
		"""
		self.active_messages.insert(Message(x,y,id, self.current_tick))

	def draw_wigdet(self):
		"""Updates the widget."""
		widg = self.widget
		for i in range(1,5):
			if self.position + i-1 in self.active_messages:
				w = findChild(name, str(i))
				w._setUpImage(self.active_messages[self.position + i-1].up_image)
				w._setHoverImage(self.active_messages[self.position + i-1].hover_image)
				w._setDownImage(self.active_messages[self.position + i-1].down_image)

	def forward(self):
		"""Sets the widget to the next icon."""
		pass

	def back(self):
		"""Sets the widget to the previous icon."""
		pass

	def tick(self):
		"""Check wether a message is old enough to be put into the archives"""
		changed = False
		for item in self.active_messages:
			item.display -= 1
			if item.dispay == 0:
				self.archive.append
				self.active_messages.remove(item)
				changed = True
		self.draw_wigdet()


class Message(object):
	"""Represents a message that is to be displayed in the MessageWidget.
	@param x,y: int position on the map where the action took place.
	@param id: message id, needed to retrieve the message from the database.
	@param created: tickid when the message was created.
	"""
	def __init__(self, x, y, id, created):
		self.x, self.y = x, y
		self.id = id
		self.read = False
		self.created = created
		self.display = 32 # TODO: select the length that the message is displayed from the db
		self.up_image = ''
		self.down_image = ''
		self.hover_image = ''