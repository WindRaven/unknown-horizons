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
from fife import fife
from fife.extensions import pychan
from horizons.util.gui import load_uh_widget
from horizons.util import Callback
from horizons.util.changelistener import metaChangeListenerDecorator
from horizons.gui.widgets.diplomacywidget import DiplomacyWidget
from horizons.gui.widgets.unitoverview import StanceWidget

import math

class DiplomacyOverview(object):
	"""Implementation of the logbook as described here:
	http://wiki.unknown-horizons.org/w/Message_System

	It displays longer messages, that are essential for scenarios.
	Headings can be specified for each entry.
	"""
	def __init__(self, session):
		self.session = session
		
		# Players need to be inited later
		self._inited = False
		
		# True if and only if the widget is currently in the process of being hidden	
		self._hiding_widget = False 
		self._gui = None
		
	def init(self):
		self.players = set(self.session.world.players)
		self.players.add(self.session.world.pirate)
		self.players.discard(self.session.world.player)
		self.players.discard(None) # e.g. when the pirate is disabled
		
		self.player = self.session.world.player
		self._inited = True

		self._init_gui()
		
	def show(self):
		# don't show if there are no messages
		#if len(self._messages) == 0:
		#	return
		if not self._inited:
			self.init()
		
		self._gui.show()
		self.session.ingame_gui.on_switch_main_widget(self)
		
	def show_diplomacy_widget(self, player):
		container_diplo_widget = self._gui.findChild(name = "diplo_widget")
		container_diplo_widget.removeAllChildren()
		container_diplo_widget.addChild(self.diplomacy_widgets[player])
		#has to redraw the gui
		self.toggle_visibility()
		self.toggle_visibility()
		
	def hide(self):
		if not self._hiding_widget:
			self._hiding_widget = True
			self.session.ingame_gui.on_switch_main_widget(None)
			self._gui.hide()
			self._hiding_widget = False
			self.session.speed_unpause(True)

	def is_visible(self):
		return self._gui.isVisible() if self._gui else False

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
		
		container_left = self._gui.findChild(name = "left_overview")
		container_right = self._gui.findChild(name = "right_overview")
		
		self.diplomacy_widgets  = {}
		for player in self.players:
			diplomacy_widget = DiplomacyWidget()
			diplomacy_widget.init(player)
			self.diplomacy_widgets[player] = diplomacy_widget 
		
		#for player in self.players:	
			#self.show_diplomacy_widget(player)
		
		angle_incr = 2 * math.pi / len(self.players)
		angle = 0
		r = 135
		icon_path='content/gui/images/tabwidget/emblems/emblem_%s.png'
		
		#x_offset and y_offset are the centers of each circles	
		x_offset_left = round(container_left.height / 3.8)
		y_offset_left = round(container_left.width / 1.7)
	
		color = self.player.color.name,
		
		player_widget = load_uh_widget('playerbuttonwidget.xml')
		icon = pychan.Icon(image = icon_path % color, position = (10, 10))
		player_widget.findChild(name = 'playerbutton').tooltip = self.player.name
		player_widget.findChild(name="icon").addChild(icon)
		player_widget.position = ((int(x_offset_left), int(y_offset_left)))
		container_left.addChild(player_widget)
		
		x_offset_right = round(container_right.height / 3.8)
		y_offset_right = round(container_right.width / 1.7)
		
		#draws other player buttons on both sides
		for player in self.players:
			
			x = round ( math.cos(angle) * r )
			y = round( math.sin(angle) * r )	
			color = player.color.name
			
			#draws left side
			player_button_widget = load_uh_widget('playerbuttonwidget.xml')
			icon = pychan.Icon(image = icon_path % color, position = (10, 10))
			player_button_widget.findChild(name = 'playerbutton').tooltip = player.name
			player_button_widget.findChild(name="icon").addChild(icon)
			player_button_widget.mapEvents({ 'playerbutton' : Callback(self.show_diplomacy_widget, player) } )
			player_button_widget.position = ((int(x + x_offset_left), int(y + y_offset_left)))
			container_left.addChild(player_button_widget)
			
			#draws right side no need for mapping
			player_widget = load_uh_widget('playerbuttonwidget.xml')
			icon = pychan.Icon(image = icon_path % color, position = (10, 10))
			player_widget.findChild(name = 'playerbutton').tooltip = player.name
			player_widget.findChild(name="icon").addChild(icon)
			player_widget.position = ((int(x + x_offset_right), int(y + y_offset_right)))
			container_right.addChild(player_widget)
				
			angle += angle_incr
	
	def _redraw(self):
		"""Redraws gui. Necessary when current  has changed."""
		pass

