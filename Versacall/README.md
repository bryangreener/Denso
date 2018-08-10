# Versacall Query Tool

This tool is ideally run on startup for computers using the versacall system. The client will run this script and will be returned the URL for the Versacall andon based on a key csv.

## Getting Started

### Running the Program

In powershell, type the following command to view examples and get more detailed information:

```Powershell
C:\PS> get-help versacall
```

Other ways of running the program are as follows.

* Run the script taking defaults for the current computer.

```Powershell
C:\PS> versacall
```

* Run the script for a specific computer name.

```Powershell
C:\PS> versacall -ComputerName COMPUTER-10
```

* Run the script for a specific server IP and panel ID.

```Powershell
C:\PS> versacall -ServerIP 127.0.0.1 -PanelID 5
```

### Running Program via GPO

This process can be automated by setting up a GPO to run this script on logon.

In `Computer Configuration -> Policies -> Administrative Templates -> System/Logon`, in the `Run these programs at user logon` setting, add the following item to run at logon:

```Powershell
powershell -command "& { . \\server_name\some_filepath\Loadversacall.ps1; versacall -Chrome }"
```

## Folder Contents

* VersacallOUs.csv
    * This csv contains separate rows for each computer.
    * Each row contains computer names, the versacall server they connect to, and the PanelID that they use in the versacall web interface.

* VersacallScript.ps1
    * Run the help command above for information on this file.

* log.log
    * This is a log of errors encountered during runtime.

## Built With

* Powershell using VSCode w/ Powershell plugin

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
