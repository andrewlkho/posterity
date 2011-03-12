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
import datetime

instapaper_username = ""
instapaper_password = ""
database = ""

def usage():
    pass

def connect_db(database):
    """Connect to the database and return connection and cursor objects."""
    try:
        connection = sqlite3.connect(database)
    except:
        return False
    return connection, connection.cursor()

def login(username, password):
    """Login to instapaper.  If successful, returns True."""
    # Install a CookieJar
    cookiejar = cookielib.CookieJar()
    opener = urllib2.build_opener(urllib2.HTTPCookieProcessor(cookiejar))
    urllib2.install_opener(opener)

    # Build the request
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

def init_db(database):
    """Create database schema and fill _metadata"""
    # Create database schema
    cursor.execute("""DROP TABLE IF EXISTS _metadata""")
    cursor.execute("""DROP TABLE IF EXISTS archive""")
    connection.commit()
    cursor.execute("""CREATE TABLE _metadata (
        key TEXT PRIMARY KEY NOT NULL,
        value TEXT NOT NULL
    )""")
    cursor.execute("""CREATE TABLE archive (
        id INTEGER PRIMARY KEY,
        url TEXT UNIQUE NOT NULL,
        title TEXT,
        description TEXT,
        pubDate REAL,
        importDate REAL NOT NULL DEFAULT (julianday('now'))
    )""")
    connection.commit()

    # Fetch the RSS feed URL and CSV form_key
    try:
        archive_page = urllib2.urlopen("http://www.instapaper.com/archive")
    except:
        sys.exit(1)
    rss_url_regex = r'"(http://www\.instapaper\.com/archive/rss/[^"]*)"'
    csv_form_key_regex = r'<input[^>]*name="form_key"[^>]*value="([^"]*)"[^>]*/>'
    big_regex = rss_url_regex + ".*" + csv_form_key_regex
    rss_url, csv_form_key = re.search(big_regex, archive_page.read(), re.DOTALL).group(1, 2)

    # Insert rss_url and csv_form_key into the `_metadata` table
    cursor.execute("""INSERT INTO _metadata (key, value) VALUES (
        'rss_url', '%s'
    )""" % rss_url)
    cursor.execute("""INSERT INTO _metadata (key, value) VALUES (
        'csv_form_key', '%s'
    )""" % csv_form_key)
    connection.commit()

    return True

def fetch_via_rss():
    """Fetch the instapaper Archive RSS feed and return a list containing 
    dictionaries.  Each dictionary in the list represents a single <item> in
    the RSS feed (i.e. a single saved article).
    """
    # Find out the URL to the RSS feed and store it in rss_url
    cursor.execute("""SELECT value FROM _metadata WHERE key='rss_url'""")
    result = cursor.fetchone()
    if result is None:
        print "The database has not been correctly initialised."
        sys.exit(2)
    rss_url = result[0]

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
            ("title", "url", "description", "pubDate"),
            [item.getElementsByTagName(field)[0].firstChild.data \
             if item.getElementsByTagName(field)[0].hasChildNodes() \
             else "" \
             for field in ("title", "link", "description", "pubDate")]
        )))
    return list

def fetch_via_csv():
    """Fetch the CSV export file and return a list of dictionaries, where each 
    dictionary represents a single line in the CSV file (i.e. a single saved
    article).
    """
    # Find out csv_form_key
    cursor.execute("""SELECT value FROM _metadata WHERE key='csv_form_key'""")
    result = cursor.fetchone()
    if result is None:
        print "The database has not been correctly initialised."
        sys.exit(2)
    csv_form_key = result[0]

    # csv_file is a reader object as defined in the `csv` module
    csv_request_data = urllib.urlencode({"form_key" : csv_form_key})
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

def update_db(article):
    """Take a dictionary representing a single article and insert it into the
    database (if it's not already there).
    """
    # If the url is absent then something has gone wrong
    if "url" not in article:
        print "Error: url has disappeared!"
        sys.exit(2)

    # Hacky way to convert the pubDate into a UTC-based ISO8601 string
    if "pubDate" in article and article["pubDate"]:
        localdatetime = datetime.datetime.strptime(article["pubDate"][0:-4], "%a, %d %b %Y %H:%M:%S")
        if article["pubDate"][-3:] == "EST":
            utcdatetime = localdatetime + datetime.timedelta(0, 0, 0, 0, 0, 5)
        elif article["pubDate"][-3:] == "EDT":
            utcdatetime = localdatetime + datetime.timedelta(0, 0, 0, 0, 0, 4)
        article["pubDate"] = utcdatetime.isoformat("T")

    # Compile the INSERT statement
    query = "INSERT OR IGNORE INTO archive (url, title, description, pubDate) VALUES ("
    query += ", ".join(["?" if field in article and article[field] else "NULL"
                        for field in ("url", "title", "description")])
    if "pubDate" in article and article["pubDate"]:
        query = ", ".join((query, "julianday('%s')" % article["pubDate"]))
    else:
        query = ", ".join((query, "NULL"))
    query += ")"

    # Execute the query
    cursor.execute(query, [article[field].decode('utf-8')
                           for field in ("url", "title", "description")
                           if field in article and article[field]])

    return True

def main():
    # Parse arguments with getopt
    try:
        opts, args = getopt.getopt(sys.argv[1:], "his:", ["help", "init", "source="])
    except getopt.GetoptError:
        usage()
        sys.exit(2)

    # Zero or no options are acceptable (if zero, then --source=rss is the default)
    if not opts:
        opts = [("--source", "rss")]
    elif len(opts) > 1:
        usage()
        sys.exit(2)

    # If help has been requested then give it
    if opts[0][0] in ("-h", "--help"):
        usage()
        sys.exit()

    # Connect to the database
    global connection, cursor
    connection, cursor = connect_db(database)

    # Perform the requested action(s)
    for opt, arg in opts:
        if opt in ("-i", "--init"):
            login(instapaper_username, instapaper_password)
            init_db(database)
        elif opt in ("-s", "--source") and arg == "rss":
            login(instapaper_username, instapaper_password)
            for article in fetch_via_rss():
                update_db(article)
            connection.commit()
        elif opt in ("-s", "--source") and arg == "csv":
            login(instapaper_username, instapaper_password)
            for article in fetch_via_csv():
                update_db(article)
            connection.commit()
        else:
            usage()
            sys.exit(2)

if __name__ == "__main__":
    main()
