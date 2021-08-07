# Wesbite Scraper API endpoints
---

- `GET /api/v1.0/cms/scan`

    - Read cms information for given domain + subdomain
    - Response (If cms scan exists):

    Request Data: {"domain": "example.com", "subdomain": "www"}

    Response :

    ```
      {
            "data": [
                {
                "cms_found_time": <N>,
                "cms_identifier": <N>,
                "cms_name": <N>,
                "cms_type": <N>,
                "domain": "<domain>",
                "language": <N>,
                "last_scan_time": <N>,
                "subdomain": <subdomain>,
                "site_information": {}
                }
            ],
            "error": <null|err_message>,
            "success": <true|false>
       }
    ```

    - Response (If scan doesn't exists):

    ```
        {"data":null,"error":null,"success":true}
    ```

    - Response (If domain or subdomain is not valid):

    ```
        {"data":null,"error":"<subdomain>.<domain> is not a valid FQDN, need valid domain and subdomain,"success":false}
    ```

    - Response (If request parmaters are missing):

    ```
        {"data":null,"error":"Parameters domain or subdomain are missing","success":false}
    ```

    - Response (If request parmaters are empty):

    ```
        {"data":null,"error":"Provide a non empty domain and subdomain","success":false}
    ```

- `POST /api/v1.0/cms/scan`

    - Scan cms for given domain + subdomain
    - Response (If cms scan exists):

    Request Data: {"domain": "example.com", "subdomain": "www"}

    Response :

    ```
      {
            "data": [
                {
                "cms_found_time": <N>,
                "cms_identifier": <N>,
                "cms_name": <N>,
                "cms_type": <N>,
                "domain": "<domain>",
                "language": <N>,
                "last_scan_time": <N>,
                "subdomain": <subdomain>,
                "site_information": {}
                }
            ],
            "error": <null|err_message>,
            "success": <true|false>
       }
    ```

    - Response (If scan does't exists):

    ```
        {"data":null,"error":null,"success":true}
    ```

    - Response (If domain or subdomain is not valid):

    ```
        {"data":null,"error":"<subdomain>.<domain> is not a valid FQDN, need valid domain and subdomain,"success":false}
    ```

    - Response (If request parmaters are missing):

    ```
        {"data":null,"error":"Parameters domain or subdomain are missing","success":false}
    ```

    - Response (If request parmaters are empty):

    ```
        {"data":null,"error":"Provide a non empty domain and subdomain","success":false}
    ```

- `POST /api/v1.0/cms/scan-from-file`

    - Scan cms for domains + subdomains read from uploaded file

    Example:
    ```
    $ cat /tmp/file1 | head -2
    example.com,www
    example.com,test6

    $ curl -F 'file=@/tmp/file1' <cms-scanner-host>:4000/api/v1.0/cms/scan-from-file
    ```

    Response :

    ```
      {
            "data": "Started cms scan for <N> installations"
            "error": <null|err_message>,
            "success": <true|false>
       }

    ```
    - Response (If no installations can be scanned):

    ```
        {"data":null,"error":"No new installation are there for scan","success":true}
    ```
