"""What every rule shares: who is calling (roles), what the guard answers and logs (decision), the
folders it knows (places), the parts of a call it reads (calls), and how it reads a shell command
(shell).

Shell commands are tokenized, not run: a program that writes files by itself, such as a Python
script in the scratch folder, is not seen by this guard. Anything it cannot parse turns into "ask",
never into "allow".
"""
