#!/usr/bin/python

import cgi
import cgitb; cgitb.enable()
import Run_Info_Diff

W  = '\033[0m'  # white (normal)
R  = '\033[31m' # red
G  = '\033[32m' # green

def getHeader():
    header = """
            <html>
                <head>
                    <title>Runinfo Diff</title> 
                </head>
                <body>
            """
    return header



def getFooter():
  footer =  """
            <!-- begin footer -->
            </body>
        </html>
       """
  return footer


form = cgi.FieldStorage()

runnumber1 = form.getvalue('runnumber1')
runnumber2 = form.getvalue('runnumber2')

body = Run_Info_Diff.main(["remote_run", runnumber1, runnumber2])
if body is not None:
    body_list=body.split("\n")
else:
    body_list = ["Diff was empty, all queried parameters are unchanged"]

print "Content-type: text/html\n\n"
print getHeader()
print "<span style=\"font-size:250%;\">Diff of run " + str(runnumber1) + " and run " + str(runnumber2) + "</span><br><br>"
for line in body_list:
    if line == "":
        continue
    elif line[0] == "+":
        print "<span style=\"color:green;\">"+line+"</span>"+"<br>"
    elif line[0] == "-":
        print "<span style=\"color:red;\">"+line+"</span>"+"<br>"
    else:
        if line == "diff truncated for clarity":
	    print line+"<br><br>"
	else:
	    print line+"<br>" 

print getFooter()














