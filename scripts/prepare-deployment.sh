#!/bin/bash
# Prepare for deployment - Run all checks and commit code

set -e

echo "🔍 FrankenAgent Lab - Pre-Deployment Checks"
echo "============================================"

# Colors
GREEN='\033[0;32m'
BLUE='\033[0;34m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Check if we're in the right directory
if [ ! -f "pyproject.toml" ]; then
    echo -e "${RED}Error: Must run from project root${NC}"
    exit 1
fi

# Step 1: Check git status
echo -e "\n${BLUE}Step 1: Checking git status...${NC}"
if [[ -n $(git status -s) ]]; then
    echo -e "${YELLOW}Uncommitted changes found${NC}"
    git status -s
else
    echo -e "${GREEN}✓ Working directory clean${NC}"
fi

# Step 2: Run tests
echo -e "\n${BLUE}Step 2: Running tests...${NC}"
if command -v poetry &> /dev/null; then
    poetry run pytest tests/ -v || {
        echo -e "${RED}✗ Tests failed!${NC}"
        exit 1
    }
    echo -e "${GREEN}✓ All tests passed${NC}"
else
    echo -e "${YELLOW}⚠ Poetry not found, skipping tests${NC}"
fi

# Step 3: Check database migrations
echo -e "\n${BLUE}Step 3: Checking database migrations...${NC}"
poetry run alembic current
echo -e "${GREEN}✓ Migration status checked${NC}"

# Step 4: Lint check (optional)
echo -e "\n${BLUE}Step 4: Running linters...${NC}"
if command -v poetry &> /dev/null; then
    poetry run ruff check frankenagent/ || echo -e "${YELLOW}⚠ Linting warnings found${NC}"
    echo -e "${GREEN}✓ Linting complete${NC}"
fi

# Step 5: Check environment files
echo -e "\n${BLUE}Step 5: Checking environment files...${NC}"
if [ -f ".env.example" ]; then
    echo -e "${GREEN}✓ .env.example exists${NC}"
else
    echo -e "${RED}✗ .env.example missing${NC}"
fi

# Step 6: Check documentation
echo -e "\n${BLUE}Step 6: Checking documentation...${NC}"
required_docs=("README.md" "DEPLOYMENT_GUIDE.md" "QUICK_START.md" "CREDITS_SYSTEM.md" "RELEASE_NOTES.md")
for doc in "${required_docs[@]}"; do
    if [ -f "$doc" ]; then
        echo -e "${GREEN}✓ $doc exists${NC}"
    else
        echo -e "${RED}✗ $doc missing${NC}"
    fi
done

# Step 7: Check deployment scripts
echo -e "\n${BLUE}Step 7: Checking deployment scripts...${NC}"
if [ -f "scripts/deploy-backend.sh" ] && [ -f "scripts/deploy-frontend.sh" ]; then
    echo -e "${GREEN}✓ Deployment scripts exist${NC}"
    chmod +x scripts/*.sh
    echo -e "${GREEN}✓ Made scripts executable${NC}"
else
    echo -e "${RED}✗ Deployment scripts missing${NC}"
fi

# Step 8: Summary
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Pre-deployment checks complete!${NC}"
echo -e "${BLUE}========================================${NC}"

# Step 9: Git commit
echo -e "\n${BLUE}Step 9: Git commit${NC}"
read -p "Commit message (or press Enter for default): " commit_msg
if [ -z "$commit_msg" ]; then
    commit_msg="Release v1.0.0 - Production ready with credit system"
fi

echo -e "\n${BLUE}Staging all changes...${NC}"
git add .

echo -e "${BLUE}Committing with message: ${commit_msg}${NC}"
git commit -m "$commit_msg" || echo -e "${YELLOW}No changes to commit${NC}"

echo -e "\n${BLUE}Current branch:${NC}"
git branch --show-current

read -p "Push to remote? (y/n): " push_confirm
if [ "$push_confirm" = "y" ]; then
    echo -e "${BLUE}Pushing to remote...${NC}"
    git push origin $(git branch --show-current)
    echo -e "${GREEN}✓ Code pushed to remote${NC}"
fi

# Step 10: Next steps
echo -e "\n${BLUE}========================================${NC}"
echo -e "${GREEN}✓ Ready for deployment!${NC}"
echo -e "${BLUE}========================================${NC}"
echo ""
echo "Next steps:"
echo "  1. Run database migrations on production:"
echo "     alembic upgrade head"
echo ""
echo "  2. Deploy backend:"
echo "     ./scripts/deploy-backend.sh"
echo ""
echo "  3. Deploy frontend:"
echo "     ./scripts/deploy-frontend.sh"
echo ""
echo "  4. Or deploy both:"
echo "     ./scripts/deploy-production.sh"
echo ""
echo "  5. Verify deployment:"
echo "     ./scripts/validate-deployment.sh"
echo ""
echo "Documentation:"
echo "  - Quick Start: QUICK_START.md"
echo "  - Deployment: DEPLOYMENT_GUIDE.md"
echo "  - Credits: CREDITS_SYSTEM.md"
echo "  - Release Notes: RELEASE_NOTES.md"
echo ""
