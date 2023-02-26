import requests 
import time 
import datetime
import os
import threading
from proxy_source_config import PROXY_LIST_URL, DAILY_LIMIT

MIN_SLEEP = 3600 * 24 / DAILY_LIMIT + 1

STORAGE = "~/proxy"



def _current_minutes():
	return int((datetime.datetime.now() - datetime.datetime(1970, 1, 1)).total_seconds() // 60)


def _save_list(proxy_list): 
	nr = _current_minutes()
	filename = os.path.join(os.path.expanduser(STORAGE), f"{nr}.txt")
	with open(filename, 'w') as f: 
		f.writelines("\n".join(proxy_list))


def _retrieve_list(): 
	try: 
		res = requests.get(PROXY_LIST_URL)
		if res.status_code == 200: 
			return [l.strip() for l in res.text.split("\n")]
	except:
		pass 

	return None  


def load(maxp=5, after = 0): 
	storage = os.path.expanduser(STORAGE)

	file_list = [ (f, int(f.split(".")[0])) for f in os.listdir(storage) ]
	file_list = sorted( file_list, key=lambda x: x[1],  reverse=True )
	file_list = [ item for item in file_list if item[1] > after]

	ret = []

	for item in file_list[0:maxp]: 
		try:
			filename = os.path.join(storage, item[0])
			with open(filename, 'r') as f: 
				lines = [l.strip() for l in f.readlines()]
				ret.extend(lines)
		except Exception as ex: 
			print(ex)

	if len(ret) == 0:
		return [], after

	return list(set(ret)), file_list[0][1]


def _monitor_function(new_proxy_fn):
	last_file_seq = 0
	while True: 
		new, last_file_seq = load(5, after = last_file_seq)
		for p in new: 
			new_proxy_fn(p)
		time.sleep(5)

	

def monitor(new_proxy_fn):
	t = threading.Thread(target=_monitor_function, args=(new_proxy_fn,), daemon=True)
	t.start()


def daemon(): 
	while True: 
		list = _retrieve_list()
		_save_list(list)
		time.sleep(MIN_SLEEP)


if __name__ == "__main__":
	daemon()
