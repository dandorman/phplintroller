#!/usr/bin/python

from gtk import STOCK_DIALOG_ERROR, STOCK_DIALOG_INFO
from pyinotify import ProcessEvent, WatchManager, Notifier, EventsCodes
from pynotify import Notification, init as notifyinit
import re

notifyinit("PHP Lint Roller")

def basename(filename):
    "Like PHP's function of the same name."
    return filename.split('/')[-1]

class PHPLintProcessEvent(ProcessEvent):
    "Class for processing updates to a file containing the output of the php -l command."

    _errorRegex = re.compile('^(.*) in (.*) on line (\d+)$')
    _okRegex = re.compile('^(No syntax errors detected) in (.*)$')
    _locked = False
    _effedFiles = []

    def process_IN_CLOSE(self, event):
	"Process IN_CLOSE_(WRITE|NO_WRITE) inotify events."

	if not self._locked:
	    self._locked = True

	    lintFile = open(event.path)
	    title = ''
	    body = ''
	    icon = ''

	    for line in [line.rstrip() for line in lintFile if line != "\n" and not line.startswith('Errors parsing')]:
		ok = self._okRegex.search(line)
		if ok:
		    [message, file] = ok.groups()
		    if file in self._effedFiles:
			self._effedFiles.remove(file)
			title = basename(file)
			body = "%s\n(%s)" % (message, file)
			icon = STOCK_DIALOG_INFO
		else:
		    [error, file, line] = self._errorRegex.search(line).groups()
		    if not file in self._effedFiles:
			self._effedFiles.append(file)
		    title = "%s, line %s" % (basename(file), line)
		    body = "%s\n(%s)" % (error, file)
		    icon = STOCK_DIALOG_ERROR

	    if body != '':
		notification = Notification(title, body, icon)
		notification.show()

	    lintFile.close()

	    self._locked = False

    def process_default(self):
	"Does nothing for any other inotify events."

	pass

if __name__ == '__main__':
    import sys

    file = len(sys.argv) < 2 and '/tmp/phplint' or sys.argv[1]

    wm = WatchManager()
    notifier = Notifier(wm, PHPLintProcessEvent())
    wm.add_watch(file, EventsCodes.IN_CLOSE_WRITE)

    while True:
	try:
	    notifier.process_events()
	    if notifier.check_events():
		notifier.read_events()
	except KeyboardInterrupt:
	    notifier.stop()
	    break
