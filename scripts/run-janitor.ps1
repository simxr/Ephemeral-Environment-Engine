param(
  [switch]$Apply,
  [double]$MaxAgeHours = 24,
  [string]$Repo = "simxr/Ephemeral-Environment-Engine"
)

$scriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
$janitor = Join-Path $scriptDir "janitor.py"

$argsList = @(
  $janitor,
  "--repo", $Repo,
  "--max-age-hours", $MaxAgeHours
)

if ($Apply) {
  $argsList += "--apply"
}

python @argsList
