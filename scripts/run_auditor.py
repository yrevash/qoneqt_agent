import asyncio
import sys
import os

sys.path.append(os.getcwd())

from app.modules.watcher.service import auditor_service

if __name__ == "__main__":
    asyncio.run(auditor_service.run_audit_cycle())