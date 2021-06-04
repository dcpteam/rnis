from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import configparser
import pandas as pd
from libs import *
from tqdm.auto import tqdm
from multiprocessing.dummy import Pool
import numpy as np
from glob import glob
from secrets import token_hex
import time
from random import randint

def clicker(df):
    time.sleep(randint(1, 60))
    log_path = ROOT_REPORT + f'log_{token_hex()}.txt'
    chrome_options = Options()
    chrome_options.add_argument('log-level=3')
    chrome_options.add_argument("--headless")
    browser = webdriver.Chrome(options=chrome_options)
    browser, session = login_rnis(browser, config['РНИС админ'])

    with open(log_path, 'a') as log_file:
        for _, row in tqdm(df.iterrows(), total=df.shape[0]):
            if row['processing_status'] == 'ended':
                result = click_checkboxs(browser, f"https://rnis.mosreg.ru/kiutr/orders/{row['uuid']}")
                if result:
                    log_file.write(row['uuid'] + '\n')
    browser.close()

ROOT_REPORT = 'Отчеты\\'

config = configparser.ConfigParser()
config.read('passwords.ini')

start_date = pd.to_datetime('2021-05-01')
end_date = pd.to_datetime('2021-05-31')

file_path = ROOT_REPORT + f"Свод_{start_date.strftime(r'%Y.%m.%d')}-{end_date.strftime(r'%Y.%m.%d')}_ссылки.xlsx"
df = pd.read_excel(file_path, dtype=str)
df = df[df['processing_status'] == 'ended']
df = df.drop_duplicates(subset=['uuid'])
print(df.shape[0])

log_files = glob(ROOT_REPORT + 'log*.txt')
log_list =[open(file, 'r').read().split('\n') for file in log_files]
log = [item for sublist in log_list for item in sublist]

df = df[~df['uuid'].isin(log)]
print(df.shape[0])

n_workers = 3
array_df = np.array_split(df, n_workers)

pool = Pool(n_workers)
pool.map(clicker, array_df)
pool.close()
pool.join()
