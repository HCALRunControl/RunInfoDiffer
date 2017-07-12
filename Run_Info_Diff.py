import cx_Oracle
import logging
import time
import difflib
 

W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green


password = raw_input("database password:")
 
database = "cms_hcl_test_runinfo/%s@cms_orcoff_prep" % password
connection = cx_Oracle.connect(database)
cur = connection.cursor()
 
fields = []
 
database = "cms_hcl_test_runinfo/%s@cms_orcoff_prep" % password
parameters_file = open("diffed_parameters.txt","r")
for line in parameters_file:
    if line[0] != "#":
        categories = line.split(":")
        prefixes = categories[1].split("\n")[0].split(" ")
        for elem in prefixes:
            field = 'CMS.' + elem + ':' + categories[0]
            fields.append(field)

parameters_file.close()
print(fields)

def get_fields(runum):
    query_return_values = {}
    for field in fields:
         try:
            SQLstatement = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id=(SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\''+field+'\'))'
            cur.execute(SQLstatement)
            query_result = cur.fetchall()
            if query_result != []:
                query_result = query_result[0][0].read()
                query_return_values[field] = query_result
            else:
                query_return_values[field] = ""
         except Exception as e:
            query_return_values[field] = "Field does not exist"
            print e
    return query_return_values

def runinfo_differ(old_parameters, new_parameters):
    if old_parameters==new_parameters:
        return False
    else:
        message = ""   
        for key in old_parameters:
            if old_parameters[key]==new_parameters[key]:
                continue
            else:
                old_string = str(old_parameters[key]).strip().splitlines()
                new_string = str(new_parameters[key]).strip().splitlines()
                d = difflib.Differ()
                changes = list(d.compare(old_string, new_string))
                if len(changes)!=0:
                    color_print(key, changes)
        return True

def color_print(parameter, message):
    print(parameter + ' changed:\n')
    for line in message:
        if line[0] == "+":
            print(G+line+W)
        elif line[0] == "-":
            print(R+line+W)

try:
    cur.execute('SELECT MAX(RUNNUMBER) FROM RUNSESSION_PARAMETER')
    previous_runnumber = cur.fetchall()[0][0]
    previous_parameter_values = get_fields(previous_runnumber)
    count = 0
    while count < 5:
        count += 1
        cur.execute('SELECT MAX(RUNNUMBER) FROM RUNSESSION_PARAMETER')
        recent_runnumber = cur.fetchall()[0][0]
        if recent_runnumber != previous_runnumber:
            new_parameter_values = get_fields(recent_runnumber)
            difference = runinfo_differ(previous_parameter_values, new_parameter_values)
            if difference:
                previous_parameter_values.clear()
                previous_parameter_values.update(new_parameter_values)
        time.sleep(10)
except BaseException as e:
    logging.exception(e)

finally:
    cur.close()
    connection.close()
