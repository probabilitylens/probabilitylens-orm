class EvaluateRequest:
    def __init__(self, params):
        self.params = params


class ComputedState:
    def __init__(self, positions=None, equity=0):
        self.positions = positions
        self.equity = equity
