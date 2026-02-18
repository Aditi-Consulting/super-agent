# 🚀 Splunk Alert Processing with LangGraph + MySQL

## Description
This project demonstrates an agentic workflow using [LangGraph](https://github.com/langchain-ai/langgraph) to automate Splunk alert processing. It reads alert data from Excel, parses logs, classifies them, and stores structured results in a MySQL database.

---

## 📦 Prerequisites
- Python 3.10+
- MySQL (local or remote)
- OpenAI API key
- Excel file with Splunk alerts

---

## 🛠️ Setup

### 1. Clone the Repository
```bash
git clone https://github.com/hasratp/ai.git
cd ai
```

### 2. Install Dependencies
```bash
pip install -r requirements.txt
```

### 3. Prepare the Database
Log into MySQL and run:
```sql
CREATE DATABASE IF NOT EXISTS monitoring;
USE monitoring;
CREATE TABLE IF NOT EXISTS alerts (
    id INT AUTO_INCREMENT PRIMARY KEY,
    time DATETIME,
    host VARCHAR(100),
    program VARCHAR(50),
    user VARCHAR(50),
    action VARCHAR(50),
    status VARCHAR(50),
    src_ip VARCHAR(50),
    dest VARCHAR(100),
    port VARCHAR(10),
    message TEXT
);
```

### 4. Add Your Credentials
Create a `.env` file in the project root:
```env
OPENAI_API_KEY=your_openai_key
OPENAI_MODEL_CLASSIFY=gpt-4.1-mini
OPENAI_MODEL_AGENT=gpt-4.1-mini
MYSQL_HOST=localhost
MYSQL_USER=your_username
MYSQL_PASSWORD=your_password
MYSQL_DATABASE=monitoring
```

---

## 🚀 Start the Application
1. Place your Excel file (e.g. `alerts.xlsx`) in the `data` directory.
2. Run:
```bash
python main.py
```

The script will:
- Read alerts from the Excel file
- Parse each alert into structured fields
- Insert them into the MySQL `alerts` table

---

## 🧩 Extending
- Add more nodes for alert classification, severity scoring, or notifications
- Swap Excel source for Splunk API for live alert ingestion
- Customize classification models

---

## 📝 License
MIT License – use freely for learning or internal tools.

---

## 📬 Contact
For questions or support, open an issue in the repository.
