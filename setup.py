from setuptools import setup, find_packages
setup(
    name="socktools",
    version="0.2",
    packages=find_packages(),

    # Project uses reStructuredText, so ensure that the docutils get
    # installed or upgraded on the target machine
    install_requires=['eventlet>=0.19.0','dnslib>=0.9.6','sphinx-argparse>=0.1.15','sphinx-rtd-theme>=0.1.9','msgpack-python>=0.4.8','web.py>=0.37'],

    package_data={
        '': ['*.txt', '*.rst','LICENSE','module','protoclass','*.json'],
    },

    # metadata for upload to PyPI
    author="Gareth Nelson",
    author_email="gareth@garethnelson.com",
    description="A library for dealing with message-based network protocols",
    license="GPLv2",
    zip_safe=False,
    keywords="sockets networking messages",
    url="https://github.com/GarethNelson/python-sock-tools",   # project home page, if any

    # could also include long_description, download_url, classifiers, etc.
)
