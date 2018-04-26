#!/usr/bin/python

import cgi
import cgitb; cgitb.enable()
import Run_Info_Diff

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

def is_an_int(data):
    try:
	int(data)
	return True
    except ValueError:
	return False


def color_print(text):
    if text == "":
        pass
    elif text[0] == "+":
        print "<span style=\"color:green;\">"+text+"</span>"+"<br>"
    elif text[0] == "-":
        print "<span style=\"color:red;\">"+text+"</span>"+"<br>"
    else:
        print text+"<br>"


def print_form(runnumber1, runnumber2, partitions, link, label):
    print "<form action="+link+" method='get' type='submit'>"
    print "<div><input type='hidden' name='runnumber1' value="+str(runnumber1)+"></div>"
    print "<div><input type='hidden' name='runnumber2' value="+str(runnumber2)+"></div>"
    if 'HCAL_HO' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HO'></div>"
    if 'HCAL_HF' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HF'></div>"
    if 'HCAL_HBHE' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HBHE'></div>"
    if 'HCAL_HBHEa' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HBHEa'></div>"
    if 'HCAL_HBHEb' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HBHEb'></div>"
    if 'HCAL_HBHEc' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_HBHEc'></div>"
    if 'HCAL_LASER' in partitions:
        print "<div><input type='hidden' name='partition' value='HCAL_LASER'></div>"
    print "<input type='submit' value='"+label+"' />"
    print "</form>"












