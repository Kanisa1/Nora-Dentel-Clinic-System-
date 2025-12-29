# Nora Dental Clinic - Windows Server Deployment Guide

## 🚀 Deploying on Windows Server with NSSM

### Prerequisites

1. **Windows Server 2016 or later** (or Windows 10/11)
2. **Python 3.11.9** installed
3. **PostgreSQL 12+** installed and running
4. **NSSM** (Non-Sucking Service Manager)
5. **Admin privileges**

---

## 📥 Step 1: Download NSSM

1. Download NSSM from: https://nssm.cc/download
2. Extract the appropriate version (win64 for 64-bit Windows)
3. Copy `nssm.exe` to your project folder: `C:\Users\HP\Nora-Dentel-Clinic-System-\`

---

## ⚙️ Step 2: Configure Environment

1. **Edit `.env` file** with production settings:
   ```env
   DJANGO_DEBUG=False
   DJANGO_SECRET_KEY=your-very-secure-random-key-here
   ALLOWED_HOSTS=localhost,127.0.0.1,your-server-ip,your-domain.com
   CSRF_TRUSTED_ORIGINS=http://localhost:8000,http://your-server-ip:8000
   
   POSTGRES_DB=nora_clinic_db
   POSTGRES_USER=nora_user
   POSTGRES_PASSWORD=your_secure_password
   POSTGRES_HOST=localhost
   POSTGRES_PORT=5432
   ```

2. **Setup Database**:
   ```sql
   -- In PostgreSQL (pgAdmin or psql)
   CREATE DATABASE nora_clinic_db;
   CREATE USER nora_user WITH PASSWORD 'your_secure_password';
   GRANT ALL PRIVILEGES ON DATABASE nora_clinic_db TO nora_user;
   ```

3. **Run Migrations**:
   ```powershell
   cd C:\Users\HP\Nora-Dentel-Clinic-System-
   .\venv\Scripts\activate
   python manage.py migrate
   python manage.py createsuperuser
   python manage.py collectstatic --noinput
   ```

---

## 🔧 Step 3: Install as Windows Service

### Automatic Installation

1. **Right-click** `install_service.bat`
2. Select **"Run as Administrator"**
3. Wait for installation to complete

The script will:
- Install the service named "NoraDentalClinic"
- Configure auto-start on system boot
- Create log files in `logs/` folder
- Start the service immediately

### Manual Installation (if needed)

```powershell
# Open PowerShell as Administrator
cd C:\Users\HP\Nora-Dentel-Clinic-System-

# Install service
.\nssm.exe install NoraDentalClinic "C:\Users\HP\Nora-Dentel-Clinic-System-\venv\Scripts\python.exe" "C:\Users\HP\Nora-Dentel-Clinic-System-\manage.py" runserver 0.0.0.0:8000 --noreload

# Set working directory
.\nssm.exe set NoraDentalClinic AppDirectory "C:\Users\HP\Nora-Dentel-Clinic-System-"

# Set display name and description
.\nssm.exe set NoraDentalClinic DisplayName "Nora Dental Clinic System"
.\nssm.exe set NoraDentalClinic Description "Healthcare Management System"

# Set auto-start
.\nssm.exe set NoraDentalClinic Start SERVICE_AUTO_START

# Set logging
mkdir logs
.\nssm.exe set NoraDentalClinic AppStdout "C:\Users\HP\Nora-Dentel-Clinic-System-\logs\service.log"
.\nssm.exe set NoraDentalClinic AppStderr "C:\Users\HP\Nora-Dentel-Clinic-System-\logs\service_error.log"

# Start service
.\nssm.exe start NoraDentalClinic
```

---

## 🔌 Step 4: Configure Windows Firewall

Allow incoming connections on port 8000:

```powershell
# Run as Administrator
netsh advfirewall firewall add rule name="Nora Clinic Port 8000" dir=in action=allow protocol=TCP localport=8000
```

Or use Windows Firewall GUI:
1. Open **Windows Defender Firewall with Advanced Security**
2. Click **Inbound Rules** → **New Rule**
3. Select **Port** → **TCP** → **Specific local ports: 8000**
4. **Allow the connection**
5. Name it "Nora Dental Clinic"

---

## 📊 Service Management Commands

### Using NSSM:

```powershell
# Check service status
nssm status NoraDentalClinic

# Start service
nssm start NoraDentalClinic

# Stop service
nssm stop NoraDentalClinic

# Restart service
nssm restart NoraDentalClinic

# Remove service
nssm remove NoraDentalClinic confirm
```

### Using Windows Services:

1. Press **Win + R**, type `services.msc`
2. Find **"Nora Dental Clinic System"**
3. Right-click for options: Start, Stop, Restart, Properties

### Using Command Line:

```powershell
# Start
net start NoraDentalClinic

# Stop
net stop NoraDentalClinic

# Check status
sc query NoraDentalClinic
```

---

## 🌐 Accessing the System

After service starts, access the system at:

- **Locally**: http://localhost:8000
- **From other computers**: http://[SERVER-IP]:8000
  - Example: http://192.168.1.100:8000

**Admin Login**:
- Username: `test_admin` (change this!)
- Password: `admin123` (change this!)

---

## 📁 Important Files

- **install_service.bat**: Install as Windows service
- **uninstall_service.bat**: Remove Windows service
- **start_manual.bat**: Start manually (for testing)
- **start_service.bat**: Service startup script
- **.env**: Configuration file
- **logs/service.log**: Application logs
- **logs/service_error.log**: Error logs

---

## 🔍 Troubleshooting

### Service won't start

1. Check logs: `logs\service_error.log`
2. Verify Python path: `where python`
3. Test manual start: Run `start_manual.bat`
4. Check database connection in `.env`

### Can't access from other computers

1. Check firewall: `netsh advfirewall firewall show rule name="Nora Clinic Port 8000"`
2. Verify server is listening: `netstat -an | findstr 8000`
3. Try accessing with server IP: `http://[IP]:8000`

### Database connection errors

1. Verify PostgreSQL is running
2. Check credentials in `.env`
3. Test database connection:
   ```powershell
   psql -U nora_user -d nora_clinic_db -h localhost
   ```

### Port 8000 already in use

1. Find process using port: `netstat -ano | findstr :8000`
2. Kill process: `taskkill /PID [process_id] /F`
3. Or change port in `install_service.bat` (e.g., 8080)

---

## 🔐 Security Checklist

- [ ] Changed DJANGO_SECRET_KEY in `.env`
- [ ] Set DJANGO_DEBUG=False
- [ ] Updated ALLOWED_HOSTS with server IP/domain
- [ ] Created new admin user (not test_admin)
- [ ] Changed database password
- [ ] Configured Windows Firewall
- [ ] Disabled unnecessary Windows services
- [ ] Set strong passwords
- [ ] Regular backups configured

---

## 💾 Backup Configuration

### Database Backup Script

Create `backup_database.bat`:

```batch
@echo off
set BACKUP_DIR=C:\Backups\NoraClinic
set TIMESTAMP=%date:~-4,4%%date:~-10,2%%date:~-7,2%_%time:~0,2%%time:~3,2%
mkdir %BACKUP_DIR% 2>nul

"C:\Program Files\PostgreSQL\14\bin\pg_dump.exe" -U nora_user -d nora_clinic_db > "%BACKUP_DIR%\backup_%TIMESTAMP%.sql"

echo Backup completed: %BACKUP_DIR%\backup_%TIMESTAMP%.sql
```

Schedule this in Windows Task Scheduler (daily at 2 AM).

---

## 📞 Production Recommendations

1. **Use a proper web server**: Consider IIS with reverse proxy for production
2. **Enable HTTPS**: Use SSL certificate
3. **Regular updates**: Keep dependencies updated
4. **Monitoring**: Setup application monitoring
5. **Backups**: Automated daily database + media backups
6. **Documentation**: Keep admin credentials secure

---

## 🎯 Next Steps

1. ✅ Service installed and running
2. ✅ Access system from browser
3. ✅ Create new admin user
4. ✅ Configure firewall
5. ⬜ Setup automated backups
6. ⬜ Configure SSL (if needed)
7. ⬜ Train clinic staff

---

**For support or issues, check the logs in `logs/` folder first!**
