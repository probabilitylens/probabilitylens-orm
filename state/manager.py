import os
import pickle

STATE_FILE = "state.pkl"


def load_state():
    if os.path.exists(STATE_FILE):
        with open(STATE_FILE, "rb") as f:
            return pickle.load(f)
    return {"positions": None, "equity": 0}


def save_state(state):
    with open(STATE_FILE, "wb") as f:
        pickle.dump(state, f)


def initialize_state(prices=None):
    return {"positions": None, "equity": 0}


def update_state(state, positions=None, equity=None):

    if state is None:
        state = {"positions": None, "equity": 0}

    if positions is not None:
        state["positions"] = positions

    if equity is not None:
        state["equity"] = equity

    return state
