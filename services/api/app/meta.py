# -*- coding: utf-8 -*-
# 维护者: 徐岸 <toxuan1998@qq.com>
# 本文件为维护者信息唯一数据源，修改姓名/邮箱请只改此处。
"""ATLAS project metadata — single source for API contact and maintainer info."""

AUTHOR_NAME = "徐岸"
AUTHOR_EMAIL = "toxuan1998@qq.com"
PROJECT_NAME = "ATLAS"

MAINTAINER = {
    "name": AUTHOR_NAME,
    "email": AUTHOR_EMAIL,
}


def maintainer_contact() -> str:
    return f"{AUTHOR_NAME} <{AUTHOR_EMAIL}>"
