import cgi, cgitb
form = cgi.FieldStorage() 
import os
def rahul(x):
	temp='this is working now'+x
	return temp
if __name__ == "__main__":
	print rahul('hello world')












