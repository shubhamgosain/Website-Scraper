import time
from threading import Thread
from scraper.utils.logger import log, params
from scraper import scraper
from scraper.api import api

def main():
    # Initiate API
    Thread(target=api.API, daemon=True, args=()).start()

    # Daily Loop to keep checking if it need to refresh or scan domains
    while True:
        # Initiate CMS scanner object
        cmo = scraper.CMSScanner()

        # Run scan for the eligible domains
        cmo.scan_urls()

        del cmo

        log.info("Sleeping for next 2 minutes for any further scan", extra=params())
        time.sleep(120)