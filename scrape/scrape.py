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
	parse_case(cases[16])
	#for case in cases:
	#	parse_case(case)


def get_cases(soup):
	return soup.findAll('ul')

def parse_case(case):
	print "case before findall(text)" + str(case)
	'''
	#extract Gaceta Parlamentaria links
	textURL = case.findAll('a', href='True',)
	print "length: "+str(len(textURL))
	#Right now, the code expects for there to be just one link
	if len(textURL) > 1:
		logger.warning("multiple case texts found")
	elif len(textURL) < 1:
		logger.warning("no case text found")
	else:
		print "type(textURL): "+str(type(textURL))
		print str(textURL)
		(textURL,) = textURL
		link = textURL['href']
		print "link is: "+link
		print "type(textURL): "+str(type(textURL))
	'''
	get_links(case)
	#extract text of case
	case = case.findAll(text=True)
	#remove empty elements
	case = [x for x in case if x !="\n"]
	logger.info("examining the following case data:"+"\n".join(case))
	#QUESTION: Is the title the entire first line?
	logger.info("finding title in "+case[0])
	title = case[0]
	logger.info("finding legislator_title, legislator, and party in "+case[1])
	second_line = re.search("por (la|el) (?P<title>[\S]*)\s(?P<legislator>[^,]*), (?P<party>[^\.]*)",case[1])
	legislator_title = second_line.group('title')
	legislator = second_line.group('legislator')
	party = second_line.group('party')
	
	#QUESTION - how are committees are separated
	logger.info("finding committees in "+case[2])
	committees = re.search("Turnada a la (?P<committees>[^.]*)",case[2]).group('committees')

	print "type case[3]: "+str(type(case[3]))


	logger.info("finding outcome in "+case[3])
	outcome = re.search(re.compile("(?P<outcome>[\w]*)",re.U),case[3]).group(0)
	#date_introduced = 
	#TODO Change to stdout
	print "title: "+title
	print "legislator_title: "+legislator_title
	print "legislator: "+legislator
	print "party: "+party
	print "committees: "+committees
	print "outcome: "+outcome
	#print "textURL: "+textURL

#	return a dict

def get_links(case):
	links={}
	logger.info("retrieving links in case")
	textURL = case.findAll('a', href=True)
	for link in textURL:
		links[link.getText()]=link['href']
	return links


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
