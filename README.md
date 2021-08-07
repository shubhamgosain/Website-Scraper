# Website Scraper

A system to execute regular HTTP based scans on websites to gain the site insights. System need to be provided with the subdomain and domain which is later scraped over regular intervals.

Application logic can be extended and modified further to work according to a specific requirement. A website can be scanned using the API endpoints given under the [API docs](https://github.com/shubhamgosain/Website-Scraper/blob/master/docs/API.md)


## Development Setup

In order to run a local development setup, the running system need to fulfill following app dependencies :-


#### Local CockroachDB instance

To setup local database, install docker and running the setup-db script. It will run a local docker CockroachDB instance and import the scraper db schema to it.

    $ ./dbschema/setup-db.sh

One can access the database with

    $ psql 'postgresql://root@localhost:26257/scraper?sslmode=disable'


#### Python import dependencies

Python app dependencies can be easily setup inside a python virtual environment using pipenv inside the project repository to make all dependencies ready,

    $ pipenv install


Also update the config used by application and edit file **src/scraper/config/config.py** to use **development.json** instead of deafult config.json.

Once config changes are done and database is ready, app can be up and running with

    $ pipenv run ./src/scraper_app
