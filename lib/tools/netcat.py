import os
import sys
import socket
import thirdparty.six as six
import thirdparty.requests as requests
import thirdparty.urllib3 as urllib3

from lib.parse.settings import config, quest
from thirdparty.html_similarity import similarity
from lib.core.dnslookup import DNSLookup
from lib.parse.colors import white, green, red, yellow, end, info, que, bad, good, run

def netcat(domain, ns, count):
	A = DNSLookup(domain, ns)
	ip = socket.gethostbyname(str(ns)) if count is 0 else str(A)
	if not A:
		print (que + 'Using DIG to get the real IP')
		print('   ' + bad + 'IP not found using DNS Lookup')
	url = 'http://' + domain
	try:
		page = requests.get(url, timeout=config['http_timeout_seconds'])
		http = 'http://' if 'http://' in page.url else 'https://'
		hncat = page.url.replace(http, '').split('/')[0]
		home = page.url.replace(http, '').split(hncat)[1]
		print (que + 'Connecting %s using as Host Header: %s'% (ip, domain))	
		data = requests.get('http://' + ip + home, headers={'host': hncat},timeout=config['http_timeout_seconds'], allow_redirects=False)
		count =+ 1
		if data.status_code in [301, 302]:
			print("   " + info + "Connection redirect to: %s"% data.headers['Location'])
			question = input("   " + info + 'Do yo want to redirect? y/n: ') if sys.version_info[0] == 3 else raw_input("   " + info + 'Do yo want to redirect? y/n: ')
		try:
			data = requests.get('http://' + ip + home, headers={'host': hncat},timeout=config['http_timeout_seconds'], allow_redirects=True)
		except requests.exceptions.ConnectionError:
			if question in ['y', 'yes', 'ye']:
				print("   " + bad +'Error while connecting to: %s'%data.headers['Location'])
		if data.status_code == 200:
			count =+ 1
			sim = similarity(data.text, page.text)
			if sim > config['response_similarity_threshold']:
				print ("   " + good + 'The connect has %d%% similarity to: %s' % (round(100 *sim, 2), url))
				print ("   " + good + '%s is the real IP'%ip)
				try:
					quest(question='\n' + info + 'IP found. Do yo want to stop tests? y/n: ', doY='sys.exit()', doN="pass")
				except KeyboardInterrupt:
					sys.exit()
			else:
				print ("   " + bad +'The connect has %d%% similarity to: %s' % (round(100 *sim, 2), url))
				print ("   " + bad +"%s is not the IP" %ip)
	except requests.exceptions.SSLError:
		print("   " + bad +'Error handshaking with SSL')
	except requests.exceptions.ReadTimeout:
		print("   " + bad +"Connection Timeout to: %s"% ip)
	except requests.ConnectTimeout:
		print("   " + bad +"Connection Timeout to: %s"% ip)
	except requests.exceptions.ConnectionError:
		print("   " + bad +"Connection Timeout to: %s"% ip)