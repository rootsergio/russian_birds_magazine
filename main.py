import datetime
import re
import json
from typing import TypedDict

import requests

from config import API_KEY, CHAT_ID
from logger import logger


class Issue(TypedDict):
    id: int
    name: str
    year: int


class Article(TypedDict):
    link: str
    name: str
    authors: list[str]
    year: int


def read_last_issue_id() -> int:
    with open('last_issue_id.txt', 'r') as file:
        last_issue = int(file.read())
    return last_issue


def get_issues() -> list[Issue]:
    """
    Получает список всех выпусков журнала
    """
    response = requests.get("https://cyberleninka.ru/journal/n/russkiy-ornitologicheskiy-zhurnal")
    text = response.text
    reg = re.compile('issues: (\[.*\])')
    issues = re.findall(reg, text)
    if issues:
        issues = json.loads(issues[0])
    return issues


def check_new_issue(issues: list[Issue], last_issue_id: int) -> Issue:
    last_issue = issues[-1]
    if last_issue["id"] != last_issue_id:
        return last_issue


def get_articles(issue: Issue) -> list[Article]:
    response = requests.get(f"https://cyberleninka.ru/api/issue/{issue['id']}/articles")
    return response.json()


def build_messages(articles: list[Article], issue: Issue) -> str:
    name = issue["name"]
    msg = f"""*Доступен новый выпуск журнала.*
[{name}](https://cyberleninka.ru/journal/n/russkiy-ornitologicheskiy-zhurnal?i={issue['id']})  

"""
    for article in articles:
        authors = ', '.join(article["authors"])
        if len(article["authors"]) == 1:
            authors = f"Автор: {authors}"
        else:
            authors = f"Авторы: {authors}"
        read_link = f"https://cyberleninka.ru/{article['link']}/viewer"
        msg += f"""*{article["name"]}*
{authors}
[читать]({read_link})  

"""
    return msg


def send_msg_tlg(msg: str):
    url = (f"https://api.telegram.org/bot{API_KEY}/sendMessage?"
           f"chat_id={CHAT_ID}"
           f"&text={msg}"
           f"&parse_mode=Markdown"
           f"&disable_web_page_preview=true")
    print(requests.get(url).json())


def write_last_issue_id(issue_id: int):
    with open('last_issue_id.txt', 'w') as file:
        file.write(str(issue_id))


if __name__ == '__main__':
    logger.info(f"{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}: Проверка обновлений журнала")
    last_issue_id = read_last_issue_id()
    issues = get_issues()
    new_issue = check_new_issue(issues, last_issue_id)
    if not new_issue:
        logger.info("Обновления не обнаружены")
    else:
        articles = get_articles(new_issue)
        messages = build_messages(articles, new_issue)
        send_msg_tlg(messages)
        write_last_issue_id(new_issue["id"])
        logger.info("Обновления получены")
