import re
import time

LINE_REGEXES = {
	"Apache Error Log": {
		"regex": re.compile(r"^\[([^\]]+)\] \[([^\]]+)\](?: \[client ([^\]]+)\])? (.*?)(?:, referer: (.*))?$"),
		"groups": ("date", "level", "client", "message", "referer"),
		"dateFormat": "%a %b %d %H:%M:%S %Y", # Sun Oct 24 06:48:26 2010
		"parseMessage": True
	},
	"Bebras Access Log": {
		# LogFormat "%{Host}i %h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" beaver_combined
		"regex": re.compile(r"^([^ ]+) ([^ ]+) ([^ ]+) ([^ ]+) \[([^\]]+) +\d\d\d\d\] \"([^\"]+)\" \d+ (\d+|-) \"([^\"]+)\" \"([^\"]+)\"$"),
		"groups": ("host", "client", "logname", "user", "date", "request", "status", "bytes", "referer", "ua"),
		"dateFormat": "%d/%b/%Y:%H:%M:%S"
	},
	"Apache Access Log (combined)": {
		# LogFormat "%h %l %u %t \"%r\" %>s %b \"%{Referer}i\" \"%{User-Agent}i\"" combined
		"regex": re.compile(r"$([^ ]+) ([^ ]+) ([^ ]+) \[([^\]]+) +\d\d\d\d\] \"([^\"]+)\" \d+ (\d+|-) \"([^\"]+)\" \"([^\"]+)\"$"),
		"groups": ("client", "logname", "user", "date", "request", "status", "bytes", "referer", "ua"),
		"dateFormat": "%d/%b/%Y:%H:%M:%S"
	}
}

MESSAGE_IGNORE = [
	re.compile("^PHP Stack trace:$"),
	re.compile(r"^PHP [ 0-9][ 0-9][ 0-9]\. .*$"),
]

MESSAGE_REGEXES = {
	"PHP Error": [
		{
			"regex": re.compile(r"^PHP (Fatal error|Parse error|Warning|Notice|Deprecated):  (.*?)(?: in (?!.*? in )(/var/www/.*?) on line (\d+))?$"),
			"groups": ("level", "message", "file", "line")
		}
	],
	"File Not Found": [
		{
			"regex": re.compile(r"^File does not exist: (.*)$"),
			"groups": ("file", )
		},
		{
			"regex": re.compile(r"^script '([^']+)' not found or unable to stat$"),
			"groups": ("file", )
		}
	],
	"Apache": [
		{ "regex": re.compile(r"^caught SIGTERM, shutting down$") },
		{ "regex": re.compile(r"^Graceful restart requested, doing restart$") }
	]
}

def groupsToDict(match, groupNames):
	groups = match.groups()
	return dict(zip(groupNames, groups))

def parseLine(line):
	for name, opts in LINE_REGEXES.iteritems():
		match = opts["regex"].match(line)
		if not match:
			continue

		parsed = groupsToDict(match, opts["groups"])
		if "dateFormat" in opts and "date" in parsed:
			parsed["date"] = time.strptime(parsed["date"], opts["dateFormat"])
		if "parseMessage" in opts and "message" in parsed:
			messageType, messageParsed = parseMessage(parsed["message"])
			if messageType == IGNORE:
				return None
			parsed["messageType"] = messageType
			parsed["messageParsed"] = messageParsed
		return parsed

	return None

IGNORE = 1
def parseMessage(message):
	for regex in MESSAGE_IGNORE:
		if regex.match(message):
			return IGNORE, None
	
	for key, allOpts in MESSAGE_REGEXES.iteritems():
		for opts in allOpts:
			match = opts["regex"].match(message)
			if not match:
				continue

			if "groups" in opts:
				parsed = groupsToDict(match, opts["groups"])
			else:
				parsed = { "message": message }
			return key, parsed

	return None, None
