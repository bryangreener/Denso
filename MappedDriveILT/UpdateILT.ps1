<#
.SYNOPSIS
	Updates Item Level Targeting in backup GPOs
.DESCRIPTION
	This function takes backed up gpo files and updates the item level
	targeting in the Drives.xml files.
.PARAMETER BackupPath
	Full path to folder containing backed up GPOs.
.PARAMETER KeyPath
	Unused parameter that was originally going to be a path to a
	csv key file which would be used to translate old groups to new ones.
.PARAMETER NewDomain
	FQDN of domain that GPOs will be updated to reflect.
.PARAMETER OldDomani
	FQDN of old domain that GPOs were backed up from.
.PARAMETER DrivesPath
	Optional parameter that points to the Drives.xml file within each gpo
	folder. This can be overridden in cases where the Drives.xml file
	is in a different location.
.NOTES
	Author:  Bryan Greener
	Email:   bryan_greener@denso-diam.com
	Company: DENSO DMMI
	Date:    2018-06-07
#>
function Update-DriveILT{
	[Cmdletbinding()]
	param(
		[Parameter(Mandatory=$True)]
		[string]$BackupPath,
		[Parameter(Mandatory=$True)]
		[string]$KeyPath,
		[Parameter(mandatory=$True)]
		[string]$NewDomain,
		[Parameter(mandatory=$True)]
		[string]$OldDomain,
		[Parameter(Mandatory=$False)]
		[string]$DrivesPath="DomainSysvol\GPO\User\Preferences\Drives\Drives.xml"
	)
	try{
		$nDomain = $NewDomain.Split('.')[0].ToUpper()
		$folders = dir -Directory -Path $BackupPath | 
			ForEach-Object { $_.FullName } | 
			Where-Object { Test-Path "$_\$DrivesPath" }

		$savedReplacements = @{}

		foreach($folder in $folders){
			[xml]$f = Get-Content "$folder\$DrivesPath"
			$f.ChildNodes | 
				select Drive | 
				select -ExpandProperty * | 
				select Filters | 
				select -ExpandProperty Filters | 
				select ChildNodes |
				select -ExpandProperty * |
				ForEach-Object{
				$child = $_
				if($child.sid){
					$trimmedGroup = $child.name.Split('\')[-1]
					$t = Get-ADGroup -Filter "name -like '*$trimmedGroup'" -Server $NewDomain
					if(!$t){
						Write-Host "ERROR QUERYING AD FOR:" -ForegroundColor Yellow
						$child | select * | %{ Write-Host $_.name -ForegroundColor Red }
						Write-Host "GPO INFORMATION:" -ForegroundColor Magenta
						Write-Host "PATH:  $folder" -ForegroundColor Red
						$child | select * | %{ $_.ParentNode | select * | %{ $_.ParentNode | select * | %{ Write-Host "DRIVE:" $_.name -ForegroundColor Red }}}
					}
					$selection = 0
					if(	$t.Count -gt 1 -and
						!$savedReplacements[$child.name]){
						while(	$selection -lt 1 -or 
								$selection -gt $t.Count){
							Write-Host "Attempting to replace $($child.name)."
							for($i=0; $i -lt $t.Count; $i++){
								Write-Host "$($i+1)) $($t[$i])"
							}
							$selection = Read-Host "Enter # of Replacement"
							if(	$selection -eq "" -or 
								$selection -lt 1 -or 
								$selection -gt $t.Count){
								Write-Host "INVALID SELECTION" -ForegroundColor Yellow
							}
						}
						$saveSelection = ""
						$selection = [int32]$selection - 1
						$san = $t[$selection].SamAccountName
						while("y","n" -notcontains $saveSelection.ToLower()){
							$saveSelection = Read-Host "Would you like the program to remember this replacement? (y/n)"
							if($saveSelection.ToLower() -eq "y"){
								$savedReplacements.Add($child.name, @("$nDomain\$san", [string]($t[$selection].SID.Value)))
								Write-Host "Selection saved. You will not be prompted for future occurances of this value." -ForegroundColor Green
								Write-Host "`tOLD VALUE: $($child.name)"
								Write-Host "`tNEW VALUE: $nDomain\$san"
							}elseif($saveSelection.ToLower() -eq "n"){
								Write-Host "Selection not saved. You will continue to be prompted each time for this replacement." -ForegroundColor Red
							}else{
								Write-Host "INVALID SELECTION" -ForegroundColor Yellow
							}
						}
						$child.name = "$nDomain\$san"
						$child.sid = [string]($t[$selection].SID.Value)
					}elseif($savedReplacements[$child.name]){
						$tempname = $child.name
						$child.name = $savedReplacements[$tempname][0]
						$child.sid = $savedReplacements[$tempname][1]
					}else{
						$child.name = "$nDomain\$($t.SamAccountName)"
						$child.sid = [string]($t.SID.Value)
					}
				}
				elseif(	$child.name -eq 'FilterTerminal' -or
						$child.name -eq 'FilterRunOnce'){
					#Unique tags that aren't used.
				}else{
					$ou = $child.name.Split(',')[0].Split('=')[-1]
					$child.name = [string](Get-ADOrganizationalUnit -Filter "name -like '$ou'" -Server $NewDomain).DistinguishedName
				}
				#}
				
			}
			$f.Save("$folder\$DrivesPath")
		}
		Write-Host "COMPLETE" -ForegroundColor Green
	}catch{
		$e = $_.Exception
		$line = $_.InvocationInfo.ScriptLineNumber
		Write-Host -ForegroundColor Yellow "caught exception: $e at $line"
	}
}
$p = "C:\gpobackup"
$k = "C:\key.csv"
$s = "new.net"
$o = "old.com"
Update-DriveILT $p $k $s $o
