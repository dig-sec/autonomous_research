"""
Research Output CLI

Query and review research outputs from Elasticsearch with filtering options.
"""
import argparse
import sys
from elasticsearch import Elasticsearch
import json

CONFIG_PATH = "config/config.yaml"

class ResearchOutputCLI:
    def __init__(self, config_path=CONFIG_PATH):
        import yaml
        # Load secure Elasticsearch configuration
        sys.path.append('src')
        from src.autonomous_research.config.secure_config import get_elasticsearch_config
        es_config = get_elasticsearch_config()
        
        self.es = Elasticsearch(
            hosts=[{"host": es_config["host"], "port": es_config["port"]}],
            http_auth=(es_config["user"], es_config["password"])
        )
        self.output_index = es_config["output_index"]

    def query_outputs(self, technique_id=None, platform=None, min_confidence=None, start_date=None, end_date=None, max_results=10):
        query = {"bool": {"must": []}}
        if technique_id:
            query["bool"]["must"].append({"term": {"technique_id": technique_id}})
        if platform:
            query["bool"]["must"].append({"term": {"platform": platform}})
        if min_confidence:
            query["bool"]["must"].append({"range": {"confidence_score": {"gte": min_confidence}}})
        if start_date or end_date:
            date_range = {}
            if start_date:
                date_range["gte"] = start_date
            if end_date:
                date_range["lte"] = end_date
            query["bool"]["must"].append({"range": {"last_updated": date_range}})
        body = {"query": query, "size": max_results}
        res = self.es.search(index=self.output_index, body=body)
        return [hit["_source"] for hit in res["hits"]["hits"]]

    def run(self):
        parser = argparse.ArgumentParser(description="Query research outputs from Elasticsearch.")
        parser.add_argument("--technique_id", type=str, help="Filter by technique ID")
        parser.add_argument("--platform", type=str, help="Filter by platform")
        parser.add_argument("--min_confidence", type=float, help="Minimum confidence score")
        parser.add_argument("--start_date", type=str, help="Start date (YYYY-MM-DD)")
        parser.add_argument("--end_date", type=str, help="End date (YYYY-MM-DD)")
        parser.add_argument("--max_results", type=int, default=10, help="Maximum results to return")
        args = parser.parse_args()
        results = self.query_outputs(
            technique_id=args.technique_id,
            platform=args.platform,
            min_confidence=args.min_confidence,
            start_date=args.start_date,
            end_date=args.end_date,
            max_results=args.max_results
        )
        print(json.dumps(results, indent=2))

if __name__ == "__main__":
    cli = ResearchOutputCLI()
    cli.run()
