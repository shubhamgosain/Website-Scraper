from werkzeug.middleware.dispatcher import DispatcherMiddleware
from prometheus_client import make_wsgi_app, Counter, Histogram
import time
from flask import g
import multiprocessing

# Registeres all the API metrics and holds all prometheus metrics methods used in app
class Metric():
    errors_metric = Counter('scraper_errors', 'Critical Exceptions in application', ['error'])
    domains_added_metric = Counter('domains_added', 'domains added into cms-scanner database', namespace='scraper')
    domains_deleted_metric = Counter('domains_deleted', 'domains deleted and cleaned from cms-scanner database', namespace='scraper')
    urls_scanned_metric = Counter('urls_scanned', 'URLs scanned for cms check', ['status'], namespace='scraper')

    request_duration_metric = Histogram(
        'scraper_response_duration_milliseconds',
        'Duration of HTTP requests',
        ['code','method','path'],
        buckets=[200, 500, 1000, 5000, 11000, 15000]
        )

    request_size_metric = Histogram(
        'scraper_response_size_byte',
        'Size of HTTP response',
        ['code','method','path'],
        buckets=[100, 500, 3000, 10000, 30000, 100000, 1000000, 10000000]
        )

    errors_metric_labels = {
            "sysapi_add_cms_error" : {
                "label" : "sysapi_add_cms_fail",
                "count" : multiprocessing.Value('i', 0)
            },
            "cms_db_update_error" : {
                "label" : "cms_db_update_fail",
                "count" : multiprocessing.Value('i', 0)
            },
            "metadata_check_error" : {
                "label" : "metadata_check_fail",
                "count" : multiprocessing.Value('i', 0)
            },
            "cms_scan_error" : {
                "label" : "cms_scan_fail",
                "count" : multiprocessing.Value('i', 0)
            },
            "scan_workers_killed" : {
                "label" : "scan_workers_killed",
                "count" : multiprocessing.Value('i', 0)
            }
        }

    urls_scanned_metric_labels = {
            "page_read_exception" : {
                "label" : "page_read_exception",
                "count" : multiprocessing.Value('i', 0)
            },
            "identified_as_wp" : {
                "label" : "identified_as_wp",
                "count" : multiprocessing.Value('i', 0)
            },
        }

    # This method is called after every response served
    def register_response_metric(self,response):
        self.request_duration_metric.labels(response.status_code, g.method, g.path).observe((time.time() - g.start_time)*1000)
        self.request_size_metric.labels(response.status_code, g.method, g.path).observe(response.content_length)

    # export the metrics on /metrics
    def export(app):
        app.wsgi_app = DispatcherMiddleware(app.wsgi_app, {
        '/metrics': make_wsgi_app()
        })