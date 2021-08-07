from typing import final
import requests
import time
import multiprocessing
import queue as q
import gc
import re
import math
import json
from multiprocessing import Process, TimeoutError
from bs4 import BeautifulSoup
from threading import Thread

from requests.models import Response
from scraper.dboperations import dboperations
from scraper.utils import utils
from scraper.utils.logger import log, params
from scraper.prometheus.prometheus import Metric
from scraper.config.config import config

# This class contains methods to scan URLs cms and refresh domains list
class CMSScanner:
    __max_workers_to_run = config["worker_count"]
    __url_queue = multiprocessing.Queue()
    __env = config["environment"]

    # Initialize necessary objects
    def __init__(self):
        self.dbo = dboperations.DBOperations(auto_commit=True)
        self.url_read_timeout = config["url_read_timeout_sec"]
        self.html_headers = {
            'Range':'bytes=0-50000',
            "User-Agent": "website-scraping-bot"
            }
        self.error_metrics = Metric.errors_metric_labels
        self.url_scan_metrics = Metric.urls_scanned_metric_labels
        self.default_subdomain = "www"

    # To read the html for given url and parse html and language
    def __read_url_html(self, domain, subdomain):
        url = "http://{0}.{1}".format(subdomain, domain)
        headers=self.html_headers
        try:
            response = requests.get(url, timeout=self.url_read_timeout, headers=headers)
        except Exception as error:
            self.url_scan_metrics["page_read_exception"]["count"].value += 1
            return None

        try:
            return response

        except Exception as error:
            log.error("Error while checking metadata from html, Error : {}".format(error), extra=params())
            self.error_metrics["metadata_check_fail"]["count"].value += 1
            return None

        finally:
            response.close()

    # To read the metas from html
    def read_metas(self, soup):
        metas = []
        if soup:
            metas =  soup.find_all('meta')
        return metas

    # To read the language from html
    def read_lang(self, soup):
        lang = ''
        if soup:
            try:
                lang = soup.html["lang"]
            except:
                pass
            # lang '-' is replaced with '_' to make lang look alike the entries in coredb
            if lang:
                lang = lang.replace('-', '_')
        return lang

    # To read the inforamtion about the website
    def read_site_info(self, soup):
        if not soup:
            return {}
        import_tags = soup.find_all(['link', 'script'])
        plugins = set()
        themes = set()
        site_info = {}
        for tag in import_tags:
            source_url = ''
            if 'src' in tag.attrs:
                if tag.attrs['src'].find('wp-content') != -1:
                    source_url = tag.attrs['src']
            elif ('href' in tag.attrs) and (tag.attrs['href'].find('wp-content') != -1):
                    source_url = tag.attrs['href']
            if source_url.find('wp-content/themes/') != -1:
                themes.add((source_url.split('wp-content/themes/')[1]).split('/')[0])
            elif source_url.find('wp-content/plugins/') != -1:
                plugins.add((source_url.split('wp-content/plugins/')[1]).split('/')[0])
        if len(themes) > 0:
            site_info['themes'] = list(themes)
        if len(plugins) > 0:
            site_info['plugins'] = list(plugins)
        return site_info

    # Return generator meta from the given page metadata
    def __get_generator_meta(self, metas):
        generator_metas = []
        for m in metas:
            if 'name' in m.attrs and (m.attrs['name'] == "generator"):
                generator_meta = m.attrs['content']
                generator_meta = utils.filter_string_for_db(generator_meta)
                generator_metas.append(generator_meta)
        del metas
        return generator_metas

    # Check if the site is wordpress
    def if_wordpress(self, generator_metas):
        for generator_meta in generator_metas:
            if (generator_meta) and (re.search("^WordPress ", generator_meta)):
                return True, generator_meta
        generator_meta = None
        if len(generator_metas) > 0:
            generator_meta = generator_metas[0]
        return False, generator_meta

    # Check a URL generator meta, language and stores information in scraper database
    # If a url is found to be having a wordpress code, it adds the cms entry in core db via systemsapi
    def scan_installation(self, domain, subdomain, dbo):
        generator_metas = []
        generator_meta = None
        lang = ''
        try:
            web_response = self.__read_url_html(domain, subdomain)
            soup = BeautifulSoup(web_response.text, features="lxml")
            metas = self.read_metas(soup)
            lang = self.read_lang(soup)
            site_info = self.read_site_info(soup)
            site_info["headers"] = dict(web_response.headers)
            site_info["status"] = web_response.status_code
            generator_metas = self.__get_generator_meta(metas)

        except Exception as e:
            error = "Error while checking url cms, Err: {}".format(e)
            log.error(error, extra=params(domain, subdomain))
            self.error_metrics["cms_scan_error"]["count"].value += 1
            return error

        try:
            is_wordpress = False
            is_wordpress, generator_meta = self.if_wordpress(generator_metas)
            dbo.update_website_scan(domain, subdomain, generator_meta, lang, is_wordpress, json.dumps(site_info))
            return None

        except Exception as e:
            error = "Error while storing url scan in db, Err: {}".format(e)
            log.error("Error while storing url scan in db, Err:", e, extra=params(domain, subdomain))
            self.error_metrics["cms_db_update_error"]["count"].value += 1
            return error

    # This is the landing function for worker, where worker pick a URL from queue and run a scan
    def __url_scan_process(self, worker_id):
        log.info("Initiating worker %s", worker_id, extra=params())
        # Creating a database conection for each worker
        dbo = dboperations.DBOperations(auto_commit=True)

        # Each worker will keep working until the queue containing urls gets empty
        while self.__url_queue.qsize() > 0:
            urls_scanned = 0
            try:
                url_obj = self.__url_queue.get(block=True, timeout=3)
                qsize = self.__url_queue.qsize()
                if (qsize % 1000) == 0:
                    log.info("CMS scan progress updated - %s url(s) left to be scanned", qsize, extra=params())
                subdomain = url_obj[1]
                domain = url_obj[0]
                if not subdomain:
                    subdomain = self.default_subdomain
            except q.Empty:
                continue
            except TimeoutError:
                log.error("Worker %s failed to read url from queue, Reason : Timeout", worker_id, extra=params())

            if not self.scan_installation(domain, subdomain, dbo):
                urls_scanned += 1

            # Provide 10 secs breathing area and db connections refresh
            if urls_scanned % 500 == 0:
                del dbo
                dbo = dboperations.DBOperations(auto_commit=True)
            if urls_scanned % 1000 == 0:
                time.sleep(30)

            # Cleaning up any garbage left
            del url_obj
            gc.collect()

        del dbo
        log.info("Ending worker %s", worker_id, extra=params())

    # This function add urls to queue and spawns the workers to start processing the queue and scan cms
    def urls_scan(self, urls):
        for url in urls:
            self.__url_queue.put(url)
        self.__total_urls = len(urls)

        workers_to_run = math.ceil(self.__total_urls/10)
        workers_to_run = workers_to_run if workers_to_run < self.__max_workers_to_run else self.__max_workers_to_run
        log.info("Spawning %s worker for scanning of %s URL", workers_to_run, self.__url_queue.qsize(), extra=params())

        jobs = []
        for worker_id in range(0, workers_to_run):
            process = Process(target=self.__url_scan_process, args=(worker_id,))
            jobs.append(process)
            process.start()

        Thread(target=self.update_scan_metrics, daemon=True, args=()).start()

        while self.__url_queue.qsize() > 100:
            worker_id=0
            for job in jobs:
                if not job.is_alive():
                    job.kill
                    job.close()
                    process = Process(target=self.__url_scan_process, args=(worker_id,))
                    jobs[worker_id] = process
                    process.start()
                    log.error("Killed and restarted zombie process, worker_id:%s",worker_id, extra=params())
                    self.error_metrics["scan_workers_killed"]["count"].value += 1
                worker_id += 1
            time.sleep(60)

    # Top update the prometheus metric counter with the count of urls getting scanned
    def update_scan_metrics(self):
        urls_scanned_previously = 0
        while True:
            urls_scanned = self.__total_urls - self.__url_queue.qsize()
            if urls_scanned > urls_scanned_previously:
                Metric.urls_scanned_metric.labels('total').inc(urls_scanned - urls_scanned_previously)
                urls_scanned_previously = urls_scanned

            for key,metric in self.error_metrics.items():
                Metric.errors_metric.labels(metric["label"]).inc(metric["count"].value)
                self.error_metrics[key]["count"].value = 0

            for key,metric in self.url_scan_metrics.items():
                Metric.urls_scanned_metric.labels(metric["label"]).inc(metric["count"].value)
                self.url_scan_metrics[key]["count"].value = 0

            if self.__url_queue.qsize() == 0:
                break
            time.sleep(10)

    # Check and Scan the eligible urls(domains, subdomains)
    def scan_urls(self):
        log.info("Starting website scan", extra=params())

        urls_to_scan = self.dbo.get_domains_to_scan(utils.get_days_old_date(config["website_scan_frequency_days"]))
        log.info("%s url(s) to be scanned", len(urls_to_scan), extra=params())

        self.urls_scan(urls_to_scan)
        log.info("Website scan done", extra=params())