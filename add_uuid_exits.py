from selenium import webdriver
import configparser
import pandas as pd
from libs import *
from tqdm.auto import tqdm

ROOT_REPORT = 'Отчеты\\'

config = configparser.ConfigParser()
config.read('passwords.ini')

browser = webdriver.Chrome()
browser, session = login_rnis(browser, config['РНИС админ'])

start_date = pd.to_datetime('2021-06-01')
end_date = pd.to_datetime('2021-06-09')

file_path = ROOT_REPORT + f"Свод_{start_date.strftime(r'%Y.%m.%d')}-{end_date.strftime(r'%Y.%m.%d')}.xlsx"
df = pd.read_excel(file_path, dtype=str)
df['Дата'] = pd.to_datetime(df['Дата'], dayfirst=True).dt.strftime(r'%d.%m.%Y')
df['Рейсы % выполнения'] = df['Рейсы % выполнения'].astype(float)
df = df[df['Рейсы % выполнения'] < 1]

orders_info = []
check_list = df[['Дата', 'Рег.номер маршрута']].drop_duplicates()
for _, row in tqdm(check_list.iterrows(), total=check_list.shape[0]):
    day = pd.to_datetime(row['Дата'], dayfirst=True)
    route_number = row['Рег.номер маршрута']
    
    temp = get_list_orders(session, route_number, day, day)
    temp = pd.DataFrame(temp, dtype=str)
    if 'date' in temp.columns:
        temp['Дата'] = pd.to_datetime(temp['date']).dt.strftime(r'%d.%m.%Y')
        temp['Выход'] = temp['turn']
        temp['Рег.номер маршрута'] = route_number
        orders_info.append(temp)
orders_info = pd.concat(orders_info)

df = df.merge(orders_info[['Дата', 'Рег.номер маршрута', 'Выход', 'uuid', 'processing_status']], 
              on=['Дата', 'Рег.номер маршрута', 'Выход'], how='left')
df['Ссылка на план-наряд'] = 'https://rnis.mosreg.ru/kiutr-control/orders/' + df['uuid']
df['Ссылка на план-наряд'] = df['Ссылка на план-наряд'].apply(make_hyperlink)
file_path = ROOT_REPORT + f"Свод_{start_date.strftime(r'%Y.%m.%d')}-{end_date.strftime(r'%Y.%m.%d')}_ссылки.xlsx"
df.to_excel(file_path)
browser.close()