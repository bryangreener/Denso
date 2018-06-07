==========
How To Run
==========
In powershell, type the following command to view examples and get more detailed information:

C:\PS> get-help versacall

========
Examples
========
C:\PS> versacall

C:\PS> versacall -ComputerName COMPUTER-10

C:\PS> versacall -ServerIP 127.0.0.1 -PanelID 5

===============
Folder Contents
===============
VersacallOUs.csv
-	This csv contains separate rows for each computer.

-	Each row contains computer names, the versacall server they 
	connect to, and the PanelID that they use in the versacall web interface.

VersacallScript.ps1
	Run the help command above for information on this file.

log.log
	This is a log of errors encountered during runtime.
