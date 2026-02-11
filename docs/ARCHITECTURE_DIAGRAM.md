# OpenClaw Architecture Diagram

Interactive system diagram documentation for the OpenClaw platform architecture.

## 📁 Files

- **`openclaw_architecture.html`** - Interactive HTML diagram (self-contained)
- **`ARCHITECTURE_DIAGRAM.md`** - This documentation file

## 🚀 How to View

### Option 1: Open Directly in Browser (Recommended)

Simply double-click the HTML file or open it in any modern web browser:

```bash
# macOS
open /Users/yoshikondo/agent-highway/docs/openclaw_architecture.html

# Linux
xdg-open /Users/yoshikondo/agent-highway/docs/openclaw_architecture.html

# Windows
start /Users/yoshikondo/agent-highway/docs/openclaw_architecture.html
```

### Option 2: Serve via Local HTTP Server

For the best experience (especially if you want to embed or share):

```bash
cd /Users/yoshikondo/agent-highway/docs

# Python 3
python -m http.server 8080

# Node.js (if installed)
npx serve .

# PHP
php -S localhost:8080
```

Then open: http://localhost:8080/openclaw_architecture.html

### Option 3: VS Code Live Server

If using VS Code with the Live Server extension, right-click the HTML file and select "Open with Live Server".

## 🎨 Features

### Visual Design
- **Dark theme** with neon accents (cyan, purple, green, orange, red)
- **Animated connections** between architecture components
- **Zoom and pan** capabilities for detailed exploration
- **Grid background** with subtle animation

### Architecture Layers

| Layer | Color | Components |
|-------|-------|------------|
| **Client Layer** | Cyan (#00ffff) | Telegram Bot, Discord Bot, Web UI |
| **Gateway Layer** | Purple (#ff00ff) | Cloudflare Worker, WebSocket Hub, REST API |
| **Sandbox Layer** | Green (#00ff88) | Moltbot Core, Subagents, Skills Engine |
| **Storage Layer** | Orange (#ffa500) | R2 Storage, KV Store, D1 Database |
| **External Services** | Red (#ff4444) | AI Gateway, Browser Rendering |

### Interactive Features

#### 1. Hover Tooltips
- Move your mouse over any component to see a brief description
- Appears instantly with component summary

#### 2. Click for Details
- Click any node to open the detail panel on the right
- Shows comprehensive information about:
  - Component description
  - Key features and capabilities
  - Technology stack
  - Scaling and architecture details

#### 3. Layer Toggles
- Use the control panel (top-right) to show/hide specific layers
- Useful for focusing on particular aspects of the architecture
- Dimmed layers remain visible but at reduced opacity

#### 4. Request Flow Animation
- Click the "▶ Animate Request Flow" button to see a typical request journey:
  ```
  Telegram → Worker → Moltbot → AI Gateway → Moltbot → KV Store → Worker → Telegram
  ```
- Watch the animated packet travel through the system
- See timing and component interactions

#### 5. Zoom and Pan
- **Scroll** to zoom in/out
- **Click and drag** to pan around the diagram
- **Double-click** or use "Reset View" button to return to default view

## 🔄 Data Flow Legend

| Color | Meaning | Example Flow |
|-------|---------|--------------|
| **Cyan** | User Request | Client → Gateway |
| **Purple** | Internal Routing | Gateway → Sandbox |
| **Green** | AI Processing | Sandbox → AI Gateway |
| **Orange** | Data Storage | Sandbox → Storage Layer |

## 🛠 Technical Details

### Built With
- **D3.js v7** - Data visualization and interaction
- **Vanilla JavaScript** - No frameworks required
- **CSS3** - Animations, gradients, and effects
- **SVG** - Scalable vector graphics

### Browser Compatibility
- ✅ Chrome 90+
- ✅ Firefox 88+
- ✅ Safari 14+
- ✅ Edge 90+

### No Build Step Required
The diagram is completely self-contained in a single HTML file:
- D3.js loaded from CDN
- No external dependencies beyond the CDN
- Works offline after initial load

## 📝 Architecture Overview

### Request Lifecycle

1. **Client Layer** - User interacts via Telegram, Discord, or Web UI
2. **Gateway Layer** - Cloudflare Worker handles authentication and routing
3. **Sandbox Layer** - Moltbot Core orchestrates agent execution
4. **External Services** - AI Gateway processes LLM requests
5. **Storage Layer** - Data persisted to R2, KV, or D1 as needed
6. **Response** - Flows back through the chain to the user

### Key Design Principles

- **Edge-First**: Cloudflare Workers provide global low-latency access
- **Modular**: Skills system allows extensibility without core changes
- **Scalable**: Subagent pool handles parallel task execution
- **Multi-Modal**: Supports multiple client interfaces simultaneously

## 🎯 Use Cases

- **Onboarding** - New team members can explore the architecture visually
- **Documentation** - Reference during technical discussions
- **Presentations** - Screenshot or present the interactive diagram
- **Debugging** - Trace request flows to understand data movement
- **Planning** - Visualize where new components fit in the architecture

## 🔮 Future Enhancements

Potential additions to the diagram:
- [ ] Real-time metrics overlay
- [ ] Component health indicators
- [ ] Deployment region visualization
- [ ] Cost flow animation
- [ ] Integration with actual monitoring data

## 📞 Support

For questions about the OpenClaw architecture:
- Check the detail panels in the interactive diagram
- Refer to the main project documentation
- Contact the architecture team

---

*Generated: 2026-02-09*  
*OpenClaw Architecture v1.0*
