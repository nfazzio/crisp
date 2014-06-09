import urllib2, os
from bs4 import BeautifulSoup as bs
import re

def main():
    setup_dirs()
    base_url = 'http://gaceta.diputados.gob.mx/Gaceta/Iniciativas/'
    directory_soup = get_soup(base_url)
    links = directory_soup.findAll('a')
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
    iniciativas = urllib2.urlopen(base_url+link)
    soup = bs(iniciativas)
    filename = os.path.basename(link)
    print filename
    iniciativa_html = os.path.join('downloads/iniciativas', filename)

    with open(iniciativa_html, 'w+') as iniciativa:
        #iniciativa.write(str(soup))
        buffered_download(iniciativas, iniciativa)

def buffered_download(page, path):
    meta = page.info()
    file_size = int(meta.getheaders("Content-Length")[0])
    print "Downloading: %s Bytes: %s" % (path.name, file_size)

    file_size_dl = 0
    block_sz = 8192
    while True:
        buffer = page.read(block_sz)
        if not buffer:
            break

        file_size_dl += len(buffer)
        path.write(buffer)
        status = r"%10d [%3.2f%%]:" % (file_size_dl, file_size_dl * 100. / file_size)
        status = status + chr(8)*(len(status)+1)
        print status,

    path.close()


if __name__ == "__main__":
    main()
