#!/usr/bin/env bash
# Script to create a new release and trigger automatic PyPI publishing
#
# Usage: ./scripts/release.sh [version]
# Example: ./scripts/release.sh 0.2.0

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

if [ -z "$1" ]; then
    echo -e "${RED}Error: Version argument required${NC}"
    echo "Usage: $0 <version> <release message>"
    echo "Example: $0 0.2.0"
    exit 1
fi

VERSION="$1"
TAG="v${VERSION}"
RELEASE_MESSAGE="$2"

echo -e "${GREEN}=== Creating release ${TAG} ===${NC}"

# Check if we're on main/master branch
CURRENT_BRANCH=$(git rev-parse --abbrev-ref HEAD)
if [[ "$CURRENT_BRANCH" != "main" && "$CURRENT_BRANCH" != "master" ]]; then
    echo -e "${YELLOW}Warning: You're on branch '${CURRENT_BRANCH}', not 'main' or 'master'${NC}"
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check for uncommitted changes
if ! git diff-index --quiet HEAD --; then
    echo -e "${RED}Error: You have uncommitted changes${NC}"
    git status --short
    exit 1
fi

# Pull latest changes
echo -e "${GREEN}Pulling latest changes...${NC}"
git pull --rebase

# Run tests
echo -e "${GREEN}Running tests...${NC}"
poetry run pytest || {
    echo -e "${RED}Tests failed! Aborting release.${NC}"
    exit 1
}

# Run ruff checks
echo -e "${GREEN}Running ruff checks...${NC}"
poetry run ruff check . || {
    echo -e "${RED}Ruff checks failed! Aborting release.${NC}"
    exit 1
}

# Verify CHANGELOG has an entry for this version dated today
TODAY=$(date +%F)
EXPECTED_HEADER="## [${VERSION}] - ${TODAY}"
if ! grep -qF "$EXPECTED_HEADER" CHANGELOG.md; then
    echo -e "${RED}Error: CHANGELOG.md is missing the expected header:${NC}"
    echo "  ${EXPECTED_HEADER}"
    echo -e "${RED}Please update CHANGELOG.md before releasing.${NC}"
    exit 1
fi
echo -e "${GREEN}✓ CHANGELOG.md contains '${EXPECTED_HEADER}'${NC}"

# Check if tag already exists
if git rev-parse "$TAG" >/dev/null 2>&1; then
    echo -e "${RED}Error: Tag $TAG already exists${NC}"
    exit 1
fi

# Create and push tag
echo -e "${GREEN}Creating tag ${TAG}...${NC}"
git tag -sa "$TAG" -m "Release $TAG" -m "$RELEASE_MESSAGE"

echo -e "${YELLOW}About to push tag ${TAG} to origin.${NC}"
echo -e "${YELLOW}This will trigger automatic publishing to PyPI!${NC}"
read -p "Continue? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo -e "${YELLOW}Aborting. Removing local tag.${NC}"
    git tag -d "$TAG"
    exit 1
fi

echo -e "${GREEN}Pushing tag to origin...${NC}"
git push origin "$TAG"

echo -e "${GREEN}✓ Release ${TAG} created and pushed!${NC}"
echo -e "${GREEN}✓ GitHub Actions will now run tests and publish to PyPI${NC}"
echo -e "${GREEN}✓ Check progress at: https://github.com/python-caldav/icalendar-search/actions${NC}"
