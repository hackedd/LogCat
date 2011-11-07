import re
import time

class LogParser(object):
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
	LOG = re.compile(r"^\[([^\]]+)\] \[([^\]]+)\] (?:\[client ([^\]]+)\])? (.*?)(?:, referer: (.*))?$")
	GROUPS = ("date", "level", "client", "message", "referer")
	DATE = "%a %b %d %H:%M:%S %Y" # Sun Oct 24 06:48:26 2010

	def parseLine(self, line):
		parseDict = LogParser.parseLineRegex(line, self.LOG, self.GROUPS)
		if parseDict == None:
			print "Unable to parse %r" % line
			return None

		parseDict["date"] = time.strptime(parseDict["date"], self.DATE)

		parser, parsed = LogParser.parseMessage(parseDict["message"])
		parseDict["message_type"] = parser
		parseDict["message_parsed"] = parsed

		return parseDict

class PHPErrorParser(LogParser):
	TYPE = "PHP Error"
	# Yes, that is two spaces between the colon and the message...
	LINE = re.compile(r"^PHP (Error|Warning|Notice|Deprecated):  (.*?)(?: in (?!.*? in )(/var/www/.*?) on line (\d+))?$")
	GROUPS = ("level", "message", "file", "line")

	@staticmethod
	def parseLine(line):
		return LogParser.parseLineRegex(line, PHPErrorParser.LINE, PHPErrorParser.GROUPS)
LogParser.addMessageParser(PHPErrorParser)

class FileNotFoundParser(LogParser):
	# File does not exist: /var/www/nl/beverwedstrijd/images/logo_6.png
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
