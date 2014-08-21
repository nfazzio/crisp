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
import sys

logger = logging.getLogger(__name__)
with open(os.path.abspath('resources/committees.csv'), 'Ur') as f:
    committees = list((committee) for committee in csv.reader(f, delimiter=','))[0]
def main():
    #TODO Finish setting up option parser
    parser = set_up_parser()
<<<<<<< HEAD

    #url to parse 
=======
    '''
    for filename in os.listdir(os.path.abspath('downloads/iniciativas')):
        with open(os.path.abspath('downloads/iniciativas/'+filename)) as page:
            print "HELLA: "+filename
            soup = BeautifulSoup(page, "lxml")
            strip_comments(soup)
            cases = get_cases(soup)
            case_dict_list = [parse_case(case) for case in cases]
            tsv_out = initialize_output(os.path.basename(filename))
            tsv_out.writeheader()
            for dictionary in case_dict_list:
                tsv_out.writerow({k: strip_accents(unicode(v)).encode('utf-8') for (k, v) in dictionary.iteritems()})
    '''
>>>>>>> multiple_files
    page = open(os.path.join(os.path.abspath('downloads/testing'),'gp62_a1primero.html'))
    #page = open(os.path.join(os.path.abspath('downloads'),'edge_cases.html'))
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
    (legislator_title, legislator_name, legislator_gender, legislator_party, suscrita) = get_legislator_info(case)
    (outcome, floor_outcome, outcome_date) = get_outcome(case)
    (returned_to, returned_to_article, returned_to_minutes, returned_to_minutes_date) = get_returned_to(case)
    case_dict["legislator_title"] = legislator_title
    case_dict["legislator_name"] = legislator_name
    case_dict["legislator_gender"] = legislator_gender
    case_dict["legislator_party"] = legislator_party
    case_dict["suscrita"] = suscrita
    case_dict["committees"] = ', '.join(get_committees(case)).decode('utf-8')
    case_dict["outcome"] = outcome
    case_dict["floor_outcome"] = floor_outcome
    case_dict["outcome_date"] = outcome_date
    case_dict["date_introduced"] = get_date_introduced(case)
    case_dict["returned_to"] = returned_to
    case_dict["returned_to_article"] = returned_to_article
    case_dict["returned_to_minutes"] = returned_to_minutes
    case_dict["returned_to_minutes_date"] = returned_to_minutes_date

    dict_links = []
    for text,url in links.iteritems():
        dict_links.append(text+": "+url)
    case_dict["links"] = str(dict_links)
    case_dict = remove_nulls(case_dict)

    return case_dict

def get_links(case):
    """Returns all links from a bill."""
    links={}
    logger.info("retrieving links in case")
    textURL = case.findAll('a', href=True)
    for link in textURL:
        links[link.getText()]="http://gaceta.diputados.gob.mx"+link['href']
    return links

def remove_nulls(dictionary):
    """Replace null/empty values with NA to make output compatible with R."""
    dictionary = {key:("NA" if value in ('', None, [], [u'']) else value) for (key,value) in dictionary.iteritems()}
    return dictionary

def get_title(case):
    """Returns the title of a bill."""
    title = re.match("^.*(?!\n)",case).group()
    return title

def get_outcome(case):
    """Returns the outcome of a case."""
    case = strip_accents(case)
    pattern = re.compile('(?P<outcome>(Dictaminada|Precluida|Desechada))\n'
                         '(?P<floor_outcome>.*?),? '
                         '(?P<date>el \w* \d{1,2} de \w* de \d{4})',re.U)
    returned_matches = [m.groupdict() for m in pattern.finditer(case)]
    if returned_matches:
        outcome, floor_outcome, outcome_date = [], [], []
        for returned_match in returned_matches:
            outcome.append(returned_match['outcome'])
            floor_outcome.append(returned_match['floor_outcome'])
            outcome_date.append(returned_match['date'])
        return outcome, floor_outcome, outcome_date
    return "","",""

def get_legislator_info(case):
    """Returns legislator title, legislator, legislator_gender, legislator_party, and suscrita from a bill."""
    # This is pretty ugly and needs to be refactored.
    #print "---------------------------\n"+case
    legislator_title = ""
    legislator_names = ""
    legislator_gender = ""
    legislator_party = ""
    suscrita = ""
    parties = "(PRD|PVEM|Movimiento Ciudadano|PRI|PAN|PT|Nueva Alianza|" \
              "Convergencia)"

    #Remove the 'en nombre' clause from the legislator_line because it is not
    #being caputred and messes up pattern matching.
    case = remove_en_nombre(case)
    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por "
                                           "(?P<title>(la|las|el|los) [\S]*)\s"
                                           "(?P<legislator>[^,].*), (del)?"
                                           "(?P<party>[^\.]*)(?:\.)",re.U),unicode(case))
    capturable_names = ["diputad", "senador", "diputado", "diputados", "diputadas"]

    #edge case for when no party is assigned to legslators before suscrita clause
    print case
    if re.search('(Presentada|Enviad(o|a)) por .* suscrita', case):
        for party in parties[1:-1].split('|'):
            party_before_suscrita = False
            if re.search(party + '.* suscrita', case):
                party_before_suscrita = True
                break
        if not party_before_suscrita:
            return legislator_edge_no_party(case)

    # If the legislator_line does not match the most common pattern
    if not legislator_line:
        legislator_title, legislator_names, legislator_gender = legislator_edge_cases(case)
        return (legislator_title, legislator_names, legislator_gender, legislator_party, suscrita)
    if legislator_line:
        print repr(case)
        #Edge case for when a comma, and not a semicolon, is used after the party
        party_exception = re.compile('(Presentada|Enviad(o|a)) por .*, (del )?' + parties + ',.*')
        if re.search(party_exception, case):
            return legislator_edge_funky_commas(case)

        # Edge case for when legislator title is a Congreso or Cámara.
        if "Congreso" in legislator_line.group():
            legislator_names = re.search("el Congreso .*?(?=(\.|,\s?\n))", legislator_line.group()).group()
        elif u"Cámara" in legislator_line.group():
            legislator_names = re.search(u"Cámara .*?(?=(,|\.))", legislator_line.group()).group()
        elif "Ejecutivo federal." in legislator_line.group():
            legislator_names = "el Ejecutivo federal"
        elif not any(x in legislator_line.group() for x in capturable_names):
            # Assume no legislator title
            print "absolute crazy case"
            print legislator_line.group()
            print legislator_line.group('title')
            print legislator_line.group('legislator')
            print legislator_line.group('party')
            return legislator_edge_no_title(case)
        else:
            legislator_title = legislator_line.group('title')
            legislator_gender = get_legislator_gender(legislator_title)
            legislator_party = legislator_line.group('party')
            #The following split handles the case where there are multiple legislators.
            legislator_names = re.split(',| y ',legislator_line.group('legislator'))
            legislator_names = [strip_accents(legislator_name) for legislator_name in legislator_names]

    print "PRE SUSCRITA:\n"
    print "title: "+legislator_line.group('title')
    print "legislator: "+legislator_line.group('legislator')
    print "party: " +legislator_line.group('party')
    print "--------"

    legislator_party, suscrita = get_suscrita(legislator_party,case)
    return (legislator_title, legislator_names, legislator_gender, legislator_party, suscrita)

def remove_en_nombre(case):
    """ Remove the tricky 'en nombre' segment that pops up in several cases"""
    print "LOG: en nombre removed"
    print "CASE BEFORE: " + case
    print "-------------------------"
    case = re.sub(' (a|en) nombre .*(?= y suscrit)?', '', case)
    return case

def legislator_edge_no_party(case):
    """ Handles case parsing in the event where there is no party before the
    suscrita clause, but the suscrita clause contains a party
    """
    legislator_title = ""
    legislator_gender = ""
    capturable_names = ["diputad", "senador", "diputado", "diputados", "diputadas"]
    #Case when there also is no legislator_title
    pre_suscrita = re.search('.* suscrita', case).group()
    print pre_suscrita
    if not any(x in pre_suscrita for x in capturable_names):
        print "CASE: NO LEGISLATOR_TITLE"
        title_flag = False
        title_line = "(?P<title>(la|las|el|los)?).*"

    else:
        title_flag = True
        title_line = "(?P<title>(la|las|el|los) [\S]*)\s"

    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por " \
                                           + title_line +
                                           "(?P<legislator>[^,].*)(,|;)? ?"
                                           "y? suscrita "
                                           "(?P<suscrita>.*)"
                                           "(?:\.)?"
                                           ,re.U),unicode(case))
    if title_flag:
        legislator_title = legislator_line.group('title')
        legislator_gender = get_legislator_gender(legislator_title)
    legislator_party = ""
    legislator_names = re.split(',| y ',legislator_line.group('legislator'))
    legislator_names = [strip_accents(legislator_name) for legislator_name in legislator_names]
    suscrita = legislator_line.group('suscrita')
    return (legislator_title, legislator_names, legislator_gender, legislator_party, suscrita)

def legislator_edge_funky_commas(case):
    """Case for when the party is separated by commas, and not a command and
    semicolon.
    """
    print case
    parties = "(PRD|PVEM|Movimiento Ciudadano|PRI|PAN|PT|Nueva Alianza|" \
              "Convergencia)"
    party = re.search(parties,case).group()
    print "party: "+party
 
    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por "
                                           "(?P<title>(la|las|el|los) [\S]*)\s"
                                           "(?P<legislator>[^,].*)?, (del |"
                                           "de los Grupos (p|P)arlamentarios del )?"
                                           "(?P<party>"+ party + "[^\.]*"
                                           ")"
                                           "(?:\.)?"
                                           ,re.U),unicode(case))
    legislator_title = legislator_line.group('title')
    legislator_gender = get_legislator_gender(legislator_title)
    legislator_party = legislator_line.group('party')
    legislator_names = re.split(',| y ',legislator_line.group('legislator'))
    legislator_names = [strip_accents(legislator_name) for legislator_name in legislator_names]
    legislator_party, suscrita = get_suscrita(legislator_party,case)
    return (legislator_title, legislator_names, legislator_gender, legislator_party, suscrita)

def legislator_edge_no_title(case):
    """Case for when there is no title in the legislator_line
    """
    legislator_line = re.search(re.compile("(Presentada|Enviad(o|a)) por "
                                           "(?P<title>(la|las|el|los)).*"
                                           "(?P<legislator>[^,].*), (del)?"
                                           "(?P<party>[^\.]*)(?:\.)",re.U),unicode(case))
    print legislator_line.group()
    legislator_title = "ERROR"
    legislator_gender = get_legislator_gender(legislator_title)
    legislator_party = legislator_line.group('party')
    legislator_names = re.split(',| y ',legislator_line.group('legislator'))
    legislator_names = [strip_accents(legislator_name) for legislator_name in legislator_names]
    legislator_party, suscrita = get_suscrita(legislator_party,case)
    return (legislator_title, legislator_names, legislator_gender, legislator_party, suscrita)

def get_suscrita(legislator_party, case):
    """Separates out the suscrita poriton from the party variable. This is
    necessary because the regex was getting horribly indecipherable.
    """
    parties = "(PRD|PVEM|Movimiento Ciudadano|PRI|PAN|PT|Nueva Alianza|" \
              "Convergencia)"
    for party in parties[1:-1].split('|'):
        pass
    suscrita = ""
    print "suscrita section"
    print "legislator_party: " + legislator_party
    match = re.search("(?:y suscrita )(?P<suscrita>.*)", legislator_party)
    print legislator_party
    if match:
        print case
        print "we got a match!"
        print legislator_party
        leg_match = re.search("(?P<legislator_party>.*?)(?:(,|;))", legislator_party)
        legislator_party = leg_match.group("legislator_party")
        suscrita = match.group("suscrita")
        print suscrita
    return legislator_party, suscrita

def get_legislator_gender(legislator_title):
    """Returns the gender from a legislator title. No inferences are made if
    the title is plural masculine (los)
    """
    legislator_gender = ""
    if re.search("^el *",legislator_title):
        legislator_gender = "male"
    elif re.search("^las? ",legislator_title):
        legislator_gender = "female"
    return legislator_gender

def legislator_edge_cases(case):
    """Returns legislator_names matches for various edge cases"""
    legislator_title,legislator_name,legislator_gender = "", "", ""
    case = strip_accents(case)
    edge_patterns = ["(?:Presentada por el )(Ejecutivo federal)(?:\. ?\n)",
                     "(?:Presentada por el )(Congreso del? .*)(?:\.)",
                     "(?:Enviada por la )(Camara de Senadores)(?:\.)",
                     "(?:Presentada por )(coordinadores de diversos grupos parlamentarios)(?:\.)"]
    for pattern in edge_patterns:
        match = re.search(pattern, case)
        if match:
            legislator_name = match.group(1)
            return legislator_title, legislator_name, legislator_gender
    #very general pattern for oddly formatted title, name
    pattern = "(Presentada|Enviad[oa] por )(?P<title>(el|la|los|las)? [\S]*) (?P<name>.*)\."
    match = re.search(pattern, case)
    if match:
        (legislator_title, legislator_name) = match.group('title','name')
        legislator_gender = get_legislator_gender(legislator_title)
        return legislator_title, legislator_name, legislator_gender
    return legislator_title, legislator_name, legislator_gender

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

def get_returned_to(case):
    """Provide a two lists for each 'Devuelta' line.
    The first is who the bill was returned to.
    The second is the article reference."""
    case = strip_accents(case)
    pattern_test = re.compile("Devuelta\n a la .*")
    pattern = re.compile("(?:Devuelta\n a la )"
                         "(?P<returned_to>.*?)"
                         "(?: para los efectos de lo dispuesto en el )"
                         "(?P<returned_to_article>.*?)"
                         "(?:\.)"
                         "(?: \(Minuta \n)?"
                         "(?P<returned_to_minutes>.*?\w)?\n,? ?"
                         "(?P<returned_to_minutes_date>.*\d)?"
                        )
    returned_matches = [m.groupdict() for m in pattern.finditer(case)]
    if returned_matches:
        returned_to, returned_to_article, returned_to_minutes, returned_to_minutes_date = [],[],[],[]
        #returned_to = returned_matches[0]['returned_to']
        #returned_to_article = returned_matches[0]['returned_to_article']
        
        for returned_match in returned_matches:
            returned_to.append(returned_match['returned_to'])
            returned_to_article.append(returned_match['returned_to_article'])
            returned_to_minutes.append(returned_match['returned_to_minutes'])
            returned_to_minutes_date.append(returned_match['returned_to_minutes_date'])
        
        # Clean up empty entries
        returned_to_minutes = [x for x in returned_to_minutes if x!=u'']
        returned_to_minutes_date = [x for x in returned_to_minutes_date if x!=u'']
        return returned_to, returned_to_article, returned_to_minutes, returned_to_minutes_date
    return None,None,None,None

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
    output_dir = os.path.abspath('output/parsed')
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)
    date = time.strftime("%Y%m%d")
    fieldnames = ['title',
                  'legislator_title',
                  'legislator_name',
                  'legislator_gender',
                  'legislator_party',
                  'suscrita',
                  'date_introduced',
                  'committees',
                  'outcome',
                  'floor_outcome',
                  'returned_to',
                  'returned_to_article',
                  'returned_to_minutes',
                  'returned_to_minutes_date',
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
