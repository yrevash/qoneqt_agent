import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from app.modules.watcher.service import auditor_service

if __name__ == "__main__":
    asyncio.run(auditor_service.run_audit_cycle())