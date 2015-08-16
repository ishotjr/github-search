#!/usr/bin/env python

import os, subprocess
import wx
from agithub import Github

class SearchFrame(wx.Frame):
	pass

if __name__ == '__main__':
	app = wx.App()
	SearchFrame(None)
	app.MainLoop()