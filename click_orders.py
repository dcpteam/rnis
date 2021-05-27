from selenium import webdriver
from selenium.webdriver.chrome.options import Options
import configparser
import pandas as pd
from libs import *
from tqdm.auto import tqdm

ROOT_REPORT = 'Отчеты\\'

config = configparser.ConfigParser()
config.read('passwords.ini')

start_date = pd.to_datetime('2021-05-18')
end_date = pd.to_datetime('2021-05-23')

file_path = ROOT_REPORT + f"Свод_{start_date.strftime(r'%Y.%m.%d')}-{end_date.strftime(r'%Y.%m.%d')}_ссылки.xlsx"
df = pd.read_excel(file_path, dtype=str)
print(df.shape[0])

log_path = ROOT_REPORT + 'log.txt'
if os.path.exists(log_path):
    log = open(log_path, 'r').read().split('\n')
    df = df[~df['uuid'].isin(log)]
    print(df.shape[0])

chrome_options = Options()
# chrome_options.add_argument("--headless")
browser = webdriver.Chrome(options=chrome_options)
browser, session = login_rnis(browser, config['РНИС админ'])

with open(log_path, 'a') as log_file:
    for _, row in tqdm(df.iterrows(), total=df.shape[0]):
        if row['processing_status'] == 'ended':
            click_checkboxs(browser, f"https://rnis.mosreg.ru/kiutr/orders/{row['uuid']}")
            log_file.write(row['uuid'] + '\n')
