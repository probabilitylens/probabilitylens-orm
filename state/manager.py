import pickle, os

STATE_FILE="state.pkl"

def load_state():
    return pickle.load(open(STATE_FILE,"rb")) if os.path.exists(STATE_FILE) else None

def save_state(s):
    pickle.dump(s,open(STATE_FILE,"wb"))

def initialize_state(prices):
    import pandas as pd
    return {"positions":pd.DataFrame(0,index=prices.index,columns=prices.columns)}

def validate_state(s,prices):
    return s

def update_state(s,pos,eq):
    s["positions"]=pos
    return s
