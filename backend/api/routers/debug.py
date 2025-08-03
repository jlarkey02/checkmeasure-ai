from fastapi import APIRouter, Query, HTTPException
from typing import Optional, List
from datetime import datetime, timedelta
from utils.enhanced_logger import enhanced_logger
from utils.error_logger import error_logger as legacy_error_logger
import json

router = APIRouter()

@router.get("/dashboard")
async def get_debug_dashboard(
    log_type: Optional[str] = Query(None, description="Filter by log type: request, response, error, claude_vision, processing_step"),
    limit: int = Query(100, description="Number of recent logs to return"),
    include_legacy: bool = Query(True, description="Include legacy error logs")
):
    """Get comprehensive debug dashboard data"""
    try:
        # Get recent logs from enhanced logger
        recent_logs = enhanced_logger.get_recent_logs(log_type=log_type, limit=limit)
        
        # Get error summary
        error_summary = enhanced_logger.get_error_summary()
        
        # Get legacy error logs if requested
        legacy_errors = []
        if include_legacy:
            legacy_errors = legacy_error_logger.get_recent_errors(20)
        
        # Get log file sizes
        log_files_info = {}
        for log_file in enhanced_logger.log_dir.glob("*.log"):
            log_files_info[log_file.name] = {
                "size_mb": log_file.stat().st_size / (1024 * 1024),
                "modified": datetime.fromtimestamp(log_file.stat().st_mtime).isoformat()
            }
        
        return {
            "dashboard": {
                "recent_logs": recent_logs,
                "error_summary": error_summary,
                "legacy_errors": legacy_errors,
                "log_files": log_files_info,
                "filters_applied": {
                    "log_type": log_type,
                    "limit": limit,
                    "include_legacy": include_legacy
                }
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to generate debug dashboard: {str(e)}")

@router.get("/logs/export")
async def export_logs(
    format: str = Query("json", description="Export format: json or csv"),
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    log_types: Optional[str] = Query(None, description="Comma-separated log types")
):
    """Export logs for analysis"""
    try:
        # Parse dates
        start_dt = datetime.fromisoformat(start_date) if start_date else None
        end_dt = datetime.fromisoformat(end_date) if end_date else None
        
        # Parse log types
        types_list = log_types.split(",") if log_types else None
        
        # Get logs
        logs = enhanced_logger.export_logs(
            start_date=start_dt,
            end_date=end_dt,
            log_types=types_list
        )
        
        if format == "json":
            return {
                "export_date": datetime.now().isoformat(),
                "filters": {
                    "start_date": start_date,
                    "end_date": end_date,
                    "log_types": types_list
                },
                "total_logs": len(logs),
                "logs": logs
            }
        elif format == "csv":
            # Convert to CSV format
            import csv
            import io
            
            output = io.StringIO()
            if logs:
                writer = csv.DictWriter(output, fieldnames=logs[0].keys())
                writer.writeheader()
                writer.writerows(logs)
            
            return {
                "csv_data": output.getvalue(),
                "total_rows": len(logs) + 1  # Include header
            }
        else:
            raise HTTPException(status_code=400, detail="Invalid format. Use 'json' or 'csv'")
            
    except ValueError as e:
        raise HTTPException(status_code=400, detail=f"Invalid date format: {str(e)}")
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to export logs: {str(e)}")

@router.get("/logs/search")
async def search_logs(
    query: str = Query(..., description="Search query"),
    log_type: Optional[str] = Query(None, description="Filter by log type"),
    limit: int = Query(50, description="Maximum results")
):
    """Search through logs"""
    try:
        # Get all recent logs
        logs = enhanced_logger.get_recent_logs(log_type=log_type, limit=1000)
        
        # Search through logs
        results = []
        query_lower = query.lower()
        
        for log in logs:
            # Convert log to string for searching
            log_str = json.dumps(log).lower()
            if query_lower in log_str:
                results.append(log)
                if len(results) >= limit:
                    break
        
        return {
            "query": query,
            "results_count": len(results),
            "results": results
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")

@router.get("/logs/claude-vision-stats")
async def get_claude_vision_stats():
    """Get Claude Vision API usage statistics"""
    try:
        # Get all Claude Vision logs
        claude_logs = enhanced_logger.get_recent_logs(log_type="claude_vision", limit=1000)
        
        if not claude_logs:
            return {
                "total_calls": 0,
                "total_cost_usd": 0,
                "average_processing_time_ms": 0,
                "calls_by_action": {}
            }
        
        # Calculate statistics
        total_cost = sum(log.get("cost_usd", 0) or 0 for log in claude_logs)
        processing_times = [log.get("processing_time_ms", 0) for log in claude_logs if log.get("processing_time_ms")]
        avg_processing_time = sum(processing_times) / len(processing_times) if processing_times else 0
        
        # Group by action
        calls_by_action = {}
        for log in claude_logs:
            action = log.get("action", "unknown")
            if action not in calls_by_action:
                calls_by_action[action] = {
                    "count": 0,
                    "total_cost": 0,
                    "avg_time_ms": 0
                }
            calls_by_action[action]["count"] += 1
            calls_by_action[action]["total_cost"] += log.get("cost_usd", 0) or 0
        
        return {
            "total_calls": len(claude_logs),
            "total_cost_usd": round(total_cost, 4),
            "average_processing_time_ms": round(avg_processing_time, 2),
            "calls_by_action": calls_by_action,
            "recent_calls": claude_logs[-10:]  # Last 10 calls
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get Claude Vision stats: {str(e)}")

@router.post("/logs/clear-old")
async def clear_old_logs(days_to_keep: int = Query(7, description="Number of days of logs to keep")):
    """Clear old log files"""
    try:
        enhanced_logger.clear_old_logs(days_to_keep=days_to_keep)
        return {
            "status": "success",
            "message": f"Cleared log files older than {days_to_keep} days"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to clear old logs: {str(e)}")

@router.get("/test")
async def test_debug_endpoint():
    """Test endpoint for debug module"""
    return {
        "message": "Debug module is ready",
        "endpoints": [
            "/api/debug/dashboard",
            "/api/debug/logs/export",
            "/api/debug/logs/search",
            "/api/debug/logs/claude-vision-stats",
            "/api/debug/logs/clear-old"
        ]
    }