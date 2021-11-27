import os
import requests
from bs4 import BeautifulSoup
from selenium import webdriver
from selenium.webdriver.firefox.options import Options
from selenium.webdriver.firefox.service import Service
import argparse

results = {
    'conf': [],
    'jnl': [],
    'tsv': []
}

# Load search string
parser = argparse.ArgumentParser(description='Publication ranking search')
parser.add_argument('search_string', nargs='+', help='search string')
args = parser.parse_args()
search_value = '+'.join(args.search_string)

# Search Core
for publication_type in ['conf', 'jnl']:
    url = 'http://portal.core.edu.au/{}-ranks/?search={}&by=all&source=CORE2021&sort=atitle&page=1'.format(publication_type, search_value)
    response = requests.get(url)
    soup = BeautifulSoup(response.text, 'html.parser')
    table = soup.find('table')

    if table is None:
        continue
    headers = table.find('tr').find_all('b')
    headers = [header.text for header in headers]

    ranking_column = headers.index('Rank')
    title_column = headers.index('Title')
    acronym_column = headers.index('Acronym') if 'Acronym' in headers else None

    publications = table.find_all('tr', {'class':['oddrow', 'evenrow']})

    
    for publication in publications:
        row = publication.find_all('td')
        if 'National' in row[ranking_column].text:
            continue

        result = {}
        result['rank'] = row[ranking_column].text.strip()
        result['title'] = row[title_column].text.strip()
        if acronym_column is not None:
            result['title'] += ' (' + row[acronym_column].text.strip() + ')'
        results[publication_type].append(result)

# Search tsv
publication_type = 'tsv'
url = 'https://www.tsv.fi/julkaisufoorumi/haku.php?nimeke={}&konferenssilyh=&issn=&tyyppi=kaikki&kieli=&maa=&wos=&scopus=&nappi=Search'.format(search_value)
service = Service(os.path.dirname(os.path.abspath(__file__)) + os.sep + 'geckodriver.exe')
options = Options()
options.headless = True
driver = webdriver.Firefox(service=service, options=options)
driver.get(url)
html = driver.page_source
soup = BeautifulSoup(html, 'html.parser')
table = soup.find('div', {'id': "tulokset"})
divs = table.find_all('div')
for i in range(2, len(divs) - 2, 2):
    result = {
        'rank': divs[i].text.strip(),
        'title': divs[i + 1].text.strip()
    }
    results[publication_type].append(result)


# Print results
for publication_type in [('conf', 'Core Conference'), ('jnl', 'Core Journal'), ('tsv', 'Tsv.fi')]:
    print(publication_type[1] + ':')
    if len(results[publication_type[0]]) == 0:
        print('\tNo results')
    for publication in results[publication_type[0]]:
        print('\t' + publication['rank'] + ':\t' + publication['title'])
    print()