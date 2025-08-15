#!/bin/bash

# EPL Data Processing Pipeline
# This script runs the data preparation Python files in sequence

set -e  # Exit on any error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}[INFO]${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

print_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Function to run a Python script
run_script() {
    local script_name=$1
    local script_number=$2
    
    print_status "Starting $script_name (Step $script_number/3)"
    
    if python3 "$script_name"; then
        print_status "Successfully completed $script_name"
    else
        print_error "Failed to run $script_name"
        exit 1
    fi
    
    echo ""
}

# Main execution
main() {
    print_status "Starting EPL Data Processing Pipeline"
    print_status "Current directory: $(pwd)"
    echo ""
    
    # Check if Python 3 is available
    if ! command -v python3 &> /dev/null; then
        print_error "Python 3 is not installed or not in PATH"
        exit 1
    fi
    
    # Check if all required files exist
    local required_files=("1_matches.py" "2_attendance.py" "3_discipline.py")
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$file" ]]; then
            print_error "Required file $file not found"
            exit 1
        fi
    done
    
    print_status "All required files found"
    echo ""
    
    # Run scripts in order
    run_script "1_matches.py" 1
    run_script "2_attendance.py" 2
    run_script "3_discipline.py" 3
    
    print_status "All data processing steps completed successfully!"
    print_status "Pipeline finished at $(date)"
}

# Run main function
main "$@"
