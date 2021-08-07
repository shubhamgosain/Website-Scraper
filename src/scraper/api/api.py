import sys
import time
from waitress import serve
from paste.translogger import TransLogger
from flask import Flask, request, g, Response
from scraper.config.config import apiconfig
from scraper.utils.logger import log, params
from scraper.prometheus.prometheus import Metric
from . import routes

class API(routes.APIRoutes):
    def __init__(self):
        self.app = Flask("cms-scanner")

        # Export the metrics on /metrics
        Metric.export(self.app)

        self.__register_routes()

        try:
            serve(TransLogger(self.app), host="0.0.0.0", port=self.__get_port(), threads='10')
        except Exception as error:
            log.error("Error while starting API, Err: %s", error, exc_info=True, extra=params())
            sys.exit(1)

    def __get_port(self):
        try:
            return apiconfig["port"]
        except Exception as error:
            log.error("Error while reading port, Err: %s", error, exc_info=True, extra=params())
            sys.exit(1)

    # declare the before and after requests method
    def __defaults(self):
        @self.app.after_request
        def after_request_func(response):
            Metric().register_response_metric(response)
            return response
        @self.app.before_request
        def before_request():
            g.start_time = time.time()
            g.path = request.path
            g.method = request.method

    # Register and declare the API routes
    def __register_routes(self):
        self.__defaults()
        @self.app.route('/ping', methods=["GET"])
        def check_ping():
            return self.check_ping(request)

        @self.app.route('/api/v1.0/cms/scan', methods=["POST"])
        def scan_domain():
            return self.scan_domain(request)

        @self.app.route('/api/v1.0/cms/scan', methods=["GET"])
        def get_domain_cms_info():
            return self.get_domain_cms_info(request)

        @self.app.route('/api/v1.0/cms/scan-from-file', methods=["POST"])
        def scan_domains_from_file():
            return self.scan_domains_from_file(request)