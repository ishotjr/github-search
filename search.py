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

		self.create_controls()
		self.do_layout()

		# Try to pre-load credentials from Git's cache
		self.credentials = git_credentials()
		if self.test_credentials():
			print('self.test_credentials()')
		else:
			print('!self.test_credentials()')		
		# TODO:
		#	self.switch_to_search_panel()

		self.SetTitle('GitHub Issue Search')
		self.Show()

	def create_controls(self):
		# set up a menu (primarily to allow Cmd-Q on OS X)
		filemenu = wx.Menu()
		filemenu.Append(wx.ID_EXIT, '&Exit')
		menuBar = wx.MenuBar()
		menuBar.Append(filemenu, '&File')
		self.SetMenuBar(menuBar)

		# start with login UI
		# TODO:
		#self.login_panel = LoginPanel(self, onlogin=self.login_accepted)

	def do_layout(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		#self.sizer.Add(self.login_panel, 1, flag=wx.EXPAND | wx.ALL, border=10)
		self.SetSizer(self.sizer)

	def test_credentials(self):
		if any(k not in self.credentials for k in ['username', 'password']):
			return False
			g = Github(self.credentials['username'], self.credentials['password'])
			status,data = g.users.orgs.get()
			if status != 200:
				print('bad credentials in store')
				return False
			self.orgs = [o['login'] for o in data]
			return True

	def login_accepted(self, username, password):
		self.credentials['username'] = username
		self.credentials['password'] = password
		if self.test_credentials():
			self.switch_to_search_panel()

	def switch_to_search_panel(self):
		self.login_panel.Destroy()
		self.search_panel = SearchPanel(self,
										orgs=self.orgs,
										credentials=self.credentials)
		self.sizer.Add(self.search_panel, 1, flag=wx.EXPAND | wx.ALL, border=10)
		self.sizer.Layout()


class LoginPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		self.callback = kwargs.pop('onlogin', None)
		wx.Panel.__init__(self, *args, **kwargs)

		self.create_controls()
		self.do_layout()

	def create_controls(self):
		self.userLabel = wx.StaticText(self, label='Username:')
		self.userBox = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.passLabel = wx.StaticText(self, label='Password (or token):')
		self.passBox = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.login = wx.Button(self, label='Log in')
		self.error = wx.StaticText(self, label='')
		self.error.SetForegroundColour((200,0,0))

		# bind events
		self.login.Bind(wx.EVT_BUTTON, self.do_login)
		self.userBox.Bind(wx.EVT_TEXT_ENTER, self.do_login)		
		self.passBox.Bind(wx.EVT_TEXT_ENTER, self.do_login)

	def do_layout(self):
		# grid arrangement for controls
		grid = wx.GridBagSizer(3,3)
		grid.Add(self.userLabel, pos=(0,0), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		grid.Add(self.userBox, pos=(0,1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		grid.Add(self.passLabel, pos=(1,0), flag=wx.TOP | wx.LEFT | wx.BOTTOM, border=5)
		grid.Add(self.passBox, pos=(1,1), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		grid.Add(self.login, pos=(2,0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		grid.Add(self.error, pos=(3,0), flag=wx.EXPAND | wx.LEFT | wx.RIGHT, border=5)
		grid.AddGrowableCol(1)

		# center the grid vertically
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add((0,0), 1)
		vbox.Add(grid, 0, wx.EXPAND)
		vbox.Add((0,0), 2)
		self.SetSizer(vbox)

	def do_login(self, _):
		u = self.userBox.GetValue()
		p = self.passBox.GetValue()
		g = Github(u, p)
		status,data = g.issues.get()
		if status != 200:
			self.error.SetLabel('ERROR: ' + data['message'])
		elif callable(self.callback):
			self.callback(u, p)


if __name__ == '__main__':
	app = wx.App()
	SearchFrame(None)
	app.MainLoop()