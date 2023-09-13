"""
This File does not affect/interact/depend on the rest of this project and was solely written to get the values in Constants.py
"""

import requests
from bs4 import BeautifulSoup as soup
import numpy as np


def extract_character_capacities_from_web() -> None:
    url: str = 'https://www.thonky.com/qr-code-tutorial/character-capacities'
    response = requests.get(url)
    html = soup(response.text, 'html.parser')
    table = html.find_all('tr')
    i: int = 0
    capacity_rows = []
    for row in table[2:]:
        data_row = row.find('td', {})
        if i % 4 == 0:
            capacity_rows.append([k.text for k in data_row.fetchNextSiblings()[1:]])
        else:
            capacity_rows.append([k.text for k in data_row.fetchNextSiblings()])
        i += 1
    capacity_table: list[list[list[int]]] = [[[0] * (len(capacity_rows) // 4) for _ in range(4)] for _ in range(4)]
    for m in range(4):
        for i in range(4):
            for idx, item in enumerate(capacity_rows[m::4]):
                capacity_table[i][m][idx] = item[i]

    for m in capacity_table:
        for ec in m:
            print(str(ec).replace("'", "", -1))
    print()
    print("#" * 50)
    print()

    for k in range(4):
        for j, i in enumerate(np.array(capacity_table).T):
            print(f'''{j + 1}:{str(list(i[k])).replace("'", "", -1)},''')
        print()


def get_total_data_codewords_from_web():
    url: str = 'https://www.thonky.com/qr-code-tutorial/error-correction-table'
    response = requests.get(url)
    html = soup(response.text, 'html.parser')
    table = html.find_all('tr')

    for row in table[2:]:
        data_row = row.find('td', {})
        print(f'\'{data_row.text}\': {data_row.fetchNextSiblings()[0].text},')


def get_total_codewords_from_web():
    url: str = 'https://www.thonky.com/qr-code-tutorial/error-correction-table'
    response = requests.get(url)
    html = soup(response.text, 'html.parser')
    table = html.find_all('tr')

    for row in table[2:]:
        data_row = row.find('td', {})
        print(f'\'{data_row.text}\': {data_row.fetchNextSiblings()[-1].text.split("=")[-1]},')


def zero_if_empty(s: str) -> str:
    return '0' if s == '' else s


def get_codewords_and_block_info():
    url: str = 'https://www.thonky.com/qr-code-tutorial/error-correction-table'
    response = requests.get(url)
    html = soup(response.text, 'html.parser')
    table = html.find_all('tr')

    for row in table[2:]:
        data_row = row.find('td', {})
        nxt_siblings = data_row.fetchNextSiblings()
        print(
            f'\'{data_row.text.replace("-", "")}\': '
            f'({nxt_siblings[0].text.strip()},'
            f' {nxt_siblings[1].text.strip()},'
            f' {nxt_siblings[2].text.strip()},'
            f' {nxt_siblings[3].text.strip()},'
            f' {zero_if_empty(nxt_siblings[4].text).strip()},'
            f' {zero_if_empty(nxt_siblings[5].text).strip()}),'
        )


# extract_character_capacities_from_web()
# get_total_data_codewords_from_web()
# get_total_codewords_from_web()
get_codewords_and_block_info()
