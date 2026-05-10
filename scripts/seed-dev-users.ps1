$ErrorActionPreference = 'Stop'
Set-Location "c:\Users\gwent\Projects\WIMS-BFP-PROTOTYPE"

$composeFile = "src/docker-compose.yml"
$keycloakContainer = "wims-keycloak"
$kcServer = "http://localhost:8080/auth"
$kcRealm = "bfp"
$kcAdminUser = "admin"
$kcAdminPass = "admin"
$password = "Password123!"

$roles = @("REGIONAL_ENCODER", "NATIONAL_VALIDATOR", "ANALYST", "NATIONAL_ANALYST", "SYSTEM_ADMIN")
$users = @(
    @{ username = "encoder_test";  email = "encoder@bfp.gov.ph";       role = "REGIONAL_ENCODER";   region = 1 },
    @{ username = "encoder_r02";   email = "encoder_r02@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 2 },
    @{ username = "encoder_r03";   email = "encoder_r03@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 3 },
    @{ username = "encoder_r04";   email = "encoder_r04@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 4 },
    @{ username = "encoder_r05";   email = "encoder_r05@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 5 },
    @{ username = "encoder_r06";   email = "encoder_r06@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 6 },
    @{ username = "encoder_r07";   email = "encoder_r07@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 7 },
    @{ username = "encoder_r08";   email = "encoder_r08@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 8 },
    @{ username = "encoder_r09";   email = "encoder_r09@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 9 },
    @{ username = "encoder_r10";   email = "encoder_r10@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 10 },
    @{ username = "encoder_r11";   email = "encoder_r11@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 11 },
    @{ username = "encoder_r12";   email = "encoder_r12@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 12 },
    @{ username = "encoder_r13";   email = "encoder_r13@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 13 },
    @{ username = "encoder_r14";   email = "encoder_r14@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 14 },
    @{ username = "encoder_r15";   email = "encoder_r15@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 15 },
    @{ username = "encoder_r16";   email = "encoder_r16@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 16 },
    @{ username = "encoder_r17";   email = "encoder_r17@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 17 },
    @{ username = "encoder_r18";   email = "encoder_r18@bfp.gov.ph";   role = "REGIONAL_ENCODER";   region = 18 },
    @{ username = "validator_test"; email = "validator@bfp.gov.ph";    role = "NATIONAL_VALIDATOR"; region = 1 },
    @{ username = "analyst_test";  email = "analyst@bfp.gov.ph";       role = "NATIONAL_ANALYST";   region = $null },
    @{ username = "analyst1_test"; email = "analyst1_test@gmail.com";  role = "NATIONAL_ANALYST";   region = $null },
    @{ username = "admin_test";    email = "admin@bfp.gov.ph";         role = "SYSTEM_ADMIN";       region = $null }
)

Write-Host "Waiting for keycloak..."
$deadline = (Get-Date).AddSeconds(90)
while ((Get-Date) -lt $deadline) {
    $status = docker inspect --format='{{.State.Health.Status}}' $keycloakContainer 2>$null
    if ($status -eq 'healthy') { break }
    Start-Sleep -Seconds 2
}

Write-Host "Authenticating Keycloak admin..."
docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh config credentials --server $kcServer --realm master --user $kcAdminUser --password $kcAdminPass | Out-Null

Write-Host "Ensuring roles..."
foreach ($role in $roles) {
    try {
        docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh create roles -r $kcRealm -s "name=$role" 2>$null | Out-Null
    } catch {
        # role probably already exists
    }
}

foreach ($u in $users) {
    $username = $u.username
    $email = $u.email
    $role = $u.role
    $region = $u.region

    Write-Host "Seeding $username ($role)..."

    try {
        docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh create users -r $kcRealm -s "username=$username" -s "enabled=true" -s "email=$email" 2>$null | Out-Null
    } catch {
        # user may already exist
    }

    docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh set-password -r $kcRealm --username $username --new-password $password | Out-Null

    try {
        docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh add-roles -r $kcRealm --uusername $username --rolename $role 2>$null | Out-Null
    } catch {
        # role likely already mapped
    }

    $usersJson = docker exec $keycloakContainer /opt/keycloak/bin/kcadm.sh get users -r $kcRealm -q "username=$username"
    $match = [regex]::Match($usersJson, '[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}')
    if (-not $match.Success) {
        throw "Failed to resolve Keycloak UUID for $username"
    }
    $uuid = $match.Value

    $regionSql = if ($null -ne $region) { $region.ToString() } else { "NULL" }

    $sql = "INSERT INTO wims.users (user_id, keycloak_id, username, role, assigned_region_id, is_active) VALUES ('$uuid'::uuid, '$uuid'::uuid, '$username', '$role', $regionSql, TRUE) ON CONFLICT (username) DO UPDATE SET keycloak_id = EXCLUDED.keycloak_id, role = EXCLUDED.role, assigned_region_id = EXCLUDED.assigned_region_id, is_active = TRUE, updated_at = now();"

    docker compose -f $composeFile exec -T postgres psql -v ON_ERROR_STOP=1 -U postgres -d wims -c $sql | Out-Null
}

Write-Host "Seed complete. Password for test users: $password"
