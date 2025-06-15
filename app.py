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
    bid_position: int  # This represents the seniority number
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
    Extract the current employee information and return the rest of the data for table parsing.
    In the new format, the current employee is the last entry.
    
    Returns a tuple: (current_employee_data, remaining_text)
    """
    lines = data.strip().split('\n')
    
    if not lines:
        return None, data
    
    # Check for old format first: "NAME SEN: NUMBER"
    first_line = lines[0].strip()
    sen_match = re.search(r'Sen:\s*(\d+)', first_line, re.IGNORECASE)
    
    if sen_match:
        # Old format processing
        seniority = int(sen_match.group(1))
        name_part = first_line[:sen_match.start()].strip()
        employee_id = ""
        
        if len(lines) > 1:
            prefs_line = lines[1].strip()
            try:
                preferences = [int(p) for p in prefs_line.split()]
            except ValueError:
                logger.warning(f"Could not parse preferences for current employee: {prefs_line}")
                return None, data
            
            current_employee = {
                "name": name_part,
                "seniority": seniority,
                "employee_id": employee_id,
                "preferences": preferences
            }
            
            remaining_text = '\n'.join(lines[2:] if len(lines) > 2 else "")
            return current_employee, remaining_text
    
    # New format: current employee is at the bottom, find the last valid employee entry
    # Look for lines that match the pattern: NAME ID# SEN BASE EQP STA BID_NUMBERS
    employee_lines = []
    current_employee_data = None
    
    for i, line in enumerate(lines):
        line = line.strip()
        if not line or "ONLY PILOTS" in line or "NAME" in line and "ID#" in line:
            continue
            
        # Check if this line starts a new employee entry (either no indentation or specific pattern)
        if not line.startswith("      ") and re.match(r'^[A-Z]', line):
            # This could be an employee line
            match = re.match(r'^([A-Z\s,]+?)\s+(\d{7})\s+(\d+)\s+([A-Z]{3})\s+(\d{3})\s+([A-Z]{3})\s+([\d\s]+)', line)
            if match:
                name = match.group(1).strip()
                employee_id = match.group(2)
                seniority = int(match.group(3))
                bid_numbers_str = match.group(7)
                
                # Collect all bid numbers for this employee (including continuation lines)
                all_bid_numbers = bid_numbers_str
                j = i + 1
                while j < len(lines) and lines[j].strip().startswith("      ") and not re.match(r'^[A-Z]', lines[j].strip()):
                    continuation_line = lines[j].strip()
                    # Extract numbers from continuation line
                    numbers_only = re.findall(r'\d+', continuation_line)
                    if numbers_only:
                        all_bid_numbers += " " + " ".join(numbers_only)
                    j += 1
                
                try:
                    preferences = [int(p) for p in all_bid_numbers.split() if p.isdigit()]
                    current_employee_data = {
                        "name": name,
                        "seniority": seniority,
                        "employee_id": employee_id,
                        "preferences": preferences
                    }
                except ValueError:
                    continue
    
    if current_employee_data:
        # Return the current employee (last one found) and all the data for processing
        return current_employee_data, data
    
    return None, data
    
def parse_bid_data(data: str) -> List[BidItem]:
    """Parse the raw bid data into a structured format."""
    lines = data.strip().split('\n')
    bid_items = []
    
    # Check if this is the old table format (header with "Seniority" or "Senority")
    first_line = lines[0].strip() if lines else ""
    is_old_table_format = ("seniority" in first_line.lower() or "senority" in first_line.lower()) and ("crew" in first_line.lower() or "id" in first_line.lower())
    
    logger.info(f"First line: '{first_line}'")
    logger.info(f"Is old table format: {is_old_table_format}")
    logger.info(f"Total lines: {len(lines)}")
    
    if is_old_table_format:
        # Handle old table format (Seniority, Crew Id, Bids)
        # Skip the header line
        for line_num, line in enumerate(lines[1:], 2):
            line = line.strip()
            if not line:  # Skip empty lines
                continue
                
            parts = line.split('\t') if '\t' in line else line.split()
            if len(parts) < 3:
                logger.warning(f"Line {line_num} has insufficient data: {line}")
                continue
                
            try:
                seniority = int(parts[0])
                employee_id = parts[1]
                
                # Parse bid numbers from remaining parts
                bid_text = ' '.join(parts[2:])
                preferences = [int(p) for p in bid_text.split() if p.isdigit()]
                
                bid_items.append(BidItem(
                    bid_position=seniority,
                    employee_id=employee_id,
                    preferences=preferences
                ))
            except ValueError as e:
                logger.warning(f"Error parsing line {line_num}: {e}")
                continue
    

    
    else:
        # Handle new format - parse all employees from the structured data
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Skip empty lines and header lines
            if not line or "ONLY PILOTS" in line or ("NAME" in line and "ID#" in line and "SEN" in line):
                i += 1
                continue
            
            # Check if this line is an employee entry
            # Pattern: NAME ID# SEN BASE EQP STA BID_NUMBERS
            if not line.startswith("      ") and re.match(r'^[A-Z]', line):
                match = re.match(r'^([A-Z\s,]+?)\s+(\d{7})\s+(\d+)\s+([A-Z]{3})\s+(\d{3})\s+([A-Z]{3})\s+([\d\s]+)', line)
                if match:
                    name = match.group(1).strip()
                    employee_id = match.group(2)
                    seniority = int(match.group(3))
                    bid_numbers_str = match.group(7)
                    
                    # Collect all bid numbers for this employee (including continuation lines)
                    all_bid_numbers = bid_numbers_str
                    j = i + 1
                    
                    # Look for continuation lines (indented lines with numbers)
                    while j < len(lines):
                        next_line = lines[j].strip()
                        if next_line.startswith("      ") and not re.match(r'^[A-Z]', next_line):
                            # This is a continuation line with more bid numbers
                            numbers_only = re.findall(r'\d+', next_line)
                            if numbers_only:
                                all_bid_numbers += " " + " ".join(numbers_only)
                            j += 1
                        else:
                            break
                    
                    try:
                        preferences = [int(p) for p in all_bid_numbers.split() if p.isdigit()]
                        bid_items.append(BidItem(
                            bid_position=seniority,
                            employee_id=employee_id,
                            preferences=preferences,
                            employee_name=name
                        ))
                    except ValueError as e:
                        logger.warning(f"Error parsing employee {name}: {e}")
                    
                    # Move to the next line after this employee's data
                    i = j
                else:
                    i += 1
            else:
                i += 1
    
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
        
        if not bid_data.strip():
            return jsonify({"error": "Please enter bid data to process"}), 400
            
        bid_items = parse_bid_data(bid_data)
        
        if not bid_items:
            return jsonify({
                "error": "Could not process the bid data. Please check your input format against the example provided. " +
                         "Make sure your data starts with your name and seniority number, followed by your bid preferences."
            }), 400
            
        # Assign lines based on seniority and preferences
        results = assign_lines(bid_items)
        
        return jsonify({"results": [result.to_dict() for result in results]})
    except Exception as e:
        logger.error(f"Error processing bids: {e}")
        error_message = str(e)
        user_message = "An error occurred while processing your bid data. "
        
        if "invalid literal for int()" in error_message:
            user_message += "There appears to be non-numeric data where numbers are expected. " + \
                           "Please check that the seniority numbers and bid preferences are all valid numbers."
        else:
            user_message += "Please make sure your data is in the correct format as shown in the example."
            
        return jsonify({"error": user_message}), 500

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
        writer.writerow(["Seniority #", "Employee ID", "Employee Name", "Awarded Line", "Message"])
        
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
