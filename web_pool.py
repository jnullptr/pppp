import requests 
import threading 
import proxy_pool as pp 
import time 
import proxy_source
from collections import namedtuple 
from utils import call_serializer, generator_serializer


Task = namedtuple("Task", "id url method headers data cookies")


# It would guarantee to call generator under generator lock 
# It would guarantee to call result_handler under rh lock
# Proxy pool must care for itself
class WebPool:
	def __init__(self, proxy_pool, task_generator, result_handler, size, timeout=4):
		self._proxy_pool = proxy_pool

		self._threads = []
		self._size = size 

		self._tasks = generator_serializer(task_generator)
		self._on_result = call_serializer(result_handler)
		self._timeout = timeout 
		
	def _run_web_request(self, t_idx, task, proxy):
		res = None 

		print(f"Attempting {task} via {proxy}")

		try:
			if task.method == "get":
				res = requests.get(
					proxies = proxy.as_requests,
					url = task.url, 
					headers = task.headers, 
					cookies = task.cookies, 
					timeout=self._timeout
					)
			elif task.method == "post":
				res = requests.post(
					proxies = proxy.as_requests,
					url = task.url, 
					headers = task.headers, 
					cookies = task.cookies, 
					data = task.data, 
					timeout=self._timeout
					)
 
		except Exception as ex: 
			print(f"Web request failed on thread {t_idx} via {proxy}")
			pass

		return res

	def _get_proxy(self):
		while True: 
			proxy = self._proxy_pool.get()
			if proxy is not None:
				return proxy

			time.sleep(1)
			print("No proxies (yet?), waiting")
	

	def _process_task(self, t_idx, task):
		time.sleep(1)

		while True: 
			proxy = self._get_proxy()
			res = self._run_web_request(t_idx, task, proxy)

			if res is not None and self._on_result(task, res):
				self._proxy_pool.rate(proxy, True)
				break

			self._proxy_pool.rate(proxy, False)
			print("Request failed, re-trying with another proxy after a short sleep")
			time.sleep(1)


	def _thread(self, t_idx):
		print("Thread started", t_idx)

		while True: 
			task = self._tasks.next()
			if task is None: 
				break
			self._process_task(t_idx, task)
		
		print("thread done and exiting", t_idx)


	def run(self):
		for i in range(0, self._size): 
			t  = threading.Thread(target=self._thread, args=(i,))
			t.start()
			self._threads.append(t)

	def join(self):
		for t in self._threads:
			t.join()




if __name__ == "__main__":
	def generator():
		for x in range(0, 100):
			url = f"http://www......+{x}"
			yield Task(x, url, "get", None, None, None) #  method headers data cookies")

	def result(task, res): 
		if 'server' not in res.headers: 
			print (task.id, task.url, res.status_code)
			return False 
		if res.headers['server'] != 'nginx': 
			print (task.id, task.url, res.status_code, res.headers['server'])
			return False

		print (task.id, task.url, res.status_code, res.headers)

		return True 

	pool = pp.ProxyPool()
	proxy_source.monitor(lambda p: pool.add(p))

	wb = WebPool(pool, generator(), result, 10)
	wb.run()

	wb.join() 
