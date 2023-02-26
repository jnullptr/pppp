import threading 
import datetime
from functools import reduce


class Proxy: 
	MAX_HISTORY = 5

	def __init__(self, as_str):
		self.host, self.port = as_str.split(":")
		self.port = int(self.port)

		self._history = []
		self._last_use  = datetime.datetime.min

		self.as_requests = proxies={ 'http': 'http://' + as_str, 'https': 'http://' + as_str }

	def __str__(self):
		return f"{self.host}:{self.port}"

	def __eq__(self, other): 
		return self.host == other.host and self.port == other.port 

	def is_dead(self): 
		if len(self._history) < Proxy.MAX_HISTORY:
			return False 
		return sum(self._history) == 0

	def report_use(self):
		self._last_use = datetime.datetime.now()

	def report_result(self, success): 
		self._history.append(1 if success else 0)
		if len(self._history) > Proxy.MAX_HISTORY:
			self._history = self._history[1:]

	def _success_score_rate(self):
		if len(self._history) == 0:
			return 1.0
		return sum(self._history) / len(self._history)

	def _use_count_score_rate(self):
		return (Proxy.MAX_HISTORY - len(self._history)) / Proxy.MAX_HISTORY

	def _age_score_rate(self):
		age = min(3600 * 24, (datetime.datetime.now() - self._last_use).total_seconds() )
		return 1.0 * age / (50.0 + age)

	def _non_dead_score_rate(self):
		return 1.0 if not self.is_dead() else 0.0

	def score(self):
		return 30.0 * self._success_score_rate() + 25.0 * self._age_score_rate() + \
			25.0 * self._non_dead_score_rate() + 20.0 * self._use_count_score_rate()


class ProxyPool: 
	def __init__(self):
		self._lock = threading.Lock()
		self._proxies = []

	def add(self, proxy):
		if type(proxy) == str: 
			proxy = Proxy(proxy)
		with self._lock:
			if self._proxies.count(proxy) > 0:
				print("Proxy ", proxy, "was already added ")
			else:
				self._proxies.append(proxy)

	def add_from_file(self, proxy_file):
		with open(proxy_file, 'r') as f: 
			lines = [l.strip() for l in f.readlines()]
		for proxy in lines: 
			self.add(proxy)

	def get(self):
		with self._lock:

			self._proxies = [p for p in self._proxies if not p.is_dead()]

			scored = [(p, p.score()) for p in self._proxies]
			max_by_score = lambda x, y: x if (x[1] > y[1]) else y

			ret = reduce(max_by_score, scored, (None, 0)) [0]
			if ret is not None: 
				ret.report_use()

			return ret

	def rate(self, proxy, success): 
		with self._lock: 
			proxy.report_result(success) 




if __name__ == "__main__":
	import random 
	p = ProxyPool()

	p1 = Proxy("p1:11")
	p2 = Proxy("p2:11")
	
	p.add(p1)
	p.add(p2)
	p.add("hackit:222")
	p.add("hackit2:222")
	p.add("hackit2:222")

	print(p1, p1.score(), p2, p2.score())

	p.rate(p1, False)
	p.rate(p2, True)
	p.rate(p2, True)
	print(p1, p1.score(), p2, p2.score())

	for i in range(1, 100): 
		np = p.get()
		if np is None: 
			print("Poool is exhausted")
			break
		print (np, np.score())
		p.rate(np, True if random.random() > 0.9 else False)
