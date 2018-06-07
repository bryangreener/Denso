function versacall{
    <#
    .SYNOPSIS
        This function opens a Versacall web interface based on input parameters.
    .DESCRIPTION
        This function automatically grabs the calling computer's name unless specified otherwise and
        looks for a mapping in the Mapping.csv file in order to generate a run command to load
        a versacall web interface using the corresponding Server IP and Panel IDs. 
    .EXAMPLE
        C:\PS> versacall
        <This command grabs the running computer's name and loads the corresponding versacall page.>
    .EXAMPLE
        C:\PS> versacall -ComputerName COMPUTER-10 -kiosk
        <This command loads the correcponding versacall page for COMPUTER-10 in Chrome.>
    .EXAMPLE
        C:\PS> versacall -ServerIP 127.0.0.1 -PanelID 5
        <This command loads the PanelID=5 versacall page hosted on the server at 127.0.0.1.>
    .PARAMETER ServerIP
        IP of server hosting the Versacall web interface.
    .PARAMETER PanelID
        Panel ID superglobal used in the server $_GET request when loading the Versacall web interface.
    .PARAMETER CustomURL
        Switch used to group the ServerIP and PanelID parameters so that if either one is specified then both are required.
    .PARAMETER ComputerName
        Computer name of computer running this script by default. This is the name used in the domain query.
    .PARAMETER CSVFolder
        Folder path to the Versacall CSV containing mapping of OU to ServerIP and PanelID. Default is the directory of this script.
    .PARAMETER CSVName
        Filename of CSV containing mapping of OU to ServerIP and PanelID.
    .PARAMETER Application
        File path of application that displays the versacall web interface.
    .PARAMETER Chrome
        Boolean value specifying whether or not to use Chrome over IE. Changes kiosk switch from -k to -kiosk.
    .NOTES
        Author:  Bryan Greener
        Email:   bryan_greener@denso-diam.com
        Company: DENSO DMMI
        Date:    2018-05-23
    #>

    #### Used to prevent 'url' fields from being required every time.
    [CmdletBinding(DefaultParameterSetName='None')]
    #### List of input parameters that can be specified by user. All are optional except for ServerIP and PanelID which are
    #    only required if either one of them is specified by user.
    param(
        [Parameter(Position=1, 
            Mandatory=$True, 
            ParameterSetName='url',
            HelpMessage='IP of server hosting Versacall page.')]
        [string]$ServerIP,
        [Parameter(Position=1, 
            Mandatory=$True, 
            ParameterSetName='url',
            HelpMessage='Panel ID superglobal parameter at end of Versacall URL.')]
        [string]$PanelID,
        [Parameter(ParameterSetName='url',
            HelpMessage='Switch used in parameter selection. If either ServerIP or PanelID are specified, then both are required.')]
        [switch]$CustomURL,
        [Parameter(HelpMessage='Computer Name (without domain) to search for in CSV. Default is current running computer.')] 
        [string]$ComputerName = $env:computername,
        [Parameter(HelpMessage='Folder containing the CSV file with Computers,IPs, and PanelIDs. Default is folder where this script is stored.')]      
        [string]$CSVFolder = "$PSScriptRoot\VersacallByComputer",
        [Parameter(HelpMessage='Name of CSV file without file path. Default is Mapping.csv.')]
        [string]$CSVName = "Mapping.csv",
        [Parameter(HelpMessage='Application that will be run in this script. Default is C:\Program files\Internet Explorer\iexplore.')]
        [string]$Application = 'C:\Program Files\Internet Explorer\iexplore',
        [Parameter(HelpMessage='Specify to use Chrome instead of IE.')]
        [switch]$Chrome,
        [Parameter(HelpMessage='Log file outut.')]
        [string]$LogFile = "$CSVFolder\..\VersacallByComputerLog.log"
    )
    try{
        #### Output all parameters to new entry in log.
        $timestamp = Get-Date
        "" | Out-File -append $LogFile
        "[$timestamp] BEGIN FUNCTION CALL
        Called by $env:userdomain\$env:username on $env:computername with parameters
        ComputerName  $ComputerName
        ServerIP      $ServerIP
        PanelID       $PanelID
        CSVFolder     $CSVFolder
        CSVName       $CSVName
        Chrome        $Chrome
        Application   $Application" | Out-File -append $LogFile
		#### If Chrome switch specified AND Chrome is not running, set application path to chrome and change to --kiosk switch.
		$panelURL = 'ommitted for security'
        if($Chrome){ 
            if(!(Get-Process chrome -ErrorAction SilentlyContinue)){
                $switch = "--kiosk"
                if([System.IO.File]::Exists("C:\Program Files (x86)\Google\Chrome\Application\chrome.exe")){
                    $Application = "C:\Program Files (x86)\Google\Chrome\Application\chrome.exe"
                }elseif([System.IO.File]::Exists("C:\Program Files (x86)\Google\Application\chrome.exe")){
                    $Application = "C:\Program Files (x86)\Google\Application\chrome.exe"
                }else{ # If Chrome isn't installed (Win10 & Win7), use IE.
                    $timestamp = Get-Date
                    "[$timestamp] WARNING -Chrome switch specified but Chrome.exe not found. Using IE instead." | Out-File -append $LogFile
                    $switch = "-k"
                }
            }else{ # Otherwise if chrome is running, use IE.
                $timestamp = Get-Date
                "[$timestamp] WARNING -Chrome switch specified but Chrome.exe is currently running. This prevents kiosk mode. Using IE instead." | Out-File -append $LogFile
                $switch = "-k"
            }
        }else{ # Otherwise use IE -k kiosk switch.
            $switch = "-k" 
        }
        #### If ServerIP and PanelID switches specified, create URL manually without lookup.
        if($PSCmdlet.ParameterSetName.Equals("url")){
            $url = 'http://' + $ServerIP + $panelURL + $PanelID
            & $Application $switch $url
        }else{ # Otherwise, find specified computer in csv and use associated ServerIP and PanelID in that row.
            foreach($row in (Import-Csv -Path (Join-Path (Split-Path -Parent $CSVFolder) $CSVName))){
                if($ComputerName -eq $row.Computer){ # If match found, create URL and run.
                    $url = 'http://' + $row.Server + $panelURL + $row.PanelID
                    & $Application $switch $url
                }
            }
            #### If no computer could be found matching specified name, throw custom error.
            if(!($url)){ throw "ComputerError" }
        #### Output success to log file, ending operation.
        $timestamp = Get-Date
        "[$timestamp] SUCCESS
        " | Out-File -append $LogFile
        }
    }catch{
        #### If custom error specified...
        if($error[0].FullyQualifiedErrorId -eq "ComputerError"){
            $timestamp = Get-Date
            "[$timestamp] WARNING Specified computer not found.
            ComputerName  $ComputerName
            CSV           $CSVFolder\..\$CSVName
            Please refer to the documentation using 'get-help versacall'" | Out-File -append $LogFile
        }else{ # Otherwise use the following error.
            Write-Host $_.Exception.Message -ForegroundColor Red
            Write-Host "Error was saved to .\log.log" -ForegroundColor Yellow 
            $timestamp = Get-Date
            "[$timestamp] ERROR $_
            " | Out-File -append $LogFile
        }
        #### Always print the following regardless of which error is thrown. Shows end of log operation.
        $timestamp = Get-Date
        "[$timestamp] OPERATION FAILED
        " | Out-File -append $LogFile
    }
}