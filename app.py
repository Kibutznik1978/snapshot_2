import os
import csv
import io
from typing import List, Dict, Optional
from flask import Flask, request, render_template, jsonify, make_response, redirect, url_for
from dataclasses import dataclass
import logging

# Configure logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

# Initialize Flask app
app = Flask(__name__)
app.secret_key = os.environ.get("SESSION_SECRET", "dev-secret-key")

@dataclass
class BidItem:
    bid_position: int
    employee_id: str
    preferences: List[int]

@dataclass
class BidResult:
    bid_position: int
    employee_id: str
    awarded_line: Optional[int] = None
    message: Optional[str] = None
    
    def to_dict(self):
        return {
            "bid_position": self.bid_position,
            "employee_id": self.employee_id,
            "awarded_line": self.awarded_line,
            "message": self.message
        }

def parse_bid_data(data: str) -> List[BidItem]:
    """Parse the raw bid data into a structured format."""
    bid_items = []
    
    for line_num, line in enumerate(data.strip().split('\n'), 1):
        line = line.strip()
        if not line:  # Skip empty lines
            continue
            
        parts = line.split()
        if len(parts) < 3:
            logger.warning(f"Line {line_num} has insufficient data: {line}")
            continue
            
        try:
            bid_position = int(parts[0])
            employee_id = parts[1]
            preferences = [int(p) for p in parts[2:]]
            
            bid_items.append(BidItem(
                bid_position=bid_position,
                employee_id=employee_id,
                preferences=preferences
            ))
        except ValueError as e:
            logger.warning(f"Error parsing line {line_num}: {e}")
            continue
            
    return bid_items

def assign_lines(bid_items: List[BidItem]) -> List[BidResult]:
    """Assign lines based on seniority and preferences."""
    # Sort by bid position (lowest number = highest seniority)
    sorted_bids = sorted(bid_items, key=lambda x: x.bid_position)
    
    # Track assigned lines
    assigned_lines = set()
    results = []
    
    for bid in sorted_bids:
        result = BidResult(
            bid_position=bid.bid_position,
            employee_id=bid.employee_id
        )
        
        # Try to assign a line from preferences
        assigned = False
        for preference in bid.preferences:
            if preference not in assigned_lines:
                assigned_lines.add(preference)
                result.awarded_line = preference
                assigned = True
                break
                
        if not assigned:
            result.message = "No preferred lines available"
            
        results.append(result)
        
    return results

@app.route("/", methods=["GET"])
def get_home():
    """Render the home page."""
    return render_template("index.html")

@app.route("/process-bids", methods=["POST"])
def process_bids():
    """Process the submitted bid data."""
    try:
        # Parse the bid data
        bid_data = request.form.get("bid_data", "")
        bid_items = parse_bid_data(bid_data)
        
        if not bid_items:
            return jsonify({"error": "No valid bid data found"}), 400
            
        # Assign lines based on seniority and preferences
        results = assign_lines(bid_items)
        
        return jsonify({"results": [result.to_dict() for result in results]})
    except Exception as e:
        logger.error(f"Error processing bids: {e}")
        return jsonify({"error": str(e)}), 500

@app.route("/download-csv", methods=["POST"])
def download_csv():
    """Download results as CSV."""
    try:
        import json
        results_data = request.form.get("results_data", "")
        results = json.loads(results_data)
        
        # Create a CSV in memory
        output = io.StringIO()
        writer = csv.writer(output)
        
        # Write header
        writer.writerow(["Bid Position", "Employee ID", "Awarded Line", "Message"])
        
        # Write data
        for result in results:
            writer.writerow([
                result.get("bid_position", ""),
                result.get("employee_id", ""),
                result.get("awarded_line", ""),
                result.get("message", "")
            ])
            
        # Create response with CSV file
        output.seek(0)
        response = make_response(output.getvalue())
        response.headers["Content-Disposition"] = "attachment; filename=bid_results.csv"
        response.headers["Content-type"] = "text/csv"
        return response
    except Exception as e:
        logger.error(f"Error generating CSV: {e}")
        return jsonify({"error": str(e)}), 500
