from selenium import webdriver
import configparser
import pandas as pd
import time
import xlrd
from libs import *


config = configparser.ConfigParser()
config.read('passwords.ini')

browser = webdriver.Chrome()
browser, session = login_rnis(browser, config['РНИС отчеты'])

start_date = pd.to_datetime('2021-05-18')
end_date = pd.to_datetime('2021-05-23')

routes = pd.read_excel('Маршруты.xlsx', dtype=str)
routes = routes.iloc[:2]

report_list = []
for _, row in routes.iterrows():
    carrier = get_carrier(session, row['Предприятие'])
    route = get_route(session, carrier, row['Рег. №'])
    filename = f"Итоговый отчет_{row['Предприятие']}_{row['Рег. №']}_{start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')}.xls"
    report_list.append({'name': filename, 'carrier_uuid': carrier['uuid'], 'route_uuid': route['uuid']})
    r = generation_report(session, carrier, route, start_date, end_date)
    if r['success'] == False:
        print('Ошибка генерации отчета', r['errors'])
    time.sleep(1)
time.sleep(10)

file_list = []
while report_list:
    items = get_report_list(session)['payload']['items']
    for report in report_list:
        filter_report = list(filter(lambda item: (item['parameters']['units']['value'] == report['carrier_uuid']) & 
            (item['parameters']['route']['value'] == report['route_uuid']), items))[0]
        if filter_report['status'] == 'done':
            file_list.append(download_report(session, filter_report, report['name']))
            report_list.remove(report)
        time.sleep(5)

df = []
for file in file_list:
    workbook = xlrd.open_workbook(file, ignore_workbook_corruption=True)
    excel = pd.read_excel(workbook, skiprows=[0,1,2,3,5], skipfooter=1, dtype=str)
    df.append(excel)
df = pd.concat(df, ignore_index=True)
df = df.iloc[:, :9]
df[r'№\nп.п.'] = range(len(df))
file_path = f"Свод_{start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')}.xlsx"
df.to_excel(file_path, index=False)
print('Сохранен', file_path)