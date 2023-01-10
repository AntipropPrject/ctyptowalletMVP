FROM python:3.10

ENV PYTHONUNBUFFERED=1

LABEL version = '0.6'
LABEL master = 'BotShackTeam'

RUN mkdir /CryptoBot
WORKDIR /CryptoBot

COPY ./requirements.txt /tmp/

RUN pip3 install --upgrade pip

RUN mkdir /tron
RUN git clone "https://github.com/andelf/tronpy.git" /tron
RUN sed -i 's/eth_abi>=2.1.1,<3.0.0/eth_abi>=2.1.1,<=3.0.1/g' /tron/setup.py
RUN pip3 install -e /tron/.

RUN pip3 install -r /tmp/requirements.txt

COPY . /CryptoBot/
