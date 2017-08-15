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
    <nfshome0Dir>
	DifferBot.py 
```

Note the files `database_pwd.txt` and `BotUrlLog.html` are listed above but do not appear in the repository. `database_ped.txt` is omitted for security and `BotUrlLog.html` is an empty log file that `Run_Info_Diff.py` will write to.

The core file of this system is `Run_Info_Diff.py`. It has two seperate modes it can run in based on the command line arguments passed in. The functionality of querying the database and calculating diffs is used by both modes. The first mode is a long lived mode which can be activated by running the command below.

```
nohup python -u Run_Info_Diff.py local_run > RunInfoDiffer.log &
```
In this mode the code will keep track of the last global run each partition will included (ignoring runs where no change was made). When a new global run is taken it will automatically check for changes. If it finds them it will update the most recent run and calculate the difference between them. It will then write to the log the url of the web interface where the changes can be found. This information is later used by the Bot to send notifications to slack.

The other mode is a single request for the difference between two runs with specified partitions included. This mode is called automatically from viewDiffer.py and will not be used by the user in normal operation. To use this mode run:

```
python Run_Info_Diff.py remote_run <runnumber 1> <runnumber 2> <whitespace seperated list of included partitions>
```

This is used by the web interface to request specific diffs without regard for when they happended.

To run the Bot a tunnel must be made to cmsusr:

```
ssh -f -ND 1080 <your_cmsusr_username>@cmsusr
nohup python -u DifferBot.py > BotLog.txt &
```

