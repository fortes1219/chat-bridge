"""Reading a shell command the way the shell would run it, without running it.

words splits a command into simple commands and reads their arguments; paths follows variables and
cd to the folder a word names; writes knows which paths a command writes; reading puts the three
together for one simple command.
"""
