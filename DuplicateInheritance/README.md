# GPO Duplicate Inheritance Viewer

This set of programs reads every OUs GPO inheritance setting in a domain then creates a graph showing all OUs with duplicated inherited GPOs in a readable format.

## Getting Started

### Prerequisites

In order to run the treeview.exe program, you must first generate the `OUAdjacency.csv` file by running the `GenOUAdjacency.ps1` script from powershell. An example of how to run this is below.

```Powershell
C:\> .\GenOUAdjacency.ps1 C:\output_path "OU=SomeOU,DN=domain,DN=com"
```

After running this command, place the output csv file in the `dist\treeview` folder before running the program.

### Running the Program

From a console, run the program using the following command.

```Bash
C:\> treeview.exe
```

## Built With

* Python 3 using Spyder with Anaconda
* Powershell using VSCode w/ Powershell plugin

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
