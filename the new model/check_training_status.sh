#!/bin/bash
# Quick script to check training status

LOG_FILE="/Users/jsmat/gaTech/AI@GT/the new model/training.log"
SCRIPT_NAME="train_model_english_focused_v2.py"

echo "=" | head -c 80 && echo ""
echo "📊 TRAINING STATUS CHECK"
echo "=" | head -c 80 && echo ""
echo ""

# Check if process is running
if ps aux | grep -v grep | grep -q "$SCRIPT_NAME"; then
    echo "✅ Training is RUNNING"
    echo ""
    ps aux | grep -v grep | grep "$SCRIPT_NAME" | awk '{print "  Process ID: " $2 "\n  CPU Usage: " $3 "%\n  Memory: " $4 "%"}'
else
    echo "❌ Training is NOT running (may have completed or crashed)"
fi

echo ""
echo "=" | head -c 80 && echo ""
echo "📝 LATEST LOG OUTPUT (last 30 lines)"
echo "=" | head -c 80 && echo ""

if [ -f "$LOG_FILE" ]; then
    tail -30 "$LOG_FILE"
else
    echo "Log file not found: $LOG_FILE"
fi

echo ""
echo "=" | head -c 80 && echo ""
echo "💡 TIPS"
echo "=" | head -c 80 && echo ""
echo "  • Watch live progress: tail -f $LOG_FILE"
echo "  • Check specific step: grep 'STEP' $LOG_FILE | tail -10"
echo "  • Check for errors: grep -i error $LOG_FILE | tail -5"
echo "  • Check completion: grep -i 'complete\|saved\|accuracy' $LOG_FILE | tail -10"

