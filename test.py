import datetime, pytz

date = datetime.datetime.now(pytz.timezone('Europe/Moscow')) + datetime.timedelta(hours=3)

print(str(date))