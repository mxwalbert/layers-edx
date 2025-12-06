#!/usr/bin/env bash
# Setup script for EPQ Java library (Linux/MacOS)
# This script clones and compiles the EPQ library for cross-validation testing

set -e

SKIP_CLONE=false

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        --skip-clone)
            SKIP_CLONE=true
            shift
            ;;
        *)
            echo "Unknown option: $1"
            echo "Usage: $0 [--skip-clone]"
            exit 1
            ;;
    esac
done

# Color codes
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
CYAN='\033[0;36m'
NC='\033[0m' # No Color

echo -e "${CYAN}Setting up EPQ library for cross-validation testing...${NC}"

# Check for Java
echo -e "\n${YELLOW}Checking Java version...${NC}"
if ! command -v java &> /dev/null; then
    echo -e "${RED}ERROR: Java not found. Please install Java 21 or higher.${NC}"
    echo -e "${YELLOW}Download from: https://adoptium.net/${NC}"
    exit 1
fi

JAVA_VERSION=$(java -version 2>&1 | head -n 1)
echo -e "${GREEN}Found: $JAVA_VERSION${NC}"

# Check if Java 21+
if [[ $JAVA_VERSION =~ version.*\"([0-9]+) ]]; then
    MAJOR_VERSION="${BASH_REMATCH[1]}"
    if [ "$MAJOR_VERSION" -lt 21 ]; then
        echo -e "${YELLOW}Warning: Java $MAJOR_VERSION detected. EPQ requires Java 21 or higher.${NC}"
    fi
else
    echo -e "${YELLOW}Warning: Could not parse Java version. EPQ requires Java 21+${NC}"
fi

# Check for Maven
echo -e "\n${YELLOW}Checking Maven...${NC}"
if ! command -v mvn &> /dev/null; then
    echo -e "${RED}ERROR: Maven not found. Please install Maven.${NC}"
    echo -e "${YELLOW}Download from: https://maven.apache.org/download.cgi${NC}"
    exit 1
fi

MVN_VERSION=$(mvn -version 2>&1 | head -n 1)
echo -e "${GREEN}Found: $MVN_VERSION${NC}"

# Create directory structure
EPQ_DIR=".venv/share/java"
EPQ_PATH="$EPQ_DIR/EPQ"

if [ ! -d "$EPQ_DIR" ]; then
    echo -e "\n${YELLOW}Creating directory: $EPQ_DIR${NC}"
    mkdir -p "$EPQ_DIR"
fi

# Clone EPQ repository
if [ "$SKIP_CLONE" = false ]; then
    if [ -d "$EPQ_PATH" ]; then
        echo -e "\n${YELLOW}EPQ directory already exists at $EPQ_PATH${NC}"
        read -p "Do you want to remove and re-clone? (y/N): " overwrite
        if [[ $overwrite =~ ^[Yy]$ ]]; then
            echo -e "${YELLOW}Removing existing EPQ directory...${NC}"
            rm -rf "$EPQ_PATH"
        else
            echo -e "${YELLOW}Skipping clone step.${NC}"
            SKIP_CLONE=true
        fi
    fi
    
    if [ "$SKIP_CLONE" = false ]; then
        echo -e "\n${YELLOW}Cloning EPQ repository...${NC}"
        pushd "$EPQ_DIR" > /dev/null
        if git clone https://github.com/usnistgov/EPQ.git; then
            echo -e "${GREEN}EPQ cloned successfully!${NC}"
        else
            echo -e "${RED}ERROR: Failed to clone EPQ repository.${NC}"
            popd > /dev/null
            exit 1
        fi
        popd > /dev/null
    fi
fi

# Compile EPQ
echo -e "\n${YELLOW}Compiling EPQ library...${NC}"
pushd "$EPQ_PATH" > /dev/null
if mvn compile; then
    echo -e "${GREEN}EPQ compiled successfully!${NC}"
else
    echo -e "${RED}ERROR: Failed to compile EPQ.${NC}"
    popd > /dev/null
    exit 1
fi

# Copy dependencies
echo -e "\n${YELLOW}Copying Maven dependencies...${NC}"
if mvn dependency:copy-dependencies -DoutputDirectory=target/dependency; then
    echo -e "${GREEN}Dependencies copied successfully!${NC}"
else
    echo -e "${RED}ERROR: Failed to copy dependencies.${NC}"
    popd > /dev/null
    exit 1
fi

popd > /dev/null

# Verify setup
echo -e "\n${YELLOW}Verifying EPQ setup...${NC}"
ELEMENT_CLASS="$EPQ_PATH/target/classes/gov/nist/microanalysis/EPQLibrary/Element.class"
JAMA_JAR="$EPQ_PATH/target/dependency/jama-1.0.3.jar"

VERIFIED=true
if [ ! -f "$ELEMENT_CLASS" ]; then
    echo -e "${RED}ERROR: EPQ classes not found at $ELEMENT_CLASS${NC}"
    VERIFIED=false
fi

if [ ! -f "$JAMA_JAR" ]; then
    echo -e "${RED}ERROR: Jama dependency not found at $JAMA_JAR${NC}"
    VERIFIED=false
fi

if [ "$VERIFIED" = true ]; then
    echo -e "\n${GREEN}✓ EPQ setup complete and verified!${NC}"
    echo -e "\n${CYAN}EPQ Location: $EPQ_PATH${NC}"
    echo -e "${CYAN}Compiled Classes: $EPQ_PATH/target/classes${NC}"
    echo -e "${CYAN}Dependencies: $EPQ_PATH/target/dependency${NC}"
else
    echo -e "\n${RED}✗ EPQ setup incomplete. Please review errors above.${NC}"
    exit 1
fi
