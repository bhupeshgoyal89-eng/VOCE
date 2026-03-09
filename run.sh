#!/bin/bash
# VOCE Startup Script
# This script sets up the environment and launches the VOCE application

set -e  # Exit on error

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Print header
echo -e "${BLUE}"
echo "╔════════════════════════════════════════════╗"
echo "║  🏢 VOCE - Vendor Obligation Control Engine║"
echo "║          Startup Script v1.0               ║"
echo "╚════════════════════════════════════════════╝"
echo -e "${NC}"

# Check Python installation
echo -e "${YELLOW}Checking Python installation...${NC}"
if ! command -v python3 &> /dev/null; then
    echo -e "${RED}❌ Python 3 not found. Please install Python 3.8 or higher.${NC}"
    exit 1
fi

PYTHON_VERSION=$(python3 --version)
echo -e "${GREEN}✅ Found: $PYTHON_VERSION${NC}"

# Check if virtual environment exists
if [ ! -d "venv" ]; then
    echo -e "${YELLOW}Creating virtual environment...${NC}"
    python3 -m venv venv
    echo -e "${GREEN}✅ Virtual environment created${NC}"
fi

# Activate virtual environment
echo -e "${YELLOW}Activating virtual environment...${NC}"
source venv/bin/activate
echo -e "${GREEN}✅ Virtual environment activated${NC}"

# Install/update dependencies
echo -e "${YELLOW}Installing dependencies from requirements.txt...${NC}"
pip install -q -r requirements.txt
echo -e "${GREEN}✅ Dependencies installed${NC}"

# Check for Gemini API key
echo -e "${YELLOW}Checking Gemini API key...${NC}"
if [ -z "$GEMINI_API_KEY" ]; then
    echo -e "${YELLOW}⚠️  GEMINI_API_KEY environment variable not set${NC}"
    echo -e "${BLUE}To enable AI obligation extraction, set your Gemini API key:${NC}"
    echo -e "${BLUE}  export GEMINI_API_KEY=\"your_api_key_here\"${NC}"
    echo ""
    read -p "Do you want to set it now? (y/n) " -n 1 -r
    echo
    if [[ $REPLY =~ ^[Yy]$ ]]; then
        read -p "Enter your Gemini API key: " API_KEY
        export GEMINI_API_KEY="$API_KEY"
        echo -e "${GREEN}✅ API key set${NC}"
    else
        echo -e "${YELLOW}⚠️  Skipping. The app will work but AI extraction will be disabled.${NC}"
    fi
else
    echo -e "${GREEN}✅ GEMINI_API_KEY is set${NC}"
fi

# Create required directories
echo -e "${YELLOW}Checking required directories...${NC}"
mkdir -p data
mkdir -p agreements
echo -e "${GREEN}✅ Directories ready${NC}"

# Check database
echo -e "${YELLOW}Checking database...${NC}"
if [ ! -f "data/voce.db" ]; then
    echo -e "${BLUE}   Creating new database...${NC}"
fi
echo -e "${GREEN}✅ Database ready${NC}"

# Display startup info
echo ""
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo -e "${GREEN}Ready to launch VOCE!${NC}"
echo -e "${BLUE}════════════════════════════════════════════${NC}"
echo ""
echo -e "${YELLOW}📝 Quick Tips:${NC}"
echo "   1. Vendor Master: Upload your vendor CSV"
echo "   2. Agreement Upload: Upload vendor agreements"
echo "   3. Obligation Register: View extracted obligations"
echo "   4. HoD Certification: Validate obligations"
echo "   5. FP&A Dashboard: Monitor metrics"
echo ""
echo -e "${YELLOW}📚 Documentation:${NC}"
echo "   • README.md - Full feature guide"
echo "   • QUICKSTART.md - 5-minute setup"
echo "   • DEPLOYMENT.md - Production deployment"
echo "   • TESTING.md - Testing procedures"
echo ""

# Launch the app
echo -e "${GREEN}🚀 Launching VOCE...${NC}"
echo -e "${BLUE}Access the app at: http://localhost:8501${NC}"
echo ""
echo -e "${YELLOW}Press Ctrl+C to stop the server${NC}"
echo ""

# Run Streamlit
streamlit run app.py
