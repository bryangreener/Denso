function FindDuplicateOUInheritance{
    param(
        [Parameter(Mandatory=$True, HelpMessage='Location where csv will be generated.')]
		[string]$OutPath,
		[Parameter(Mandatory=$True, HelpMessage='Distinguished name of OU to query.')]
		[string]$OU_DN
    )
    # Check if file path exists and if csv can be opened there.
    try{
        Set-Location -Path $OutPath
        $OutPath += "\OUAdjacency.csv"
        "" | out-file -Encoding ASCII $OutPath
    }catch{ Write-Host $_.Exception.Message -ForegroundColor Red }

    $arr = New-Object System.Collections.ArrayList
    $map = New-Object System.Collections.ArrayList
    $outobj = New-Object System.Collections.ArrayList

    # Query AD for all sub OUs
    $ous = dsquery OU $OU_DN -limit 0
    # Parse OUs and save to array.
    foreach($i in $ous){ 
        $i = $i.Replace("`"","") # Remove quotes from items
        # Console output
        if((Get-GPInheritance -Target $i).GpoInheritanceBlocked){
            Write-Host $i -ForegroundColor Red
        }else{
            Write-Host $i -ForegroundColor Green
        }
        # Split OU result item at commas and strip unnecessary information
        $a = ([System.Collections.ArrayList]$i.Split(","))
        $a.Reverse()
        $a.RemoveRange(0,3)
        for($j = 0; $j -lt $a.Count; $j++){
            $a[$j] = $a[$j].Remove(0,3)
        }
        $a = $a -join '\' # Add backslash back in for OU location
        # This line is a mess. It gets all the inherited GPOs for an OU then takes their displaynames and concatenates them with tabs. Then it splits those back up and adds to an array.
        [void]$arr.add(($a, !(Get-GPInheritance -Target $i).GpoInheritanceBlocked, (((Get-GPInheritance -Target $i).InheritedGpoLinks | foreach-object{ Get-GPO -Name ($_.DisplayName) | Foreach-Object{ $_.DisplayName } }) -join "`t") -join "`t").split("`t"))
    }

    # Read array items and generate 0s and 1s corresponding to whether or not two OUs have duplicate inherited GPOs.
    foreach($i in $arr){
        [void]$outobj.Add($i[0]) #column names
        $temp = New-Object System.Collections.ArrayList
        $ti = $($i -join ",")
        $tti = $($i[2..($i.Count-1)] -join ",")
        foreach($j in $arr){ #compare current OU with all other OUs
            $tj = $($j -join ",")
            $ttj = $($j[2..($j.Count-1)] -join ",")
            if(($ti -ne $tj) -and ($tti -eq $ttj)){
                [void]$temp.Add(1) #duplicate
            }
            else{
                [void]$temp.Add(0) #different
            }
        }
        [void]$map.Add($temp)
    }
    # Output to csv
    try{
        # Encoding prevents pandas read_csv encoding error in python.
        $outobj -join "," | out-file -Encoding ASCII $OutPath #header
        foreach($row in $map){
            $row -join "," | out-file -append -Encoding ASCII $OutPath
        }
    }catch{ Write-Host $_.Exception.Message -ForegroundColor Red }
}