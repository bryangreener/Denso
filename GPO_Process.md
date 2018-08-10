# GPO Migration Process

The following is a guide explaining the steps taken during the migration of a GPO from one domain to another using the tools in this repository.

## Step 1: Generating the Migration Table

1. In Group Policy Management, right click on any GPO and click 'Import Settings'.
2. Click 'Next' until you get to the 'Migrating References' page. In here, click the radio button to allow you to click 'New' in order to create a new migration table. 
3. With the Migration Table Editor open, click 'Tools' and 'Populate from GPO'. 
   + In here, you can select all of the GPOs in the domain in order to populate the Migration Table with every possible setting. 
4. Next, click 'File' and save this migration table somewhere on your computer.
5. Finally, follow the instructions in [Migration Table Refactor](https://github.com/bryangreener/Denso/tree/master/MigrationTableRefactor) to update the entries in this table with your specified mappings.

## Step 2: Update GPO Mapped Drive Item Level Targeting

