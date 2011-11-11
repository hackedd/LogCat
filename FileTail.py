import os
import sys
from signal import SIGINT
from select import select
from time import sleep
from multiprocessing import Process, Event, Queue

class FileTail(Process):
	SLEEP_TIME = 1

	def __init__(self, filename):
		Process.__init__(self)

		self.buf = ""
		self.filename = filename
		self.queue = Queue()

		self.stopping = Event()
	
	def requestStop(self):
		self.stopping.set()
	
	def getTitle(self):
		return os.path.basename(self.filename)

	def getQueue(self):
		return self.queue

	def getFD(self):
		# We get the socket FD of the underlying pipe from the queue object.
		# We hope that the internal reader variable doesn't change.
		return self.queue._reader.fileno()

	def run(self):
		fp = open(self.filename, "r")
		buf = fp.read()
		while "\n" in buf:
			line, buf = buf.split("\n", 1)
			self.queue.put(line)

		while not self.stopping.is_set():
			read = fp.read(1)
			if not read:
				sleep(self.SLEEP_TIME)

			buf += read
			while "\n" in buf:
				line, buf = buf.split("\n", 1)
				self.queue.put(line)

		fp.close()

from subprocess import Popen, PIPE, STDOUT
class SSHFileTail(FileTail):
	def __init__(self, server, filename):
		FileTail.__init__(self, filename)

		self.server = server
	
	def getTitle(self):
		return self.server + ":" + os.path.basename(self.filename)

	def run(self):
		cmd = ["ssh", self.server, "tail -f \"" + self.filename + "\""]
		ssh = Popen(cmd, stdin = PIPE, stdout = PIPE, stderr = STDOUT)

		#ssh.stdin.close()
		fp = ssh.stdout

		buf = ""
		while not self.stopping.is_set():
			r, w, x = select([fp], [], [], self.SLEEP_TIME)
			if fp not in r:
				continue

			buf += fp.read(1)
			if "\n" in buf:
				line, buf = buf.split("\n", 1)
				self.queue.put(line)

		if ssh.poll() == None:
			ssh.send_signal(SIGINT)
			ssh.wait()
		if ssh.returncode not in (0, 255):
			print >>sys.stderr, "SSH Process (%s) exited with code %d" % (cmd, ssh.returncode)