#!/usr/bin/python

import cgi
#import cgitb; cgitb.enable()
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
    body = Run_Info_Diff.main(["remote_run_html", runnumber1, runnumber2, partitions,True])
    if body is not None:
        body_list=body.split("\n")
    else:
        body_list = ["Diff was empty, all queried parameters are unchanged"]

    print "Content-type: text/html\n\n"
    print viewDiffer.getHeader()

    print """
      <style>
        body {
           font-family: Consolas,monaco,monospace; 
        }
        table {
          font-size: 12px;
        }
        .diff td{
           padding-right: 8px;
         }
        .diff_add {
          background-color: #ddffdd;
        }
        .diff_chg {
          background-color: #ffffbb;
        }
        .diff_sub {
          background-color: #ffdddd;
        }
      </style>
    """
    print "<span style=\"font-size:250%;\">Diff of run " + str(runnumber1) + " and run " + str(runnumber2) + "</span><br><br>"

    print body    
    #for line in body_list:
    #    if line == "":
    #        continue
    #    else:
    #        viewDiffer.color_print(line)

    print "<br><br>"
    viewDiffer.print_form(runnumber1, runnumber2, partitions, "/cgi-bin/RunInfoDiffer/truncated_Diff.py", "Click for truncated diff")
    print viewDiffer.getFooter()

else:
    print "Content-type: text/html\n\n"
    print viewDiffer.getHeader()
    print "Please don't do that it's rude"
    print viewDiffer.getFooter()


