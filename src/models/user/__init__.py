from beanie import Document
from pydantic import Field

import utils


class User(Document):
    username: str
    email: str
    password: str = Field(default_factory=utils.generate_password)

    class Settings:
        name = "users"
