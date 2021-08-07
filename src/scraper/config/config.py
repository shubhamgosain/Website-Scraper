import json
import sys
import os
import logging as log

def load_config():
    try:
        log.info("Reading config")
        with open("config/config.json") as data:
            config = json.load(data)
            if "environment" not in config:
                log.error("Environment not specified, please provide 'environment' key in config")
                sys.exit(1)
            if config["environment"] not in ["development", "production"]:
                log.error("Environment not supported, supported values are 'development' and 'production'",)
                sys.exit(1)
            return config

    except TypeError:
        log.error("Invalid JSON config file", exc_info=True)
        sys.exit(1)

    except FileNotFoundError:
        log.error("Config file not found", exc_info=True)
        sys.exit(1)

    except Exception as error:
        log.error("Unable to read config, Err: %s", error, exc_info=True)
        sys.exit(1)

config = load_config()

dbconfig = config["database"]

apiconfig = config["api"]