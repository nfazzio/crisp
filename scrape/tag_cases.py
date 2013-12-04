#!/usr/bin/python
# -*- coding: utf-8 -*-
import os
import urllib2
import csv
import time
import logging
import os
import urllib2
import csv
import time
import logging
import re
from bs4 import BeautifulSoup, Comment
import argparse
import itertools
import unicodedata

logger = logging.getLogger(__name__)
with open(os.path.abspath('resources/committees.csv'), 'Ur') as f:
    committees = list((committee) for committee in csv.reader(f, delimiter=','))[0]
def main():
    #TODO Finish setting up option parser
    parser = set_up_parser()

    #url to parse 
    page = open(os.path.join(os.path.abspath('downloads'),'gp62_a1primero.html'))
    soup = BeautifulSoup(page, "lxml")
    strip_comments(soup)
    cases = get_cases(soup)
    case_dict_list = [parse_case(case) for case in cases]
    # Create output file
    tsv_out = initialize_output('test')
    tsv_out.writeheader()
    for dictionary in case_dict_list:
        # print {k: v.encode('utf8') for (k, v) in dictionary.items()}
        # tsv_out.writerow({k: v.encode('utf8') for (k, v) in dictionary.items()})
        tsv_out.writerow({k: strip_accents(unicode(v)) for (k, v) in dictionary.iteritems()})

def get_cases(soup):
    """Returns all bills from an html page."""
    return soup.findAll('ul')

def parse_case(case):
    """Takes in a bill, and returns a dict of it's pertinent information."""
    #case_dict = dict.fromkeys(['title','legislator_title','legislator','party','date_introduced','committees','outcome','text_url','Gaceta Parlamentaria','links'])
    links = get_links(case)    
    #extract text of case
    case = case.findAll(text=True)
    case = unicode.join(u'\n',map(unicode,case))
    #remove empty elements
    case = case.strip()
    case_dict={}
    case_dict["title"] = get_title(case)
    (legislator_title, legislator_name, legislator_gender, legislator_party) = get_legislator_info(case)
    case_dict["legislator_title"] = legislator_title
    case_dict["legislator_name"] = legislator_name
    case_dict["legislator_gender"] = legislator_gender
    case_dict["legislator_party"] = legislator_party
    case_dict["committees"] = ', '.join(get_committees(case)).decode('utf-8')
    case_dict["outcome"] = get_outcome(case)
    case_dict["date_introduced"] = get_date_introduced(case)

    dict_links = []
    for text,url in links.iteritems():
        dict_links.append(text+": "+url)
    case_dict["links"] = str(dict_links)
    case_dict = remove_nulls(case_dict)

    return case_dict

def get_links(case):
    """Returns all links from a bill."""
    #returns a dictionary of the links contained within the case
    links={}
    logger.info("retrieving links in case")
    textURL = case.findAll('a', href=True)
    for link in textURL:
        links[link.getText()]="http://gaceta.diputados.gob.mx"+link['href']
    return links

def remove_nulls(dictionary):
    """Replace null/empty values with NA to make output compatible with R."""
    dictionary = {key:("NA" if value in ('', None) else value) for (key,value) in dictionary.iteritems()}
    return dictionary

def get_title(case):
    """Returns the title of a bill."""
    title = re.match("^.*(?!\n)",case).group()
    return title

def get_outcome(case):
    """Returns the outcome of a case."""
    # TODO FIX
    outcome_match = re.search(re.compile("(?P<outcome>(Dictaminada|Precluida|Desechada))",re.U),case)
    outcome = ""
    if outcome_match:
        outcome = outcome_match.group()
    return outcome

def get_legislator_info(case):
    """Returns legislator title, legislator, legislator_gender, and legislator_party from a bill."""
    legislator_title = ""
    legislator_name = ""
    legislator_gender = ""
    legislator_party = ""
    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por (?P<title>(la|las|el|los)? [\S]*)\s(?P<legislator>[^,]*), (?P<party>[^\.]*?\.)",re.U),unicode(case))
    if legislator_line:
        # Edge case for when legislator title is a Congreso.
        if "Congreso" in legislator_line.group():
            legislator_title = re.search("el Congreso .*?\.", legislator_line.group()).group()
        elif u"Cámara" in legislator_line.group():
            legislator_title = re.search(ur"Cámara .*?\.", legislator_line.group()).group()
        else:
            legislator_title = legislator_line.group('title')
            legislator_name = legislator_line.group('legislator')
            if re.search("el diputado *",legislator_title):
                legislator_gender = "male"
            elif re.search("el diputado *",legislator_title):
                legislator_gender = "female"
            legislator_party = legislator_line.group('party')
    return (legislator_title, legislator_name, legislator_gender, legislator_party)

def get_committees(case):
    """Provide a list of subcommittees that a bill was passed to."""
    logger.info("finding committees")
    committee_line = re.search(re.compile("Turnada a las? (?P<committees>[^.]*)",re.U),case)
    committees_match = []
    if committee_line:
        committee_line = committee_line.group()
        bool_committees_match = [committee.decode('utf-8') in committee_line for committee in committees]
        committees_match = [bool_match*committee for bool_match,committee in zip(bool_committees_match,committees)]
        committees_match = filter(None, committees_match)
    return committees_match

def get_date_introduced(case):
    """Returns the date that a bill was introduced"""
    logger.info("finding date introduced")
    # date_line = re.search(", n.mero.*", case).group()
    # date = re.search("\w* \d{1,2} de \w* de \d{4}",date_line).group()
    date = None
    for date in re.finditer(u"\w* \d{1,2} de \w* de \d{4}", case):
        pass
    if date != None:
        return date.group()
    else:
        return ''

def initialize_output(name):
    """creates a DictWriter that writes the output tsv"""
    output_dir = os.path.abspath('output')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    date = time.strftime("%Y%m%d")
    fieldnames = ['title','legislator_title','legislator_name','legislator_gender','legislator_party','date_introduced','committees','outcome','links']
    output_file = open(os.path.normpath(os.path.join(output_dir,date+"_"+name+".tsv")),'wb')
    return csv.DictWriter(output_file, fieldnames, delimiter='\t')

def strip_comments(soup):
    """Removes comments from html for easier handling"""
    comments = soup.findAll(text=lambda text:isinstance(text, Comment))
    [comment.extract() for comment in comments]
    return soup

def strip_accents(s):
    """strips accented characters from the output, to make friendly for R"""
    return ''.join(c for c in unicodedata.normalize('NFD', s)
                  if unicodedata.category(c) != 'Mn')

def set_up_parser():
    """sets up an argument parser"""
    parser = argparse.ArgumentParser(description='Scrape bill data from Mexican Congress')
    parser.add_argument('--verbose', '-v', help="will print logger.info statements", action="store_true")
    args = parser.parse_args()
    if args.verbose:
        logging.basicConfig(level=logging.INFO)
    logger = logging.getLogger(__name__)
    return parser

if __name__ == "__main__":
    main()
