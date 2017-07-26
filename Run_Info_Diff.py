#!/var/bin/python 
import sys

import cgi
import cgitb

import cx_Oracle
import logging
import time
import difflib
import os
from operator import itemgetter
import subprocess 

W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green

has_changed = False

fields = []

#get parameters from file and add them to a list 
parameters_file = open("diffed_parameters.txt","r")
for line in parameters_file:
    if line[0] != "#":
        categories = line.split(":")
	if len(categories) > 1:
	    parameter = categories[0].split(" ")[0]
            prefixes = categories[1].split("\n")[0].split(" ")
            for elem in prefixes:
                if elem != "":
                    field = 'CMS.' + elem + ':' + parameter
                    fields.append(field)

parameters_file.close()


#query runinfo db to get value of all specified parameters
def get_fields(runum):
    query_return_values = {}
    for field in fields:
         try:
            SQLstatement = 'SELECT value, runsession_parameter_id FROM runsession_string WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\''+field+'\'))'
            cur.execute(SQLstatement)
            query_result = cur.fetchall()
            if len(query_result) > 1:
                query_result.sort(key=itemgetter(1))
            if query_result != []:
                query_result = query_result[0][0].read()
                query_return_values[field] = query_result
            else:
                query_return_values[field] = ""
         except Exception as e:
            query_return_values[field] = "Query error encountered"
            logging.exception(e)
            print e
    return query_return_values

#compare sets of values to  get diff between them
def runinfo_differ(old_parameters, new_parameters):
    global has_changed
    changed_parameters = {}
    if old_parameters==new_parameters:
        has_changed = False
        return
    else:
        message = ""   
        for key in old_parameters:
            if old_parameters[key]==new_parameters[key]:
                continue
            else:
                old_string = str(old_parameters[key]).strip().splitlines()
                new_string = str(new_parameters[key]).strip().splitlines()
                #get diff between two strings
		d=difflib.Differ()
                changes = list(d.compare(old_string, new_string))
		#extract relevant lines for message from diff
                diff_with_context = trim_changes(changes)
		#condense diff so that identical diffs are reported together
                changed_parameters.setdefault(tuple(diff_with_context), []).append(key) 
        final_diff = ""
        for key in changed_parameters:
	    #split condensed diff by parameter (same parameter in different partitions stay together)
	    split_by_parameter = {}
            for value in changed_parameters[key]:
		split_by_parameter.setdefault(value.split(":")[1], []).append(value)
	    #get final message
	    for parameter in split_by_parameter:
                if len(diff_with_context)!=0:
                    final_diff += format_diff(parameter + " in " + ", ".join(list(map(lambda x: x.split(":")[0].split(".")[1], split_by_parameter[parameter]))), list(key))
        has_changed = True
        return final_diff

#remove excess lines that appear in origional diff
def trim_changes(changes):
    trimmed = []
    #remove all lines are not changed or possible context
    for elem in changes:
        if elem[0]=="+" or elem[0]=="-" or ("{" in elem and "}" not in elem):
            trimmed.append(elem)
    context_diff = []
    #remove excess possible context so only context around changed line remains
    for i in range(0,len(trimmed)):
        elem = trimmed[i]
        if elem[0] == "+" or elem[0] == "-":
            context_diff.append(trimmed[i])
        elif elem[0]==" " and ("{" in elem) and (i<len(trimmed)-1):
                if trimmed[i+1][0]!=" " and "#" not in trimmed[i+1]:
                    context_diff.append(trimmed[i])
    return context_diff

#format message
def format_diff(parameter, message):
    diff_value = ""
    #print(parameter + ' changed:\n')
    diff_value += parameter + ' has changed:\n'
    number_of_lines = len(message)
    for i in range(0,10):
        line = message[i]
        if line[0] == "+":
            #print(G+line+W)
            diff_value += line+"\n"
        elif line[0] == "-":
            #print(R+line+W)
            diff_value += line+"\n"
        elif line[0] == " ":
            #print(line)
            diff_value += line+"\n"
	if (i == 9  and number_of_lines > 10):
            #print "diff truncated for clarity"
            diff_value += "diff truncated for clarity\n"
        elif (i == number_of_lines-1):
            break
    return diff_value

#search for most recent global runnumber
def get_global_runnumber():
    cur.execute('SELECT MAX(RUNNUMBER) FROM RUNSESSION_PARAMETER')
    runum = cur.fetchall()[0][0]
    is_global = False
    #loop backwards through runs until global run is found
    while is_global == False:
        SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\'CMS.HCAL_LEVEL_1:FM_FULLPATH\'))'
        cur.execute(SQL)
        parameter_value = cur.fetchall()
        if parameter_value != []:
            path = parameter_value[0][0].read()
            #print path
            if "/hcalpro/Global/" in path:
                is_global = True
        runum -= 1
    return runum + 1

def send_notification(message):
    subprocess.call(["./mailOut.pl", "ciaran_godfrey", "Run Parameters Changed", message])

#main run loop for automatic alarmer
def local_execute():
    #previous_runnumber = get_global_runnumber()
    previous_runnumber = 299020
    previous_parameter_values = get_fields(previous_runnumber)
    count = 0
    while count < 10:
        count += 1
        #recent_runnumber = get_global_runnumber()
	recent_runnumber = 299025
	if recent_runnumber != previous_runnumber:
            new_parameter_values = get_fields(recent_runnumber)
	    difference = runinfo_differ(previous_parameter_values, new_parameter_values)
	    if has_changed:
		url = "http://hcalmon.cms/cgi-bin/RunInfoDiffer/viewDiffer.py?runnumber1="+str(previous_runnumber)+"&runnumber2="+str(recent_runnumber)
		difference = "For colored message follow link at bottom of page \n\n"+ difference
                difference += "\n" + url
		send_notification(difference)
		log = open("BotUrlLog.txt","a")
		log.write("\n"+url)
		log.close()
                previous_parameter_values.clear()
                previous_parameter_values.update(new_parameter_values)
        time.sleep(60)

#run for web interface
def remote_execute(runnumber_1, runnumber_2):
    return runinfo_differ(get_fields(runnumber_1), get_fields(runnumber_2))

#control database conection and decide on run mode
def main(argv):
    try:
	password_file = open("database_pwd","r")
        password = password_file.readline().split("\n")[0]
	password_file.close()
        database = "cms_hcl_runinfo/%s@cms_rcms" % password
        connection = cx_Oracle.connect(database)
        global cur
        cur = connection.cursor()    
        run_method = argv[0]
        if run_method == "local_run":
            return local_execute()
        elif run_method == "remote_run":
            runnum1 = argv[1]
            runnum2 = argv[2]
            return remote_execute(runnum1, runnum2)
    except BaseException as e:
        logging.exception(e)
    
    finally:
        cur.close()
        connection.close()

if __name__ == "__main__":
    main(sys.argv[1:])















