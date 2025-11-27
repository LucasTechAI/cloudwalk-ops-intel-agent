#!/bin/bash

# format_black.sh - Script to format Python code using Black.
echo "Formatting Python code with Black..."
echo "=========================================="

# Format all Python files in the project
black src/ test/ setup/ 

echo ""
echo "Formatting complete!"