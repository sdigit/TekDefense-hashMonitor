#!/usr/bin/env python                                                                                                                                                                                      

'''
This is hashMonitor! This tool will collect hashes from data breeches reported via Twitter and specific web resources.
This works by checking popular accounts on twitter like @Dumpmon and @PastebinDorks and web resources.
hashMonitor will go to each link they tweet and scrape out MD5, SHA1, and SHA256 Hashes.

@TekDefense
Ian Ahl | www.TekDefense.com | 1aN0rmus@tekDefense.com

Version: 0.3.2

Changelog:

.3
The twitter API now requires an API to view tweets. To avoid having 
eveyone generate an API key I instead modified the code to use the
twitter website.
[+] See above
[+] Proxy support
[+] URLLIB2 instead of httplib2
[+] Spelling corrections, thanks @tekwizz123
[+] Removed the import and the functions for the twitter API


.2
[+] Optimize database for faster hash insertion
[+] Added option to specify a database name and path
[+] Added error handling to the hash insert to DB
[+] Optimized link2DB function and added error handling
[+] Fixed a problem with listing hashes
[+] Added a summary option
[+] Started an account function, not done yet though!
[+] Fixed a bug in the hashes2DB that gave an incorrect count on how many hashes were added to the database
[+] Added a function to remove hashes from the database. Will take a .pot or any other text file with hashes in it.
[+] Added monitoring of of web resources as well. Mostly using @AndrewMohawk's pasteLert.

.1 
[+] Initial Release

TODO

[-] Collect the real URL as well as the shortened one.
'''

import sqlite3, re, datetime, httplib2, argparse, sys, urllib, urllib2

listMonitor = ['Dumpmon', 'PastebinDorks', 'TekDefense']
listURLMonitor = ['https://twitter.com/PastebinDorks', 'https://twitter.com/dumpmon', 'http://www.leakedin.com/']
listURLs = []
hashMonDB = 'hashMon.db'
today = datetime.datetime.now()
now = today.strftime("%Y-%m-%d %H:%M")
MD5 = '([a-fA-F0-9]{32})\W'
SHA1 = '([a-fA-F0-9]{40})\W'
SHA256 = '([a-fA-F0-9]{64})\W'
listTypes = [('MD5',MD5),('SHA1',SHA1), ('SHA256',SHA256),]
listResults = []
listNewURLs = []
hashType = ''
hashList = False

parser = argparse.ArgumentParser(description='hashMonitor is a tool that will collect hashes from data breeches reported via Twitter')
parser.add_argument('-d', '--database', help='This option is used to specify a database name. ./hashMonitor.py -d databaseName.db')
parser.add_argument('-o', '--output', help='This option will output the results to a file. ./hashMonitor.py -o output.txt')
parser.add_argument('-l', '--list', help='This option will return a list of all the hashes in the database. Use ANY, MD5, SHA1, or SHA256. ./hashMonitor.py -l MD5')
parser.add_argument('-s', '--summary', action='store_true', default=False, help='This option will display stats on URLs scanned and Hashes collected ./hashMonitor.py -s')
parser.add_argument('-a', '--add', help='This option will add a twitter account to the monitor db ./hashMonitor.py -a TWITTERHANDLE')
parser.add_argument('-r', '--remove', help='This option will remove hashes from the database from any text base file that includes hashes like a .pot file ./hashMonitor.py -r hashcat.pot')
args = parser.parse_args()

if args.output:
    oFile = args.output
    print '[+] Printing results to file:', args.output
    o = open(oFile, "w")
    sys.stdout = o

if args.list:
    hashList = True
    if args.list.upper() == 'ANY' or args.list.upper() == 'MD5' or args.list.upper() == 'SHA1' or args.list.upper() == 'SHA256':
        hashType = args.list.upper()
    else:
        print '[!] You must choose -l ANY, -l MD5, =l SHA1, or -l SHA256'
        sys.exit()

if args.database:
    hashMonDB = args.database

def webLinkPull():
    global listURLs
    for i in listURLMonitor:
        url = i
        print url
        try:
            proxy = urllib2.ProxyHandler()
            opener = urllib2.build_opener(proxy)
            response = opener.open(url)
            content = response.read()
            contentString = str(content)
            regURL = 'http:\/\/www\.pastebin.com\/\w{1,12}'
            regURL2 = 'http:\/\/pastebin.com\/raw\.php...\w{1,10}'
            regURLComp = re.compile(regURL)
            regexURLSearch = re.findall(regURLComp, contentString) 
            regURLComp2 = re.compile(regURL2)
            regexURLSearch2 = re.findall(regURLComp2, contentString)
            for i in regexURLSearch:
                listURLs.append(i)  
            for i in regexURLSearch2:
                listURLs.append(i)      
        except:
            print '[-] Unable to pull results for ' + i
    
def links2DB():
    print '[*] Adding links to the DB if they have not been scanned previously.'
    con = sqlite3.connect(hashMonDB)
    with con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS URLs(URL TEXT PRIMARY KEY, DATE TEXT)')
        con.commit()
        n = 0
        for i in listURLs:
            try:
                cur.execute("INSERT INTO URLs(URL, DATE) VALUES(?,?)", (i, now))
                listNewURLs.append(i)
                print '[+] Adding ' + i + ' into the DB'
            except:
                n = n + 1
        if n > 0:
            print '[-] ' + str(n) + ' links were previously scanned' 
    con.commit()
    con.close()
    
def collectHashes():
    global listResults
    if len(listNewURLs) > 0:
        print '[+] Searching for hashes in the new URLs'
        for URL in listNewURLs:
            try:
                proxy = urllib2.ProxyHandler()
                opener = urllib2.build_opener(proxy)
                response = opener.open(URL)
                content = response.read()
                contentString = str(content)
                for reg in listTypes:
                    regVal = reg[1]
                    regexValue = re.compile(regVal)
                    regexSearch = re.findall(regexValue,contentString)
                    for result in regexSearch:
                        listResults.append((result, reg))
            except:
                print '[-] Unable to collect hashes for ' + URL
        listResults = list(set(listResults)) 
    else:
        print '[-] No new URLs to search'

def hashes2DB():
    print '[*] Inserting new hashes to the DB if any are found.'
    con = sqlite3.connect(hashMonDB)
    n = 0
    with con:
        cur = con.cursor()
        cur.execute('CREATE TABLE IF NOT EXISTS HASHES(HASH TEXT PRIMARY KEY, TYPE TEXT)')
        con.commit()
        for i in listResults:
            try:
                cur.execute("INSERT INTO HASHES(HASH, TYPE) VALUES(?,?)", (i[0], i[1][0]))
                n = n + 1                
                print '[+] Adding ' + i[0] + ' to the DB'
            except:
                print '[-] ' + i[0] + ' already exists in database'
        print '[+] Added ' + str(n) + ' Hashes to the Database'
    con.commit()
    con.close()

def listHashes():
    if hashList == True:
        con = sqlite3.connect(hashMonDB)
        with con:
            cur = con.cursor()
            if hashType == 'MD5' or hashType == 'SHA1' or hashType == 'SHA256':
                cur.execute('SELECT HASH FROM HASHES where TYPE = ?', (hashType, ))
                results = cur.fetchall()
                for i in results:
                    print i[0]
            else:
                cur.execute('SELECT HASH FROM HASHES')
                results = cur.fetchall()
                for i in results:
                    print i[0]


def summary():
    con = sqlite3.connect(hashMonDB)
    with con:
        cur = con.cursor()
        cur.execute('SELECT TYPE, COUNT(HASH) FROM HASHES GROUP BY TYPE')
        rows = cur.fetchall()
        num = 0
        for row in rows:
            num = num + row[1]
            print '[+] ' + row[0] + ': ' + str(row[1])
        print '[+] You have collected a total of ' + str(num) + ' hashes in this database!'
        cur.execute('SELECT URL, COUNT(URL) FROM URLS')
        rows = cur.fetchall()
        num = 0
        for row in rows:
            num = num + row[1]
        print '[+] You have scraped a total of ' + str(num) + ' URLs listed in this database!'

def hashRemove():
    print '[*] Checking to see if there are any matches between the database and ' + potFile + '. Any matches will be removed from the database!'
    global listResults
    fileImport =open(potFile)
    strFile=''  
    for line in fileImport:
        strFile += line
    regVal = MD5
    regexValue = re.compile(regVal)
    regexSearch = re.findall(regexValue,strFile)
    listResults = []
    for j in regexSearch:
        listResults.append(j)
    listResults = list(set(listResults))
    con = sqlite3.connect(hashMonDB)
    with con:
        n = 0
        cur = con.cursor()
        for i in listResults:
            cur.execute('SELECT HASH FROM HASHES WHERE HASH = ?', (i, ))
            row = cur.fetchone()
            if row != None:
                print '[-] ' + row[0] + ' is being removed from the database'
                cur.execute('DELETE FROM HASHES WHERE HASH = ?', (row[0], ))
                n = n + 1
        print '[+] Removed ' + str(n) + ' hashes from the database'

print '[*] Running hashMonitor.py'


if args.list:
    listHashes()
elif args.summary == True:
    summary()
elif args.remove:
    potFile = args.remove
    hashRemove()
else:
    #accounts()
    #twitterLinkPull()
    webLinkPull()
    links2DB()
    collectHashes()
    hashes2DB()
