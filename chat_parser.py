import logging
import asyncio
from telethon import TelegramClient
import datetime
from telethon.tl.types import Channel
import argparse
import requests
import string
import aiohttp
import random
from bs4 import BeautifulSoup
import logging
import asyncio
from aiohttp_socks import ProxyConnector


parser = argparse.ArgumentParser()
parser.add_argument("--urls", nargs="+", type=str)
parser.add_argument("--name", type=str)
parser.add_argument("--hostIp", help="Host IP address")


args = parser.parse_args()
print(args.hostIp)

api_id = 21545783
api_hash = "389839339699f6a919ac6ead583df8fa"
session_name = "app/session.session"
queryKey = [
    "а",
    "б",
    "в",
    "г",
    "д",
    "е",
    "ё",
    "ж",
    "з",
    "и",
    "й",
    "к",
    "л",
    "м",
    "н",
    "о",
    "п",
    "р",
    "с",
    "т",
    "у",
    "ф",
    "х",
    "ц",
    "ч",
    "ш",
    "щ",
    "ъ",
    "ы",
    "ь",
    "э",
    "ю",
    "я",
    "a",
    "b",
    "c",
    "d",
    "e",
    "f",
    "g",
    "h",
    "i",
    "j",
    "k",
    "l",
    "m",
    "n",
    "o",
    "p",
    "q",
    "r",
    "s",
    "t",
    "u",
    "v",
    "w",
    "x",
    "y",
    "z",
    "0",
    "1",
    "2",
    "3",
    "4",
    "5",
    "6",
    "7",
    "8",
    "9",
]

logging.basicConfig(
    level=logging.INFO, format="[%(asctime)s] [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

file_handler = logging.FileHandler("chat_parser.log")
file_handler.setLevel(logging.INFO)
file_handler.setFormatter(
    logging.Formatter("[%(asctime)s] [%(levelname)s] %(message)s")
)

# Добавление обработчика к логгеру
logger.addHandler(file_handler)


def generate_random_string(length):
    letters = string.ascii_letters
    return "".join(random.choice(letters) for _ in range(length))


def get_username(entity):
    if hasattr(entity, "username") and entity.username is not None:
        return entity.username
    else:
        return None


def serialize_participant(participant):
    return {
        "user_id": participant.id,
        "first_name": participant.first_name,
        "last_name": participant.last_name
        if hasattr(participant, "last_name")
        else None,
        "last_online": participant.status.was_online.strftime("%Y-%m-%d %H:%M:%S")
        if participant.status and hasattr(participant.status, "was_online")
        else None,
        "scam": participant.scam,
        "fake": participant.fake,
        "premium": hasattr(participant, "premium") and participant.premium is not None,
        "lang_code": participant.lang_code,
        "is_self": participant.is_self,
        "deleted": participant.deleted,
        "phone": participant.phone,
        "bot": participant.bot,
        "verified": participant.verified,
        "image": hasattr(participant, "photo") and participant.photo is not None,
    }


def send_request_to_server(user_data):
    server_url = f"http://{args.hostIp}:7777/agents/{args.name}/save"
    json = {"jsonData": user_data}
    try:
        response = requests.post(server_url, json=json)
        response.raise_for_status()
        logger.info(
            f"Запрос успешно отправлен на сервер. Код ответа: {response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса на сервер: {e}")


async def enrich_account_description(session, account_name):
    try:
        async with session.get(f"https://t.me/{account_name}") as response:
            html = await response.text()

        soup = BeautifulSoup(html, "html.parser")

        description_element = soup.select_one(".tgme_page_description")
        description = (
            description_element.get_text(strip=True) if description_element else None
        )

        if description and "If you haveTelegram, you can" in description:
            return True, description
        else:
            return False, description

    except Exception as e:
        logger.error(f"Ошибка при выполнении запроса для {account_name}: {str(e)}")
        return True, None


async def process_account_batch(session, account_batch, data):
    tasks = []
    consecutive_count = 0  # Счетчик последовательных повторений фразы
    for account_name in account_batch:
        task = asyncio.create_task(enrich_account_description(session, account_name))
        tasks.append(task)

    results = await asyncio.gather(*tasks)

    for (has_telegram_description, description), account_name in zip(
        results, account_batch
    ):
        data["accounts"][account_name]["description"] = description

        logger.info(f"Описание пользователя {account_name}: {description}")

        if has_telegram_description:
            logger.info(
                f"Найдено описание пользователя с фразой 'If you haveTelegram, you can': {account_name}"
            )
            consecutive_count += 1
            if consecutive_count >= 10:
                return True  # Прерывание цикла итерации аккаунтов
        else:
            consecutive_count = 0  # Сброс счетчика при отсутствии фразы

    return False


async def main(chat_urls_or_usernames):
    user_data = {"chats": {}, "accounts": {}}
    try:
        async with TelegramClient(session_name, api_id, api_hash) as client:
            for chat_url_or_username in chat_urls_or_usernames:
                try:
                    chat = await client.get_entity(chat_url_or_username)
                    if not chat.megagroup:
                        logger.error(
                            f"Чат {chat_url_or_username} не распаршен, он не является мегагруппой"
                        )
                        continue
                except Exception as e:
                    logger.error(
                        f"Чат {chat_url_or_username} не распаршен, произошла ошибка. {e}"
                    )
                    continue

                logger.info(f"Обработка чата: {chat.title}")
                chat_data = {
                    "chat_id": chat.id,
                    "title": chat.title if hasattr(chat, "title") else None,
                    "last_online": chat.date.strftime("%Y-%m-%d %H:%M:%S")
                    if chat.date and hasattr(chat, "date")
                    else None,
                }
                user_data["chats"][chat_url_or_username] = chat_data

                try:
                    total_messages = (await client.get_messages(chat, 1)).total
                except Exception as e:
                    logger.error(
                        f"Произошла ошибка при получении сообщений в чате: {chat.title}, {e}"
                    )
                    continue

                processed_participants = 0
                total_participants = 0

                for letter in queryKey:
                    participants = await client.get_participants(chat, search=letter)
                    total_participants += len(participants)

                    for participant in participants:
                        processed_participants += 1
                        logger.info(
                            f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Обработка участника {processed_participants}/{total_participants}"
                        )

                        if not isinstance(participant, Channel) and not getattr(
                            participant, "bot", False
                        ):
                            username = get_username(participant)
                            if username is not None:
                                if username not in user_data["accounts"]:
                                    user_data["accounts"][username] = {
                                        "user_id": participant.id,
                                        "first_name": participant.first_name,
                                        "last_name": participant.last_name
                                        if hasattr(participant, "last_name")
                                        else None,
                                        "last_online": participant.status.was_online.strftime(
                                            "%Y-%m-%d %H:%M:%S"
                                        )
                                        if participant.status
                                        and hasattr(participant.status, "was_online")
                                        else None,
                                        "date_updated": datetime.datetime.now().strftime(
                                            "%Y-%m-%d %H:%M:%S"
                                        ),
                                        "chats": {chat_url_or_username: []},
                                    }
                                else:
                                    if (
                                        chat_url_or_username
                                        not in user_data["accounts"][username]["chats"]
                                    ):
                                        user_data["accounts"][username]["chats"][
                                            chat_url_or_username
                                        ] = []

                                full_user_info = serialize_participant(participant)
                                user_data["accounts"][username][
                                    "full_user_info"
                                ] = full_user_info

                processed_messages = 0

                async for message in client.iter_messages(chat, limit=10000):
                    sender = message.sender
                    if (
                        sender is not None
                        and not isinstance(sender, Channel)
                        and not getattr(sender, "bot", False)
                    ):
                        username = get_username(sender)
                        if username is not None:
                            if username not in user_data["accounts"]:
                                user_data["accounts"][username] = {
                                    "user_id": sender.id,
                                    "first_name": sender.first_name,
                                    "last_name": sender.last_name
                                    if hasattr(sender, "last_name")
                                    else None,
                                    "last_online": sender.status.was_online.strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    )
                                    if sender.status
                                    and hasattr(sender.status, "was_online")
                                    else None,
                                    "date_updated": datetime.datetime.now().strftime(
                                        "%Y-%m-%d %H:%M:%S"
                                    ),
                                    "chats": {chat_url_or_username: []},
                                }
                            else:
                                if (
                                    chat_url_or_username
                                    not in user_data["accounts"][username]["chats"]
                                ):
                                    user_data["accounts"][username]["chats"][
                                        chat_url_or_username
                                    ] = []

                            full_user_info = serialize_participant(sender)
                            user_data["accounts"][username][
                                "full_user_info"
                            ] = full_user_info

                            processed_messages += 1
                            progress = processed_messages / total_messages * 100
                            logger.info(
                                f"[{datetime.datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] Обработка сообщений: {processed_messages}/{total_messages} ({progress:.2f}%)"
                            )

                            if message.text and message.text.strip() != "":
                                user_data["accounts"][username]["chats"][
                                    chat_url_or_username
                                ].append(message.text)
    except Exception as e:
        logger.error(f"Произошла глобальная ошибка. {e}")

    accounts = list(user_data["accounts"].keys())
    num_accounts = len(accounts)
    batch_size = 50
    num_batches = (num_accounts + batch_size - 1) // batch_size

    batch_index = 0
    while batch_index < num_batches:
        start_index = batch_index * batch_size
        end_index = min(start_index + batch_size, num_accounts)
        account_batch = accounts[start_index:end_index]

        proxy_url = f"socks5://{generate_random_string(15)}:{generate_random_string(15)}@host.docker.internal:9050"
        connector = ProxyConnector.from_url(proxy_url, ssl=False)

        print(proxy_url)
        print(batch_index, num_batches)

        async with aiohttp.ClientSession(connector=connector) as session:
            has_telegram_description = await process_account_batch(
                session, account_batch, user_data
            )

            if has_telegram_description:
                logger.info(
                    "Одно или несколько описаний содержат фразу 'If you haveTelegram, you can'. "
                )

            else:
                batch_index += 1
    print("делаю запрос")
    send_request_to_server(user_data)
    print("сделал запрос")


print(args.urls)
chat_urls_or_usernames = args.urls
asyncio.run(main(chat_urls_or_usernames))
