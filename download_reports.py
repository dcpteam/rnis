from selenium import webdriver
import configparser
import pandas as pd
import time
import xlrd
from libs import *
from tqdm.auto import tqdm

ROOT_REPORT = 'Отчеты\\'

config = configparser.ConfigParser()
config.read('passwords.ini')

browser = webdriver.Chrome()
browser, session = login_rnis(browser, config['РНИС отчеты'])

start_date = pd.to_datetime('2021-05-01')
end_date = pd.to_datetime('2021-05-31')

routes = pd.read_excel('Маршруты.xlsx', dtype=str)

report_list = []
for _, row in tqdm(routes.iterrows(), total=routes.shape[0]):
    carrier = get_carrier(session, row['Предприятие'])
    route = get_route(session, carrier, row['Рег. №'], row['Номер'])
    filename = f"Итоговый отчет_{row['Предприятие']}_{row['Рег. №']}_{start_date.strftime('%Y.%m.%d')}-{end_date.strftime('%Y.%m.%d')}.xls"
    report_list.append({'name': filename, 'carrier_uuid': carrier['uuid'], 'route_uuid': route['uuid']})
    r = generation_report(session, carrier, route, start_date, end_date)
    if r['success'] == False:
        print('Ошибка генерации отчета', r['errors'])
    time.sleep(1)
time.sleep(5)

def _filter_item(item, report):
    if (item['report_uri'] == 'summary_route_turns_report') and ('route' in item['parameters']):
        return (item['parameters']['units']['value'] == report['carrier_uuid']) & \
        (item['parameters']['route']['value'] == report['route_uuid'])
    else:
        return False

file_list = []
while report_list:
    items = get_report_list(session)['payload']['items']
    for report in report_list:
        filter_report = list(filter(lambda item: _filter_item(item, report), items))[0]
        if filter_report['status'] == 'done':
            file_list.append(download_report(session, filter_report, report['name']))
            report_list.remove(report)
        time.sleep(5)

df = []
for file in file_list:
    try:
        workbook = xlrd.open_workbook(file, ignore_workbook_corruption=True)
        excel = pd.read_excel(workbook, skiprows=[0,1,2,3,5], skipfooter=1)
    except xlrd.biffh.XLRDError:
        excel = pd.read_html(file)[0]
        excel.columns = excel.columns.get_level_values(4)
        excel = excel.iloc[:-1]
    df.append(excel)
df = pd.concat(df, ignore_index=True)
df = df.iloc[:, 1:9]
df['Дата'] = pd.to_datetime(df['Дата'], dayfirst=True).dt.date
df.insert(0, '№п.п.', range(len(df)))
df['Рейсы % выполнения'] = df['Рейсы % выполнения'].astype(float)
file_path = ROOT_REPORT + f"Свод_{start_date.strftime(r'%Y.%m.%d')}-{end_date.strftime(r'%Y.%m.%d')}.xlsx"
df.to_excel(file_path, index=False)
print('Сохранен', file_path)
browser.close()