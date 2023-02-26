import threading 


class pipeline:
    def __init__(self):
        self.message = 0
        self.producer_lock = threading.Lock()
        self.consumer_lock = threading.Lock()
        self.consumer_lock.acquire()

    def get_message(self, name):
        self.consumer_lock.acquire()
        message = self.message
        self.producer_lock.release()
        return message

    def set_message(self, message, name):
        self.producer_lock.acquire()
        self.message = message
        self.consumer_lock.release()


class qpipeline(queue.Queue):
    def __init__(self):
        super().__init__(maxsize=10)

    def get_message(self, name):
        return self.get()

    def set_message(self, value, name):
        self.put(value)


class generator_serializer: 
	def __init__(self, generator):
		self._lock = threading.Lock()
		self._generator = generator 

	def next(self):
		item = None 

		with self._lock: 
			try: 
				item = next(self._generator)
			except StopIteration:
				pass

		return item


class call_serializer:
	def __init__(self, fn):
		self._fn = fn
		self._lock = threading.Lock()

	def __call__(self, *args, **kwargs): 
		with self._lock: 
			ret  = self._fn(*args, **kwargs)
		return ret


if __name__ == "__main__":
	format = "%(asctime)s: %(message)s"
	logging.basicConfig(format=format, level=logging.INFO, datefmt="%H:%M:%S")
	logging.info("Main    : before creating thread")

	gs = generator_serializer(i for i in range(1, 100))

	while True: 
		i = gs.next()
		if i is None: 
			break

		print (i)

	def fn(x, y, z): 
		print(x, y, z)
	cs = call_serializer(fn)
	cs(1, z=3, y=2)