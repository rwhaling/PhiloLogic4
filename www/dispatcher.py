#!/usr/bin/env python

import sys
import reports
import traceback
from functions import access_control
from wsgiref.handlers import CGIHandler
from cgi import FieldStorage
from functions import clean_hitlists
import functions as f
from philologic.DB import DB
from functions.wsgi_handler import WSGIHandler


def philo_dispatcher(environ,start_response):
    report = FieldStorage().getvalue('report')
    access = access_control(environ, start_response)
    config = f.WebConfig()
    db = DB(config.db_path + '/data/')
    request = WSGIHandler(db, environ)
    if access:
        try:                
            if request.content_type == "json":
                try:
                    path_components = [c for c in environ["PATH_INFO"].split("/") if c]
                except:
                    path_components = []
                if path_components:
                    yield ''.join([i for i in getattr(reports, report or "navigation")(environ,start_response)])
                else:
                    yield ''.join([i for i in getattr(reports, report or "concordance")(environ,start_response)])
            else:
                yield f.webApp.angular(environ,start_response)
        except Exception as e:
            traceback.print_exc()
            yield getattr(reports, "error")(environ,start_response)
    else:
        yield getattr(reports, 'access')(environ, start_response)
        
if __name__ == "__main__":
    CGIHandler().run(philo_dispatcher)
    clean_hitlists()
