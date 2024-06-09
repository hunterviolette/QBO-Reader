from setuptools import setup
from qbo.qbo import QuickbooksRegister

setup(
    name='qbo',
    version='1.0',
    packages=['qbo'],
    install_requires=['pandas'],
)