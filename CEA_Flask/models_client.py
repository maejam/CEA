from xmlrpc.client import ServerProxy


proxy = ServerProxy('http://models:3000', allow_none=True)
