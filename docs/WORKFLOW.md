## Current Workflow (Demo):

User Opens Client Profile
        ↓
GET /profile → Database Cache (<1s)
        ↓
Displays: Segment, Switch Prob, Drivers, Media, Recommendations
        ↓
User Clicks "Force Event" (simulates auto-monitoring)
        ↓
POST /analyze → Agents Service (~30s)
   ├─ Segmentation Agent (Gemini) → Classify segment + compute switch prob
   ├─ Media Fusion Agent (Gemini) → Analyze sentiment on exposures
   └─ NBA Agent (Gemini) → Generate recommendations
        ↓
Compare: old_switch_prob vs new_switch_prob
        ↓
IF change ≥ 3% → Generate Alert
        ↓
Alert → SSE Stream → UI Banner
        ↓
User Clicks "Propose Product"
        ↓
POST /actions → Logs to database → Appears in Insights Feed


## Production Workflow:

Background Job (every 30 mins) OR Event Trigger (new trade/news)
        ↓
Auto-runs /analyze for monitored clients
        ↓
Agents compute fresh switch probability
        ↓
Alert generated if threshold crossed
        ↓
RM receives real-time notification
        ↓
RM takes action → Tracked for outcome learning
