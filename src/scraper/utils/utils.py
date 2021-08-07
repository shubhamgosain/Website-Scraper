import re
from datetime import datetime, timedelta

def filter_domains(raw_items):
    domains=[]
    for domain in raw_items:
        if is_valid_domain(domain):
            domains.append(domain)
    return domains

def get_days_old_date(duration_in_days):
    return (datetime.now().date() - timedelta(days=(duration_in_days)))

def filter_string_for_db(text):
    return text.replace("'","''")

def is_valid_domain(domain):
    if re.match("(?:[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.)+[a-z0-9][a-z0-9-]{0,61}[a-z0-9]",domain):
        return True
    return False

def validate_request_parameter(request):
    data = request.get_json()
    try:
        if ("domain" in data) and ("subdomain" in data) :
            domain = data["domain"]
            subdomain = data["subdomain"]
            if (domain == "") or (subdomain == ""):
                return "Provide a non empty domain and subdomain"
            if not is_valid_domain("{0}.{1}".format(subdomain, domain)):
                return "{}.{} is not a valid FQDN, need valid domain and subdomain".format(subdomain, domain)
        else:
            return "Parameters domain or subdomain are missing"
        return None
    except Exception as error:
        return "Failed while validating parameters, Err: {}".format(error)