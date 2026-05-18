import asyncio
from api.models import ScanRequest
from agent.brain import start_scan, SCAN_STATE

async def test():
    req = ScanRequest(app_url="http://localhost:3001")
    scan_id = await start_scan(req)
    print("FINISHED SCAN:", scan_id)
    print("FINDINGS:", SCAN_STATE[scan_id]["findings_so_far"])
    print("EXPLORED:", SCAN_STATE[scan_id]["nodes_explored"])
    print("TOTAL EXPLORE:", SCAN_STATE[scan_id]["nodes_total"])

asyncio.run(test())
