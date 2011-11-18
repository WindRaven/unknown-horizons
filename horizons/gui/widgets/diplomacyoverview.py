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

from fife.extensions import pychan
from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.util.changelistener import metaChangeListenerDecorator
import math

class DiplomacyOverview(object):
	"""Implementation of the logbook as described here:
	http://wiki.unknown-horizons.org/w/Message_System

	It displays longer messages, that are essential for scenarios.
	Headings can be specified for each entry.
	"""
	def __init__(self, session):
		self.session = session
		
		self._init_gui()
		self._hiding_widget = False # True if and only if the widget is currently in the process of being hidden
	
	def show(self):
		# don't show if there are no messages
		#if len(self._messages) == 0:
		#	return
		
		players = set(self.session.world.players)
		players.add(self.session.world.pirate)
		players.discard(self.session.world.player)
		players.discard(None) # e.g. when the pirate is disabled
		
		self._gui.show()
		self.session.ingame_gui.on_switch_main_widget(self)
		
		angle_incr = 2 * math.pi / len(players)
		angle = 0
		r = 140
		icon_path='content/gui/images/tabwidget/emblems/emblem_%s.png'
		
		for player in players:
			x = round ( math.cos(angle) * r )
			y = round( math.sin(angle) * r )
			container = self._gui.findChild(name = "left_overview")
			x_offset = round(container.height / 3.5)
			y_offset = round(container.width / 1.7)
			color = player.color.name
			icon = pychan.Icon(image = icon_path % color, position = (int(x + x_offset), int(y + y_offset)))
			container.addChild(icon)
			#print (round(math.sin(angle) * r ) ,round ( math.cos(angle) * r ) )
			angle += angle_incr
			
			#icon( image = icon_path % color, x = x, y = y)
			

	def hide(self):
		if not self._hiding_widget:
			self._hiding_widget = True
			self.session.ingame_gui.on_switch_main_widget(None)
			self._gui.hide()
			self._hiding_widget = False
			self.session.speed_unpause(True)

	def is_visible(self):
		return self._gui.isVisible()

	def toggle_visibility(self):
		if self.is_visible():
			self.hide()
		else:
			self.show()

	def _init_gui(self):
		"""Initial init of gui."""
		self._gui = load_uh_widget("diplo_log.xml")
		self._gui.mapEvents({
		  'cancelButton' : self.hide
		  })

	def _redraw(self):
		"""Redraws gui. Necessary when current  has changed."""
		pass

