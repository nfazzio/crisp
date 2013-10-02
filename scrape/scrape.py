import urllib2
from BeautifulSoup import BeautifulSoup

basePage = 'http://gaceta.diputados.gob.mx/gp_iniciativas.html'
def main():
	response = urllib2.urlopen(basePage)
	soup = BeautifulSoup(response)
	print response.read()
	print getLinks(soup)

def getLinks(soup):
	return soup.findAll('a')

if __name__ == "__main__":
	main()
