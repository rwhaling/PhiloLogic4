#!/usr/bin/env python

import os
from philologic.DB import DB
import sys
import socket
import re
import hashlib
import time
from wsgi_handler import WSGIHandler

def check_access(environ, config, db):
    incoming_address = environ['REMOTE_ADDR']
    access = {}
    access_file = config.db_path + '/data/' + config['access_file']
    if not os.path.isfile(access_file):
        return make_token(incoming_address, db)
    else:
        execfile(access_file, globals(), access)
        domain_list = set(access["domain_list"])
        blocked_ips = set(access["blocked_ips"])

        fq_domain_name = socket.getfqdn(incoming_address).split(',')[-1]
        edit_domain = re.split('\.', fq_domain_name)

        if re.match('edu', edit_domain[-1]):
            match_domain = '.'.join([edit_domain[-2], edit_domain[-1]])
        else:
            if len(edit_domain) == 2:
                match_domain = '.'.join([edit_domain[-2], edit_domain[-1]])
            else:
                match_domain = fq_domain_name

        access_granted = True
        if incoming_address not in blocked_ips:
            if incoming_address in domain_list or match_domain in domain_list:
                access_granted = True  # We disable access control
            else:
                access_granted = False
        if access_granted == True:
            return make_token(incoming_address, db)
        else:
            return ()
        
def login_access(environ, config, db, headers):
    request = WSGIHandler(db, environ)
    if request.authenticated:
        access = True
    else:
        if request.username and request.password:
            access = check_login_info(config, request)
            if access:
                incoming_address = environ['REMOTE_ADDR']
                token = make_token(incoming_address, db)
                if token:
                    h, ts = token
                    headers.append( ("Set-Cookie", "hash=%s" % h) )
                    headers.append( ("Set-Cookie", "timestamp=%s" % ts) )
        else:
            access = False
    return access, headers

def check_login_info(config, request):
    try:
        password_file = open(config.db_path + "/data/logins.txt")
    except IOError:
        return (True, default_reports)
    access = False
    for line in password_file:
        fields = line.strip().split('\t')
        user = fields[0]
        passwd = fields[1]
        if user == request.username:
            if passwd == request.password:
                access = True
                break
            else:
                access = False
                break
    return access

def make_token(incoming_address, db):
    h = hashlib.md5()
    h.update(incoming_address)
    now = str(time.time())
    h.update(now)
    secret = db.locals.secret
    h.update(secret)
    return (h.hexdigest(), now)
