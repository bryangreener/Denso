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
				if(	$child.name -eq 'FilterTerminal' -or
					$child.name -eq 'FilterRunOnce'){
					# Do nothing as these are unique tags that are unused.
				}
				else{ #For all other cases
					if(!$child.sid){ # Distinguished Name
                        #$t = get-ADGroup -Identity $child.name -Server $NewDomain
						#$child.name = $child.name.Split(',')[0].Split('=')[-1]
						$ou = $child.name.Split(',')[0].Split('=')[-1]
						$t = [string](Get-ADOrganizationalUnit -Filter "name -like '$ou'" -Server $NewDomain).DistinguishedName
					}
					else{
                        $trimmedGroup = $child.name.Split('\')[-1]
                        $t = Get-ADGroup -Filter "name -like '*$trimmedGroup'" -Server $NewDomain
                    }
					if(!$t){
						Write-Host "ERROR QUERYING $($NewDomain.ToUpper()) FOR:" -ForegroundColor Yellow
						$child | select * | %{ Write-Host $_.name.split('\')[-1] -ForegroundColor Red }
						Write-Host "GPO INFORMATION:" -ForegroundColor Magenta
						Write-Host "PATH:  $folder" -ForegroundColor Red
						$child | select * | %{ $_.ParentNode | select * | %{ $_.ParentNode | select * | %{ Write-Host "DRIVE:" $_.name -ForegroundColor Red }}}
					}
					$selection = 0
					if(	$t.Count -gt 1 -and
						!$savedReplacements[$child.name]){
						while(	$selection -lt 1 -or 
								$selection -gt $t.Count+2){
							Write-Host "Attempting to replace $($child.name)."
							for($i=0; $i -lt $t.Count; $i++){
								Write-Host "$($i+1)) $($t[$i])"
							}
							Write-Host "$($t.Count+1)) MANUAL ENTRY"
							Write-Host "$($t.Count+2)) IGNORE ENTRY" 
							$selection = Read-Host "Enter # of Replacement"
							if(	$selection -eq "" -or 
								$selection -lt 1 -or 
								$selection -gt $t.Count+2){
								Write-Host "INVALID SELECTION" -ForegroundColor Yellow
							}
						}
						$saveSelection = ""
						if($selection -eq $t.Count+1){ #MANUAL REPLACEMENT
							$entry = Read-Host "Enter the Name of the new user/group"
							$res = Get-ADGroup -Filter "name -like '*$entry'" -Server $NewDomain
							if($res.Count -gt 1){
								$selection = 0
								while( 	$selection -lt 1 -or
										$selection -gt $res.Count){
									Write-Host "Users/Groups Similar to Entry:"
									for($i = 0; $i -lt $res.Count; $i++){
										Write-Host "$($i+1)) $($res[$i])"
									}
									$selection = Read-Host "Enter # of Replacement"
									if( $selection -eq "" -or
										$selection -lt 1 -or
										$selection -gt $res.Count){
											Write-Host "INVALID SELECTION" -ForegroundColor Yellow
									}
								}
								
							}
							$selection = [int32]$selection - 1
							$san = $res[$selection].SamAccountName
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
							$child.sid = [string]($res[$selection].SID.Value)
						}
						elseif($selection -eq $t.Count+2){ # IGNORE CASE
							while("y","n" -notcontains $saveSelection.ToLower()){
								$saveSelection = Read-Host "Would you like the program to remember this choice? (y/n)"
								if($saveSelection.ToLower() -eq "y"){
									$savedReplacements.Add($child.name, @([string]($t[$selection].SID.Value), [string]($t[$selection].SID.Value)))
									Write-Host "Selection saved. You will not be prompted for future occurances of this value." -ForegroundColor Green
									Write-Host "`tOLD VALUE: $($child.name)"
									Write-Host "`tNEW VALUE: $($child.name)"
								}elseif($saveSelection.ToLower() -eq "n"){
									Write-Host "Selection not saved. You will continue to be prompted each time for this replacement." -ForegroundColor Red
								}else{
									Write-Host "INVALID SELECTION" -ForegroundColor Yellow
								}
							}
						}
						else{
							$selection = [int32]$selection - 1
							if($child.sid){
								$san = $t[$selection].SamAccountName
							}else{
								$san = $t[$selection].DistinguishedName
							}
							while("y","n" -notcontains $saveSelection.ToLower()){
								$saveSelection = Read-Host "Would you like the program to remember this replacement? (y/n)"
								if($saveSelection.ToLower() -eq "y"){
									if($child.sid){
										$savedReplacements.Add($child.name, @("$nDomain\$san", [string]($t[$selection].SID.Value)))
									}else{
										$savedReplacements.Add($child.name, @("$san"))
									}
									Write-Host "Selection saved. You will not be prompted for future occurances of this value." -ForegroundColor Green
									Write-Host "`tOLD VALUE: $($child.name)"
									Write-Host "`tNEW VALUE: $nDomain\$san"
								}elseif($saveSelection.ToLower() -eq "n"){
									Write-Host "Selection not saved. You will continue to be prompted each time for this replacement." -ForegroundColor Red
								}else{
									Write-Host "INVALID SELECTION" -ForegroundColor Yellow
								}
							}
							if($child.sid){
								$child.name = "$nDomain\$san"
								$child.sid = [string]($t[$selection].SID.Value)
							}else{
								$child.name = "$san"
							}
						}
					}elseif($savedReplacements[$child.name]){
						$tempname = $child.name
						$child.name = $savedReplacements[$tempname][0]
						if($child.sid){
							$child.sid = $savedReplacements[$tempname][1]
						}
					}else{
						if($child.sid){
							$child.name = "$nDomain\$($t.SamAccountName)"
							$child.sid = [string]($t.SID.Value)
						}else{
							$child.name = $t
						}
					}
				}
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
