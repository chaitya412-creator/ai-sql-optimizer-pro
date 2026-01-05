import { BrowserRouter as Router, Routes, Route, Navigate } from 'react-router-dom';
import Layout from './components/Layout/Layout';
import Dashboard from './pages/Dashboard';
import Connections from './pages/Connections';
import Monitoring from './pages/Monitoring';
import Optimizer from './pages/Optimizer';
import Configuration from './pages/Configuration';
import MLPerformance from './pages/MLPerformance';
import IndexManagement from './pages/IndexManagement';
import WorkloadAnalysis from './pages/WorkloadAnalysis';
import PatternLibrary from './pages/PatternLibrary';

function App() {
  return (
    <Router>
      <Layout>
        <Routes>
          <Route path="/" element={<Navigate to="/dashboard" replace />} />
          <Route path="/dashboard" element={<Dashboard />} />
          <Route path="/connections" element={<Connections />} />
          <Route path="/monitoring" element={<Monitoring />} />
          <Route path="/optimizer" element={<Optimizer />} />
          <Route path="/workload-analysis" element={<WorkloadAnalysis />} />
          <Route path="/configuration" element={<Configuration />} />
          <Route path="/ml-performance" element={<MLPerformance />} />
          <Route path="/index-management" element={<IndexManagement />} />
          <Route path="/pattern-library" element={<PatternLibrary />} />
        </Routes>
      </Layout>
    </Router>
  );
}

export default App;
