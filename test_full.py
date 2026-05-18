import asyncio
import os
import sys

# Configure logging before importing anything
import logging
logging.basicConfig(level=logging.INFO, stream=sys.stdout)

from api.models import ScanRequest
from agent.brain import start_scan, SCAN_STATE, _run_scan, _new_scan_id, _init_scan

async def test():
    req = ScanRequest(app_url="http://localhost:3001")
    scan_id = _new_scan_id()
    _init_scan(scan_id, req)
    
    print(f"Starting scan {scan_id}")
    await _run_scan(scan_id, req)
    
    print("FINISHED SCAN:", scan_id)
    print("FINDINGS:", SCAN_STATE[scan_id]["findings_so_far"])
    print("EXPLORED:", SCAN_STATE[scan_id]["nodes_explored"])
    print("TOTAL EXPLORE:", SCAN_STATE[scan_id]["nodes_total"])
    print("GAPS:", len(SCAN_STATE[scan_id]["gaps"]))

asyncio.run(test())
