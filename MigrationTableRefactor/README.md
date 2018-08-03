# Migration Table Refactor

This tool procedurally updates values in a saved migrationtable based on input parameters in order to properly migrate GPOs to a new domain environment.

## Getting Started

### Prerequisites

This program requires a .migtab Migration Table file already created. This is the file that will be updated. This program also requires a csv in the format of SampleKey.csv that contains the mappings from old to new domain. 

### Running the Program

In powershell, type the following command:

```Powershell
C:\> Import-Module MigTab
```

This imports the module so that you can run its functions.

Finally, call the program and pass in the appropriate filepaths to both
the migration table and the csv key. There is also an optional third parameter
that allows you to pass in a list of local groups/users that should be kept
during the update. Any local group/user that isn't passed in (or that isnt in
the default parameter list) won't be kept in the migration.
Use the following command structure as an example:

```Powershell
C:\> Update-MigTable C:\temp\mt.migtable C:\temp\key.csv
```

Example using the optional third parameter:

```Powershell
C:\> Update-MigTable C:\temp\mt.migtable C:\temp\key.csv User1,User2,Group1
```

## Folder Contents
* Old Test Scripts
    * This folder contains test scripts that don't function fully.

* MigTab.psm1
    * This is a powershell module. See the section on how to run this script for more information.

* SampleKey.csv
    * This is a sample csv file showing the structure that your csv needs to fit.

## Built With

* Powershell using VSCode w/ Powershell plugin

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
