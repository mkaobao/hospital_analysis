import urllib

thisurl = "https://www.google.com.tw/"
handle = urllib.urlopen(thisurl)
html_get = handle.read()

print html_get