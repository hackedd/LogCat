import re
import time

class LogParser(object):
	IGNORE = "IGNORE"
	messageParsers = []

	def __init__(self):
		pass

	@staticmethod
	def addMessageParser(mp):
		LogParser.messageParsers.append(mp)

	@staticmethod
	def parseMessage(message):
		for mp in LogParser.messageParsers:
			parsed = mp.parseLine(message)
			if parsed != None:
				return mp.TYPE, parsed
		return None, None
	
	def parseLine(self, line):
		return None
	
	@staticmethod
	def parseLineRegex(line, regex, groupNames):
		match = regex.match(line)
		if not match:
			return None
		groups = match.groups()
		if len(groups) != len(groupNames):
			raise Exception("Unable to parse line %r. Unexpected group count." % line)
		return dict(zip(groupNames, groups))

class ApacheErrorLogParser(LogParser):
	LOG = re.compile(r"^\[([^\]]+)\] \[([^\]]+)\](?: \[client ([^\]]+)\])? (.*?)(?:, referer: (.*))?$")
	GROUPS = ("date", "level", "client", "message", "referer")
	DATE = "%a %b %d %H:%M:%S %Y" # Sun Oct 24 06:48:26 2010

	def parseLine(self, line):
		parseDict = LogParser.parseLineRegex(line, self.LOG, self.GROUPS)
		if parseDict == None:
			print "Unable to parse %r" % line
			return None

		parseDict["date"] = time.strptime(parseDict["date"], self.DATE)

		parser, parsed = LogParser.parseMessage(parseDict["message"])
		if parser == LogParser.IGNORE:
			return None
		parseDict["message_type"] = parser
		parseDict["message_parsed"] = parsed

		return parseDict

class PHPErrorParser(LogParser):
	TYPE = "PHP Error"
	# Yes, that is two spaces between the colon and the message...
	LINE = re.compile(r"^PHP (Fatal error|Parse error|Warning|Notice|Deprecated):  (.*?)(?: in (?!.*? in )(/var/www/.*?) on line (\d+))?$")
	GROUPS = ("level", "message", "file", "line")

	@staticmethod
	def parseLine(line):
		return LogParser.parseLineRegex(line, PHPErrorParser.LINE, PHPErrorParser.GROUPS)
LogParser.addMessageParser(PHPErrorParser)

class PHPIgnore(LogParser):
	TYPE = LogParser.IGNORE
	LINE = re.compile(r"^PHP [ 0-9][ 0-9][ 0-9]\. .*$")

	@staticmethod
	def parseLine(line):
		if line == "PHP Stack trace:" or PHPIgnore.LINE.match(line):
			return True
LogParser.addMessageParser(PHPIgnore)

class FileNotFoundParser(LogParser):
	TYPE = "File Not Found"
	LINE = [re.compile(r"^File does not exist: (.*)$"), re.compile(r"^script '([^']+)' not found or unable to stat$")]
	GROUPS = ("file", )

	@staticmethod
	def parseLine(line):
		for regex in FileNotFoundParser.LINE:
			parsed = LogParser.parseLineRegex(line, regex, FileNotFoundParser.GROUPS)
			if parsed != None:
				return parsed
		return None
LogParser.addMessageParser(FileNotFoundParser)

class ApacheLifeCycleParser(LogParser):
	TYPE = "Apache"

	@staticmethod
	def parseLine(line):
		if line == "caught SIGTERM, shutting down":
			return {"type": "shutdown", "message": line}
		if (line.endswith("-- resuming normal operations") or 
			line == "Graceful restart requested, doing restart"):
			return {"type": "restart", "message": line}
		return None
LogParser.addMessageParser(ApacheLifeCycleParser)
