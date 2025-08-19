import sys
import types

# Create a minimal dummy eurostatapiclient module to satisfy imports during tests
dummy = types.SimpleNamespace()
class EurostatAPIClient:
    def __init__(self, *args, **kwargs):
        pass
    def get_data(self, *args, **kwargs):
        return []
dummy.EurostatAPIClient = EurostatAPIClient
sys.modules['eurostatapiclient'] = dummy