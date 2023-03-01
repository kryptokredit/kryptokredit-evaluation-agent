import requests
import config
import time

from dotenv import load_dotenv
import os
load_dotenv()


def pull_from_graph(wallet_address, query):
    url = "https://api.thegraph.com/subgraphs/name/luiscmogrovejo/test-krypto-kredit"

    with open('./queries/{}.graphql'.format(query), 'r') as f:
        query = f.read()

    query = query % ("payer_value")
    response = requests.post(url, json={'query': query})

    return response.json()

def fetch_invoice_payments(wallet_address):
    json = pull_from_graph(wallet_address, 'payments_query')
    print(json)



def fetch_derogatory_marks(wallet_address):
    json = pull_from_graph(wallet_address, 'derogetory_marks_query')
    print(json)


def fetch_credit_score(wallet_address):
    url = f"https://api.spectral.finance/api/v1/addresses/{wallet_address}"
    authorization = "Bearer " + os.getenv('spectral')
    headers = {"Authorization": authorization}

    print('Fetching MACRO score...')
    response = requests.get(url, headers=headers)
    if response.status_code == 200:
        data = response.json()
        macro_score = data["score"]
        print(f"MACRO score: {macro_score}")
        return macro_score
    elif response.status_code == 404:
        print(f"Request failed with status code: {response.status_code}")
        print(f"Attempting to generate credit score...")
        generate_credit_score(wallet_address)
        return -1
    else:
        print(f"Request failed with status code: {response.status_code}")
        return -1


def generate_credit_score(wallet_address):
    url = f"https://api.spectral.finance/api/v1/addresses/{wallet_address}/calculate_score"
    authorization = "Bearer " + os.getenv('spectral')
    headers = {"Authorization": authorization}
    response = requests.post(url, data={}, headers=headers)

    if response.status_code == 200:
        print(f"MACRO score scheduled...try again in 15 seconds")
    else:
        print(f"Request failed with status code: {response.status_code}")
