from setuptools import setup, find_packages


setup(
    name="my_multivisor",
    version="0.1",
    packages=find_packages(),
    entry_points=dict(console_scripts=["my_multivisor=my_multivisor.__main__:main"]),
)
