from datetime import datetime as dt

now = dt.now()
other = dt.strptime("2018-07-01 16:30", "%Y-%m-%d %H:%M")
print other.replace(hour=0, minute=0)
print other
