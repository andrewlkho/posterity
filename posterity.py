#!/usr/bin/env python

import sys
import getopt
import re
import urllib
import urllib2
import cookielib
import xml.dom.minidom
import csv
import sqlite3

instapaper_username = ""
instapaper_password = ""
database = ""

def usage():
    pass

def login(username, password):
    """Login to instapaper.  If successful, returns True."""
    data = urllib.urlencode({"username" : username, "password" : password})
    request = urllib2.Request('http://www.instapaper.com/user/login', data)

    try:
        response = urllib2.urlopen(request)
    except:
        return False

    # Bit of a hack: instapaper only sets a cookie if login was successful
    if response.info().getheader("Set-Cookie"):
        return True
    else:
        return False

def fetch_via_rss():
    """Fetch the instapaper Archive RSS feed and return a list containing 
    dictionaries.  Each dictionary in the list represents a single <item> in
    the RSS feed (i.e. a single saved article).
    """
    # Find out the URL to the RSS feed and store it in rss_url
    try:
        archive_page = urllib2.urlopen("http://www.instapaper.com/archive")
    except:
        return False
    rss_regex = r'"(http://www\.instapaper\.com/archive/rss/[^"]*)"'
    rss_url = re.search(rss_regex, archive_page.read()).group(1)

    # rss_dom is the entire RSS file as a Document object
    try:
        rss = urllib2.urlopen(rss_url)
    except:
        return False
    rss_dom = xml.dom.minidom.parse(rss)

    # Assemble and return the list of dictionaries
    list = []
    for item in rss_dom.getElementsByTagName('item'):
        list.append(dict(zip(
            ("title", "link", "description", "pubDate"),
            [item.getElementsByTagName(field)[0].firstChild.data \
             if item.getElementsByTagName(field)[0].hasChildNodes() \
             else "" \
             for field in ("title", "link", "description", "pubDate")]
        )))
    return list

def fetch_via_export():
    """Fetch the CSV export file and return a list of dictionaries, where each 
    dictionary represents a single line in the CSV file (i.e. a single saved
    article).
    """
    # Find out form_key
    try:
        archive_page = urllib2.urlopen("http://www.instapaper.com/archive")
    except:
        return False
    form_key_regex = r'<input[^>]*name="form_key"[^>]*value="([^"]*)"[^>]*/>'
    form_key = re.search(form_key_regex, archive_page.read()).group(1)

    # csv_file is a reader object as defined in the `csv` module
    csv_request_data = urllib.urlencode({"form_key" : form_key})
    csv_request_url = "http://www.instapaper.com/export/csv"
    csv_request = urllib2.Request(csv_request_url, csv_request_data)
    try:
        csv_file = urllib2.urlopen(csv_request)
    except:
        return False

    # Assemble and return the list of dictionaries
    list = []
    for line in csv.reader(csv_file):
        dictionary = dict(zip(("url", "title", "description", "folder"), line))
        if dictionary["url"] != "URL" and dictionary["folder"] == "Archive":
            del dictionary["folder"]
            list.append(dictionary)
    return list

def init_db(database):
    """Check that we can connect to the database and that the `archive` table 
    exists.  If successful, it returns a cursor object.
    """
    try:
        connection = sqlite3.connect(database)
    except:
        return False
    cursor = connection.cursor()
    cursor.execute("""CREATE TABLE IF NOT EXISTS archive (
                          id INTEGER PRIMARY KEY,
                          url TEXT UNIQUE NOT NULL,
                          title TEXT,
                          description TEXT,
                          pubDate REAL,
                          importDate REAL NOT NULL DEFAULT (julianday('now'))
                      );""")
    connection.commit()
    return cursor

def main():
    # Parse arguments with getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "hre", ["help", "rss", "export"])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # If no options have been given --rss is the default
    if not opts:
        opts = [("--rss", "")]

    # Install a CookieJar
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    urllib2.install_opener(opener)

    # What to do with given options
    for opt, arg in opts:
        if opt in ("-h", "--help"):
            usage()
            sys.exit()
        elif opt in ("-r", "--rss"):
            login(instapaper_username, instapaper_password)
            fetch_via_rss()
        elif opt in ("-e", "--export"):
            login(instapaper_username, instapaper_password)
            fetch_via_export()

if __name__ == "__main__":
    main()
