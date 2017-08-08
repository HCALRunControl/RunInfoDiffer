import sys
from commands import getoutput
from HTMLParser import HTMLParser
from time import sleep
import json
import requests
reload(sys)
sys.setdefaultencoding('utf-8')

class webDifferParser(HTMLParser):

    def __init__(self):
         HTMLParser.__init__(self)
         self.data = []
    def handle_data(self, data):
         if not data.isspace() and "Runinfo Diff" not in data and "Run Info Differ Log":
              self.data.append(data.strip())
    def clear_diff(self):
         self.data = []

parser = webDifferParser()
log_url = "http://hcalmon.cms/RunInfoDiffer/BotUrlLog.html"
def read_log():
    log = getoutput('curl -s -k --socks5-hostname localhost:1080 \"'+log_url+'\"')
    parser.clear_diff()
    #print log
    for line in log.splitlines():
	parser.feed(line)
    return parser.data[-2]+"&"+parser.data[-1]

def get_diff(url):
    diff = getoutput('curl -s -k --socks5-hostname localhost:1080 \"'+url+'\"')
    parser.clear_diff()
    for line in diff.splitlines():
	parser.feed(line)

def send_slack_message(runnumber1, runnumber2, message):
    webhook_url = 'WEBHOOK'
    slack_data = {'text': "Run parameters changed between run %d and run %d ```%s```" % (runnumber1, runnumber2, message)}
    response = requests.post(
      webhook_url, data=json.dumps(slack_data),
      headers={'Content-Type': 'application/json'}
    )
    if response.status_code != 200:
        print 'Request to slack returned an error %s, the response is:\n%s' % (response.status_code._codes[response.status_code][0], response.text)


def is_int(string):
    try:
	int(string)
	return True
    except ValueError:
	return False

previous_url = read_log()
while True:
    new_url = read_log()
    if new_url != previous_url:
	get_diff(new_url)
	previous_url = new_url
	message = ""
	for line in parser.data:
	    if "Diff of run" in line:
		runnumbers =[]
		for word in line.split(" "):
		    if is_int(word):
			runnumbers.append(int(word))
	    else:
		message += line+"\n"
	send_slack_message(runnumbers[0], runnumbers[1], message)
	#print message
    sleep(20)










		
