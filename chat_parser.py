# скрипт для парсингов чатов (пользователей и сообщений)
import logging
import asyncio
from telethon import TelegramClient
import datetime
from telethon.tl.types import Channel
import argparse
import requests

parser = argparse.ArgumentParser()
parser.add_argument("--urls", nargs="+", type=str)
parser.add_argument("--name", type=str)
parser.add_argument("--hostIp", help="Host IP address")

args = parser.parse_args()

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
        "premium": participant.premium,
        "lang_code": participant.lang_code,
        "is_self": participant.is_self,
        "deleted": participant.deleted,
        "phone": participant.phone,
        "bot": participant.bot,
        "verified": participant.verified,
        "image": hasattr(participant, "photo") and participant.photo is not None,
    }


def send_request_to_server(user_data):
    print(user_data)
    print(args.hostIp, args.name)
    server_url = "http://${args.hostIp}:7777/agents/{args.name}/save"
    json = {"jsonData": user_data}
    try:
        response = requests.post(server_url, json=json)
        response.raise_for_status()
        logger.info(
            f"Запрос успешно отправлен на сервер. Код ответа: {response.status_code}"
        )
    except requests.exceptions.RequestException as e:
        logger.error(f"Ошибка при отправке запроса на сервер: {e}")


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

    print("делаю запрос")
    send_request_to_server(user_data)
    print("сделал запрос")


print(args.urls)
chat_urls_or_usernames = args.urls
asyncio.run(main(chat_urls_or_usernames))
