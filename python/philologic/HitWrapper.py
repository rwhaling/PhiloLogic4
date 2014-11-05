#!/usr/bin/python

import time
import sys
from itertools import islice
import sqlite3

obj_dict = {'doc': 1, 'div1': 2, 'div2': 3, 'div3': 4,
            'para': 5, 'sent': 6, 'word': 7}

class HitWrapper(object):

    def __init__(self, hit, db, obj_type=False, encoding=None):
        self.db = db
        self.hit = hit
        #print >> sys.stderr, self.hit
        self.philo_id = hit
        if obj_type:
            self.type = obj_type
        else:
            try:
                length = len(hit[:hit.index(0)])
            except ValueError:
                length = len(hit)
            if length >= 7: length = 7
            self.type = [k for k in obj_dict if obj_dict[k] == length][0]

        self.bytes = []
        self.wordids = []
        if self.type == "word" and len(list(hit)) == 7:
            self.wordids.append(list(hit))
            self.bytes = [self.byte_start]
        else:
            word_data = list(hit)[7:]
            while word_data:
                try:
                    self.wordids.append(word_data.pop(0))
                    self.bytes.append(word_data.pop(0))
                except IndexError:
                    pass

        self.bytes.sort()

    def __getitem__(self, key):
        if key in obj_dict:
            return ObjectWrapper(self.hit, self.db, obj_type=key,encoding=self.encoding)
        else:
            return self.__metadata_lookup(key)
    
    def __getattr__(self, name):
        if name in obj_dict:
            return ObjectWrapper(self.hit, self.db, obj_type=name,encoding=self.encoding)
        else:
            return self.__metadata_lookup(name)
        
    def __metadata_lookup(self, field):
        width = 7
        philo_id = self.philo_id[:width]
        metadata = None
        while width:
            try:
                metadata = self.db.get_id_lowlevel(philo_id[:width])[field]
            except (TypeError,IndexError):
                ## if self.db[philo_id[:width]] returns None
                width -= 1
                continue
            except sqlite3.OperationalError:
                break
            if metadata != None:
                break
            width -= 1
        if metadata == None:
            metadata = ''
        if self.db.encoding:
            try:
                return metadata.decode(self.db.encoding, 'ignore')
            except AttributeError:
                ## if the metadata is an integer
                return metadata
        else:
            return metadata
    
    def get_page(self):
        if self.type == "word" and len(list(self.hit)) > 7:
            page_i = self.hit[6]
        else:
            page_i = self["page"]
        if page_i:
            page_id = [self.hit[0],0,0,0,0,0,0,0,page_i]
            return PageWrapper(page_id)
        else:
            return None
           
class ObjectWrapper(object):
    
    def __init__(self, hit, db, obj_type=False, encoding=None):
        self.db = db
        self.hit = hit
        if obj_type:
            self.philo_id = hit[:obj_dict[obj_type]]
            self.type = obj_type
        else:
            self.philo_id = hit
            try:
                length = len(hit[:hit.index(0)])
            except ValueError:
                length = len(hit)
            self.type = [k for k in obj_dict if obj_dict[k] == length][0]
        self.bytes = bytes        

    def __getitem__(self, key):
        if key in obj_dict:
            return ObjectWrapper(self.hit, self.db, key,encoding=self.encoding)
        else:
            return self.__metadata_lookup(key)
        
    def __getattr__(self, name):
        if name in obj_dict:
            return ObjectWrapper(self.hit, self.db, name,encoding=self.encoding)
        else:
            return self.__metadata_lookup(name)
        
    def __metadata_lookup(self, field):
        metadata = None
        try:
            metadata = self.db.get_id_lowlevel(self.philo_id)[field]
        except (TypeError,IndexError):
            ## if self.db[self.philo_id[:width]] returns None]
            metadata = ''
        except sqlite3.OperationalError:
            metadata = ''            
        if metadata == None:
            metadata = ''
        if self.db.encoding:
            try:
                return metadata.decode(self.db.encoding, 'ignore')
            except AttributeError:
                ## if the metadata is an integer
                return metadata
        else:
            return metadata

    def get_page(self):
        if self.type == "word" and len(list(self.hit)) > 7:
            page_i = self.hit[6]
        else:
            page_i = self["page"]
        if page_i:
            page_id = [self.hit[0],0,0,0,0,0,0,0,page_i]
            return PageWrapper(page_id)
        else:
            return None
            
class PageWrapper(object):
    def__init__(self,id,db):
        self.db = db
        self.hit = id
        self.philo_id = id
        self_type = "page"
        self.row = None
        self.bytes = []
        
    def __getitem__(self,key):
        if self.row == None:
            self.row = self.db.get_page(self.philo_id)
        return __safe__lookup(row,key,self.db.encoding)

    def __getattr__(self,name):
        if self.row == None:
            self.row = self.db.get_page(self.philo_id)
        return __safe__lookup(row,name,self.db.encoding)



def __safe__lookup(row,field,encoding="utf-8"):
    metadata = ""
    try: 
        metadata = row[field]
    except:
        pass
    metadata_string = ""
    try: 
        metadata_string = metadata.decode(encoding,"ignore")
    except AttributeError:
        metadata_string = str(metadata).decode(encoding,"ignore")
    return metadata_string