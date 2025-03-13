# counter.py
_id_count = 0

def increment():
    """Increments the counter by 1."""
    global _id_count
    _id_count += 1

def get_value():
    """Returns the current value of the counter."""
    return _id_count

def set_value(value):
    """Sets the counter to a specific value."""
    global _id_count
    _id_count = value