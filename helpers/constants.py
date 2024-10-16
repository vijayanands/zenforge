import hashlib
from collections import defaultdict
from typing import Dict, List

unique_user_emails = [
    "vijayanands@gmail.com",
    "vijayanands@yahoo.com",
    "vjy1970@gmail.com",
    "email2vijay@gmail.com",
]

user_to_external_users: Dict[str, List[str]] = defaultdict(list)
external_user_to_user: Dict[str, str] = defaultdict()


def map_user(external_username: str):
    hash_value = int(hashlib.md5(external_username.encode()).hexdigest(), 16)
    mapped_user_email = unique_user_emails[hash_value % len(unique_user_emails)]
    external_user_to_user[external_username] = mapped_user_email
    user_to_external_users[mapped_user_email].append(external_username)
