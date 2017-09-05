#!/usr/bin/python

import cgi
import cgitb; cgitb.enable()
import Run_Info_Diff
import viewDiffer

form = cgi.FieldStorage()

runnumber1 = form.getvalue('runnumber1')
runnumber2 = form.getvalue('runnumber2')
partitions = form.getlist('partition')

#runnumber1 = 301276
#runnumber2 = 301279
#partitions = ["HCAL_HO", "HCAL_HF", "HCAL_HBHEa", "HCAL_HBHEb", "HCAL_HBHEc", "HCAL_LASER"]


if viewDiffer.is_an_int(runnumber1) and viewDiffer.is_an_int(runnumber2) and int(runnumber1)>0 and int(runnumber2)>0:
    body = Run_Info_Diff.main(["remote_run", runnumber1, runnumber2, partitions])
    if body is not None:
        body_list=body.split("\n")
    else:
        body_list = ["Diff was empty, all queried parameters are unchanged"]

    print "Content-type: text/html\n\n"
    print viewDiffer.getHeader()
    print "<span style=\"font-size:250%;\">Diff of run " + str(runnumber1) + " and run " + str(runnumber2) + "</span><br><br>"
    
    counter = 0
   
    for line in body_list:
        if line == "":
            continue
        elif "has changed" in line:
            viewDiffer.color_print(line)
            counter = 0
        elif counter < 20:
            viewDiffer.color_print(line)
            counter += 1
        elif counter == 20:
            print "diff truncated for clarity<br><br>"
            counter += 1

    print "<br><br>"
    viewDiffer.print_form(runnumber1, runnumber2, partitions, "/cgi-bin/RunInfoDiffer/complete_Diff.py", "Click for complete diff") 
    print viewDiffer.getFooter()

else:
    print "Content-type: text/html\n\n"
    print viewDiffer.getHeader()
    print "Please don't do that it's rude"
    print viewDiffer.getFooter()


