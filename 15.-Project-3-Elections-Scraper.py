
import requests
from bs4 import BeautifulSoup as BS
import csv
import sys
import os
import unicodedata

URL = 'https://volby.cz/pls/ps2017nss/ps3?xjazyk=CZ'
payload = {'area':None,
           'municipality': None}


def parse_command_line():
    while True:
        if len(sys.argv) != 3:
            print('Not correct number of arguments (2)')
            break
        else:
            arg = sys.argv[1:]
            count = 0
            for k, v in payload.items():
                payload[k] = arg[count]
                count += 1
            return payload


def scrape_area():
    parsed_command_line = parse_command_line()
    r = requests.get(URL)
    soup = BS(r.text, 'html.parser')
    result_town = None
    for table in soup.find_all('table'):
        for child in filter(lambda x:x != '\n', table.children):
            for info in filter(lambda x:x != '\n', child):
                if info.string == parsed_command_line['area']:
                    result_town = child

    result_town_list = [i for i in filter(lambda x:x != '\n', result_town)]
    area_link = result_town_list[-1].find('a').get('href')
    area_url = "/".join(URL.split("/")[:-1]) + "/" + area_link
    return area_url


def scrape_municipality_url_id_name(scrape_area, parse_command_line):
    parsed_command_line = parse_command_line
    r = requests.get(scrape_area)
    soup = BS(r.text, 'html.parser')
    result_municipality = None
    for table in soup.find_all('table'):
        for child in filter(lambda x: x != '\n', table.children):
            for info in filter(lambda x: x != '\n', child):
                if info.string == parsed_command_line['municipality']:
                    result_municipality = child

    result_municipality_list = [i for i in filter(lambda x: x != '\n', result_municipality)]
    municipality_id = result_municipality_list[0].string
    municipality_name = result_municipality_list[1].string
    municipality_link = result_municipality_list[0].find('a').get('href')
    municipality_url = "/".join(URL.split("/")[:-1]) + "/" + municipality_link

    return [municipality_url, municipality_id, municipality_name]


def scrape_election_tables(scrape_municipality_url_id_name):
    scrape_municipality = scrape_municipality_url_id_name
    r =requests.get(scrape_municipality[0])
    soup = BS(r.text, 'html.parser')
    voters = []
    tables = []
    for table in soup.find_all('table'):
        tables.append(table)

    for row in filter(lambda x:x != '\n', tables[0].children):
        try:
            voters_in_the_list = row.find('td', {'class': 'cislo', 'headers':'sa2'}).string
            voters_in_the_list = unicodedata.normalize("NFKD", str(voters_in_the_list))
            distributed_voting_envelopes = row.find('td', {'class': 'cislo', 'headers':'sa3'}).string
            distributed_voting_envelopes = unicodedata.normalize("NFKD", str(distributed_voting_envelopes))
            valid_votes = row.find('td', {'class': 'cislo', 'headers':'sa6'}).string
            valid_votes = unicodedata.normalize("NFKD", str(valid_votes))
            voters.extend([voters_in_the_list, distributed_voting_envelopes,valid_votes])
        except:
            pass
    scrape_municipality.extend(voters)
    return scrape_municipality


def scrape_election_parties(scrape_municipality_url_id_name):
    scrape_municipality = scrape_municipality_url_id_name
    r = requests.get(scrape_municipality[0])
    soup = BS(r.text, 'html.parser')
    tables = []
    for table in soup.find_all('table'):
        tables.append(table)
    result_str = ''
    for table in tables[1:]:
        for row in filter(lambda x:x != '\n', table.children):
            for i in filter(lambda x:x != '\n', row.find_all('td')):
                try:
                    result_str += i.string + '; '
                except:
                    pass
            result_str += ' | '
    return result_str

def format_table(scrape_election_tables, scrape_election_parties):
    header = ['municipality code', 'name of location', 'voters in the list', 'distributed voting envelopes',
              'valid votes']
    formated_header = []
    formated_data = []
    table = scrape_election_tables
    dic = {}
    results = [char for char in scrape_election_parties.split(' | ') if char != '']
    results = [char.split(';') for char in results]
    for i in results:
        dic[i[1]] = [i[2] + ' voters', i[3] + ' %']
    for k,v in dic.items():
        header.append(k)
    for char in header:
        formated_data.append(len(char)+20)
        formated_header.append('{:^{w}}'.format(char, w=len(char)+20))
    formated_header = '|'+'|'.join(formated_header)+ '|'

    count = 5
    formated_results = 5 * ' ' + sum(formated_data[0:5]) * ' ' + ' '
    for k,v in dic.items():
        len_v = ''
        for i in v:
            len_v += i + ';'
        len_v = len_v.rstrip(';')
        width = formated_data[count]+1
        len_v = '{:^{w}}'.format(len_v, w=width)
        formated_results += len_v
        '|'.join(formated_results)
        count +=1
    formated_table = [[formated_header], [formated_results]]
    return formated_table

def write_election_table(format_table):
    mode = 'a' if 'elections_results.csv' in os.listdir() else 'w'
    with open('elections_results.csv', mode) as file:
        writer = csv.writer(file)
        writer.writerows(format_table)

def main():
    parsed_line = parse_command_line()
    scrape_municipality = scrape_municipality_url_id_name(scrape_area(), parsed_line)
    election_parties = scrape_election_parties(scrape_municipality)
    election_tables = scrape_election_tables(scrape_municipality)
    formatted_table = format_table(election_tables, election_parties)
    write_election_table(formatted_table)

main()