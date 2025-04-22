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

def parse_bid_data(data: str) -> tuple[List[BidItem], Optional[BidItem]]:
    """
    Parse the raw bid data into a structured format.
    Returns a tuple of (regular_bid_items, current_employee_bid)
    """
    bid_items = []
    current_employee_bid = None
    lines = data.strip().split('\n')
    
    # First, look for a current employee entry at the top
    # Format: Employee Name: [name], ID: [id], Preferences: [pref1, pref2, ...]
    for i, line in enumerate(lines):
        line = line.strip()
        if not line:
            continue
            
        # Check if this line contains current employee information
        if ("employee" in line.lower() or "name" in line.lower()) and "id" in line.lower() and "preferences" in line.lower():
            try:
                # Extract employee details using various possible formats
                employee_parts = line.split(',')
                
                # Extract employee ID
                employee_id = None
                for part in employee_parts:
                    if "id" in part.lower():
                        # Find the ID after the colon or similar delimiter
                        id_part = part.split(':')[-1].strip()
                        # Clean up any extra text and get just the ID
                        employee_id = ''.join(c for c in id_part.split()[0] if c.isalnum())
                
                # Extract preferences
                preferences = []
                for part in employee_parts:
                    if "preferences" in part.lower():
                        pref_part = part.split(':')[-1].strip()
                        # Extract numbers from the preferences part
                        preferences = [int(p) for p in pref_part.split() if p.isdigit()]
                
                if employee_id and preferences:
                    # Use a very high bid position to ensure this employee is processed last
                    current_employee_bid = BidItem(
                        bid_position=999999,  # Very high number to ensure lowest seniority
                        employee_id=employee_id,
                        preferences=preferences
                    )
                    logger.info(f"Found current employee: ID={employee_id}, Preferences={preferences}")
                    # Remove this line from further processing
                    lines.pop(i)
                    break
            except Exception as e:
                logger.warning(f"Error parsing current employee data: {e}")
    
    # Now parse the regular bid data
    for line_num, line in enumerate(lines, 1):
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
            
    return bid_items, current_employee_bid

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
        bid_items, current_employee_bid = parse_bid_data(bid_data)
        
        if not bid_items and not current_employee_bid:
            return jsonify({"error": "No valid bid data found"}), 400
            
        # If there's a current employee, add them to the bid items list
        all_bids = bid_items.copy()
        if current_employee_bid:
            all_bids.append(current_employee_bid)
            
        # Assign lines based on seniority and preferences
        results = assign_lines(all_bids)
        
        # Mark the current employee's result in a special way
        if current_employee_bid:
            for result in results:
                if result.employee_id == current_employee_bid.employee_id:
                    result.message = (result.message or "") + " (Current Employee)"
        
        return jsonify({
            "results": [result.to_dict() for result in results],
            "has_current_employee": current_employee_bid is not None
        })
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
