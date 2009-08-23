from pyinotify import *
import pynotify
import re
from gtk import STOCK_DIALOG_ERROR, STOCK_DIALOG_INFO

pynotify.init("PHP Lint Processor")

class PHPLintProcessEvent(ProcessEvent):
    def __init__(self):
	self._errorRegex = re.compile('^(.*) in (.*) on line (\d+)$')
	self._okRegex = re.compile('^(No syntax errors detected) in (.*)$')
	self._locked = False
	self._effedFiles = []

    def process_IN_CLOSE(self, event):
	if self._locked == False:
	    self._locked = True

	    lintFile = open('/tmp/phplint')
	    title = ''
	    body = ''
	    icon = ''

	    for line in [line.rstrip() for line in lintFile if line != "\n" and not line.startswith('Errors parsing')]:
		ok = self._okRegex.search(line)
		if ok:
		    [message, file] = ok.groups()
		    if file in self._effedFiles:
			self._effedFiles.remove(file)
			title = file.split('/').pop()
			body = message
			icon = STOCK_DIALOG_INFO
		else:
		    [error, file, line] = self._errorRegex.search(line).groups()
		    if not file in self._effedFiles:
			self._effedFiles.append(file)
		    file = file.split('/').pop()
		    title = file + ', line ' + line
		    body = error
		    icon = STOCK_DIALOG_ERROR

	    if body != '':
		notification = pynotify.Notification(title, body, icon)
		notification.show()

	    lintFile.close()

	    self._locked = False

    def process_default(self):
	return

wm = WatchManager()
notifier = Notifier(wm, PHPLintProcessEvent())
wm.add_watch('/tmp/phplint', EventsCodes.IN_CLOSE_WRITE)

while True:
    try:
	notifier.process_events()
	if notifier.check_events():
	    notifier.read_events()
    except KeyboardInterrupt:
	notifier.stop()
	break
