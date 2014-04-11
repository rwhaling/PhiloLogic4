#!/usr/bin/env python
import sys
import os
import subprocess
from datetime import datetime
import struct
import HitList
import re
import unicodedata
from QuerySyntax import parse_query, group_terms

def query(db,terms,corpus_file=None,corpus_size=0,method=None,method_arg=None,limit=3000,filename=""):
    sys.stdout.flush()
    tstart = datetime.now()
    print >> sys.stderr, "STARTING query for %s at" % repr(terms), tstart

    parsed = parse_query(terms)
    grouped = group_terms(parsed)
    split = split_terms(grouped)

#    expandedterms = format_query(terms,db) # format_query is SLOW!   
    print >> sys.stderr, "QUERY FORMATTED at ", datetime.now() - tstart
    words_per_hit = len(split)
    print >> sys.stderr, "QUERY SPLIT at ", datetime.now() - tstart, repr(split)
    origpid = os.getpid()
    if not filename:
        hfile = str(origpid) + ".hitlist"
    dir = db.locals["db_path"] + "/hitlists/"
    filename = filename or (dir + hfile)
    hl = open(filename, "w")
    err = open("/dev/null", "w")
    freq_file = db.locals["db_path"]+"/frequencies/normalized_word_frequencies"
    pid = os.fork()
    if pid == 0:
        os.umask(0)
        os.chdir(dir)
        os.setsid()
        pid = os.fork()
        if pid > 0:
            os._exit(0)
        else:
            #now we're detached from the parent, and can do our work.
            print >> sys.stderr, "WORKER DETACHED at ", datetime.now() - tstart
            args = ["search4", db.path,"--limit",str(limit)]
            if corpus_file and corpus_size:
                args.extend(("--corpusfile", corpus_file , "--corpussize" , str(corpus_size)))
            if method and method_arg:
                args.extend((method,str(method_arg)))
            worker = subprocess.Popen(args,stdin=subprocess.PIPE,stdout=hl,stderr=err)
            print >> sys.stderr, "SUBPROC RUNNING at ", datetime.now() - tstart
#            worker.communicate(format_query(terms,db))
# ouch! I was running format_query twice!
#            worker.communicate(expandedterms) # I/O is taking a long time too!            
            print >> sys.stderr, "STARTING QUERY EXPANSION at ", datetime.now() - tstart
            expand_query(split,freq_file,worker.stdin)
            worker.stdin.close()
            print >> sys.stderr, "SUBPROC INPUT CLOSED at ", datetime.now() - tstart
            worker.wait()
            #do something to mark query as finished
            flag = open(filename + ".done","w")
            flag.write(" ".join(args) + "\n")
            flag.close()
            print >> sys.stderr, "SUBPROC DONE at ", datetime.now() - tstart
            os._exit(0)
    else:
        hl.close()
        return HitList.HitList(filename,words_per_hit,db)

def split_terms(grouped):
    split = []
    for group in grouped:
        if len(group) == 1:
            kind,token = group[0]
            if kind == "QUOTE" and token.find(" ") > 1: #we can split quotes on spaces if there is no OR
                for split_tok in token[1:-1].split(" "):
                    split.append( ("QUOTE",'"'+split_tok+'"' ) )
                continue
            elif kind == "RANGE":
                for split_tok in token.split("-"):
                    split_group.append( ("TERM",split_tok) )
                continue
        split.append(group)
    return split

def expand_query(split, freq_file, dest_fh):
    first = True
    for group in split:
        if first == True:
            first = False
        else: # bare newline starts a new group, except the first
            dest_fh.write("\n")
        # if we have multiple terms in the group, should check to make sure they don't repeat
        # if it's a single term, we can skip that
        if len(group) == 1: # if we have a one-token group, don't need to sort and uniq
            filters = subprocess.Popen("cut -f 2", stdin=subprocess.PIPE,stdout=dest_fh, shell=True)            
        else: # otherwise we need to merge the egrep results and remove duplicates.
            filters = subprocess.Popen("cut -f 2 | sort | uniq", stdin=subprocess.PIPE,stdout=dest.fh, shell=True)

        for kind,token in group: # or, splits, and ranges should have been taken care of by now.
            if kind == "TERM" or kind == "RANGE":
                norm_tok = token.decode("utf-8").lower()
                norm_tok = [i for i in unicodedata.normalize("NFKD",norm_tok) if not unicodedata.combining(i)]
                norm_tok = "".join(norm_tok).encode("utf-8")                
                grep_command = ['egrep', '-wi', "^%s" % norm_tok, '%s' % freq_file]
                grep_proc = subprocess.Popen(grep_command,stdout=filters.stdin)
                grep_proc.wait()
            elif kind == "QUOTE":
                filters.write(token + "\n") 
            # what to do about NOT?
        filters.stdin.close()    
        filters.wait()
    return

def format_parsed_query(parsed_split,db):
    command = ""
    clauses = [[]]
    prior_label = "OR"
#        print parsed_split
    for label, token in parsed_split:
        if label == "QUOTE_S":
            if prior_label != "OR":
                clauses.append([])
                command += "\n"
            subtokens = token.split(" ")
            clauses[-1] += subtokens
            command += "\n".join(subt+"\n" for subt in subtokens)
        elif label == "TERM":
            if prior_label != "OR":
                clauses.append([])
                command += "\n"
            expanded = []
            norm_tok = token.decode("utf-8").lower()
            norm_tok = [i for i in unicodedata.normalize("NFKD",norm_tok) if not unicodedata.combining(i)]
            norm_tok = "".join(norm_tok).encode("utf-8")
            #print >> sys.stderr, "TERMS:", norm_tok
            matches = word_pattern_search(norm_tok,db.locals["db_path"]+"/frequencies/normalized_word_frequencies")
            #print >> sys.stderr, "MATCHES:"
            #print >> sys.stderr, matches                
            for m in matches:
                if m not in expanded:
                    expanded += [m]                                              
            #subtokens should be expanded against word_frequencies here
            #AFTER unicode-stripping, of course.
            clauses[-1] += expanded
            command += "\n".join(subt for subt in expanded)
            if expanded:
                command += "\n"
#            print >> sys.stderr, expanded
        elif label == "NOT":
            #Need to decide something to do with NOT
            break
        prior_label = label
#        print clauses
#        print "\n".join("\n".join(c for c in clause) for clause in clauses) 
#    print >> sys.stderr, "COMMAND", command
    return command

def format_query(qstring,db):
    parsed = parse_query(qstring)
    parsed_split = []
    for label,token in parsed:
        l,t = label,token
        if l == "QUOTE":
            subtokens = t[1:-1].split(" ")
            parsed_split += [("QUOTE_S",sub_t) for sub_t in subtokens if sub_t]
        else:
            parsed_split += [(l,t)]
    command = format_parsed_query(parsed_split,db)
    #print >> sys.stderr, "QUERY_COMMAND",repr(command)
    return command

def word_pattern_search(term, path):
    command = ['egrep', '-wi', "^%s" % term, '%s' % path]
    process = subprocess.Popen(command, stdout=subprocess.PIPE)
    match, stderr = process.communicate()
    #print >> sys.stderr, "RESULTS:",repr(match)
    match = match.split('\n')
    match.remove('')
    ## HACK: The extra decode/encode are there to fix errors when this list is converted to a json object
    #return [m.split("\t")[1].strip().decode('utf-8', 'ignore').encode('utf-8') for m in match]
    return [m.split("\t")[1].strip() for m in match]

def old_format_query(qstring):
    q = [level.split("|") for level in qstring.split(" ") ]
    qs = ""
    for level in q:
        for token in level:
            qs += token + "\n"
        qs += "\n"
    qs = qs[:-1] # to trim off the last newline.  just a quirk of the language.
    return qs
    
def get_context(file,offset,file_length,width,f):
    lo = max(0,offset - width)
    breakpoint = offset - lo
    ro = min(file_length, offset + width)

    fh = open(file)
    fh.seek(lo)
    buf = fh.read(ro - lo)
    lbuf = buf[:breakpoint]
    rbuf = buf[breakpoint:]
    (word,rbuf) = re.split("[\s.;:,<>?!]",rbuf,1)
    fh.close()    

    return f.format(lbuf + "<span rend=\"preserve\" style=\"color:red\"> " + word + "</span> " + rbuf)
    
def get_object(file,start,end):
    fh = open(file)
    fh.seek(start)
    buf = fh.read(end - start)
    fh.close()
    return buf
