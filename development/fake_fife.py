from horizons.ext.dummy import Dummy

# Fake the FIFE module and replace horizons.gui. It depends on pychan and does
# some isinstance checks which Dummy fails.
import sys

fife = Dummy
sys.modules["horizons.gui"] = Dummy
sys.modules["horizons.gui.ingamegui"] = Dummy
sys.modules["horizons.gui.mousetools"] = Dummy
sys.modules["horizons.gui.keylisteners"] = Dummy
sys.modules["horizons.gui.tabs"] = Dummy
sys.modules["fife.fife"] = Dummy
sys.modules["fife.extensions"] = Dummy
sys.modules["fife.extensions.fife_timer"] = Dummy
sys.modules["enet"] = Dummy
