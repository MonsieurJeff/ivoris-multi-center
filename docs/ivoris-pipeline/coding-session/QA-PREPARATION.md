# Q&A Preparation

**Anticipated questions and prepared answers**

---

## Technical Questions

### "Why SQL Server and not PostgreSQL/MySQL?"

**Answer:**
> "Ivoris is a German dental software that uses SQL Server. We work with what the customer has. The good news is - our Python code would work with minor changes for any database. Just swap the connection string and driver."

---

### "Why not use an ORM like SQLAlchemy?"

**Answer:**
> "For this specific use case - a read-only extraction - raw SQL is simpler and more transparent. ORMs are great for applications with complex CRUD, but here we have one query that runs once a day. Keeping it simple makes it easier to debug and hand off to others."

---

### "What about connection pooling?"

**Answer:**
> "For a daily batch job that runs once and exits, connection pooling isn't necessary. If this were a web service handling many requests, absolutely - we'd use a connection pool. Right design for right use case."

---

### "How do you handle errors?"

**Answer:**
> "The script logs errors and exits with a non-zero status. The cron job captures output to a log file. For production, I'd add email alerts on failure. We could also add retry logic with exponential backoff."

---

### "What if the database schema changes?"

**Answer:**
> "Good question! The query will fail if columns are renamed or removed. For production, I'd add a schema validation step at startup - check that expected columns exist before running. Also, versioning the extraction query helps track changes."

---

### "How do you handle large datasets?"

**Answer:**
> "This query extracts one day's data - usually small. For large historical extractions, I'd add pagination or chunking. Also consider streaming to file instead of loading all into memory."

---

### "Why JSON and not just CSV?"

**Answer:**
> "Both! JSON preserves structure better - service_codes as an array instead of comma-separated string. CSV is better for Excel users. We support both formats via --format flag."

---

### "What about data privacy/GDPR?"

**Answer:**
> "Great point. Patient data is sensitive. In production:
> - Encrypt files at rest
> - Secure transfer (SFTP, not plain FTP)
> - Access logging
> - Data retention policies
> - Consider pseudonymization if full IDs aren't needed"

---

## Architecture Questions

### "Why not use a workflow tool like Airflow?"

**Answer:**
> "For a single daily task, Airflow is overkill. It adds operational complexity - another service to maintain. Simple cron works. If we had 10+ interdependent extraction jobs, then Airflow makes sense."

---

### "Should this be a microservice?"

**Answer:**
> "Not for a batch job. Microservices make sense for request/response workloads. This is fire-and-forget - runs once, writes file, exits. A simple script is the right tool."

---

### "What about Docker for production?"

**Answer:**
> "Yes! Docker makes deployment consistent. Package the script, dependencies, and cron into one container. Same image runs in dev, staging, production. We could also use Kubernetes CronJob."

---

### "How would you scale this to multiple clinics?"

**Answer:**
> "That's actually our multi-center extension! Each clinic gets its own entry in centers.yml. The script loops through all centers, extracts from each, outputs separate files. Same code, different config."

---

## Process Questions

### "How did you figure out the schema?"

**Answer:**
> "Pure exploration. INFORMATION_SCHEMA queries to list tables and columns. Then TOP 5 * FROM each table to see sample data. Foreign key queries to understand relationships. Takes about 30 minutes for an unfamiliar database."

---

### "How long did this take to build?"

**Answer:**
> "The core extraction - a few hours. Most time spent understanding the schema and business requirements. The code itself is straightforward once you know what to extract."

---

### "What would you do differently?"

**Answer:**
> "Add more robust error handling from the start. Also, I'd set up a test database with known data - makes it easier to verify the extraction is correct."

---

## German-Specific Questions

### "What's GKV vs PKV?"

**Answer:**
> "German healthcare has two systems:
> - **GKV** (Gesetzliche Krankenversicherung) - Public/statutory insurance, ~90% of population
> - **PKV** (Private Krankenversicherung) - Private insurance, ~10%
> - **Selbstzahler** - Self-pay, no insurance
>
> Billing codes and reimbursement differ between them - that's why we track insurance status."

---

### "What are those service codes like '01', '1040', 'Ä935'?"

**Answer:**
> "These are German dental billing codes:
> - Numbers (01, 1040) are from BEMA - the public insurance fee schedule
> - Ä-codes (Ä935) are from GOZ/GOÄ - private insurance fee schedules
>
> Each code represents a specific procedure with a set reimbursement amount."

---

## If You Don't Know

**Template response:**
> "That's a good question. I don't have a definitive answer right now, but I can look into it and follow up. [Note it down visibly]"

**Or:**
> "Let me think about that... [pause] My initial thought is [X], but I'd want to verify before giving a definitive answer."

---

## Questions to Deflect

### "Can you help me with my specific database?"

**Answer:**
> "I'd be happy to discuss offline! The principles we covered today apply - explore the schema, map requirements to tables, build incrementally. Let's connect after the session."

### "What about [complex edge case]?"

**Answer:**
> "Great edge case. For today's scope, we're keeping it simple. That would be a good enhancement for version 2. Let's note it and discuss offline."
