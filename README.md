# Denso Summer Internship 2018

This repository contains programs and scripts written while working at Denso during Summer 2018. These programs focus on improving work flow for a domain administrator and speed up the process of GPO migrations by improving on the tools provided by Microsoft.

## Getting Started

### GPO Migration Process

The following is a guide explaining the steps taken during the migration of a GPO from one domain to another using the tools in this repository.

#### Step 1: Generating the Migration Table

1. In Group Policy Management, right click on any GPO and click `Import Settings...`.
2. Click `Next` until you get to the `Migrating References` page. In here, click the radio button to allow you to click `New` in order to create a new migration table. 
3. With the Migration Table Editor open, click `Tools` and `Populate from GPO`. 
   * In here, you can select all of the GPOs in the domain in order to populate the Migration Table with every possible setting. 
4. Next, click `File` and save this migration table somewhere on your computer.
5. Finally, follow the instructions in [MigrationTableRefactor](https://github.com/bryangreener/Denso/tree/master/MigrationTableRefactor)
   * THis will update the entries in this table with your specified mappings.

#### Step 2: Update GPO Mapped Drive Item Level Targeting

1. Back up all the GPOs from the old domain that need to be migrated to the new domain. These backup folders need to be in the same folder.
2. Follow the instructions in [MappedDriveILT](https://github.com/bryangreener/Denso/tree/master/MappedDriveILT)
   * This will update the item level targeting settings in all the backed up GPOs.

#### Step 3: Import GPOs to new Domain

1. Open `Group Policy Management`.
2. Create a new GPO that you will import the old GPO settings into.
3. Right click on this GPO and click `Import Settings...`.
4. Click `Next` until you get to the `Backup Location` screen and select the folder with your backed up (and updated) GPOs.
5. Click `Next` and select the GPO whose settings need to be imported into this new GPO.
6. Click `Next` until you get to the `Migrating References` page.
7. Select the migration table that you edited in Step 1 and check the `Use migration table exclusively` checkbox.
8. Click `Next` until you finish this wizard.

This will have imported all of the updated settings from the old GPO into the GPO in the new domain.

#### Step 4 (Optional): Reduce Redundant GPO Settings

In order to improve the GPO replication times across the forest, follow the instructions in [Compare_GPOs](https://github.com/bryangreener/Denso/tree/master/Compare_GPOs).

## Built With

* Powershell using VSCode w/ Powershell plugin
* Python 3 using Spyder with Anaconda
* C# with Visual Studio 2017 Community Edition

## Authors

[Bryan Greener](https://github.com/bryangreener)

## License

This project is not available for distribution. See the [LICENSE.txt](https://github.com/bryangreener/Denso/blob/master/LICENSE.txt) file for details.
