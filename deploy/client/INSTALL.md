# WIMS-BFP – Installation guide (office server PC)

This guide is for the person who sets up and looks after the WIMS-BFP server PC. You do not
need to be a programmer. Follow the sections in order. Every command is typed into
**Windows PowerShell** (Start menu → type "PowerShell" → right-click → *Run as administrator*
when the guide says so).

**What you are building:** one office PC (the *server*) runs WIMS-BFP. Every other office PC
opens it in a web browser at **https://wims.bfp.lan**. The server needs an internet connection
only for email and map pictures; WIMS itself works on the office network without internet.

> **Status of this package.** The scripts were written and reviewed but not yet run on a
> Windows PC. Before go-live, someone must complete
> [DEPLOYMENT_TEST_CHECKLIST.md](DEPLOYMENT_TEST_CHECKLIST.md) once on the real server PC.
> Menu names of third-party programs (Rancher Desktop, Windows) can differ slightly by version.

---

## 1. Install the container runtime (not Docker Desktop)

WIMS runs inside *containers*. Something on the PC has to run containers. Use **Rancher Desktop**
(free, open source).

**Why not Docker Desktop?** Docker Desktop is free only for personal use, education and
organisations under 250 employees and USD 10 million revenue. BFP is a large government
agency, so Docker Desktop would probably need a paid licence. Rancher Desktop runs the same
containers at no cost. *(Licence terms change; check Docker's current terms before relying on
this. Do not install Docker Desktop on this PC.)*

1. Check the PC: Windows 10 (64-bit, version 2004 or newer) or Windows 11, at least 8 GB RAM,
   at least 40 GB free disk space, and virtualisation enabled in the BIOS (it usually is).
2. Install **Rancher Desktop** (Windows installer from rancherdesktop.io, copied to the PC on a
   USB stick if the PC has no internet).
3. Open it. On first start choose **dockerd (moby)** as the container engine (*Preferences →
   Container Engine*) and **disable Kubernetes** (*Preferences → Kubernetes*). Kubernetes would
   waste about 1.5 GB of memory.
4. *Preferences → Application → Behavior*: tick **Automatically start at login** and
   **Start in the background**.
5. Wait until Rancher Desktop says it is running, then open a new PowerShell and check:

   ```powershell
   docker version
   docker compose version
   ```

   Both must print version numbers without errors.

*Advanced option:* Docker Engine installed directly inside WSL2 also works for the containers
themselves, but these scripts expect the `docker` command to work from Windows PowerShell.
Use Rancher Desktop unless you have a reason not to.

## 2. Limit how much memory the container system may use

Without a limit, the container system can take most of an 8 GB PC and make Windows unusable.

1. Open Notepad and paste exactly this:

   ```ini
   [wsl2]
   memory=4GB
   processors=2
   swap=2GB
   ```

2. Save it as **`C:\Users\<your user name>\.wslconfig`** (File name `.wslconfig`, type
   *All files*, not `.txt`).
3. In PowerShell run `wsl --shutdown`, then start Rancher Desktop again.

WIMS needs about 3 GB of that 4 GB. If the PC has 16 GB of memory you may use `memory=6GB`.

## 3. Give the server PC a fixed IP address

Office PCs find the server by its address, so the address must never change.

1. Best option: in the **router**, find the server PC in the list of connected devices and
   *reserve* (or "bind") its current address (also called a DHCP reservation).
2. Alternative: Windows *Settings → Network → (your connection) → IP assignment → Edit →
   Manual*, enter an address outside the router's automatic range (for example
   `192.168.1.50`), subnet mask `255.255.255.0`, the router's address as gateway and DNS.
3. Write the address down. This guide uses **192.168.1.50**.

## 4. Make the name `wims.bfp.lan` work on every office PC

Choose **A** (preferred) or **B**.

**A – in the router:** in the router's *DNS* or *Local hostnames* page, add
`wims.bfp.lan` → `192.168.1.50`. Then every PC on the network knows the name. (Not every
router has this; if yours does not, use B.)

**B – on each PC, one time:** open Notepad **as administrator**, open
`C:\Windows\System32\drivers\etc\hosts` (choose *All files*), add a line at the bottom

```
192.168.1.50  wims.bfp.lan
```

and save. Also do this on the server PC itself.

Test from an office PC: `ping wims.bfp.lan` must answer from 192.168.1.50.

> The name is fixed on purpose. A different name needs a **new bundle** built with that name
> (`build-bundle.ps1 -WimsHost <name>`); the address of the server may change (see section 3
> and `setup-certs.ps1`) but the name may not.

## 5. Copy the bundle to the server PC

The bundle is a folder that contains `images\wims-images.tar` (about 2–3 GB), the scripts and
this guide. Copy the **whole folder** from the USB drive to **`C:\WIMS`**. Do not compress it
with Windows "Send to → Compressed folder" (the large file does not fit).

Open PowerShell **in that folder**:

```powershell
cd C:\WIMS
Set-ExecutionPolicy -Scope Process Bypass
```

(The second line only lasts for this PowerShell window and only allows these scripts to run.)

## 6. Install WIMS

```powershell
.\setup-secrets.ps1 -ServerIp 192.168.1.50
```

It asks for: the server's IP, the **first administrator** (username, email, a starting
password), and optional email settings. It then creates random passwords and the master
encryption key in a file called `.env`.

**Right now, copy `C:\WIMS\.env` to a second safe place** (a USB stick kept in a locked drawer
or safe). If this file is lost, encrypted data and backups can never be read again.

```powershell
.\install.ps1 -OpenFirewall
```

This checks the bundle files for damage, loads the programs, creates the certificate, starts
everything and creates the administrator. The first start takes **5–15 minutes**. It ends
with "WIMS-BFP is running". If it stops with a red error, send the text to the developers and
keep the window open.

Check the containers: `docker ps` shows seven names beginning with `wims-`.

## 7. Windows Firewall

`install.ps1 -OpenFirewall` (run as administrator) adds the rule automatically. To do it by
hand, in an **administrator** PowerShell:

```powershell
New-NetFirewallRule -DisplayName "WIMS-BFP HTTPS" -Direction Inbound -Protocol TCP -LocalPort 443,80 -Action Allow -Profile Private,Domain
```

Make sure the office network is set to **Private** (*Settings → Network → Properties*), or the
rule does not apply. Port 443 is the secure website; port 80 only forwards to 443.

## 8. Install the certificate on **each** office PC (one time per PC)

WIMS uses an encrypted (HTTPS) connection with a certificate made on the server by *your own*
certificate authority. Browsers only trust it after the authority is installed. Without this
step, browsers show a "not secure" warning, and **offline mode will not work**.

1. On the server, take **`C:\WIMS\certs\WIMS-BFP-CA.crt`** and **`install-ca-office-pc.ps1`**
   (both in `C:\WIMS\certs\`) and copy them to the office PC (USB stick). These are public files.
   **Never** copy `certs\ca\ca.key`.
2. On the office PC, with both files in one folder, right-click PowerShell → *Run as
   administrator*, then:

   ```powershell
   cd <folder with the two files>
   Set-ExecutionPolicy -Scope Process Bypass
   .\install-ca-office-pc.ps1
   ```

   (No script wanted? Double-click `WIMS-BFP-CA.crt` → *Install Certificate* → *Local
   Machine* → *Place all certificates in the following store* → **Trusted Root Certification
   Authorities**.)
3. Close and reopen the browser. Open **https://wims.bfp.lan**. There must be **no warning**
   and a padlock.
4. *Firefox* keeps its own list: *Settings → Privacy & Security → Certificates → View
   Certificates → Authorities → Import*.

The certificate is valid for about 2 years; the authority for 10. When the server certificate
nears its end (or the server's IP changes), run `.\setup-certs.ps1` on the server and then
`docker compose restart nginx`; the office PCs do not need anything again.

## 9. First login

1. Open **https://wims.bfp.lan** and sign in with the administrator username and the starting
   password you typed in section 6.
2. WIMS asks you to **choose a new password** (12+ characters with upper and lower case, a
   digit and a symbol; the last 3 passwords cannot be reused).
3. WIMS shows a **QR code**. Install an authenticator app on your phone (Microsoft
   Authenticator, Google Authenticator or FreeOTP), scan the code, and type the 6-digit code
   it shows. From now on, administrators and validators need the phone code at each sign-in.
4. In **Admin → System** create the other users (encoders, validators, analysts), give each
   their role and region. New users get an email with a link; if email does not work, set a
   temporary password instead (section 12).

## 10. Keep it running: power and start-up

- **Never sleep:** *Settings → System → Power → Screen and sleep* → set *sleep* to **Never**.
  Also run in an administrator PowerShell: `powercfg /hibernate off`.
- **Network adapter:** *Device Manager → Network adapters → (your adapter) → Properties →
  Power Management* → untick *Allow the computer to turn off this device*.
- **After a power cut:** in the BIOS set *Restore on AC power loss* to **Power On**. In Windows,
  set the PC to sign in by itself (`netplwiz` → untick *Users must enter a user name and
  password*) **only if the room is locked**, because the container system starts when this
  user signs in.
- Rancher Desktop is set to start at login (section 1). The WIMS containers are set to
  restart on their own (`restart: unless-stopped`), so after a reboot WIMS is back in about
  5 minutes without anyone doing anything.
- **Windows Update:** set *Active hours* to office hours so it does not restart the PC while
  people are working.
- Check once after setting everything: restart the PC and confirm https://wims.bfp.lan opens
  by itself.

## 11. Daily backups – and where the master key copy lives

Two folders are created by each backup:

| Folder | Contains | Keep |
|---|---|---|
| `wims-backup-<date>` | the databases, uploaded files | on external media |
| `wims-backup-<date>-secrets` | `.env` (**master key**, passwords) and the certificate authority | **somewhere else** – a different USB stick or the safe |

The master key unlocks the encrypted personal data. Data and key must **not** travel together:
anyone who finds both can read everything.

**Set it up once** (backs up every day at 18:00 to the PC, administrator not needed):

```powershell
cd C:\WIMS
.\schedule-backup.ps1 -Destination C:\WIMS-Backups -SecretsDestination C:\WIMS-Secrets -Time 18:00
```

**Every day (or at least every week):** plug in the external drive and copy the newest
`wims-backup-…` folder to it; copy the `…-secrets` folder to the *other* medium. The PC keeps
the last 14 data backups automatically.

**Run a backup right now by hand:**

```powershell
.\backup.ps1 -Destination E:\WIMS-Backups -SecretsDestination F:\WIMS-Secrets
```

It prints "Backup complete" only if the files were checked and are readable.

**Test a restore** after the first week and then every few months (it proves the backups work):
see section 14, on a spare PC if possible.

## 12. When the internet is down

- WIMS keeps working on the office network. Encoders can keep working even if the network
  between their PC and the server drops: records wait in the browser and are sent when the
  connection returns (offline mode needs section 8 done on that PC).
- **Email does not work** (no verification, password-reset or alert emails). A new user, or a
  user who forgot the password, cannot use the email link. Use the fallback:
  1. An administrator signs in → **Admin → System → Users**.
  2. Find the user → **Set a temporary password** → type one (12+ characters, upper and lower
     case, digit, symbol).
  3. Tell the user the password in person or by phone. At the next sign-in they must change it.
- If the **only administrator** forgot their password and email is down: open
  `https://wims.bfp.lan/auth/admin`, sign in as **`kcadmin`** (the password is
  `KEYCLOAK_ADMIN_PASSWORD` in `C:\WIMS\.env`), choose realm **bfp**, *Users* → the user →
  *Credentials* → *Reset password* (switch *Temporary* on).
- Map pictures need internet; the map shows grey squares while offline. Everything else works.

## 13. Applying an update bundle

You receive a new bundle folder (same layout as in section 5).

1. Copy the new bundle files **over** `C:\WIMS`, replacing files. **Do not delete `.env` or the
   `certs` folder** (they are not part of the bundle, so a normal copy keeps them).
2. In PowerShell:

   ```powershell
   cd C:\WIMS
   Set-ExecutionPolicy -Scope Process Bypass
   .\install.ps1
   ```

   It first takes a backup (to `C:\WIMS-Backups`), verifies the new files, loads the new
   programs, and restarts WIMS. Your data stays. The database updates itself on start.
3. Open https://wims.bfp.lan, sign in and check a few records. If anything is wrong, restore the
   backup taken at step 2 (section 14) and tell the developers.

## 14. Restoring from a backup (or moving to a new PC)

On a **new** PC: do sections 1–5 first (no `setup-secrets.ps1`!). Then, with the backup
and secrets folders available:

```powershell
cd C:\WIMS
Set-ExecutionPolicy -Scope Process Bypass
.\restore.ps1 -BackupFolder E:\WIMS-Backups\wims-backup-20260101-180000 `
              -SecretsFolder F:\WIMS-Secrets\wims-backup-20260101-180000-secrets
```

It restores the passwords, master key and certificate authority, loads the programs, replaces
the data, and starts WIMS. Because the authority is restored, office PCs keep trusting the
site. Type `RESTORE` when asked. On the same PC the command is the same; it **replaces the
current data** with the backup.

## 15. If something is wrong

| Problem | What to do |
|---|---|
| Browser says "connection refused" / cannot be reached | `docker ps` – all seven `wims-` containers should say *Up*; if not: `docker compose up -d` in `C:\WIMS`. Check the firewall (7) and the name (4). |
| Browser shows a certificate warning | Section 8 was not done on that PC, or the PC is opening the IP address instead of the name `wims.bfp.lan`. |
| Page loads, then login fails | Open the address by **name**, never by IP. Check the PC's clock (login codes need the right time). |
| Server very slow | `docker stats --no-stream` shows memory per service; send it to the developers. Check `.wslconfig` (section 2). |
| Need the logs | `docker compose logs --tail 200 backend` (or `keycloak`, `nginx`, `postgres`, `celery-worker`, `frontend`). |
| Stop / start everything | `docker compose stop` / `docker compose up -d` (in `C:\WIMS`). Never run `docker compose down -v`: the `-v` **deletes all data**. |
