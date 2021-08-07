import logging
from scraper.config.config import config

# First argument will be domain, second will be subdomain. It will send empty string in no arguments are passed.
def params(*args):
    if len(args)==2:
        return {
            'domain': args[0],
            'subdomain': args[1]
        }
    return {
        'domain': "_",
        'subdomain': "_"
    }

# Initialize the loggers
def get_logger():
    # Default logging format
    logging.basicConfig(level=logging.INFO, format='time=%(asctime)s app={} level=%(levelname)s method=%(funcName)s message=%(message)s'.format(config["app_name"]))

    # For logger that also logs domain and subdomain if given. Params function is necessary to be passed here.
    log = logging.getLogger(config["app_name"])
    log.setLevel(logging.INFO)
    formatter = logging.Formatter('time=%(asctime)s app=%(name)s level=%(levelname)s domain=%(domain)s subdomain=%(subdomain)s method=%(funcName)s message=%(message)s')
    ch = logging.StreamHandler()
    ch.setFormatter(formatter)
    ch.setLevel(logging.INFO)
    log.propagate = False
    log.addHandler(ch)
    return log

log = get_logger()