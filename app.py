import os
import csv
import io
import re
from typing import List, Dict, Optional, Tuple
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
    employee_name: Optional[str] = None

@dataclass
class BidResult:
    bid_position: int
    employee_id: str
    awarded_line: Optional[int] = None
    message: Optional[str] = None
    employee_name: Optional[str] = None
    
    def to_dict(self):
        return {
            "bid_position": self.bid_position,
            "employee_id": self.employee_id,
            "employee_name": self.employee_name,
            "awarded_line": self.awarded_line,
            "message": self.message
        }

def extract_current_employee(data: str) -> Tuple[Optional[dict], str]:
    """
    Extract the current employee information from the top of the input and 
    return the rest of the data for table parsing.
    
    Returns a tuple: (current_employee_data, remaining_text)
    """
    lines = data.strip().split('\n')
    
    # Check if the first line contains a name and seniority
    if not lines:
        return None, data
    
    # Look for a pattern like "NAME SEN: NUMBER" in the first line
    first_line = lines[0].strip()
    sen_match = re.search(r'Sen:\s*(\d+)', first_line, re.IGNORECASE)
    
    if not sen_match:
        # If no seniority info is found, assume it's just regular bid data
        return None, data
    
    # Extract seniority number
    seniority = int(sen_match.group(1))
    
    # Extract name (everything before "Sen:")
    name_part = first_line[:sen_match.start()].strip()
    
    # Generate an employee ID (could be based on name or just "EMP" + seniority)
    employee_id = f"EMP{seniority}"
    
    # Next line should contain the preferences
    if len(lines) > 1:
        prefs_line = lines[1].strip()
        try:
            preferences = [int(p) for p in prefs_line.split()]
        except ValueError:
            # If we can't parse the preferences, skip this employee
            logger.warning(f"Could not parse preferences for current employee: {prefs_line}")
            return None, data
        
        # Create a dictionary with the current employee's information
        current_employee = {
            "name": name_part,
            "seniority": seniority,
            "employee_id": employee_id,
            "preferences": preferences
        }
        
        # Return current employee data and the rest of the text starting from line 3
        # (or line 2 if there are only 2 lines)
        remaining_text = '\n'.join(lines[2:] if len(lines) > 2 else "")
        return current_employee, remaining_text
    
    return None, data  # Default fallback
    
def parse_bid_data(data: str) -> List[BidItem]:
    """Parse the raw bid data into a structured format."""
    # First, check for current employee information at the top
    current_employee, table_data = extract_current_employee(data)
    
    bid_items = []
    
    # Process the bid table
    lines = table_data.strip().split('\n')
    
    # Skip header line if it exists (Sen ID Bids)
    start_idx = 0
    if lines and not lines[0].strip().isdigit() and any(keyword in lines[0].lower() for keyword in ['sen', 'id', 'bid']):
        start_idx = 1
    
    # Process each line in the table
    for line_num, line in enumerate(lines[start_idx:], start_idx + 1):
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
    
    # Add the current employee as the last item if present
    if current_employee:
        bid_items.append(BidItem(
            # Use the actual seniority from the employee data
            bid_position=current_employee["seniority"],
            employee_id=current_employee["employee_id"],
            preferences=current_employee["preferences"],
            employee_name=current_employee["name"]
        ))
            
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
            employee_id=bid.employee_id,
            employee_name=bid.employee_name
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
        writer.writerow(["Bid Position", "Employee ID", "Employee Name", "Awarded Line", "Message"])
        
        # Write data
        for result in results:
            writer.writerow([
                result.get("bid_position", ""),
                result.get("employee_id", ""),
                result.get("employee_name", ""),
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
