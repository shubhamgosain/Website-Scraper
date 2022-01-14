import sys
import psycopg2
import logging as log
import traceback
import random
from datetime import datetime, timezone
from scraper.config.config import dbconfig
from scraper.utils.logger import log, params

class DBViews:
    def get_cms_view(domain, subdomain, scan_time, cms_name, cms_type, cms_identifier, cms_found_time, language, site_information):
        cms_view = {
            "domain" : domain,
            "subdomain" : subdomain,
            "last_scan_time" : scan_time,
            "cms_name" : cms_name,
            "cms_type" : cms_type,
            "cms_identifier" : cms_identifier,
            "cms_found_time": cms_found_time,
            "language" : language,
            "site_information" : site_information
        }
        return cms_view

class DBOperations:
    __pgpassword = ""
    __dbhost = ""
    __dbuser = ""
    __dbname = ""
    __port = ""

    def __init__(self, auto_commit):
        try:
            self.__dbhost = random.choice(dbconfig["hosts"])
            self.__dbuser = dbconfig["user"]
            self.__dbname = dbconfig["name"]
            self.__pgpassword = ""
            self.__port = dbconfig["port"]
            self.__key = dbconfig["key"]
            self.__cert = dbconfig["cert"]

        except Exception as error:
            log.error('Error reading the db config, Err : %s', error, exc_info=True, extra=params())
            sys.exit(1)

        try:
            self.__my_connection = psycopg2.connect( host=self.__dbhost, user=self.__dbuser, password=self.__pgpassword, dbname=self.__dbname, port=self.__port, sslkey=self.__key, sslcert=self.__cert)
            self.__my_connection.autocommit = auto_commit

        except (Exception, psycopg2.Error) as error:
            if 'self.__my_connection' in locals():
                self.__my_connection.rollback()
            log.error("Database connection error\n%s", error, exc_info=True, extra=params())
            sys.exit(1)

    # Read all domains
    def get_domain_list(self):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT name FROM domain")
            result = conn.fetchall()
        except (Exception, psycopg2.Error) as error :
            log.error("Failed to fetch record from Database Err: %s", error, exc_info=True, extra=params())
            return
        domains = []
        for domain in result:
            domains.append(domain[0])
        return domains

    # Store all the new domains found that are not in our database
    def store_domains(self, domains):
        log.info("Storing %s domains", len(domains), extra=params())
        conn = self.__my_connection.cursor()
        try:
            if len(domains) > 0:
                query = "INSERT INTO domain(name) VALUES "
                batch_id = 0
                while(batch_id*30000 < len(domains)):
                    query = "INSERT INTO domain(name) VALUES "
                    domains_batch = domains[batch_id*30000 : (batch_id+1)*30000]
                    if len(domains_batch) == 0:
                        continue
                    for domain in domains_batch:
                        query += "('{}'),".format(domain)
                    batch_id += 1
                    query = query[:-1]
                    conn.execute(query)
            log.info("Successfully stored {} domains".format(len(domains)), extra=params())
        except (Exception, psycopg2.Error) as error :
            log.error("Failed to store domains, Err: %s", error, exc_info=True, extra=params())
            sys.exit(1)

    # Cleanup the domains
    def cleanup_domains(self, domains):
        log.info("Cleaning up %s domains", len(domains), extra=params())
        conn = self.__my_connection.cursor()
        try:
            if len(domains) > 0:
                conn.execute("DELETE FROM domain WHERE name IN %s RETURNING id",(tuple(domains),))
            log.info("Sucessfully Cleaned up {} domains".format(len(domains)), extra=params())
        except (Exception, psycopg2.Error) as error :
            log.error("Failed while doing domains cleanup, %s", error, extra=params())
            sys.exit(1)

    # Update the entries in database after each website scan
    def update_website_scan(self, domain, subdomain, generator_meta, lang, is_wordpress, site_info):
        conn = self.__my_connection.cursor()
        domain_id = None
        subdomain_id = None
        cms_name_id = None
        cms_type_id = None
        cms_identifier_id = None
        cms_identifier = 'cms-scanner'
        cms_found_time = None
        if lang == '':
            lang = None

        try:
            conn.execute("SELECT id FROM domain WHERE domain.name = %s", (domain,))
            result = conn.fetchone()
            if result is None:
                conn.execute("INSERT INTO domain(name) VALUES (%s) returning id", (domain,))
                result = conn.fetchone()
            domain_id = result[0]

            conn.execute("SELECT id FROM subdomain WHERE subdomain.name = %s", (subdomain,))
            result = conn.fetchone()
            if result is None:
                conn.execute("INSERT INTO subdomain(name) VALUES (%s) returning id", (subdomain,))
                result = conn.fetchone()
            subdomain_id = result[0]

            if is_wordpress:
                conn.execute("SELECT id FROM cms_type WHERE name = %s", ('WordPress',))
                result = conn.fetchone()
                if result is None:
                    conn.execute("INSERT INTO cms_type(name) VALUES (%s) returning id", ('WordPress',))
                    result = conn.fetchone()
                cms_type_id = result[0]

            conn.execute("SELECT id FROM cms_identifier WHERE name = %s", (cms_identifier,))
            result = conn.fetchone()
            if result is None:
                conn.execute("INSERT INTO cms_identifier(name) VALUES (%s) returning id", (cms_identifier,))
                result = conn.fetchone()
            cms_identifier_id = result[0]

            if generator_meta is not None:
                conn.execute("SELECT id FROM cms_name WHERE cms_name.name = %s", (generator_meta,))
                result = conn.fetchone()
                if result is None:
                    conn.execute("INSERT INTO cms_name(name) VALUES (%s) returning id", (generator_meta,))
                    result = conn.fetchone()
                cms_name_id = result[0]

            conn.execute("SELECT cms_found_time FROM cms WHERE domain_id = %s AND subdomain_id = %s AND cms_type_id = %s", (domain_id, subdomain_id, cms_type_id,))
            result = conn.fetchone()
            if result is None:
                if is_wordpress:
                    cms_found_time = datetime.now(timezone.utc)
            else:
                cms_found_time = result[0]

            conn.execute("UPDATE cms SET scan_time = %s, cms_name_id = %s, cms_type_id = %s, cms_identifier_id = %s, cms_found_time = %s, language = %s, site_information = %s WHERE domain_id = %s AND subdomain_id = %s RETURNING id",(datetime.now(timezone.utc), cms_name_id, cms_type_id, cms_identifier_id, cms_found_time, lang, site_info, domain_id, subdomain_id,))
            result = conn.fetchone()
            if result is None:
                conn.execute("INSERT INTO cms(scan_time, domain_id, subdomain_id, cms_name_id, cms_type_id, cms_identifier_id, cms_found_time, language, site_information) VALUES (%s,%s,%s,%s,%s,%s,%s,%s,%s)",(datetime.now(timezone.utc), domain_id, subdomain_id, cms_name_id, cms_type_id, cms_identifier_id, cms_found_time, lang, site_info))

            # cleaning up unecessary objects
            del domain, subdomain, generator_meta, lang, is_wordpress, domain_id, subdomain_id, cms_name_id, cms_type_id, result, cms_found_time
            conn.close()

        except Exception as error:
            log.error("Failed while storing the domain cms scan report. Err : %s, Date : %s", error, [domain_id, subdomain_id, cms_name_id, cms_type_id, cms_identifier_id, cms_found_time, lang], exc_info=True, extra=params())

    # Get the list of domains to run cms scan
    def get_domains_to_scan(self, date):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT q1.domain, s.name AS \"subdomain\" FROM (SELECT d.name as \"domain\",c.subdomain_id FROM domain d LEFT JOIN cms c ON d.id=c.domain_id WHERE (c.scan_time::DATE < %s OR c.scan_time IS NULL)) q1 LEFT JOIN subdomain s ON s.id=q1.subdomain_id", (date,))
            result = conn.fetchall()
            domains=[]
            for domain in result:
                domains.append([domain[0], domain[1]])
            return domains

        except (Exception, psycopg2.Error) as error :
            log.error("Failed to fetch domain list to scan from database, Err : %s", error, extra=params())
            sys.exit(1)


    # check_if_cms_entry checks if cms is already identified as WoordPress earlier
    def check_if_cms_entry(self, domain, subdomain):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT * FROM cms_view WHERE domain = %s and subdomain = %s and cms_type = 'WordPress'", (domain, subdomain))
            result = conn.fetchone()
            if result is None:
                return False
            return True

        except (Exception, psycopg2.Error) as error :
            log.error("Failed to check the WordPress cms entry in database, Err : %s", error, extra=params(domain, subdomain))
            return False

    # Get the list of domains and subdomains which are not yet ready to run scan on
    def get_urls_not_to_scan(self, date):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT domain, subdomain FROM cms_view WHERE scan_time > %s", (date,))
            result = conn.fetchall()
        except (Exception, psycopg2.Error) as error :
            log.error("Failed to fetch domain list to scan from database, Err : %s", error, extra=params())

        domains={}
        for domain in result:
            if domain[1] not in domains:
                domains[domain[1]] = []
            domains[domain[1]].append(domain[0])
        return domains

    # Get the last date of sysapi domain refresh date
    def get_sysapi_domain_last_fetch(self):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT time::date FROM sysapi_domain_last_fetch ORDER BY time DESC LIMIT 1")
            result = conn.fetchone()
            if result:
                return result[0]
            return None
        except Exception as error:
            log.error("Failed to read domains last refresh date, Err : %s", error, extra=params())

    # Update the date of sysapi domain refresh date
    def update_sysapi_domain_last_fetch(self):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("DELETE FROM sysapi_domain_last_fetch")
            conn.execute("INSERT INTO sysapi_domain_last_fetch VALUES (%s)", (datetime.now(timezone.utc),))
            log.info("Updated domains last refresh date", extra=params())
        except Exception as error:
            log.error("Failed to update domains refresh date, Err : %s", error, extra=params())

    def read_scan_information(self, domain, subdomain):
        conn = self.__my_connection.cursor()
        try:
            conn.execute("SELECT domain, subdomain, scan_time, cms_name, cms_type, cms_identifier, cms_found_time, language, site_information FROM cms_view WHERE domain = %s AND subdomain = %s", (domain, subdomain,))
            result = conn.fetchall()
            json_result = []
            if result:
                for row in result:
                    json_row = DBViews.get_cms_view(row[0], row[1], row[2], row[3], row[4], row[5], row[6], row[7], row[8])
                    json_result.append(json_row)
            return json_result
        except Exception as error:
            log.error("Failed to read domain information, Err : %s", error, extra=params())

    def __refresh_cursor(self, conn):
        if conn:
            conn.close()
        return self.__my_connection.cursor()

    def commit_changes(self):
        self.__my_connection.commit()

    def __del__(self):
        if 'self.__my_connection' in locals():
            self.__my_connection.close()