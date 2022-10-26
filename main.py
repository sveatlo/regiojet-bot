#!/usr/bin/env python3

import os
import logging
import sys
import time
import click
import requests
from selenium import webdriver
from selenium.common.exceptions import NoSuchElementException
import selenium

locations = {
    'Trnava': (1723745000, 'CITY'),
    'Brno': (10202002, 'CITY'),
}

class Bot():
    def __init__(self, from_location, to_location, date, required_seats, telegram_bot_token = None, telegram_chat_id = None):
        self.from_id, self.from_type = from_location
        self.to_id, self.to_type = to_location
        self.date = date
        self.required_seats = required_seats

        self.driver = webdriver.Chrome()

        self.check_interval = 30
        self.telegram_bot_token = telegram_bot_token
        self.telegram_chat_id = telegram_chat_id

    def check(self):
        """
        check runs a single check operation on the page. Returns true if enough seats are available on the requested connection
        """

        self.driver.get(f"https://shop.regiojet.sk/?departureDate={self.date}&fromLocationId={self.from_id}&fromLocationType={self.from_type}&toLocationId={self.to_id}&toLocationType={self.to_type}")

        time.sleep(1)

        try:
            e = self.driver.find_element_by_xpath('//*[@id="free-seats-desktop"]/div')
        except NoSuchElementException:
            e = self.driver.find_element_by_xpath('//*[@id="free-seats-mobile"]/div')
        logging.debug(f"empty seats element content={e.text};required={self.required_seats}")
        logging.debug(f"empty seats element intcontent={int(e.text)}")
        free_seats = int(e.text)

        return free_seats >= self.required_seats

    def loop_check(self):
        """
        loop_check runs .check() in a loop every {check_interval} seconds and returns when seats are available whilst notifying the telegram chat
        """

        while True:
            try:
                res = self.check()
            except NoSuchElementException as e:
                logging.fatal("No connections?")
                raise e
                sys.exit(1)

            if res:
                break

            logging.info(f"No empty seats yet :/ waiting for {self.check_interval}s")
            time.sleep(self.check_interval)

        logging.info(f"empty seats available")

        if self.telegram_bot_token is not None and self.telegram_chat_id is not None:
            requests.get(f"https://api.telegram.org/bot{self.telegram_bot_token}/sendMessage", {
                'chat_id': self.telegram_chat_id,
                'text': 'The watched RegioJet connection has sufficient free seats. Act quickly!'
            })


@click.command()
@click.option('-f', '--from', 'from_name', required=True, prompt=True)
@click.option('-t', '--to', 'to_name', required=True, prompt=True)
@click.option('-d', '--date', 'date', required=True, prompt=True)
@click.option('-n', '--required-seats', 'required_seats', required=True, default=1, type=int)
def main(from_name, to_name, date, required_seats):
    if date is None:
        date = time.strftime('%Y-%m-%d')

    try:
        from_location = locations[from_name]
        to_location = locations[to_name]
    except KeyError:
        logging.fatal(f"Unknown `to` or `from` location")
        sys.exit(1)

    telegram_bot_token = os.environ.get('TELEGRAM_BOT_TOKEN')
    telegram_chat_id = os.environ.get('TELEGRAM_CHAT_ID')
    bot = Bot(from_location, to_location, date, required_seats, telegram_bot_token=telegram_bot_token, telegram_chat_id=telegram_chat_id)
    bot.loop_check()
    time.sleep(30)

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    main()   # pylint: disable=E1120
