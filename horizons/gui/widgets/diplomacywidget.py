class DiplomacyWidget(pychan.widgets.Container):
	"""TODO"""
	def __init__(self, **kwargs):
		super(StanceWidget, self).__init__(size=(245,50), **kwargs)
		widget = load_uh_widget('diplomacywidget.xml')
		self.addChild(widget)

	def init(self, instance):
		self.instance = instance
		self.toggle_stance()
		self.mapEvents({
			'aggressive': Callback(self.set_stance, 'aggressive'),
			'hold_ground': Callback(self.set_stance, 'hold_ground'),
			'none': Callback(self.set_stance, 'none'),
			'flee': Callback(self.set_stance, 'flee')
			})

	def remove(self, caller=None):
		"""Removes instance ref"""
		self.mapEvents({})
		self.instance = None

	def set_stance(self, stance):
		self.instance.set_stance(stance)
		self.toggle_stance()

	def toggle_stance(self):
		self.findChild(name='aggressive').set_inactive()
		self.findChild(name='hold_ground').set_inactive()
		self.findChild(name='none').set_inactive()
		self.findChild(name='flee').set_inactive()
		self.findChild(name=self.instance.stance).set_active()
