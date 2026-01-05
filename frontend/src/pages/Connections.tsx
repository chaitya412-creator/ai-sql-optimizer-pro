import { useState, useEffect } from 'react';
import { Plus, Trash2, Edit, CheckCircle, XCircle, Loader } from 'lucide-react';
import { getConnections, createConnection, deleteConnection, testConnection } from '../services/api';
import type { Connection, ConnectionCreate } from '../types';

export default function Connections() {
  const [connections, setConnections] = useState<Connection[]>([]);
  const [loading, setLoading] = useState(true);
  const [error, setError] = useState<string | null>(null);
  const [showForm, setShowForm] = useState(false);
  const [testingId, setTestingId] = useState<number | null>(null);
  const [formData, setFormData] = useState<ConnectionCreate>({
    name: '',
    engine: 'postgresql',
    host: '',
    port: 5432,
    database: '',
    username: '',
    password: '',
    ssl_enabled: false,
    monitoring_enabled: true,
  });

  useEffect(() => {
    loadConnections();
  }, []);

  const loadConnections = async () => {
    try {
      setLoading(true);
      setError(null);
      const data = await getConnections();
      setConnections(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load connections');
    } finally {
      setLoading(false);
    }
  };

  const handleSubmit = async (e: React.FormEvent) => {
    e.preventDefault();
    try {
      await createConnection(formData);
      setShowForm(false);
      setFormData({
        name: '',
        engine: 'postgresql',
        host: '',
        port: 5432,
        database: '',
        username: '',
        password: '',
        ssl_enabled: false,
        monitoring_enabled: true,
      });
      loadConnections();
    } catch (err: any) {
      alert(err.message || 'Failed to create connection');
    }
  };

  const handleDelete = async (id: number) => {
    if (!confirm('Are you sure you want to delete this connection?')) return;
    try {
      await deleteConnection(id);
      loadConnections();
    } catch (err: any) {
      alert(err.message || 'Failed to delete connection');
    }
  };

  const handleTest = async (id: number) => {
    try {
      setTestingId(id);
      const result = await testConnection(id);
      alert(result.success ? `✓ ${result.message}` : `✗ ${result.message}`);
    } catch (err: any) {
      alert(`✗ ${err.message || 'Connection test failed'}`);
    } finally {
      setTestingId(null);
    }
  };

  const getEngineColor = (engine: string) => {
    const colors: Record<string, string> = {
      postgresql: 'bg-blue-100 text-blue-800 dark:bg-blue-900/30 dark:text-blue-300',
      mysql: 'bg-orange-100 text-orange-800 dark:bg-orange-900/30 dark:text-orange-300',
      oracle: 'bg-red-100 text-red-800 dark:bg-red-900/30 dark:text-red-300',
      mssql: 'bg-purple-100 text-purple-800 dark:bg-purple-900/30 dark:text-purple-300',
    };
    return colors[engine] || 'bg-gray-100 text-gray-800 dark:bg-gray-900/30 dark:text-gray-300';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center h-64">
        <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-blue-600"></div>
      </div>
    );
  }

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-white">Database Connections</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Manage your database connections
          </p>
        </div>
        <button
          onClick={() => setShowForm(!showForm)}
          className="flex items-center space-x-2 px-4 py-2 bg-gradient-to-r from-blue-500 to-purple-600 text-white rounded-lg hover:from-blue-600 hover:to-purple-700 transition-all shadow-lg"
        >
          <Plus className="w-5 h-5" />
          <span>Add Connection</span>
        </button>
      </div>

      {error && (
        <div className="bg-red-50 dark:bg-red-900/20 border border-red-200 dark:border-red-800 rounded-lg p-4">
          <p className="text-red-800 dark:text-red-200">{error}</p>
        </div>
      )}

      {/* Connection Form */}
      {showForm && (
        <div className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6">
          <h2 className="text-xl font-semibold text-gray-900 dark:text-white mb-4">
            New Connection
          </h2>
          <form onSubmit={handleSubmit} className="space-y-4">
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Connection Name
                </label>
                <input
                  type="text"
                  required
                  value={formData.name}
                  onChange={(e) => setFormData({ ...formData, name: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="My Database"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Database Engine
                </label>
                <select
                  value={formData.engine}
                  onChange={(e) => setFormData({ ...formData, engine: e.target.value as any })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                >
                  <option value="postgresql">PostgreSQL</option>
                  <option value="mysql">MySQL</option>
                  <option value="oracle">Oracle</option>
                  <option value="mssql">MS SQL Server</option>
                </select>
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Host
                </label>
                <input
                  type="text"
                  required
                  value={formData.host}
                  onChange={(e) => setFormData({ ...formData, host: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="localhost"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Port
                </label>
                <input
                  type="number"
                  required
                  value={formData.port}
                  onChange={(e) => setFormData({ ...formData, port: parseInt(e.target.value) })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Database
                </label>
                <input
                  type="text"
                  required
                  value={formData.database}
                  onChange={(e) => setFormData({ ...formData, database: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="mydb"
                />
              </div>
              <div>
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Username
                </label>
                <input
                  type="text"
                  required
                  value={formData.username}
                  onChange={(e) => setFormData({ ...formData, username: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="user"
                />
              </div>
              <div className="md:col-span-2">
                <label className="block text-sm font-medium text-gray-700 dark:text-gray-300 mb-1">
                  Password
                </label>
                <input
                  type="password"
                  required
                  value={formData.password}
                  onChange={(e) => setFormData({ ...formData, password: e.target.value })}
                  className="w-full px-3 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:ring-2 focus:ring-blue-500 dark:bg-gray-700 dark:text-white"
                  placeholder="••••••••"
                />
              </div>
            </div>
            <div className="flex space-x-3">
              <button
                type="submit"
                className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 transition-colors"
              >
                Create Connection
              </button>
              <button
                type="button"
                onClick={() => setShowForm(false)}
                className="px-4 py-2 bg-gray-200 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-300 dark:hover:bg-gray-600 transition-colors"
              >
                Cancel
              </button>
            </div>
          </form>
        </div>
      )}

      {/* Connections List */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
        {connections.length === 0 ? (
          <div className="col-span-full text-center py-12 text-gray-500 dark:text-gray-400">
            No connections yet. Add your first database connection to get started.
          </div>
        ) : (
          connections.map((conn) => (
            <div
              key={conn.id}
              className="bg-white dark:bg-gray-800 rounded-lg shadow-lg border border-gray-200 dark:border-gray-700 p-6 hover:shadow-xl transition-shadow"
            >
              <div className="flex items-start justify-between mb-4">
                <div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-white">
                    {conn.name}
                  </h3>
                  <span className={`inline-block px-2 py-1 text-xs font-medium rounded-full mt-2 ${getEngineColor(conn.engine)}`}>
                    {conn.engine.toUpperCase()}
                  </span>
                </div>
                <div className="flex items-center space-x-1">
                  {conn.monitoring_enabled ? (
                    <CheckCircle className="w-5 h-5 text-green-500" />
                  ) : (
                    <XCircle className="w-5 h-5 text-gray-400" />
                  )}
                </div>
              </div>
              
              <div className="space-y-2 text-sm text-gray-600 dark:text-gray-400 mb-4">
                <p><span className="font-medium">Host:</span> {conn.host}:{conn.port}</p>
                <p><span className="font-medium">Database:</span> {conn.database}</p>
                <p><span className="font-medium">User:</span> {conn.username}</p>
              </div>

              <div className="flex space-x-2">
                <button
                  onClick={() => handleTest(conn.id)}
                  disabled={testingId === conn.id}
                  className="flex-1 flex items-center justify-center space-x-1 px-3 py-2 bg-blue-50 dark:bg-blue-900/30 text-blue-600 dark:text-blue-400 rounded-lg hover:bg-blue-100 dark:hover:bg-blue-900/50 transition-colors disabled:opacity-50"
                >
                  {testingId === conn.id ? (
                    <Loader className="w-4 h-4 animate-spin" />
                  ) : (
                    <CheckCircle className="w-4 h-4" />
                  )}
                  <span className="text-sm">Test</span>
                </button>
                <button
                  onClick={() => handleDelete(conn.id)}
                  className="px-3 py-2 bg-red-50 dark:bg-red-900/30 text-red-600 dark:text-red-400 rounded-lg hover:bg-red-100 dark:hover:bg-red-900/50 transition-colors"
                >
                  <Trash2 className="w-4 h-4" />
                </button>
              </div>
            </div>
          ))
        )}
      </div>
    </div>
  );
}
