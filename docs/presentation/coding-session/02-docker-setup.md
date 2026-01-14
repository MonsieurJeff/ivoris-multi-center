# Step 2: Docker Setup

> **💬 Talking Points**
> - "Docker lets us run SQL Server on Mac/Windows without installing it natively"
> - "It's the same SQL Server that runs in production - just containerized"
> - "One command to start, one command to stop - no messy installations"

---

## Why Docker?

- **Portability**: Works on any machine (Mac, Windows, Linux)
- **Isolation**: Doesn't pollute your system
- **Reproducibility**: Same environment everywhere
- **Easy scaling**: Spin up multiple databases for testing

---

> **💬 Talking Points - docker-compose.yml**
> - "Let me walk through this file line by line"
> - "ACCEPT_EULA=Y - Microsoft requires this legally"
> - "The volume is key - without it, data would be lost when container stops"
> - "Port 1433 is the default SQL Server port"

## The docker-compose.yml Explained

```yaml
version: '3.8'

services:
  sqlserver:
    image: mcr.microsoft.com/mssql/server:2019-latest
    container_name: ivoris-sqlserver
    environment:
      - ACCEPT_EULA=Y                    # Required: Accept license
      - SA_PASSWORD=YourStrong@Passw0rd  # SA (admin) password
      - MSSQL_PID=Express                # Edition: Express is free
    ports:
      - "1433:1433"                       # Host:Container port mapping
    volumes:
      - sqlserver_data:/var/opt/mssql    # Persist data

volumes:
  sqlserver_data:                         # Named volume for persistence
```

**Line by line:**

| Line | Explanation |
|------|-------------|
| `image: mcr.microsoft.com/mssql/server:2019-latest` | Official Microsoft SQL Server image |
| `ACCEPT_EULA=Y` | Legal requirement to accept license |
| `SA_PASSWORD` | System Admin password (must be strong) |
| `MSSQL_PID=Express` | Free edition, sufficient for development |
| `ports: "1433:1433"` | Expose SQL Server port to host |
| `volumes` | Keep data when container restarts |

---

## Commands

### Start the database

```bash
cd ~/Projects/outre_base/sandbox/ivoris-pipeline

# Start in background (-d = detached)
docker-compose up -d
```

**What happens:**
1. Docker downloads SQL Server image (first time only, ~500MB)
2. Creates container named `ivoris-sqlserver`
3. Starts SQL Server on port 1433
4. Creates persistent volume for data

### Check status

```bash
# See running containers
docker ps

# Expected output:
# CONTAINER ID   IMAGE                                        STATUS         PORTS                    NAMES
# abc123...      mcr.microsoft.com/mssql/server:2019-latest   Up 2 minutes   0.0.0.0:1433->1433/tcp   ivoris-sqlserver
```

### View logs

```bash
# See SQL Server startup logs
docker logs ivoris-sqlserver

# Follow logs in real-time
docker logs -f ivoris-sqlserver
```

**Look for:** `SQL Server is now ready for client connections`

### Stop the database

```bash
# Stop but keep data
docker-compose stop

# Stop and remove container (data persists in volume)
docker-compose down

# Stop and DELETE all data (careful!)
docker-compose down -v
```

---

> **💬 Talking Points - Connecting**
> - "There are three ways to connect - CLI, GUI, or Python"
> - "For data exploration, I prefer Azure Data Studio - it's free and works great"
> - "For scripting and automation, we'll use pyodbc from Python"

## Connect to SQL Server

### Option 1: sqlcmd (command line)

```bash
# From inside container
docker exec -it ivoris-sqlserver /opt/mssql-tools/bin/sqlcmd \
  -S localhost -U sa -P 'YourStrong@Passw0rd'

# From host (requires sqlcmd installed)
sqlcmd -S localhost,1433 -U sa -P 'YourStrong@Passw0rd'
```

### Option 2: Azure Data Studio (GUI)

1. Download: https://azure.microsoft.com/products/data-studio
2. New Connection:
   - Server: `localhost,1433`
   - Authentication: SQL Login
   - User: `sa`
   - Password: `YourStrong@Passw0rd`

### Option 3: Python (pyodbc)

```python
import pyodbc

conn_str = (
    "DRIVER={ODBC Driver 18 for SQL Server};"
    "SERVER=localhost,1433;"
    "DATABASE=DentalDB;"
    "UID=sa;"
    "PWD=YourStrong@Passw0rd;"
    "TrustServerCertificate=yes"
)

conn = pyodbc.connect(conn_str)
cursor = conn.cursor()
cursor.execute("SELECT @@VERSION")
print(cursor.fetchone()[0])
```

---

## Port Conflicts

If port 1433 is already in use:

```bash
# Check what's using port 1433
lsof -i :1433

# Option 1: Stop the other service
# Option 2: Use different port in docker-compose.yml
ports:
  - "1434:1433"  # Use 1434 on host

# Then connect with:
sqlcmd -S localhost,1434 -U sa -P 'YourStrong@Passw0rd'
```

---

## Multi-Center Setup (Part 2)

For the extension challenge, we use port 1434:

```yaml
# docker-compose.yml for multi-center
services:
  sqlserver:
    container_name: ivoris-multi-sqlserver
    ports:
      - "1434:1433"  # Different port to avoid conflict
```

---

## Quick Reference

| Command | Description |
|---------|-------------|
| `docker-compose up -d` | Start database |
| `docker-compose stop` | Stop database |
| `docker-compose down` | Remove container |
| `docker-compose down -v` | Remove container + data |
| `docker ps` | List running containers |
| `docker logs <name>` | View container logs |
| `docker exec -it <name> bash` | Shell into container |

---

## Next Step

→ [03-explore-database.md](./03-explore-database.md) - Explore the database structure
