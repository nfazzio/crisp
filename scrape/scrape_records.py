import urllib2, os
from bs4 import BeautifulSoup as bs
import re

def main():
    setup_dirs()
    base_url = 'http://gaceta.diputados.gob.mx/gp_iniciativas.html'
    directory_soup = get_soup(base_url)
    links = directory_soup.findAll('a')
    base_url = 'http://gaceta.diputados.gob.mx'
    for link in links:
        download_iniciativa(link, base_url)

def setup_dirs():
    if not os.path.exists('downloads/iniciativas'):
        os.makedirs('downloads/iniciativas/')

def get_soup(url):
    base = urllib2.urlopen(url)
    soup = bs(base.read())
    base.close()
    return soup

def download_iniciativa(link, base_url):
    link = link['href']
    if (link == '57/gp57_iniciativas.html') or ('mailto' in link):
        print "skipping " + base_url+link
        return
    print str(base_url+link)
    iniciativas = urllib2.urlopen(str(base_url+link))
    filename = os.path.basename(link)
    print filename
    iniciativa_html = os.path.join('downloads/iniciativas', filename)

    with open(iniciativa_html, 'w+') as iniciativa:
        iniciativa.write(iniciativas.read())

if __name__ == "__main__":
    main()
