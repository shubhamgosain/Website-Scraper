-- CMS scanner
--
-- Shubham Gosain

--CREATE DATABASE scraper ENCODING = 'UTF-8';

-- \connect scraper

-- DROP TABLE IF EXISTS domain;
-- DROP TABLE IF EXISTS subdomain;
-- DROP TABLE IF EXISTS cms_type;
-- DROP TABLE IF EXISTS cms_version;
-- DROP TABLE IF EXISTS scan_date;
-- DROP TABLE IF EXISTS cms;

CREATE TABLE domain (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE subdomain (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE cms_name (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE cms_type (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE cms_identifier (
    id SERIAL NOT NULL PRIMARY KEY,
    name TEXT NOT NULL UNIQUE
);

CREATE TABLE cms (
    id SERIAL NOT NULL PRIMARY KEY,
    scan_time TIMESTAMPTZ,
    domain_id INT8 NOT NULL REFERENCES domain (id) ON DELETE CASCADE,
    subdomain_id INT8 NOT NULL REFERENCES subdomain (id) ON DELETE CASCADE,
    cms_name_id INT8 REFERENCES cms_name (id) ON DELETE CASCADE,
    cms_type_id INT8 REFERENCES cms_type (id) ON DELETE CASCADE,
    cms_identifier_id INT8 REFERENCES cms_identifier (id) ON DELETE CASCADE,
    cms_found_time TIMESTAMPTZ,
    language TEXT,
    site_information JSONB,
    INDEX (domain_id, subdomain_id),
    INDEX (cms_type_id, domain_id, subdomain_id)
);

CREATE VIEW cms_view (domain, subdomain, scan_time, cms_name, cms_type, cms_identifier, cms_found_time, language, site_information)  AS (SELECT q4.domain, q4.subdomain, q4.scan_time, q4.cms_name, cms_type.name AS "cms_type", q4.cms_identifier, q4.cms_found_time, q4.language, q4.site_information FROM (SELECT q3.domain, q3.subdomain, q3.scan_time, q3.cms_name, q3.cms_type_id, q3.cms_identifier_id, q3.cms_found_time, q3.language, q3.site_information, cms_identifier.name AS "cms_identifier" FROM (SELECT q2.domain, q2.subdomain, q2.scan_time, q2.cms_type_id, q2.cms_identifier_id, q2.cms_found_time, q2.language, q2.site_information, cc.name AS "cms_name" FROM (SELECT s.name AS subdomain, q1.domain, q1.scan_time, q1.cms_name_id, q1.cms_type_id, q1.cms_identifier_id, q1.cms_found_time, q1.language, q1.site_information FROM (SELECT d.name AS domain, c.subdomain_id, c.scan_time, c.cms_name_id, c.cms_type_id, c.cms_identifier_id, c.cms_found_time, c.language, c.site_information FROM domain AS d INNER JOIN cms AS c ON d.id = c.domain_id) AS q1 INNER JOIN subdomain AS s ON s.id = q1.subdomain_id) AS q2 LEFT JOIN cms_name AS cc ON cc.id = q2.cms_name_id) q3 LEFT JOIN cms_identifier ON q3.cms_identifier_id=cms_identifier.id) q4 LEFT JOIN cms_type ON q4.cms_type_id=cms_type.id);