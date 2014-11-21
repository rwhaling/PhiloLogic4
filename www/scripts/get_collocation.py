#!/usr/bin/env python

import os
import sys
import urlparse
sys.path.append('..')
from philologic.DB import DB
from functions.wsgi_handler import WSGIHandler
from wsgiref.handlers import CGIHandler
import reports as r
import functions as f
import cgi
from json import dumps

def collocation_fetcher(environ,start_response):
    status = '200 OK'
    headers = [('Content-type', 'application/json; charset=UTF-8'),("Access-Control-Allow-Origin","*")]
    start_response(status,headers)
    config = f.WebConfig()
    db = DB(config.db_path + '/data/')
    request = WSGIHandler(db, environ)
    hits = db.query(request["q"],request["method"],request["arg"],**request.metadata)
    config = f.WebConfig()
    collocation_object = r.fetch_collocation(hits, request, db, config)
    yield dumps(collocation_object)

if __name__ == "__main__":
    CGIHandler().run(collocation_fetcher)