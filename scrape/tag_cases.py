#!/usr/bin/python

import os
import urllib2
import csv
import time
import logging
import re
from bs4 import BeautifulSoup, Comment
import argparse
import lxml


#logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def main():
	#TODO Finish setting up option parser
	parser = argparse.ArgumentParser(description='Scrape bill data from Mexican Congress')
	parser.add_argument('--verbose', '-v', help="will print logger.info statements", action="store_true")
	args = parser.parse_args()
	if args.verbose:
		logging.basicConfig(level=logging.INFO)
	logger = logging.getLogger(__name__)

	# Create output file
	#TODO make header
	tsv = initialize_output('test')
	#header = 

	#url to parse 
	#TODO parameterize this
	base_page = 'http://gaceta.diputados.gob.mx/Gaceta/Iniciativas/62/gp62_a1primero.html'

	logger.info("connecting to "+base_page)
	response = urllib2.urlopen(base_page)
	logger.info("connected to "+base_page)
	soup = BeautifulSoup(response, "lxml")
	strip_comments(soup)
	cases = get_cases(soup)
	for case in cases:
		parse_case(case)
	#parse_case(cases[1])
	#for case in cases:
	#	parse_case(case)


def get_cases(soup):
	return soup.findAll('ul')

def parse_case(case):
	case_dict = dict.fromkeys(['title','legislator_title','legislator','party','date_introduced','committees','outcome','text_url','Gaceta Parlamentaria'])
	links = get_links(case)	
	#extract text of case
	case = case.findAll(text=True)
	case = unicode.join(u'\n',map(unicode,case))
	#remove empty elements
	case = case.strip()

	logger.info("examining the following case data:"+case.strip())
	logger.info("grabbing title")
	title = re.match("^.*(?!\n)",case).group()

	(legislator_title, legislator, party) = get_legislator_info(case)
	committees = get_committees(case)



	logger.info("finding outcome ")
	outcome_match = re.search(re.compile("(?P<outcome>(Dictaminada|Precluida|Desechada))",re.U),case)
	outcome = ""
	if outcome_match:
		outcome = outcome_match.group()
	#date_introduced = 
	#TODO Change to stdout
	print "title: "+title
	print "legislator_title: "+legislator_title
	print "legislator: "+legislator
	print "party: "+party
	print "committees: "+committees
	print "outcome: "+outcome
	for text,url in links.iteritems():
		print text+": "+url

	#print "textURL: "+textURL

#	return a dict

def get_links(case):
	#returns a dictionary of the links contained within the case
	links={}
	logger.info("retrieving links in case")
	textURL = case.findAll('a', href=True)
	for link in textURL:
		links[link.getText()]="http://gaceta.diputados.gob.mx"+link['href']
	return links

def get_legislator_info(case):
	logger.info("finding legislator_title, legislator, and party")
	legislator_title = ""
	legislator = ""
	party = ""
	legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por (?P<title>(la|las|el|los)? [\S]*)\s(?P<legislator>[^,]*), (?P<party>[^\.]*)",re.U),unicode(case))
	if legislator_line:
		legislator_title = legislator_line.group('title')
		legislator = legislator_line.group('legislator')
		party = legislator_line.group('party')
	return (legislator_title, legislator, party)

def get_committees(case):
	#TODO Split committees based on list provided by constanza
	logger.info("finding committees")
	committees = ""
	committees_line = re.search("Turnada a las? (?P<committees>[^.]*)",case)
	if committees_line:
		committees = committees_line.group('committees')
	return committees

def initialize_output(name):
	output_dir = os.path.abspath('output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	date = time.strftime("%Y%m%d")
	fieldnames = ['title','legislator_title','legislator','party','date_introduced','committees','outcome','text_url']
	output_file = open(os.path.normpath(os.path.join(output_dir,date+"_"+name+".csv")),'w')
	return csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')

def strip_comments(soup):
	comments = soup.findAll(text=lambda text:isinstance(text, Comment))
	[comment.extract() for comment in comments]
	return soup

if __name__ == "__main__":
	main()
