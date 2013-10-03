#!/usr/bin/python

import os
import urllib2
import csv
import time
import string
import logging
from BeautifulSoup import BeautifulSoup

def main():
	# Create output file
	tsv = initialize_output('test')
	#header = 
	#csv.writerow(header)
	# url to parse 
	base_page = 'http://gaceta.diputados.gob.mx/Gaceta/Iniciativas/62/gp62_a1primero.html'

	logging.info("connecting to "+base_page)
	response = urllib2.urlopen(base_page)
	logging.info("connected to "+base_page)
	soup = BeautifulSoup(response)
	print response.read()
	cases = get_cases(soup)
	parse_case(cases[0])
	#for case in cases:
	#	parse_case(case)


def get_cases(soup):
	return soup.findAll('ul')

def parse_case(case):
	case = case.findAll(text=True)
	for line in case:
		print line
	title = case[0]
	legislator_title = case[2]
	#legislator = 
	#party = 
	#date_introduced = 
	#committees = 
	#outcome = 
	#textURL =
#	return a dict

def initialize_output(name):
	output_dir = os.path.abspath('output')
	if not os.path.exists(output_dir):
		os.makedirs(output_dir)
	date = time.strftime("%Y%m%d")
	fieldnames = ['title','legislator_title','legislator','party','date_introduced','committees','outcome','text_url']
	output_file = open(os.path.normpath(os.path.join(output_dir,date+"_"+name+".csv")),'w')
	return csv.DictWriter(output_file, fieldnames=fieldnames, delimiter='\t')


if __name__ == "__main__":
	main()
