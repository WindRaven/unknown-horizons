from fife.extensions import pychan
from horizons.util.gui import load_uh_widget, get_res_icon
from horizons.util import Callback
from horizons.gui.widgets import TooltipIcon
from horizons.gui.tabs.tabinterface import TabInterface
#from horizons.gui.widgets.diplomacyoverview import DiplomacyOverview
from horizons.command.diplomacy import AddAllyPair, AddNeutralPair, AddEnemyPair

class DiplomacyWidget(pychan.widgets.Container):
	"""TODO"""
	def __init__(self):
		super(DiplomacyWidget, self).__init__(size=(245,50),position=(0,0))
		widget = load_uh_widget('diplomacywidget.xml')
		self.addChild(widget)
		self.widget = widget
		
	def init(self, player):
		self.widget.mapEvents({
			'ally' : self.add_friend,
			'neutral' : self.add_neutral,
			'enemy' : self.add_enemy})
		
		self.local_player = player.session.world.player
		self.player = player
		self.diplomacy = player.session.world.diplomacy
		self.toggle_diplomacy_state()
	
	def remove(self, caller=None):
		"""Removes instance ref"""
		self.mapEvents({})
		self.instance = None
		
	def toggle_diplomacy_state(self):
		if self.diplomacy.are_friends(self.local_player, self.player):
			state = 'ally'
		elif self.diplomacy.are_neutral(self.local_player, self.player):
			state = 'neutral'
		else:
			state = 'enemy'
			
		self.findChild(name='enemy').set_inactive()
		self.findChild(name='neutral').set_inactive()
		self.findChild(name='ally').set_inactive()
		self.findChild(name=state).set_active()
		
	def add_friend(self):
		"""
		Callback for setting ally status between local player and tab's player
		"""
		AddAllyPair(self.player, self.local_player).execute(self.player.session)
		self.toggle_diplomacy_state()	

	def add_neutral(self):
		"""
		Callback for setting neutral status between local player and tab's player
		"""
		AddNeutralPair(self.player, self.local_player).execute(self.player.session)	
		self.toggle_diplomacy_state()

	def add_enemy(self):
		"""
		Callback for setting enemy status between local player and tab's player
		"""
		AddEnemyPair(self.player, self.local_player).execute(self.player.session)
		self.toggle_diplomacy_state()


		
