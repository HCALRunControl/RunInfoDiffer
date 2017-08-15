# RunInfoDiffer

This code is a tool to monitor parameters in the Runinfo Database to track changes made between global HCAL runs. It has two main interfaces in order to allow for on demand inquiries into changes between any two runs as well providing notification of changes as they happen. The system consists of three major components. The first is a long lived process that is responsible for querying the runinfo database and calculating the resulting diff. The second is a web framework that provides an interface for users to look at the differences between runs. The third is a slackbot that sends a message to slack each time a new change is made. The complete architecture is shown in the diagram below.

INSERT DIAGRAM

To run the differ clone this repository into hcalmon. `DifferBot.py` should be moved to `cmshcalweb01`. The structure should be as follows:

```
hcalmon:
    /var/www
        /cgi-bin/<RuninfoDifferDirName>
	    Run_Info_Diff.py
	    viewDiffer.py
	    diffed_parameters.txt
	    mailOut.pl
	    database_pwd.txt	
        /html/<RuninfoDifferDirName>
	    index.html
	    BotUrlLog.html

cmshcalweb01:
    
```

Note the files `database_pwd.txt` and `BotUrlLog.html` are listed above but do not appear in the repository. `database_ped.txt` is omitted for security and `BotUrlLog.html` is an empty log file that `Run_Info_Diff.py` will write to.

To start the longlived mode of `Run_Info_Diff.py` run:

```
nohup python -u local_run > RunInfoDiffer.log &
```

To run the Bot a tunnel must be made to cms usr:

```
ssh -f -ND 1080 <your_cmsusr_username>@cmsusr
nohup python -u DifferBot.py > BotLog.txt &
```

