import cx_Oracle
import logging
import time
import difflib

password = raw_input("database password:")
database = "cms_hcl_test_runinfo/%s@cms_orcoff_prep" % password


connection = cx_Oracle.connect(database)
cur = connection.cursor()

#tab = cur.execute('SELECT RUNNUMBER FROM RUNNUMBERTBL WHERE rownum=1')
#tab = cur.execute('SELECT MAX(RUNNUMBER) FROM RUNSESSION_PARAMETER')
#tables = cur.fetchall()
#print tables


fields = ['CMS.HCAL_HBHEa:HCAL_CFGSCRIPT','CMS.HCAL_LEVEL_1:HCAL_CFGSCRIPT','CMS.HCAL_LASER:HCAL_CFGSCRIPT','CMS.HCAL_HBHEb:HCAL_CFGSCRIPT','CMS.HCAL_HO:HCAL_CFGSCRIPT','CMS.HCAL_HBHEc:HCAL_CFGSCRIPT','CMS.HCAL_HF:HCAL_CFGSCRIPT','CMS.HCAL_HBHEa:CFGDOC_TXT','CMS.HCAL_HBHEb:CFGDOC_TXT','CMS.HCAL_HBHEc:CFGDOC_TXT','CMS.HCAL_LASER:CFGDOC_TXT','CMS.HCAL_HO:CFGDOC_TXT','CMS.HF:CFGDOC_TXT']
def get_fields(runum):
    value = {}
    for field in fields:
        try:
            SQLstatement = 'SELECT value FROM runsession_string  WHERE runsession_parameter_id=(SELECT id FROM runsession_parameter WHERE (runnumber='+str(runum)+' AND name=\''+field+'\'))'
            r = cur.execute(SQLstatement)
            result = cur.fetchall()
            if result != []:
                result = result[0][0].read()
            value[field] = result
        except Exception as e:
            value[field] = "Field does not exist"
            print e
    return value

def diff(old, new):
    if old==new:
        return None
    else:
        message = ""	
        for key in old:
            if old[key]==new[key]:
                continue
            else:
                old_string = str(old[key]).strip().splitlines()
                new_string = str(new[key]).strip().splitlines()
                d = difflib.Differ()
                result = list(d.compare(old_string, new_string))
                message = key + ' changed:\n'
                for line in result:
                    if line[0] == "+" or line[0] == "-":
                        message += line + '\n'
        return message

try:
    cur.execute('SELECT runnumber FROM RUNSESSION_PARAMETER where runnumber=1000027333')
    previous_runnumber = cur.fetchall()[0][0]
    previous_value = get_fields(previous_runnumber)
    count = 0
    while count < 5:
        count += 1
        cur.execute('SELECT MAX(RUNNUMBER) FROM RUNSESSION_PARAMETER')
        recent_runnumber = cur.fetchall()[0][0]
        if recent_runnumber != previous_runnumber:
            new_value = get_fields(recent_runnumber)
            difference = diff(previous_value, new_value)
    	    if difference != None:
                print difference
                previous_value.clear()
                previous_value.update(new_value)
        time.sleep(10)
except Exception as e:
    logging.exception(e)

cur.close()
connection.close()

