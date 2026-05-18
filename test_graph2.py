import asyncio
from api.models import ScanRequest
from agent.brain import start_scan, SCAN_STATE
from engine.crawler import crawl
from engine.graph_builder import build_coverage_graph

async def test():
    req = ScanRequest(app_url="http://localhost:3001")
    elements = await crawl(req.app_url, max_pages=10)
    graph = build_coverage_graph(elements, req.existing_tests_path)
    count = 0
    for nid, attrs in graph.nodes(data=True):
        print(nid, attrs.get("element_type", "NO_ELEMENT_TYPE"))
        if attrs.get("element_type") == "page": count += 1
    print("TOTAL PAGE NODES:", count)

asyncio.run(test())
