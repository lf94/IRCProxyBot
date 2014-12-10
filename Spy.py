import irc.bot
import irc.strings
import threading
import time
import sys
from datetime import datetime

# Shared variables for communication between threads
_SHARED = {
	'owner': "",
	'headquarters': "",
	'servers': dict(),
	'nickname': "daniel1", 
	'_COMMANDS': ["infiltrate", "assimilate", "retreat", "users", "disguise"],
	'origin': {
		'server': "",
		'channel': "",
		'context': None,
	}
}

class Spy(irc.bot.SingleServerIRCBot):
	def __init__(self, server, channel, port):
		self.server = server
		self.channel = channel
		irc.bot.SingleServerIRCBot.__init__(self, [(server,port)], _SHARED['nickname'], _SHARED['nickname'])

	def on_welcome(self, context, event):
		if _SHARED['origin']['context'] == None:
			_SHARED['origin']['context'] = context
		else:
			_SHARED['servers'][self.server]['context'] = context
		context.join(self.channel)

	def on_join(self, context, event):
		_SHARED['origin']['context'].action(_SHARED['origin']['channel'], "successfully infiltrated {0}.".format(event.target));
		pass

	def on_pubmsg(self, context, event):
		self.do(context, event)

	def on_privmsg(self, context, event):
		self.do(context, event)

	def do(self, context, event):
		if not self.understand(context, event):
			user = event.source.split("!")[0]
			incoming = event.arguments[0]
			current_time = datetime.now().strftime('%m-%d %H:%M')
			_SHARED['origin']['context'].privmsg(event.target+"-teddy", "[{2}] <{0}> {1}".format(user, incoming, current_time))

	def is_owner(self, context, event):
		user = event.source.split("!")[0]
		if user != self.owner:
			return False
		return True

	def understand(self, context, event):
		if self.server == _SHARED['origin']['server']:
			if event.target == _SHARED['origin']['channel']:
				text = event.arguments[0]
				chunks = text.split(" ")
				for command in _SHARED['_COMMANDS']:
					if chunks[0] == ":"+command:
						getattr(self, command)(context,event)
						return True
		return False

	def get_args(self, event):
		return event.arguments[0].split(" ")

	def infiltrate(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.action(self.channel, "Format: :infiltrate irc.server.tld #channel")
			return

		server = arguments[1]
		channel = arguments[2]

		context.action(self.channel, "joining {0} {1}".format(server, channel))
		context.action(self.channel, "relay channel @ {0}-teddy".format(channel))
	
		context.join(channel+"-teddy")
		self.connect_to(server, channel)

	def disguise(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.action(self.channel, "Format: :disguise irc.server.tld username")
			return

		server = arguments[1]
		username = arguments[2]
		return

	def users(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.privmsg(self.channel, "Format: :users irc.server.tld #channel")
			return

		server = arguments[1]
		channel = arguments[2]

		users = _SHARED['servers'][server]['channels'][channel].users().keys()
		context.action(_SHARED['origin']['channel'], "{0}".format(users))

	def commands(self, context, event):
		context.privmsg(self.channel, "Commands: {0}".format(str(_SHARED['COMMANDS'])))

	def retreat(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.privmsg(self.channel, "Format: :users irc.server.tld #channel")
			return

		server = arguments[1]
		channel = arguments[2]

		if channel is not None:
			if server is not None:
				for existing_server in _SHARED['servers'].keys():
					if existing_server == server:
						for existing_channel in _SHARED['servers'][server]['channels'].keys():
							if existing_channel == channel:
								_SHARED['servers'][existing_server]['context'].part(channel)
								context.part(channel+"-teddy")
								context.action(_SHARED['origin']['channel'], "retreated from {0} {1}".format(channel, server))
								return 
					
		if server is not None:
			for existing_server in _SHARED['servers'].keys():
				if existing_server == server:
					del _SHARED['servers'][existing_server]
					for channel in _SHARED['servers'][existing_server]['channels'].keys():
						context.part(channel+"-teddy")
					_SHARED['servers'][existing_server]['context'].disconnect()
					context.action(_SHARED['origin']['channel'], "retreated from {0}".format(server))
					return

		context.privmsg(_SHARED['origin']['channel'], "Invalid invocation or not there.")

	def connect_to(self, requested_server, channel):
		for existing_server in _SHARED['servers'].keys():
			if existing_server == requested_server:
				_SHARED['servers'][existing_server]['context'].join(channel)
				return

		bot = Spy(requested_server, channel, 6667)
		_SHARED['servers'][requested_server] = dict()
		_SHARED['servers'][requested_server]['channels'] = bot.channels
		bot.start()

def main():
	if len(sys.argv) != 4:
		print("Usage: python daniel1.py owner server channel\nNote: bash is a bitch, remember # is comment in bash.")
	_SHARED['owner'] = sys.argv[1];
	_SHARED['origin']['server'] = sys.argv[2]
	_SHARED['origin']['channel'] = sys.argv[3]
	Spy(_SHARED['origin']['server'], _SHARED['origin']['channel'], 6667).start()

main()
