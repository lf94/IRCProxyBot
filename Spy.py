import irc.bot
import irc.strings
import threading
import time
import sys
from datetime import datetime

# Shared variables for communication between threads
_SHARED = {
	'owner': "",
	'servers': dict(),
	'nickname': "daniel1", 
	'_COMMANDS': ["commands", "infiltrate", "assimilate", "retreat", "users", "disguise"],
	'origin': {
		'server': "",
		'channel': "",
		'key': "",
		'context': None,
	}
}

class Spy(irc.bot.SingleServerIRCBot):
	def __init__(self, server, channel, key, port):
		self.server = server
		self.channel = channel
		self.key = key
		irc.bot.SingleServerIRCBot.__init__(self, [(server,port)], _SHARED['nickname'], _SHARED['nickname'])

	def on_welcome(self, context, event):
		if _SHARED['origin']['context'] == None:
			_SHARED['origin']['context'] = context
		else:
			_SHARED['servers'][self.server] = dict()
			_SHARED['servers'][self.server]['channels'] = self.channels
			_SHARED['servers'][self.server]['context'] = context
		context.join(self.channel, self.key)

	def on_join(self, context, event):
			_SHARED['origin']['context'].action(event.target+"-conspiracy", "| {0} has joined.".format(event.source));

	def on_part(self, context, event):
			user = event.source.split("!")[0]
			_SHARED['origin']['context'].action(event.target+"-conspiracy", "| {0} has left.".format(user));

	def on_mode(self, context, event):
		user = event.source.split("!")[0]
		msg = event.arguments[0]
		_SHARED['origin']['context'].action(event.target+"-conspiracy", "| {0} sets mode {1} {2}".format(user, msg, event.target));

	def on_action(self, context, event):
		user = event.source.split("!")[0]
		msg = event.arguments[0]
		_SHARED['origin']['context'].action(event.target+"-conspiracy", "| {0} {1}".format(user, msg));

	def on_kick(self, context, event):
		user = event.source.split("!")[0]
		msg = event.arguments[0]
		_SHARED['origin']['context'].action(event.target+"-conspiracy", "| {0} has kicked {1} from {2}".format(user, msg, event.target));

	def on_quit(self, context, event):
		user = event.source.split("!")[0]
		msg = event.arguments[0]
		print("{0} {1}".format(user, msg))

	def on_pubmsg(self, context, event):
		self.do(context, event)

	def on_privmsg(self, context, event):
		self.do(context, event)

	def do(self, context, event):
		if not self.understand(context, event):
			user = event.source.split("!")[0]
			incoming = event.arguments[0]
			current_time = datetime.now().strftime('%m-%d %H:%M')
			_SHARED['origin']['context'].privmsg(event.target+"-conspiracy", "[{2}] <{0}> {1}".format(user, incoming, current_time))

	def is_owner(self, context, event):
		user = event.source.split("!")[0]
		if user != _SHARED['owner']:
			return False
		return True

	def understand(self, context, event):
		my_owner = self.is_owner(context, event)
		if not my_owner:
			return

		if self.server == _SHARED['origin']['server']:
			if event.target == _SHARED['origin']['channel'] or (my_owner and event.target == _SHARED['nickname']) or event.target in self.channels.keys():
				if my_owner and event.target == _SHARED['nickname']:
					event.target = _SHARED['owner']
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
		if len(arguments) < 3:
			context.action(self.channel, "Format: :infiltrate irc.server.tld #channel (key)")
			return

		server = arguments[1]
		channel = arguments[2]
		if len(arguments) > 3:
			key = arguments[3]
		else:
			key = ''

		if self.in_channel(server, channel):
			return

		context.action(event.target, "joining {0} {1}".format(server, channel))
		context.action(event.target, "relay channel @ {0}-conspiracy".format(channel))
	
		context.join(channel+"-conspiracy")
		self.connect_to(server, channel, key)

	def disguise(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.action(self.channel, "Format: :disguise irc.server.tld username")
			return

		server = arguments[1]
		username = arguments[2]

		if not self.in_channel(server, channel):
			return
		return

	def assimilate(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) < 4:
			context.action(self.channel, "Format: :assimilate irc.server.tld #channel msg")
			return

		server = arguments[1]
		channel = arguments[2]
		msg = ' '.join(arguments[3:])

		if not self.in_channel(server, channel):
			return
	
		_SHARED['servers'][server]['context'].privmsg(channel, msg)	

	def users(self, context, event):
		arguments = self.get_args(event)
		if len(arguments) != 3:
			context.privmsg(self.channel, "Format: :users irc.server.tld #channel")
			return

		server = arguments[1]
		channel = arguments[2]


		if not self.in_channel(server, channel):
			return

		users = str(list(_SHARED['servers'][server]['channels'][channel].users()))
		context.action(event.target, "{0}".format(users))

	def commands(self, context, event):
		context.privmsg(event.target, "Commands: {0}".format(str(_SHARED['_COMMANDS'])))

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
								context.part(channel+"-conspiracy")
								context.action(event.target, "retreated from {0} {1}".format(channel, server))
								return 
					
		if server is not None:
			for existing_server in _SHARED['servers'].keys():
				if existing_server == server:
					del _SHARED['servers'][existing_server]
					for channel in _SHARED['servers'][existing_server]['channels'].keys():
						context.part(channel+"-conspiracy")
					_SHARED['servers'][existing_server]['context'].disconnect()
					context.action(event.target, "retreated from {0}".format(server))
					return

		context.privmsg(event.target, "Invalid invocation or not there.")

	def connect_to(self, requested_server, channel, key):
		for existing_server in _SHARED['servers'].keys():
			if existing_server == requested_server:
				_SHARED['servers'][existing_server]['context'].join(channel, key)
				return

		bot = Spy(requested_server, channel, key, 6667)
		threading.Thread(group=None, target=bot.start).start()

	def in_channel(self, server, channel):
		if server in _SHARED['servers'].keys():
				if channel in _SHARED['servers'][server]['channels'].keys():
					return True
		return False

def main():
	if len(sys.argv) != 4:
		print("Usage: python daniel1.py owner server channel\nNote: bash is a bitch, remember # is comment in bash.")
	_SHARED['owner'] = sys.argv[1];
	_SHARED['origin']['server'] = sys.argv[2]
	_SHARED['origin']['channel'] = sys.argv[3]
	if len(sys.argv) > 4:
		_SHARED['origin']['key'] = sys.argv[4]
	Spy(_SHARED['origin']['server'], _SHARED['origin']['channel'], _SHARED['origin']['key'], 6667).start()

main()
