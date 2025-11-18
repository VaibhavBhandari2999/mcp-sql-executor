# MCP Agent Demo

A minimal **Model Context Protocol (MCP)** server that lets an LLM safely query a Local/Cloud database (MySQL, PostgreSQL) using SQL tools, then summarizes the results into a natural-language answer.

This repo shows how to:

- Run an MCP server over stdio using `fastmcp`
- Connect to DB using a connection pool
- Plan safe SQL via an LLM (planner -> SQL + params)
- Call the MCP tool from a Python client and summarize results

---

## Project Structure

```text
.
├── server.py         # MCP server exposing a 'sql_query' tool
├── db.py             # DB connection pool + 'query()' helper
├── planner.py        # LLM-based SQL planner (natural-language -> SQL + params)
├── summarizer.py     # LLM-based answer summarizer for result rows
├── mcp_client.py     # MCP stdio client wrapper
├── run.py            # End-to-end demo: question -> SQL -> DB -> answer
├── requirements.txt
└── README.md
```
---

## Prerequisites:
One of:

- Local MySQL

- Local PostgreSQL

- AWS RDS (MySQL or Postgres)

An OpenAI-compatible API key (OpenAI or any provider exposing the same API)

mysqld/psql available on your PATH

## Installing and Setup
### 1. Install python dependencies

From the project root:
```code

python -m venv .venv
source .venv/bin/activate

pip install -r requirements.txt

```

### 2. Start Server (if local)

2.1 MySQL
In one terminal tab:
```code 
mysqld
```

Note -
    To stop server: 

You can do Contrl+C but sometimes it doesn’t work

So you'll have to go into a new terminal tab and run

    > pkill -f mysqld

2.2 PostgreSQL
In your terminal:
```code
brew services start postgresql
```

### 3. Setup DB

3.1. MySQL
(In another tab, we can do > mysql -u <username> -p -h 127.0.0.1 -P 3306)

3.2. PostgreSQL
(In another tab, we can do >psql -h 127.0.0.1 -U <user> -d <database>)

On first login, username is root, but switch to your created user later

- Create Database

- Create User

- Create Table(s)

### 4. Add Data

Add data to your tables

## Defining Env variables
Create an .env file in project root which contains:
```code
DB_HOST= (mostly 127.0.0.1)
DB_PORT= (3306 for MySQL, 5432 for Postgres)
DB_USER= (username you created)
DB_PASSWORD= (password you created)
DB_DATABASE= (DB you created)
DB_ENGINE= (mysql or postgres)

OPENAI_API_KEY=sk-...
OPENAI_MODEL=gpt-4o-mini
OPENAI_BASE_URL=https://api.openai.com/v1

PYTHON_BIN=/absolute/path/to/your/.venv/bin/python
MCP_CWD=/absolute/path/to/your/project
```

You can use Deepseek models through OpenRouter(https://openrouter.ai/) as well. 
    
- Change the API key and model to the ones you want. 
- The BASE_URL then changes to https://openrouter.ai/api/v1

Note - To use AWS RDS, simply replace DB_HOST with your RDS endpoint and ensure your IP has access on port 3306 or 5432.


## Run Pipeline
```bash
python3 run.py
```

Output will look like:
```
Question: Show price and stock for PS12745538

[Plan]
{
  "sql": "SELECT price, in_stock FROM parts WHERE ps_num = %s",
  "params": ["PS12745538"]
}

[Raw rows JSON]
[{"price": "39.95", "in_stock": 1}]

---------- Answer ----------
The price of PS12745538 is 39.95 and it is in stock.
```