from selenium import webdriver
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.common.by import By
from selenium.webdriver.support.ui import WebDriverWait
from selenium.webdriver.support import expected_conditions as EC
import requests
import pandas as pd
import os


def login_rnis(browser, user_config):
    """Функция залогинивается в РНИС с заданными логином и паролем.
    """
    browser.get('https://rnis.mosreg.ru')
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="root"]/div/form/div[1]/input')))
    browser.find_element_by_xpath('//*[@id="root"]/div/form/div[1]/input').send_keys(user_config['login'])
    browser.find_element_by_xpath('//*[@id="root"]/div/form/div[2]/div/input').send_keys(user_config['password'])
    browser.find_element_by_xpath('//*[@id="root"]/div/form/a').click()
    WebDriverWait(browser, 10).until(EC.presence_of_element_located((By.XPATH, '//*[@id="Home"]')))
    # Для чистых запросов
    session = requests.Session()
    cookies = browser.get_cookies()
    for cookie in cookies:
        session.cookies.set(cookie['name'], cookie['value'])
    return browser, session


def get_carrier(session, name):
    """Функция находит объект организации из РНИС по названию.
    """
    data = {"headers": {"meta": {"filters": {"withComponent": "kiutr"}, "search": name, "pagination": {
        "page": 1, "limit": 50}}, "token": session.cookies['token']}, "payload": {}}
    r = session.post(
        'https://api.rnis.mosreg.ru/ajax/request?com.rnis.organizational_units.action.units', json=data).json()
    return r['payload']['items'][0]


def get_route(session, carrier, number):
    """Функция находит по объекты организации и номеру маршрута маршрут из РНИС.
    """
    data = {'headers': {'meta': {'filters': {'withComponent': 'kiutr',
                                             'withCarriers': [carrier['uuid']]},
                                 'search': str(number),
                                 'pagination': {'page': 1, 'limit': 50}},
                        'token': session.cookies['token']},
            'payload': {}}
    r = session.post('https://api.rnis.mosreg.ru/ajax/request?com.rnis.geo.action.route.list.short', json=data).json()
    return r['payload']['items'][0]


def generation_report(session, carrier, route, start_date, end_date):
    """Функция отправляет задание на формирование отчета по заданным объектам организации, маршрута и дат.
    """
    data = {'headers': {'meta': {}, 'token': session.cookies['token']},
             'payload': {'report': {'name': 'Итоговый отчет о работе выходов по маршруту (общие показатели)',
               'uri': 'summary_route_turns_report'},
              'parameters': {'items': [{'name': 'Начало отчетного периода',
                 'type': 'singleValueDate',
                 'key': 'date_from',
                 'value': start_date.strftime(r'%Y-%m-%d'),
                 'required': True,
                 'placeholder': ''},
                {'name': 'Время начала отчетного периода',
                 'type': 'singleValueTime',
                 'key': 'time_from',
                 'value': '00:00',
                 'required': True,
                 'placeholder': ''},
                {'name': 'Конец отчетного периода',
                 'type': 'singleValueDate',
                 'key': 'date_to',
                 'value': end_date.strftime(r'%Y-%m-%d'),
                 'required': True,
                 'placeholder': ''},
                {'name': 'Время конца отчетного периода',
                 'type': 'singleValueTime',
                 'key': 'time_to',
                 'value': '23:59',
                 'required': True,
                 'placeholder': ''},
                {'name': 'Перевозчики',
                 'type': 'multiSelectAsync',
                 'key': 'units',
                 'required': True,
                 'options': {'subject': 'com.rnis.organizational_units.action.units',
                  'labelKey': 'name',
                  'valueKey': 'uuid',
                  'filters': {'withComponent': 'kiutr'},
                  'model': 'App\\Model\\Unit',
                  'service': 'organizational_units'},
                 'placeholder': '',
                 'value': carrier['uuid']},
                {'name': 'Номер/регистрационный номер маршрута',
                 'type': 'singleSelectAsync',
                 'key': 'route',
                 'required': True,
                 'options': {'subject': 'com.rnis.geo.action.route.list.short',
                  'labelKey': ['number', 'registration_number', 'title'],
                  'valueKey': 'uuid',
                  'filters': {'withComponent': 'kiutr', 'withCarriers': '%units%'},
                  'model': 'App\\Model\\Route',
                  'service': 'geo'},
                 'placeholder': '',
                 'value': route['uuid']},
                {'name': 'Выходы',
                 'type': 'multiSelect',
                 'key': 'turns',
                 'required': False,
                 'options': {'options': []},
                 'placeholder': '',
                 'value': ''},
                {'name': 'Вид сообщения',
                 'type': 'singleSelect',
                 'key': 'transport_connection_type',
                 'required': False,
                 'options': {'options': [None]},
                 'placeholder': ''}]},
              'report_template_uuid': None,
              'create_template': False,
              'template_name': ''}}
    r = session.post('https://api.rnis.mosreg.ru/ajax/request?com.rnis.reports.action.report.create', json=data).json()
    return r


def get_report_list(session):
    """Функция получает список текущих отчетов - в процессе формирования и сформированные.
    """
    data = {'headers': {'meta': {'filters': {},
           'order': {'column': 'created_at', 'direction': 'desc'},
           'search': '',
           'pagination': {'page': 1, 'limit': 100}},
          'token': session.cookies['token']},
         'payload': {}}
    r = session.post('https://api.rnis.mosreg.ru/ajax/request?com.rnis.reports.action.document.list', json=data).json()
    return r


def download_report(session, item, name=None):
    """Функция скачивет отчет по объекту из функции get_report_list.
    """
    uuid = item['uuid']
    report_name = item['report_name']
    created_at = pd.to_datetime(item['created_at'])
    if not name:
        name = report_name + '_' + created_at.strftime('%d-%m-%Y_%H-%M-%S') + '.xls'
    # file_path = os.path.expanduser('~\\Downloads\\') + name
    file_path = 'Отчеты\\' + name
    payload = {'uuid': uuid, 'format': 'xls', 'name': name}
    file = session.get('https://api.rnis.mosreg.ru/ajax/download_report', params=payload)
    with open(file_path, 'wb') as f:
        f.write(file.content)
    print('Сохранен', file_path)
    return file_path


def click_checkboxs(browser, order_url):
    """Функция прокликивает все рейсы в одном наряде.
    """
    def _click(browser):
        """Функция кликает все чекбоксы на текущей странице.
        """
        try:
            checkboxs = browser.find_elements_by_xpath('//div[@class="snake-info__checkbox"]')
            for box in checkboxs:
                if box.text == 'Незачет':
                    box.click()
        except EC.StaleElementReferenceException:
            _click(browser)
    def _save(browser):
        """Функция обрабатывает сохранение изменений.
        """
        browser.find_element_by_xpath('//div[@class="b-modal__header-link _save"]').click()
        result = WebDriverWait(browser, 100).until(
            lambda driver: driver.find_element(By.XPATH, '//div[@class="changes changes-in-order changes-success"]') or\
                   driver.find_element(By.XPATH, '//div[@class="changes changes-in-order changes-fail"]'))
        if result.text == 'Изменения не сохранены':
            print('Повторное сохранение')
            _save(browser)
    browser.get(order_url)
    WebDriverWait(browser, 20).until(EC.presence_of_element_located((By.XPATH, '//div[@class="accordion__item"]')))
    _click(browser)
    _save(browser)


def get_list_orders(session, route_number, start_date, end_date):
    """Функция получает список всех выходов для определенного маршрута.
    """
    payload = {'headers': {'meta': {'pagination': {'page': 1, 'limit': 100},
               'order': {'column': 'date', 'direction': 'desc'},
               'filters': {'withRouteRegNumbers': [route_number],
                'withComponent': 'kiutr',
                'short': True,
                'withPeriod': [f'{start_date.strftime("%Y-%m-%d")}T00:00:00+03:00', f'{end_date.strftime("%Y-%m-%d")}T00:00:00+03:00']},
               'response_data': ['items/uuid',
                'items/number',
                'items/unit_uuid',
                'items/carrier_uuid',
                'items/date',
                'items/updated_at',
                'items/turn',
                'items/is_opened',
                'items/shifts/runs/route_name',
                'items/shifts/runs/route_number',
                'items/shifts/runs/route_registration_number',
                'items/shifts/runs/vehicle_state_number',
                'items/shifts/runs/driver_name',
                'items/order_recalc/shifts/runs/vehicle_state_number',
                'items/order_recalc/shifts/runs/driver_name',
                'items/processing_status',
                'items/provision_status',
                'items/provision_status_data',
                'items/execution_status',
                'items/is_proceeding',
                'items/is_additional',
                'items/is_calc_ended',
                'items/capacity_type_uuids',
                'items/route_kind_uuid',
                'items/shifts/runs/capacity',
                'items/release_years']},
              'token': session.cookies['token']},
             'payload': {}}
    r = session.post('https://api.rnis.mosreg.ru/ajax/request?com.rnis.geo.action.order.list', json=payload).json()
    return r['payload']['items']


def get_order_info(session, uuid_order):
    """Функция получает подробную информацию по наряду.
    """
    payload = {'headers': {'meta': {},
        'token': session.cookies['token']},
        'payload': {'uuid': uuid_order}}
    r = session.post('https://api.rnis.mosreg.ru/ajax/request?com.rnis.geo.action.order.get', json=payload).json()
    return r