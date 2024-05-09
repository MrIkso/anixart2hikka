#!/usr/bin/env python
import argparse
import csv
import re
import sys

import requests

HIKKA_API = "https://hikka.io/api"

success_added_count: int = 0
flied_added_count: int = 0


class AnixartDataModel:
    def __init__(self, anime_index, anime_rus_title, anime_orig_title, anime_alt_title, is_fav, watch_status, rate):
        self.anime_index = anime_index
        self.anime_rus_title = anime_rus_title
        self.anime_orig_title = anime_orig_title
        self.anime_alt_title = anime_alt_title
        self.is_fav = is_fav
        self.watch_status = watch_status
        self.rate = rate


def send_get_request(url, params=None):
    response = requests.get(url, params=params)
    return response


def send_post_request(url, params=None, data=None):
    response = requests.post(url, params=params, data=data)
    return response

def is_json_key_present(json, key):
    try:
        buf = json[key]
    except KeyError:
        return False

    return True

def main(argv):
    parser = argparse.ArgumentParser(formatter_class=argparse.RawDescriptionHelpFormatter,
                                     description='anixart2hikka - конвертер закладок з Anixart на сайт hikka.io')
    parser.add_argument('--csv_file', type=str, help="Шлях до файлу csv")
    parser.add_argument('--token', type=str, help="Введіть ваш token з сайту hikka.io")

    opts = parser.parse_args(argv)
    start_convert(opts.csv_file, opts.token)


def start_convert(file, token):
    print(file, token)
    data_model = read_csv(file)

    for item in data_model:
        search_and_add_to_list(item, token)

    print(f"Успішно додано: {success_added_count}, не вдалося додати: {flied_added_count}")


def search_and_add_to_list(item: AnixartDataModel, token):
    global success_added_count, flied_added_count

    print(f"Шукаємо: {item.anime_orig_title}/{item.anime_rus_title}")
    # Параметри запиту (query parameters)
    query_params = {
        'size': '30'
    }

    headers = {
        "auth": f"{token}",
    }
    search_data = {
        "query": f"{fix_title(item.anime_orig_title)}"
    }

    # sending post request and saving response as response object
    search_request = requests.post(f"{HIKKA_API}/anime", params=query_params, json=search_data)

    json_data = search_request.json()

    # print(json_data)

    if is_json_key_present(json_data, 'list'):
        json_list = json_data.get('list')
        if json_list:
            # беремо перший елемент з пошуку і беремо його slug
            hikka_slug = json_list[0]["slug"]
            print(f"Знайдено: {hikka_slug}")

            watch_data = {
                "note": "",
                "episodes": 0,
                "rewatches": 0,
                "score": convert_anixart2hikka_score(item.rate),
                "status": f"{convert_anixart2hikka_status(item.watch_status)}"
            }

            requests.put(f"{HIKKA_API}/watch/{hikka_slug}", headers=headers, json=watch_data)
            success_added_count += 1
        else:
            print(f"Аніме за назвою: {item.anime_orig_title}/{item.anime_rus_title} не було знайдено! Ви можете "
                      f"знайти його на сайті вручну, та додати самотушки")
            flied_added_count += 1
    else:
        print(f"Аніме за назвою: {item.anime_orig_title}/{item.anime_rus_title} не було знайдено! Ви можете "
              f"знайти його на сайті вручну, та додати самотушки")
        flied_added_count += 1


# читаємо файл закладок і конветруємо його в модель @AnixartDataModel
def read_csv(file):
    data_list = []
    with open(file, newline='', encoding='utf-8-sig') as csvfile:
        reader = csv.reader(csvfile)
        for row in reader:
            if not row or row[0].startswith('#'):
                continue  # Пропустити порожні рядки або рядки з коментарями
            model = AnixartDataModel(row[0], row[1], row[2], row[3], row[4], row[5], row[6])
            data_list.append(model)

    return data_list


# "completed" "watching" "planned" "on_hold" "dropped"
def convert_anixart2hikka_status(status: str):
    if "Не смотрю" in status:
        return "on_hold"
    elif "Смотрю" in status:
        return "watching"
    elif "В планах" in status:
        return "planned"
    elif "Просмотрено" in status:
        return "completed"
    elif "Отложено" in status:
        return "on_hold"
    elif "Брошено" in status:
        return "dropped"


def fix_title(title: str):
    pattern = r'TV-(\d+)'
    return re.sub(pattern, r'Season \1', title)


def convert_anixart2hikka_score(rating: str):
    current_rating = get_rating(rating)
    if current_rating != 0:
        return current_rating * 2
    return 0


def get_rating(rating_str):
    # Регулярний вираз для пошуку оцінки
    pattern = r'(\d+)\s+из\s+(\d+)'

    # Пошук оцінки за допомогою регулярного виразу
    match = re.search(pattern, rating_str)

    # Отримання значень оцінки
    if match:
        rating = int(match.group(1))  # Оцінка "X"
        total_rating = int(match.group(2))  # Загальна оцінка "Y"
        print(f"Оцінка: {rating}, Загальна оцінка: {total_rating}")
        return rating
    else:
        return 0


if __name__ == '__main__':
    main(sys.argv[1:])
