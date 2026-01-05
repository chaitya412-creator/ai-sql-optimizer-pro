# Frontend Implementation Guide - AI SQL Optimizer Pro

## 🎨 Stunning UI Design Overview

The frontend is built with **React + Vite + TailwindCSS + Recharts** for a modern, responsive, and beautiful user interface.

### Design Principles
- **Modern & Clean**: Minimalist design with focus on functionality
- **Responsive**: Works on desktop, tablet, and mobile
- **Dark Mode Ready**: CSS variables for easy theme switching
- **Performance**: Optimized with Vite for fast loading
- **Accessibility**: ARIA labels and keyboard navigation

---

## 📁 Complete File Structure

```
frontend/
├── public/
│   └── vite.svg
├── src/
│   ├── components/
│   │   ├── Layout/
│   │   │   ├── Layout.tsx          # Main layout wrapper
│   │   │   ├── Sidebar.tsx         # Navigation sidebar
│   │   │   └── Header.tsx          # Top header with breadcrumbs
│   │   ├── Dashboard/
│   │   │   ├── StatsCards.tsx      # Metrics cards (queries, avg time, etc.)
│   │   │   ├── QueryTable.tsx      # Top bottlenecks table
│   │   │   └── PerformanceChart.tsx # Performance trends chart
│   │   ├── Connections/
│   │   │   ├── ConnectionList.tsx   # List of connections
│   │   │   ├── ConnectionCard.tsx   # Individual connection card
│   │   │   ├── ConnectionForm.tsx   # Add/Edit modal
│   │   │   └── TestConnection.tsx   # Connection test button
│   │   ├── Monitoring/
│   │   │   ├── MonitoringStatus.tsx # Agent status display
│   │   │   ├── MonitoringControls.tsx # Start/Stop controls
│   │   │   └── DiscoveredQueries.tsx # List of discovered queries
│   │   ├── Optimizer/
│   │   │   ├── QueryInput.tsx       # SQL query input
│   │   │   ├── OptimizationResults.tsx # Results display
│   │   │   ├── ExecutionPlanViewer.tsx # Plan visualization
│   │   │   ├── SQLDiffViewer.tsx    # Side-by-side comparison
│   │   │   └── RecommendationsList.tsx # Index/stats recommendations
│   │   └── UI/
│   │       ├── Button.tsx           # Reusable button component
│   │       ├── Card.tsx             # Card component
│   │       ├── Modal.tsx            # Modal dialog
│   │       ├── Table.tsx            # Data table
│   │       ├── Badge.tsx            # Status badge
│   │       ├── Spinner.tsx          # Loading spinner
│   │       └── CodeBlock.tsx        # Syntax-highlighted code
│   ├── pages/
│   │   ├── Dashboard.tsx            # Main dashboard page
│   │   ├── Connections.tsx          # Connections management page
│   │   ├── Monitoring.tsx           # Monitoring agent page
│   │   └── Optimizer.tsx            # Query optimizer page
│   ├── services/
│   │   └── api.ts                   # Axios API client
│   ├── types/
│   │   └── index.ts                 # TypeScript interfaces
│   ├── hooks/
│   │   ├── useConnections.ts        # Connections hook
│   │   ├── useMonitoring.ts         # Monitoring hook
│   │   └── useOptimizer.ts          # Optimizer hook
│   ├── utils/
│   │   ├── formatters.ts            # Data formatting utilities
│   │   └── constants.ts             # App constants
│   ├── styles/
│   │   └── globals.css              # Global styles + CSS variables
│   ├── App.tsx                      # Main app with routing
│   └── main.tsx                     # Entry point
├── index.html
├── package.json
├── vite.config.ts
├── tsconfig.json
├── tailwind.config.js
└── postcss.config.js
```

---

## 🎨 Key UI Components

### 1. Dashboard Page
**Features:**
- 4 metric cards (Total Queries, Avg Execution Time, Slow Queries, Active Connections)
- Performance trend chart (Recharts line chart)
- Top 10 bottlenecks table with "Optimize" button
- Real-time updates every 30 seconds

**Design:**
- Gradient background (blue to purple)
- Glass-morphism cards with backdrop blur
- Animated counters for metrics
- Interactive chart with tooltips

### 2. Connections Page
**Features:**
- Grid of connection cards
- Add New Connection button (opens modal)
- Edit/Delete/Test actions per connection
- Connection status indicators (green/red)

**Design:**
- Card-based layout with hover effects
- Database type icons (PostgreSQL, MySQL, Oracle, MSSQL)
- Color-coded status badges
- Smooth transitions

### 3. Monitoring Page
**Features:**
- Agent status display (Running/Stopped)
- Start/Stop/Trigger Now controls
- Configuration panel (interval, max queries)
- Discovered queries table with timestamps

**Design:**
- Split layout (controls on left, results on right)
- Pulsing indicator for running agent
- Timeline view for discovered queries
- Filterable and sortable table

### 4. Optimizer Page
**Features:**
- SQL query input (CodeMirror or textarea)
- Connection selector dropdown
- Analyze button with loading state
- Results panel:
  - Original vs Optimized SQL (side-by-side)
  - Execution plan visualization (tree view)
  - AI explanation (markdown formatted)
  - Recommendations list (CREATE INDEX, ANALYZE, etc.)

**Design:**
- Two-column layout (input left, results right)
- Syntax highlighting for SQL
- Collapsible sections
- Copy-to-clipboard buttons
- Diff highlighting (red for removed, green for added)

---

## 🎨 Color Scheme & Styling

### CSS Variables (globals.css)
```css
:root {
  --background: 0 0% 100%;
  --foreground: 222.2 84% 4.9%;
  --primary: 221.2 83.2% 53.3%;
  --primary-foreground: 210 40% 98%;
  --secondary: 210 40% 96.1%;
  --secondary-foreground: 222.2 47.4% 11.2%;
  --muted: 210 40% 96.1%;
  --muted-foreground: 215.4 16.3% 46.9%;
  --accent: 210 40% 96.1%;
  --accent-foreground: 222.2 47.4% 11.2%;
  --destructive: 0 84.2% 60.2%;
  --destructive-foreground: 210 40% 98%;
  --border: 214.3 31.8% 91.4%;
  --input: 214.3 31.8% 91.4%;
  --ring: 221.2 83.2% 53.3%;
  --radius: 0.5rem;
}
```

### Tailwind Classes
- **Cards**: `bg-white dark:bg-gray-800 rounded-lg shadow-lg p-6`
- **Buttons**: `bg-blue-600 hover:bg-blue-700 text-white px-4 py-2 rounded-md transition`
- **Badges**: `px-2 py-1 rounded-full text-xs font-semibold`
- **Tables**: `w-full border-collapse`

---

## 🔌 API Integration (services/api.ts)

```typescript
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const api = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
});

// Connections
export const getConnections = () => api.get('/api/connections');
export const createConnection = (data: any) => api.post('/api/connections', data);
export const testConnection = (id: number) => api.post(`/api/connections/${id}/test`);
export const deleteConnection = (id: number) => api.delete(`/api/connections/${id}`);

// Monitoring
export const getMonitoringStatus = () => api.get('/api/monitoring/status');
export const startMonitoring = () => api.post('/api/monitoring/start');
export const stopMonitoring = () => api.post('/api/monitoring/stop');
export const triggerMonitoring = () => api.post('/api/monitoring/trigger');

// Optimizer
export const optimizeQuery = (data: any) => api.post('/api/optimizer/optimize', data);

// Dashboard
export const getDashboardStats = () => api.get('/api/dashboard/stats');
export const getTopQueries = () => api.get('/api/dashboard/top-queries');
```

---

## 📊 Charts & Visualizations

### Performance Chart (Recharts)
```typescript
import { LineChart, Line, XAxis, YAxis, CartesianGrid, Tooltip, Legend } from 'recharts';

<LineChart width={800} height={300} data={data}>
  <CartesianGrid strokeDasharray="3 3" />
  <XAxis dataKey="timestamp" />
  <YAxis />
  <Tooltip />
  <Legend />
  <Line type="monotone" dataKey="avgTime" stroke="#8884d8" />
  <Line type="monotone" dataKey="slowQueries" stroke="#82ca9d" />
</LineChart>
```

### Execution Plan Tree
- Recursive component for nested plan nodes
- Color-coded by operation type (Seq Scan = red, Index Scan = green)
- Expandable/collapsible nodes
- Cost and row estimates displayed

---

## 🚀 Quick Start Commands

```bash
# Navigate to frontend
cd ai-sql-optimizer-pro/frontend

# Install dependencies
npm install

# Start development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

---

## 📦 NPM Dependencies

Already defined in `package.json`:
- react, react-dom, react-router-dom
- axios
- recharts
- lucide-react (icons)
- tailwindcss, postcss, autoprefixer
- vite, @vitejs/plugin-react
- typescript, @types/react, @types/react-dom

---

## 🎯 Implementation Priority

### Phase 1: Core Structure (DONE)
- ✅ Configuration files
- ✅ Package.json
- ✅ Dockerfile

### Phase 2: Essential Files (NEXT)
1. src/main.tsx - Entry point
2. src/App.tsx - Routing
3. src/styles/globals.css - Styling
4. src/services/api.ts - API client
5. src/types/index.ts - TypeScript types

### Phase 3: Layout Components
6. src/components/Layout/Layout.tsx
7. src/components/Layout/Sidebar.tsx
8. src/components/Layout/Header.tsx

### Phase 4: Pages
9. src/pages/Dashboard.tsx
10. src/pages/Connections.tsx
11. src/pages/Monitoring.tsx
12. src/pages/Optimizer.tsx

### Phase 5: Feature Components
13-30. Dashboard, Connections, Monitoring, Optimizer components

### Phase 6: UI Components
31-38. Reusable UI components (Button, Card, Modal, etc.)

---

## 🎨 Stunning UI Features

1. **Animated Transitions**: Smooth page transitions with Framer Motion
2. **Loading States**: Skeleton screens and spinners
3. **Toast Notifications**: Success/error messages
4. **Responsive Design**: Mobile-first approach
5. **Dark Mode**: Toggle between light/dark themes
6. **Syntax Highlighting**: SQL code with Prism.js
7. **Interactive Charts**: Hover effects and tooltips
8. **Drag & Drop**: Reorder connections
9. **Search & Filter**: Real-time filtering
10. **Keyboard Shortcuts**: Power user features

---

## 📝 Next Steps

To complete the frontend implementation, create the remaining 35 files following the structure above. Each component should:
- Use TypeScript for type safety
- Follow React best practices (hooks, functional components)
- Implement error handling
- Include loading states
- Be responsive and accessible

The backend is 100% complete and ready to integrate with the frontend once all files are created.
