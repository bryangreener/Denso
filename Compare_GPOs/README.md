# GPO Comparison Tool

This tool compares two GPO html reports (generated using Get-GPOReport or from within GPMC) and shows which GPO settings are duplicates and which are different. This tool is used to reduce the overhead of GPOs by showing any unnecessary settings that would cause replication times between ADs to increase. These settings can then be removed manually.

## Getting Started

### Prerequisites

This program requires a folder containing GPO html reports as input. To get these reports, you can use the following command in powershell.

```Powershell
Get-GPO -all | %{ Get-GPOReport -Name $_.DisplayName -ReportType HTML -Path "C:\bin_folder\$($_.DisplayName).html" }
```

This will generate html reports in the bin_folder path for every GPO in a domain. These need to be the only files in this folder for the program to run correctly.

### Running the Program

From a console, run the program using the following command.

```bash
C:\> C:\exe_path\compare_reports.exe C:\bin_folder C:\output_folder
```

Where output_folder is some existing folder where the comparison report files will be saved. The compare_reports.exe file is contained in the `dist\compare_reports\` folder in this repository and must remain in that containing folder in order to run properly.

Depending on the number of GPO reports in the bin folder, this program can take a very long time to run. For example, if there are 50 reports in this folder then each of the 50 reports will be compared against the other 49 reports in that folder. Thus the total comparisons would be 2,450 output files.

## Built With

* Python 3 using Spyder with Anaconda

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
