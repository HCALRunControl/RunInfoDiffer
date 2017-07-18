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



def getFooter():
  footer =  """
            <!-- begin footer -->
            </body>
        </html>
       """
  return footer

form =cgi.FieldStorage()

runnumber1 = form.getvalue('runnumber1')
runnumber2 = form.getvalue('runnumber2')

body = main("remote_run", runnumber1, runnumber2).split("\n")

print getHeader()
for line in body:
    if line[0] == "+":
        print(G+line+W)
    elif line[0] == "-":
        print(R+line+W)
    elif line[0] == " ":
        print(line) 

print getFooter()














