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
			self.switch_to_search_panel()

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
		self.login_panel = LoginPanel(self, onlogin=self.login_accepted)

	def do_layout(self):
		self.sizer = wx.BoxSizer(wx.VERTICAL)
		self.sizer.Add(self.login_panel, 1, flag=wx.EXPAND | wx.ALL, border=10)
		self.SetSizer(self.sizer)

	def test_credentials(self):
		if any(k not in self.credentials for k in ['username', 'password']):
			return False
		g = Github(self.credentials['username'], self.credentials['password'])
		status,data = g.user.orgs.get()
		if status != 200:
			print('bad credentials in store')
			print(status)
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


class SearchPanel(wx.Panel):
	def __init__(self, *args, **kwargs):
		self.orgs = kwargs.pop('orgs', [])
		self.credentials = kwargs.pop('credentials', {})
		wx.Panel.__init__(self, *args, **kwargs)

		self.create_controls()
		self.do_layout()

	def create_controls(self):
		self.results_panel = None
		self.orgChoice = wx.Choice(self, choices=self.orgs, style=wx.CB_SORT)
		self.searchTerm = wx.TextCtrl(self, style=wx.TE_PROCESS_ENTER)
		self.searchTerm.SetFocus()
		self.searchButton = wx.Button(self, label="Search")

		# bind events
		self.searchButton.Bind(wx.EVT_BUTTON, self.do_search)
		self.searchTerm.Bind(wx.EVT_TEXT_ENTER, self.do_search)

	def do_layout(self):
		# arrange choice, query box, and button horizontally
		hbox = wx.BoxSizer(wx.HORIZONTAL)
		hbox.Add(self.orgChoice, 0, wx.EXPAND)
		hbox.Add(self.searchTerm, 1, wx.EXPAND | wx.LEFT, 5)
		hbox.Add(self.searchButton, 0, wx.EXPAND | wx.LEFT, 5)
		
		# dock everything to the top, leaving room for the results
		self.vbox = wx.BoxSizer(wx.VERTICAL)
		self.vbox.Add(hbox, 0, wx.EXPAND)
		self.SetSizer(self.vbox)

	def do_search(self, event):
		term = self.searchTerm.GetValue()
		org = self.orgChoice.GetString(self.orgChoice.GetCurrentSelection())
		g = Github(self.credentials['username'], self.credentials['password'])
		code,data = g.search.issues.get(q="user:{} {}".format(org, term))
		if code != 200:
			self.display_error(code, data)
		else:
			self.display_results(data['items'])

	def display_results(self, results):
		if self.results_panel:
			self.results_panel.Destroy()
		self.results_panel = SearchResultsPanel(self, -1, results=results)
		self.vbox.Add(self.results_panel, 1, wx.EXPAND | wx.TOP, 5)
		self.vbox.Layout()

	def display_error(self, code, data):
		if self.results_panel:
			self.results_panel.Destroy()
		if 'errors' in data:
			str = ''.join('\n\n{}'.format(e['message']) for e in data['errors'])
		else:
			str = data['message']
		self.results_panel = wx.StaticText(self, label=str)
		self.results_panel.SetForegroundColour((200,0,0))
		self.vbox.Add(self.results_panel, 1, wx.EXPAND | wx.TOP, 5)
		self.vbox.Layout()
		width = self.results_panel.GetSize().x
		self.results_panel.Wrap(width)


class SearchResultsPanel(wx.ScrolledWindow):
	def __init__(self, *args, **kwargs):
		results = kwargs.pop('results', [])
		wx.PyScrolledWindow.__init__(self, *args, **kwargs)

		# lay out search controls inside scrollable area
		vbox = wx.BoxSizer(wx.VERTICAL)
		if not results:
			vbox.Add(wx.StaticText(self, label="(no results)"), 0, wx.EXPAND)
		for r in results:
			vbox.Add(SearchResult(self, result=r), flag=wx.TOP | wx.BOTTOM, border=8)
		self.SetSizer(vbox)
		self.SetScrollbars(0, 4, 0, 0)

class SearchResult(wx.Panel):
	def __init__(self, *args, **kwargs):
		self.result = kwargs.pop('result', {})
		wx.Panel.__init__(self, *args, **kwargs)

		self.create_controls()
		self.do_layout()

	def create_controls(self):
		titlestr = self.result['title']
		if self.result['state'] != 'open':
			titlestr += ' ({})'.format(self.result['state'])
		teststr = self.first_line(self.result['body'])
		self.title = wx.StaticText(self, label=titlestr)
		self.text = wx.StaticText(self, label=textstr)

		# adjust the title font
		titleFont = wx.Font(16, wx.FONTFAMILY_DEFAULT, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_BOLD)
		self.title.SetFont(titleFont)

		# bind click and hover events on this whole control
		self.Bind(wx.EVT_LEFT_UP, self.on_click)
		self.Bind(wx.EVT_ENTER_WINDOW, self.enter)
		self.Bind(wx.EVT_LEAVE_WINDOW, self.leave)

	def do_layout(self):
		vbox = wx.BoxSizer(wx.VERTICAL)
		vbox.Add(self.title, flag=wx.EXPAND | wx.BOTTOM, border=2)
		vbox.Add(self.text, flag=wx.EXPAND)
		self.SetSizer(vbox)

	def enter(self, _):
		self.title.SetForegroundColour(wx.BLUE)
		self.text.SetForegroundColour(wx.BLUE)

	def leave(self, _):
		self.title.SetForegroundColour(wx.BLACK)
		self.text.SetForegroundColour(wx.BLACK)

	def on_click(self, event):
		import webbrowser
		webbrowser.open(self.result['html_url'])

	def first_line(self, body):
		return body.split('\n')[0].strip() or '(no body)'


if __name__ == '__main__':
	app = wx.App()
	SearchFrame(None)
	app.MainLoop()