# Versacall Query Tool

This tool is ideally run on startup for computers using the versacall system. The client will run this script and will be returned the URL for the Versacall andon based on a key csv.

## Built With

* Powershell using VSCode w/ Powershell plugin

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.


## How To Run

In powershell, type the following command to view examples and get more detailed information:

C:\PS> get-help versacall

## Examples

```
C:\PS> versacall
```
```
C:\PS> versacall -ComputerName COMPUTER-10
```
```
C:\PS> versacall -ServerIP 127.0.0.1 -PanelID 5
```

## Folder Contents

* VersacallOUs.csv
-	This csv contains separate rows for each computer.

-	Each row contains computer names, the versacall server they 
	connect to, and the PanelID that they use in the versacall web interface.

* VersacallScript.ps1
	Run the help command above for information on this file.

* log.log
	This is a log of errors encountered during runtime.
