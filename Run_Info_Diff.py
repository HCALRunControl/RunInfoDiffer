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

#allow finally to run if process is killed
class SigTerm(SystemExit): pass
def sigterm(sig,frm): raise SigTerm
signal.signal(15,sigterm)

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

#parameter list for each partition
HO_fields = fill_list('HCAL_HO')
HF_fields = fill_list('HCAL_HF')
HBHE_fields = fill_list('HCAL_HBHE')
#HBHEa_fields = fill_list('HCAL_HBHEa')
#HBHEb_fields = fill_list('HCAL_HBHEb')
#HBHEc_fields = fill_list('HCAL_HBHEc')
LASER_fields = fill_list('HCAL_Laser')

#map from partition name in parameters to list names
parameter_map = {"HCAL_HO":HO_fields,"HCAL_HF":HF_fields,"HCAL_HBHE":HBHE_fields,"HCAL_LASER":LASER_fields}

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
    changed_parameters = {}
    if old_parameters==new_parameters:
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
        return final_diff

#Get html diff
def runinfo_differ_html(old_parameters, new_parameters):
    changed_parameters = []
    if old_parameters==new_parameters:
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
                diff_with_context = trim_changes(changes)

                htmlDiffer = difflib.HtmlDiff(wrapcolumn=90)
                body       = htmlDiffer.make_table(old_string, new_string, "", "", True,3)
                #body_list  = difflib.context_diff(old_string,new_string,"old","new","","",5)
                #body = ""
                #for line in body_list:
                #    body += "<br>"+line+"</br>"

                diffDict = {}
                diffDict['htmldiff']= body
                diffDict['ListOfPartitions']= [key.split(":")[0].replace("CMS.","")]
                diffDict['pamName']        = key.split(":")[1]
                diffDict['lineDiff']        = tuple(diff_with_context)
                foundSameDiff = False
                for diffs in changed_parameters:
                    if diffDict['lineDiff']==diffs['lineDiff']:
                        foundSameDiff=True
                        diffs['ListOfPartitions'].extend( diffDict['ListOfPartitions'])
                if not foundSameDiff:
                    changed_parameters.append(diffDict) 

        #changedparameters = {diff:[partitions with diff],...}
        for diffs in changed_parameters:
            message += "<br>"+diffs['pamName'] +" changed in "+ str(diffs['ListOfPartitions']) +"</br>"
            message +=diffs['htmldiff']
        return message 

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
                if trimmed[i+1][0]!=" " and "#" not in trimmed[i]:
                    context_diff.append(trimmed[i])
    return context_diff

#format message
def format_diff(parameter, message):
    diff_value = ""
    diff_value += parameter + ' has changed:\n'
    number_of_lines = len(message)
    for i in range(0,number_of_lines):
        line = message[i]
        if line[0] == "+":
            diff_value += line+"\n"
        elif line[0] == "-":
            diff_value += line+"\n"
        elif line[0] == " ":
            diff_value += line+"\n"
        """if (i == 19 and number_of_lines > 20):
            diff_value += "diff truncated for clarity\n"
        elif (i == number_of_lines-1):
            break"""
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

def is_HCAL_in(runum):
    SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\'CMS.LVL0:HCAL\'))'
    cur.execute(SQL)
    hcal_status = cur.fetchall()[0][0].read()
    print hcal_status
    if hcal_status == "In":
        return True
    else:
        return False

def is_HF_in(runum):
    SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\'CMS.LVL0:HF\'))'
    cur.execute(SQL)
    hcal_status = cur.fetchall()[0][0].read()
    if hcal_status == "In":
        return True
    else:
        return False

#check if run has entered Running state
def is_running(runnumber):
    SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runnumber)+' AND name=\'CMS.LVL0:RC_STATE\'))'
    cur.execute(SQL)
    for row in cur:
        value = row[0].read()
        if value == "Running":
            return True
        else:
            continue
    return False

#get list of included partitions
def get_unmasked_partitions(runnumber):
    for key in parameter_map:
        SQL = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id= ANY (SELECT id FROM runsession_parameter WHERE (runnumber='+str(runnumber)+' AND name=\'CMS.'+key+':EMPTY_FMS\'))'
        cur.execute(SQL)
        masked = cur.fetchall()
        if masked == []:
            continue
        masked_value = masked[0][0].read()
        masked_partitions = masked_value.split("[")[1].split("]")[0].split(", ")
        included_partitions = []
        for key in parameter_map:
            if key not in masked_partitions:
                included_partitions.append(key)
        return included_partitions
    all_partitions = list(parameter_map)
    return []

#check if all keys in dictionary have no value
def dict_is_empty(dictionary):
    for key in dictionary:
        if dictionary[key] == None:
            continue
        else:
            return False
    return True

#send mail
def send_notification(message):
    subprocess.call(["./mailOut.pl", "ciaran_godfrey", "Run Parameters Changed", message])

#main run loop for automatic alarmer
def local_execute():
    previous_runnumber = get_global_runnumber()
    #previous_runnumber = 300918
    #assign initial runnumber to each partition. Right now this does not look for inclusion so each partition must be included in one run this sees for it to work correctly
    HO_run = previous_runnumber
    HF_run = previous_runnumber
    HBHE_run = previous_runnumber
    #HBHEa_run = previous_runnumber
    #HBHEb_run = previous_runnumber
    #HBHEc_run = previous_runnumber
    LASER_run = previous_runnumber
    #map between partition name in parameter and most recent runnumber
    runnumber_map = {'HCAL_HO':HO_run,'HCAL_HF':HF_run,'HCAL_HBHE':HBHE_run,'HCAL_LASER':LASER_run}
    while True:
        #look for new global run
        recent_runnumber = get_global_runnumber()
        #recent_runnumber = 300919
        #print recent_runnumber
        #only proceed if there is a new global run that has reached the state running
        #print get_unmasked_partitions(recent_runnumber)
        if recent_runnumber != previous_runnumber and is_running(recent_runnumber):
            included_partitions = get_unmasked_partitions(recent_runnumber)
            #check if HCAL is out
            #when HCAL and HF are merged remove explicit references to HF
            #this should simply remove everything if HCAL is out
            if not is_HCAL_in(recent_runnumber):
                del included_partitions[:]
            partition_runs = {}
            partition_diffs = {}
            #get diff by partition and store them in a dictionary
            for partition in included_partitions:
                partition_runs.setdefault(runnumber_map[partition], []).append(partition)
            for key in partition_runs:
                temp_parameters = []
                for partition in partition_runs[key]:
                    temp_parameters.extend(parameter_map[partition])
                partition_diffs[key] = runinfo_differ(get_fields(key, temp_parameters), get_fields(recent_runnumber, temp_parameters))
            #only proceed if changes have been made
            if not dict_is_empty(partition_diffs):
                #build readable message
                message = "All partitions diffed against last included run\n\n"
                for key in partition_runs:
                    message += "Diff of "+', '.join(partition_runs[key])+" between run "+str(key)+" and run "+str(recent_runnumber)+"\n"
                    if partition_diffs[key] != None:
                        message += partition_diffs[key]
                BotInfo = []
                for key in partition_runs:
                    url = "http://hcalmon.cms/cgi-bin/RunInfoDiffer/truncated_Diff.py?runnumber1="+str(key)+"&amp;runnumber2="+str(recent_runnumber)
                    for partition in partition_runs[key]:
                        url += "&amp;partition="+partition
                    BotInfo.append(url)
                #send mail
                #send_notification(message)
                #write to log
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
def remote_execute(runnumber_1, runnumber_2, used_partitions,isHtml=False):
    parameters = []
    for key in parameter_map:
        if key in used_partitions:
            parameters.extend(parameter_map[key])
    if isHtml:
        return runinfo_differ_html(get_fields(runnumber_1, parameters), get_fields(runnumber_2, parameters))
    else:
        return runinfo_differ(get_fields(runnumber_1, parameters), get_fields(runnumber_2, parameters))

#control database conection and decide on run mode
def main(argv):
    try:
        password_file = open("database_pwd.txt","r")
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
        elif run_method == "remote_run_html":
            runnum1 = argv[1]
            runnum2 = argv[2]
            used_partitions = argv[3]
            return remote_execute(runnum1, runnum2, used_partitions,True)
 
    
    except BaseException as e:
        logging.exception(e)
    
    finally:
        cur.close()
        connection.close()
    print time.strftime("%H:%M:%S")

if __name__ == "__main__":
    main(sys.argv[1:])















