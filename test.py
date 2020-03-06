import time
import datetime
from ruamel import yaml
a = None

# 格式化成2016-03-20 11:45:39形式
now_time = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime())
print(now_time)
print(type(now_time))
print(datetime.datetime.now())

a = 'sdafasdf'
with open('./log.yaml','a') as file:
    yaml.dump(a, file, Dumper=yaml.RoundTripDumper)
