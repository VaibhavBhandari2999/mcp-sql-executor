import sys
import json

from planner import plan_sql
from mcp_client import call_sql_via_mcp
from summarizer import summarize


def main():
    

    question = "Show price and stock for PS12745538"
    print(f"Question: {question}")

    #Plan SQL
    plan = plan_sql(question)
    print("\nPlan:")
    print(json.dumps(plan, indent=2))

    #Execute SQL via MCP
    rows_json = call_sql_via_mcp(plan["sql"], plan["params"])
    print("\nRaw rows JSON:")
    print(rows_json)

    rows = json.loads(rows_json)

    #Summarize SQL results into natural language answer
    answer = summarize(question, rows)
    print("\n---------- Answer ----------")
    print(answer)


if __name__ == "__main__":
    main()
