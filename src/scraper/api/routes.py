import http
from flask import jsonify
from threading import Thread
from scraper.dboperations import dboperations
from scraper import scraper
from scraper.utils import utils
from scraper.utils import logger
from scraper.config.config import config
from scraper.prometheus.prometheus import Metric
from scraper.utils.logger import log, params

class Response:
    def response(data, error, status_code):
        success = True
        if error:
            success = False

        return {
            "data": data,
            "error": error,
            "success": success
        }, status_code

# Class contains definition of API routes
class APIRoutes():
    def check_ping(self, request):
        return "Ping: OK"

    def scan_domain(self, request):
        error = utils.validate_request_parameter(request)
        if error != None:
            log.info("Invalid request, skipping to scan. Err: %s", error, extra=params())
            return Response.response(None, error, http.HTTPStatus.BAD_REQUEST)
        request_data = request.get_json()
        domain = request_data["domain"]
        subdomain = request_data["subdomain"]

        dbo = dboperations.DBOperations(auto_commit=True)
        cmo = scraper.CMSScanner()
        error = cmo.scan_installation(domain, subdomain, dbo)
        if error == None:
            data = dbo.read_scan_information(domain, subdomain)
            Metric.urls_scanned_metric.labels("total").inc(1)
            del dbo, cmo
            return Response.response(data, None, http.HTTPStatus.OK)
        log.info("Failed to read information, Err: %s", error, extra=params(domain, subdomain))
        return Response.response(None, "Failed to read information, Err: {}".format(error), http.HTTPStatus.INTERNAL_SERVER_ERROR)

    def get_domain_cms_info(self, request):
        error = utils.validate_request_parameter(request)
        if error != None:
            return Response.response(None, error, http.HTTPStatus.BAD_REQUEST)
        request_data = request.get_json()
        domain = request_data["domain"]
        subdomain = request_data["subdomain"]

        dbo = dboperations.DBOperations(auto_commit=True)
        data = dbo.read_scan_information(domain, subdomain)
        del dbo
        if len(data) == 0:
            data = None
        return Response.response(data, None, http.HTTPStatus.OK)

    def scan_domains_from_file(self, request):
        urls_to_scan = []
        uploaded_file = request.files['file']
        domains_not_to_scan = dboperations.DBOperations(auto_commit=True).get_urls_not_to_scan(utils.get_days_old_date(config["domain_scan_frequency_days"]))
        for line in uploaded_file.readlines():
            line = line.decode('utf-8').strip().split(',')
            domain = line[0]
            subdomain = line[1]
            if (subdomain in domains_not_to_scan) and (domain in domains_not_to_scan[subdomain]):
                log.info("URL is already scanned in last %s days, skipping to scan", config["domain_scan_frequency_days"], extra=params(domain, subdomain))
                continue
            if utils.is_valid_domain("{0}.{1}".format(subdomain, domain)):
                urls_to_scan.append([line[0], line[1]])
            else:
                log.info("URL FQDN is invalid, skipping to scan", extra=params(domain, subdomain))

        if len(urls_to_scan) > 0:
            scraper.CMSScanner().urls_scan(urls_to_scan)
            return Response.response("Started cms scan for {} installations".format(len(urls_to_scan)), None, http.HTTPStatus.OK)
        return Response.response("No new installation are there for scan", None, http.HTTPStatus.OK)