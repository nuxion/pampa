# SPDX-FileCopyrightText: 2023-present Xavier Petit <nuxion@gmail.com>
#
# SPDX-License-Identifier: MIT
from importlib.metadata import PackageNotFoundError
from importlib.metadata import version as package_version

try:
    __version__ = package_version("pampa")
except PackageNotFoundError:
    __version__ = "0+unknown"
