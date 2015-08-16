#!/usr/bin/env python

import os, subprocess
import wx
from agithub import Github

GITHUB_HOST = 'github.com'
def git_credentials():
	os.environ['GIT_ASKPASS'] = 'true'
	p = subprocess.Popen(['git', 'credential', 'fill'],
		stdout=subprocess.PIPE,
		stdin=subprocess.PIPE)
	stdout,_ = p.communicate('host={}\n\n'.format(GITHUB_HOST))

	creds = {}
	for line in stdout.split('\n')[:-1:]:
		k,v = line.split('=')
		creds[k] = v
	return creds

class SearchFrame(wx.Frame):
	def __init__(self, *args, **kwargs):
		kwargs.setdefault('size', (600,500))
		wx.Frame.__init__(self, *args, **kwargs)

		self.credentials = {}
		self.orgs = []

		#self.create_controls()
		#self.do_layout()

		# Try to pre-load credentials from Git's cache
		self.credentials = git_credentials()
		#if self.test_credentials():
		#	self.switch_to_search_panel()

		self.SetTitle('GitHub Issue Search')
		self.Show()

if __name__ == '__main__':
	app = wx.App()
	SearchFrame(None)
	app.MainLoop()