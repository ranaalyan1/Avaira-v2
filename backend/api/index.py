from mangum import Mangum
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))
from server import app
handler = Mangum(app)
