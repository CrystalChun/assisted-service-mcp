#!/usr/bin/env python3
"""
Main entry point for the OpenShift Assisted Installer Log Analyzer.
"""
import logging
import json
from datetime import datetime
from typing import List, Optional

from service_client.assisted_service_api import InventoryClient

from log_analyzer.log_analyzer import LogAnalyzer, ClusterAnalyzer
from log_analyzer.signatures import ALL_SIGNATURES, SignatureResult


def json_serial(obj):
    """JSON serializer for objects not serializable by default json code."""
    if isinstance(obj, datetime):
        return obj.isoformat()
    raise TypeError(f"Type {type(obj)} not serializable")


async def analyze_cluster(
    cluster_id: str,
    api_client: InventoryClient,
    specific_signatures: Optional[List[str]] = None,
) -> List[SignatureResult]:
    """
    Analyze a cluster based off of its data and events.

    Args:
        cluster_id: UUID of the cluster to analyze
        api_client: Client to fetch cluster data and events with
        specific_signatures: List of specific signature names to run (None for all)

    Returns:
        List of SignatureResult objects
    """
    logger = logging.getLogger(__name__)

    # Initialize API client
    logger.info("Analyzing cluster: %s", cluster_id)

    try:
        # Download cluster data and events
        cluster_data = await api_client.get_cluster(cluster_id)
        events = await api_client.get_events(cluster_id)

        # Initialize log analyzer
        log_analyzer = LogAnalyzer(logs_archive)

        # Determine which signatures to run
        signatures_to_run = ALL_SIGNATURES
        if specific_signatures:
            signature_classes = {sig.__name__: sig for sig in ALL_SIGNATURES}
            signatures_to_run = []
            for sig_name in specific_signatures:
                if sig_name in signature_classes:
                    signatures_to_run.append(signature_classes[sig_name])
                else:
                    logger.warning("Unknown signature: %s", sig_name)

        # Run signatures
        results = []
        for signature_class in signatures_to_run:
            logger.debug("Running signature: %s", signature_class.__name__)
            try:
                signature = signature_class()
                result = signature.analyze(log_analyzer)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(
                    "Error running signature %s: %s", signature_class.__name__, e
                )

        return results

    except Exception as e:
        logger.error("Error analyzing cluster %s: %s", cluster_id, e)
        raise


async def analyze_cluster_logs(
    cluster_id: str,
    api_client: InventoryClient,
    specific_signatures: Optional[List[str]] = None,
) -> List[SignatureResult]:
    """
    Analyze a cluster's logs.

    Args:
        cluster_id: UUID of the cluster to analyze
        api_client: Client to fetch log files with
        specific_signatures: List of specific signature names to run (None for all)

    Returns:
        List of SignatureResult objects
    """
    logger = logging.getLogger(__name__)

    # Initialize API client
    logger.info("Analyzing cluster: %s", cluster_id)

    try:
        analyzer = ClusterAnalyzer()
        # first call the api to get the cluster and check if logs are available
        cluster = await api_client.get_cluster(cluster_id)
    
        cluster_metadata = cluster.to_dict()
        
        if cluster.logs_info != "completed":
            print("logs are not available, defaulting to signatures that don't require logs")
            analyzer.set_cluster_metadata(cluster_metadata)
            events = await api_client.get_events(cluster_id)
            events = json.loads(events)
            analyzer.set_cluster_events(events)
            signatures_to_run = [signature for signature in ALL_SIGNATURES if not signature.logs_required]
            print(len(signatures_to_run))
        else:
            output_file = "cluster_metadata.json"
            analyzer.set_cluster_metadata(cluster_metadata)

            with open(output_file, "w") as f:
                json.dump(analyzer.metadata, f, indent=2, default=json_serial)
            print(f"cluster_metadata written to {output_file}")
            # Download logs
            print("downloading logs")
            logs_archive = await api_client.get_cluster_logs(cluster_id)
            analyzer = LogAnalyzer(logs_archive)
            cluster_data_from_file = analyzer.metadata
            output_file = "cluster_data_from_file.json"
            with open(output_file, "w") as f:
                json.dump(cluster_data_from_file, f, indent=2, default=json_serial)
            print(f"cluster_data_from_file written to {output_file}")
            # Determine which signatures to run
            signatures_to_run = ALL_SIGNATURES
            if specific_signatures:
                signature_classes = {sig.__name__: sig for sig in ALL_SIGNATURES}
                signatures_to_run = []
                for sig_name in specific_signatures:
                    if sig_name in signature_classes:
                        signatures_to_run.append(signature_classes[sig_name])
                    else:
                        logger.warning("Unknown signature: %s", sig_name)
            
        # Run signatures
        results = []
        for signature_class in signatures_to_run:
            print("signature_class", signature_class.__name__)
            logger.debug("Running signature: %s", signature_class.__name__)
            try:
                signature = signature_class()
                result = signature.analyze(analyzer)
                if result:
                    results.append(result)
            except Exception as e:
                logger.error(
                    "Error running signature %s: %s", signature_class.__name__, e
                )

        return results

    except Exception as e:
        logger.error("Error analyzing cluster %s: %s", cluster_id, e)
        raise


def print_results(results: List[SignatureResult]) -> None:
    """Print analysis results to stdout."""
    if not results:
        print("No issues found in the cluster logs.")
        return

    print("OpenShift Assisted Installer Log Analysis")
    print("=" * 50)
    print()

    for result in results:
        print(result)
