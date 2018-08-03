# GPO Comparison Tool

This tool compares two GPO html reports (generated using Get-GPOReport or from within GPMC) and shows which GPO settings are duplicates and which are different. This tool is used to reduce the overhead of GPOs by showing any unnecessary settings that would cause replication times between ADs to increase. These settings can then be removed manually.

## Built With

* Python 3 using Spyder with Anaconda

## How to Use

This program requires a folder containing GPO html reports as input. To get these reports, you can use the following two lines in powershell.

$gpos = Get-GPO -all
$gpos | %{ Get-GPOReport -Name $_.DisplayName -ReportType HTML -Path "C:\bin_folder\$($_.DisplayName).html" }

This will generate html reports in the bin_folder path for every GPO in a domain. From here, run the program using the following commands.

C:\> C:\exe_path\compare_reports.exe C:\bin_folder C:\output_folder

Where output_folder is some existing folder where the comparison report files will be saved.

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
