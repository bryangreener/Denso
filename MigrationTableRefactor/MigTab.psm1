<#
.SYNOPSIS
	This function updates a migration table with specified values.
.DESCRIPTION
	This function takes in a migration table and a csv key file and uses the
	csv key values to update items in the migration table.
.EXAMPLE
	C:\PS> Import MigTab
	C:\PS> Update-MigTable C:\MT.migtable C:\Key.csv
	<This command updates a migration table using a key csv.
.EXAMPLE
	C:\PS> Import-MigTab
	C:\PS> Update-MigTable C:\MT.migtable C:\Key.csv Admins,Users,Computers
	<This command updates a migration table using a key csv and retains the
	Admins, Users, and Computers items.>
.PARAMETER MigrationTableFullPath
	Absolute filepath of .migtable file to be updated.
.PARAMETER MigtableKeyCSVPath
	Absolute filepath of .csv key file used to update .migtable.
.PARAMETER local
	Array of users/groups that will be set to keep current value in updated
	migration table.
.NOTES
	Author:		Bryan Greener
	Email:		bryan_greener@denso-diam.com
	Company:	DENSO DMMI
	Date:		2018-06-01
#>
function Update-MigTable{
	[Cmdletbinding()]
	param(
		[Parameter(Mandatory=$True,
			HelpMessage="Full path of .migtable file.")]
		[string]$MigrationTableFullPath,
		[Parameter(Mandatory=$True,
			HelpMessage="Full path of .csv key file.")]
		[string]$MigtableKeyCSVPath,
		[Parameter(Mandatory=$False,
			HelpMessage="Array of local users/groups to retain.")]
		[string[]]$local=@(	"Administrators", 
							"Power Users", 
							"Users", 
							"Computers", 
							"Remote Desktop Users")#, 
							#"Network Configuration Operators", 
							#"Backup Operators",
							#"Local_Admin")
	)
	try{
		# MT is an xml variable populated by the migtable.
		# mtns is a namespace variable that prevents unneeded info in tags
		# key is the csv data
		[xml]$MT = Get-Content $MigrationTableFullPath
		$mtns = $MT.DocumentElement.NamespaceURI 
		#$key = Import-Csv $MigtableKeyCSVPath
		# For each mapping item in migtable, check in csv key and if there is
		# a match then check if item is Free Text or SID. If so, and if the item
		# is not a SID then set item to be removed on migration. Otherwise
		# item gets replaced with new value based on csv key. SIDs stay same.
		$MT.MigrationTable.Mapping | 
			#%{ $i = $_; $k = $_.Source -match $key |
			%{ $i = $_; MatchString $i.Source $MigtableKeyCSVPath; $k | %{ 
			if( $i.Type -ne 'Unknown'){
				[void]$i.RemoveChild($i.LastChild)
				$child = $MT.CreateElement('Destination', $mtns)
				$child.InnerXml = $i.Source -replace $k.Source, $k.Destination
				[void]$i.AppendChild($child)
			}elseif($i.Type -eq 'Unknown' -and 
					!$local.Contains($i.Source) -and
					$i.Source -notmatch "^S-\d-\d+-(\d+-){1,14}\d+$"){
				[void]$i.RemoveChild($i.LastChild)
				$child = $Mt.CreateElement('DestinationNone', $mtns)
				[void]$i.AppendChild($child)
			};
			$MT.Save($MigrationTableFullPath); # Save migtable file
			}
			}
		<#ALT METHOD WITHOUT USING PIPES
		foreach($i in $MT.Migrationtable.Mapping){
			$k = $i.Source -match $key
			if($i.Type -ne 'Unknown'){
				[void]$i.RemoveChild($i.LastChild)
				$child = $MT.CreateElement('Destination', $mtns)
				$child.InnerXml = $i.Source -replace $k.Source, $k.Destination
				[void]$i.AppendChild($child)
			}elseif(!$local.Contains($i.Source) -and
					$i.Source -notmatch "^S-\d-\d+-(\d+-){1,14}\d+$"){
				[void]$i.RemoveChild($i.LastChild)
				$child = $Mt.CreateElement('DestinationNone', $mtns)
				[void]$i.AppendChild($child)
			}
			$MT.save($MigrationTableFullPath)
		} #>
	}catch{ #Output error
		$e = $_.Exception
		$line = $_.InvocationInfo.ScriptLineNumber
		#$msg = $e.Message
		Write-Host -ForegroundColor Yellow "caught exception: $e at $line"
	}
}
<#
.SYNOPSIS
	Helper function that returns csv row to use in main function.
.DESCRIPTION
	Helper function that takes in a string and a csv file then returns
	the row of the csv that is the closest match to the compare string.
#>
function MatchString{
	param(
		[Parameter(Mandatory=$True)]
		[string]$s,
		[Parameter(Mandatory=$True)]
		[string]$MigtableKeyCSVPath
	)
	
	try{
		$key = Import-Csv $MigtableKeyCSVPath
		$seq = @{}
		foreach($k in $key){
			$seq.Add($k.Source, 0)
			$k = $k.Source
			$numSequential = 0
			for($i=0; $i -lt $s.Length; $i++){
				if($s[$i] -eq $k[0]){
					$j = 0
					while($i -lt $s.Length -and 
						$j -lt $k.Length -and 
						$s[$i] -eq $k[$j]){
						$numSequential++
						$i++
						$j++
					}
					if($numSequential -gt $seq[$k]){
						$seq[$k] = $numSequential
					}
					$numSequential = 0
				}
			}
		}
		$maxval = ($seq.Values | Measure-Object -Maximum).Maximum
        $res = $($seq.Keys)[($($seq.Values).indexof([int32]$maxval))]
        $script:k = $key | Where { $_.Source -eq $res }
	}catch{
		$e = $_.Exception
		$line = $_.InvocationInfo.ScriptLineNumber
		#$msg = $e.Message
		Write-Host -ForegroundColor Yellow "caught exception: $e at $line"
	}
}

export-modulemember -function Update-MigTable