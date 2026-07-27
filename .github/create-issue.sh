#!/bin/bash
# Quick issue creation script
# Usage: ./create-issue.sh "title" "description" "label"
# Labels: critical, high, medium, low, bug, enhancement

if [ $# -lt 2 ]; then
  echo "Usage: ./create-issue.sh \"Title\" \"Description\" \"label\""
  echo "Labels: critical, high, medium, low, bug, enhancement"
  exit 1
fi

TITLE="$1"
BODY="$2"
LABEL="${3:-high}"

echo "Creating issue: $TITLE (label: $LABEL)"
gh issue create --title "$TITLE" --body "$BODY" --label "$LABEL"
