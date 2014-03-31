#!/usr/bin/python
# -*- coding: utf-8 -*-
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
    #page = open(os.path.join(os.path.abspath('downloads'),'test.html'))
    soup = BeautifulSoup(page, "lxml")
    strip_comments(soup)
    cases = get_cases(soup)
    case_dict_list = [parse_case(case) for case in cases]
    # Create output file
    tsv_out = initialize_output('test')
    tsv_out.writeheader()
    for dictionary in case_dict_list:
        tsv_out.writerow({k: strip_accents(unicode(v)) for (k, v) in dictionary.iteritems()})

def get_cases(soup):
    """Returns all bills from an html page."""
    return soup.findAll('ul')

def parse_case(case):
    """Takes in a bill, and returns a dict of it's pertinent information."""
    links = get_links(case)    
    #Extract text of case.
    case = case.findAll(text=True)
    case = unicode.join(u'\n',map(unicode,case))
    #Remove empty elements.
    case = case.strip()
    #Assign values to dictionary keys
    case_dict={}
    case_dict["title"] = get_title(case)
    (legislator_title, legislator_name, legislator_gender, legislator_party) = get_legislator_info(case)
    (outcome, floor_outcome, outcome_date) = get_outcome(case)
    case_dict["legislator_title"] = legislator_title
    case_dict["legislator_name"] = legislator_name
    case_dict["legislator_gender"] = legislator_gender
    case_dict["legislator_party"] = legislator_party
    case_dict["committees"] = ', '.join(get_committees(case)).decode('utf-8')
    case_dict["outcome"] = outcome
    case_dict["floor_outcome"] = floor_outcome
    case_dict["outcome_date"] = outcome_date
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
    # print case
    outcome, floor_outcome, outcome_date = ['', '', '']
    outcome_match = re.search(re.compile('(?P<outcome>(Dictaminada|Precluida|Desechada))\n'
                                         '(?P<floor_outcome>.*?),? '
                                         '(?P<date>el \w* \d{1,2} de \w* de \d{4})',re.U),case)
    if outcome_match:
        outcome = outcome_match.group('outcome')
        floor_outcome = outcome_match.group('floor_outcome')
        outcome_date = outcome_match.group('date')
    return outcome, floor_outcome, outcome_date

def get_legislator_info(case):
    """Returns legislator title, legislator, legislator_gender, and legislator_party from a bill."""
    legislator_title = ""
    legislator_names = ""
    legislator_gender = ""
    legislator_party = ""
    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por (?P<title>(la|las|el|los) [\S]*)\s(?P<legislator>[^,].*), (?P<party>[^\.]*\.)",re.U),unicode(case))
    capturable_names = ["diputad", "senador", "diputado", "diputados", "diputadas"]
    # Edge case for when presented to "Ejecutivo federal"
    '''if not legislator_line:
        legislator_line = re.search("Presentada por el Ejecutivo federal\. ?\n", case)
        if legislator_line:
            break
        legislator_line = re.search("Presentada por el Congreso de Guanajuato", case)

        print "EJECUTIVO CAPTURE"
        print legislator_line'''
    if not legislator_line:
        legislator_names = legislator_edge_cases(case)
        return (legislator_title, legislator_names, legislator_gender, legislator_party)
    if not legislator_line:
        print "HUGE ERROR - DID NOT PARSE LEGISLATOR LINE" + "\n" + "***********" + "\n" + unicode(case) + "\n" + "***********"
    if legislator_line:
        #print "examining: " + legislator_line.group()
        # Edge case for when legislator title is a Congreso or Cámara.
        if "Congreso" in legislator_line.group():
            #print "found congreso in: "+legislator_line.group()
            legislator_names = re.search("el Congreso .*?(?=\.)", legislator_line.group()).group()
            #print "legislator name is: " + legislator_names
        elif u"Cámara" in legislator_line.group():
            #print "found camara in: "+legislator_line.group()
            legislator_names = re.search(u"Cámara .*?(?=(,|\.))", legislator_line.group()).group()
        elif "Ejecutivo federal." in legislator_line.group():
            print "EJECUTIVO ASSIGNMENT"
            legislator_names = "el Ejecutivo federal"
        elif not any(x in legislator_line.group() for x in capturable_names):
            #print "WEIRD CASE, searching within: " + legislator_line.group()
            legislator_names = re.search("(?<=presentad[aos]{1-3} por) .*?(?=(\.|\,))", legislator_line.group()).group()
        else:
            legislator_title = legislator_line.group('title')
            if re.search("el diputado *",legislator_title):
                legislator_gender = "male"
            elif re.search("la diputada *",legislator_title):
                legislator_gender = "female"
            legislator_party = legislator_line.group('party')
            #The following split handles the case where there are multiple legislators.
            legislator_names = re.split(',| y ',legislator_line.group('legislator'))
            legislator_names = [strip_accents(legislator_name) for legislator_name in legislator_names]
    else:
        legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) .*", re.U), unicode(case))
        if legislator_line:
            print "WE CAUGHT THE HUGE ERROR" + "\n" + "proposed legislator_line: " + legislator_line.group()
        else: print "CAN'T PARSE HUGE ERROR" + case
    return (legislator_title, legislator_names, legislator_gender, legislator_party)

def legislator_edge_cases(case):
    """Returns legislator_names matches for various edge cases"""
    print "EDGE CASE: "+case
    case = strip_accents(case)
    edge_patterns = ["(?:Presentada por el )(Ejecutivo federal)(?:\. ?\n)",
                     "(?:Presentada por el )(Congreso del? .*)(?:\.)",
                     re.compile("(?:Enviada por la )(Camara de Senadores)(?:\.)",re.U)]
    for pattern in edge_patterns:
        match = re.search(pattern, case)
        if match:
            print "RETURNING "+match.group()
            return match.group(1)
    print "RETURNING NOTHING"
    print "BUT SRSLY: THIS IS THE CASE :"
    for line_num, line in enumerate(case.split("\n")):
        print str(line_num) + ": " + line
    return ""

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
        #Passes through all the dates, so that the final date is stored in the variable.
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
    fieldnames = ['title',
                  'legislator_title',
                  'legislator_name',
                  'legislator_gender',
                  'legislator_party',
                  'date_introduced',
                  'committees',
                  'outcome',
                  'floor_outcome',
                  'outcome_date',
                  'links']
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
