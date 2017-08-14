#!/var/bin/python 
import sys
import signal
import cgi
import cgitb

import cx_Oracle
import logging
import time
import difflib
import os
from operator import itemgetter
import subprocess 

import datetime
import signal

class SigTerm(SystemExit): pass

def sigterm(sig,frm): raise SigTerm

signal.signal(15,sigterm)

W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green

has_changed = False

#HO_fields = []
#HF_fields = []
#HBHEa_fields = []
#HBHEb_fields = []
#HBHEc_fields = []
#LASER_fields = []


#get parameters from file and add them to a list
def fill_list(partition):
    parameter_list = [] 
    parameters_file = open("diffed_parameters.txt","r")
    for line in parameters_file:
        if line[0] != "#":
            categories = line.split(":")
	    if len(categories) > 1:
	        parameter = categories[0].split(" ")[0]
                prefixes = categories[1].split("\n")[0].split(" ")
                for elem in prefixes:
                    if elem != "" and elem == partition:
                        field = 'CMS.' + elem + ':' + parameter
                        parameter_list.append(field)
    parameters_file.close()
    return parameter_list

HO_fields = fill_list('HCAL_HO')
HF_fields = fill_list('HCAL_HF')
HBHEa_fields = fill_list('HCAL_HBHEa')
HBHEb_fields = fill_list('HCAL_HBHEb')
HBHEc_fields = fill_list('HCAL_HBHEc')
LASER_fields = fill_list('HCAL_LASER')

parameter_map = {"HCAL_HO":HO_fields,"HCAL_HF":HF_fields,"HCAL_HBHEa":HBHEa_fields,"HCAL_HBHEb":HBHEb_fields,"HCAL_HBHEc":HBHEc_fields,"HCAL_LASER":LASER_fields}

#query runinfo db to get value of all specified parameters
def get_fields(runum,parameters):
    query_return_values = {}
    for field in parameters:
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
        return None
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

#check if xdaq parameter has been published
def is_running(runnumber):
    SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runnumber)+' AND name=\'CMS.LVL0:RC_STATE\'))'
    cur.execute(SQL)
    #parameter_value = cur.fetchall()
    #print parameter_value
    #states = []
    for row in cur:
	value = row[0].read()
    	if value == "Running":
	    return True
    	else:
	    continue
    return False

def get_unmasked_partitions(runnumber):
    SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runnumber)+' AND name=\'CMS.HCAL_LEVEL_1.EMPTY_FMS\'))'
    cur.execute(SQL)
    masked_partitions = cur.fetchall()
    included_partitions = []
    for key in parameter_map:
	if key not in masked_partitions:
	     included_partitions.append(key)
    return included_partitions

def dict_is_empty(dictionary):
    for key in dictionary:
	if dictionary[key] == None:
	    continue
	else:
	    return False
    return True


def send_notification(message):
    subprocess.call(["./mailOut.pl", "ciaran_godfrey", "Run Parameters Changed", message])

#main run loop for automatic alarmer
def local_execute():
    previous_runnumber = get_global_runnumber()
    #previous_runnumber = 300898
    HO_run = previous_runnumber
    HF_run = previous_runnumber
    HBHEa_run = previous_runnumber
    HBHEb_run = previous_runnumber
    HBHEc_run = previous_runnumber
    LASER_run = previous_runnumber
    runnumber_map = {'HCAL_HO':HO_run,'HCAL_HF':HF_run,'HCAL_HBHEa':HBHEa_run,'HCAL_HBHEb':HBHEb_run,'HCAL_HBHEc':HBHEc_run,'HCAL_LASER':LASER_run}
    while True:
        recent_runnumber = get_global_runnumber()
	#recent_runnumber = 300918
	print recent_runnumber
	if recent_runnumber != previous_runnumber and is_running(recent_runnumber):
	    included_partitions = get_unmasked_partitions(recent_runnumber)
	    partition_runs = {}
	    partition_diffs = {}
	    for partition in included_partitions:
		partition_runs.setdefault(runnumber_map[partition], []).append(partition)
	    for key in partition_runs:
		temp_parameters = []
		for partition in partition_runs[key]:
		    temp_parameters.extend(parameter_map[partition])
		partition_diffs[key] = runinfo_differ(get_fields(key, temp_parameters), get_fields(recent_runnumber, temp_parameters))
	    if not dict_is_empty(partition_diffs):
		message = "All partitions diffed against last included run\n\n"
		for key in partition_runs:
		    message += "Diff of "+', '.join(partition_runs[key])+" between run "+str(key)+" and run "+str(recent_runnumber)+"\n"
		    if partition_diffs[key] != None:
			message += partition_diffs[key]
		BotInfo = []
		for key in partition_runs:
		    url = "http://hcalmon.cms/cgi-bin/RunInfoDiffer/viewDiffer.py?runnumber1="+str(key)+"&amp;runnumber2="+str(recent_runnumber)
		    for partition in partition_runs[key]:
			url += "&amp;partition="+partition
		    BotInfo.append(url)
		#print str(BotInfo)
	        send_notification(message)
	        log = open("BotUrlLog.html","r+")
		lines = log.readlines()
		log.seek(0)
		log.truncate()
		max_lines = 100
		if len(lines) >= max_lines:
		    lines.pop(0)
		lines.append(str(BotInfo)+"<br>"+"\n")
		for line in lines:
		    log.write("%s" % line)
		log.close()
                for key in included_partitions:
		    runnumber_map[key] = recent_runnumber
        time.sleep(120)

#run for web interface
def remote_execute(runnumber_1, runnumber_2, used_partitions):
    parameters = []
    for key in parameter_map:
	if key in used_partitions:
	    parameters.extend(parameter_map[key])
    return runinfo_differ(get_fields(runnumber_1, parameters), get_fields(runnumber_2, parameters))

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
	    used_partitions = argv[3]
            return remote_execute(runnum1, runnum2, used_partitions)
    
    except BaseException as e:
        logging.exception(e)
    
    finally:
        cur.close()
        connection.close()
	print time.strftime("%H:%M:%S")

if __name__ == "__main__":
    main(sys.argv[1:])















