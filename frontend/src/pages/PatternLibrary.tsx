import React, { useState, useEffect } from 'react';
import { Search, Filter, RefreshCw, Database, TrendingUp, CheckCircle, BookOpen, X } from 'lucide-react';
import PatternCard from '../components/Patterns/PatternCard';
import {
  getAllPatterns,
  getCategories,
  getStatistics,
  loadCommonPatterns,
  searchPatterns,
  type Pattern,
  type PatternCategory,
  type PatternStatistics,
  type PatternFilters,
} from '../services/patterns';

const PatternLibrary: React.FC = () => {
  const [patterns, setPatterns] = useState<Pattern[]>([]);
  const [categories, setCategories] = useState<PatternCategory[]>([]);
  const [statistics, setStatistics] = useState<PatternStatistics | null>(null);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Filters
  const [searchQuery, setSearchQuery] = useState('');
  const [selectedDatabase, setSelectedDatabase] = useState<string>('');
  const [selectedCategory, setSelectedCategory] = useState<string>('');
  const [minSuccessRate, setMinSuccessRate] = useState<number>(0);
  const [sortBy, setSortBy] = useState<string>('success_rate');
  
  // Modal
  const [selectedPattern, setSelectedPattern] = useState<Pattern | null>(null);
  const [showModal, setShowModal] = useState(false);

  // Load initial data
  useEffect(() => {
    loadInitialData();
  }, []);

  // Load data when filters change
  useEffect(() => {
    if (searchQuery) {
      handleSearch();
    } else {
      loadPatterns();
    }
  }, [selectedDatabase, selectedCategory, minSuccessRate, sortBy]);

  const loadInitialData = async () => {
    setLoading(true);
    try {
      const [statsData, categoriesData] = await Promise.all([
        getStatistics(),
        getCategories(),
      ]);
      setStatistics(statsData);
      setCategories(categoriesData);
      await loadPatterns();
    } catch (err: any) {
      setError(err.message || 'Failed to load data');
    } finally {
      setLoading(false);
    }
  };

  const loadPatterns = async () => {
    setLoading(true);
    setError(null);
    try {
      const filters: PatternFilters = {
        database_type: selectedDatabase || undefined,
        category: selectedCategory || undefined,
        min_success_rate: minSuccessRate > 0 ? minSuccessRate / 100 : undefined,
        sort_by: sortBy,
        limit: 100,
      };
      const data = await getAllPatterns(filters);
      setPatterns(data);
    } catch (err: any) {
      setError(err.message || 'Failed to load patterns');
    } finally {
      setLoading(false);
    }
  };

  const handleSearch = async () => {
    if (!searchQuery.trim()) {
      loadPatterns();
      return;
    }
    
    setLoading(true);
    setError(null);
    try {
      const data = await searchPatterns(searchQuery, {
        database_type: selectedDatabase || undefined,
        category: selectedCategory || undefined,
      });
      setPatterns(data);
    } catch (err: any) {
      setError(err.message || 'Search failed');
    } finally {
      setLoading(false);
    }
  };

  const handleLoadCommonPatterns = async () => {
    setLoading(true);
    setError(null);
    try {
      const result = await loadCommonPatterns();
      alert(`Successfully loaded ${result.patterns_loaded} common patterns`);
      await loadInitialData();
    } catch (err: any) {
      setError(err.message || 'Failed to load common patterns');
    } finally {
      setLoading(false);
    }
  };

  const handleViewDetails = (pattern: Pattern) => {
    setSelectedPattern(pattern);
    setShowModal(true);
  };

  const closeModal = () => {
    setShowModal(false);
    setSelectedPattern(null);
  };

  return (
    <div className="min-h-screen bg-gray-50 p-8">
      <div className="max-w-7xl mx-auto">
        {/* Header */}
        <div className="mb-8">
          <div className="flex items-center justify-between">
            <div>
              <h1 className="text-3xl font-bold text-gray-900 mb-2">Pattern Library</h1>
              <p className="text-gray-600">
                Browse and explore optimization patterns learned from successful optimizations
              </p>
            </div>
            <button
              onClick={handleLoadCommonPatterns}
              disabled={loading}
              className="px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 disabled:bg-gray-400 transition-colors flex items-center space-x-2"
            >
              <Database className="w-4 h-4" />
              <span>Load Common Patterns</span>
            </button>
          </div>
        </div>

        {/* Statistics Cards */}
        {statistics && (
          <div className="grid grid-cols-1 md:grid-cols-4 gap-6 mb-8">
            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Patterns</p>
                  <p className="text-3xl font-bold text-gray-900">{statistics.total_patterns}</p>
                </div>
                <div className="p-3 bg-blue-100 rounded-lg">
                  <BookOpen className="w-8 h-8 text-blue-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Avg Success Rate</p>
                  <p className="text-3xl font-bold text-green-600">{statistics.avg_success_rate.toFixed(1)}%</p>
                </div>
                <div className="p-3 bg-green-100 rounded-lg">
                  <CheckCircle className="w-8 h-8 text-green-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Total Applications</p>
                  <p className="text-3xl font-bold text-purple-600">{statistics.total_applications}</p>
                </div>
                <div className="p-3 bg-purple-100 rounded-lg">
                  <Database className="w-8 h-8 text-purple-600" />
                </div>
              </div>
            </div>

            <div className="bg-white rounded-lg shadow-md p-6">
              <div className="flex items-center justify-between">
                <div>
                  <p className="text-sm text-gray-600 mb-1">Success Rate</p>
                  <p className="text-3xl font-bold text-orange-600">{statistics.overall_success_rate.toFixed(1)}%</p>
                </div>
                <div className="p-3 bg-orange-100 rounded-lg">
                  <TrendingUp className="w-8 h-8 text-orange-600" />
                </div>
              </div>
            </div>
          </div>
        )}

        {/* Search and Filters */}
        <div className="bg-white rounded-lg shadow-md p-6 mb-8">
          <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-5 gap-4">
            {/* Search */}
            <div className="lg:col-span-2">
              <label className="block text-sm font-medium text-gray-700 mb-2">Search</label>
              <div className="relative">
                <input
                  type="text"
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
                  placeholder="Search patterns..."
                  className="w-full px-4 py-2 pl-10 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
                />
                <Search className="absolute left-3 top-2.5 w-5 h-5 text-gray-400" />
              </div>
            </div>

            {/* Database Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Database</label>
              <select
                value={selectedDatabase}
                onChange={(e) => setSelectedDatabase(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Databases</option>
                <option value="postgresql">PostgreSQL</option>
                <option value="mysql">MySQL</option>
                <option value="mssql">MSSQL</option>
              </select>
            </div>

            {/* Category Filter */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Category</label>
              <select
                value={selectedCategory}
                onChange={(e) => setSelectedCategory(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="">All Categories</option>
                {categories.map((cat) => (
                  <option key={cat.name} value={cat.name}>
                    {cat.display_name} ({cat.count})
                  </option>
                ))}
              </select>
            </div>

            {/* Sort */}
            <div>
              <label className="block text-sm font-medium text-gray-700 mb-2">Sort By</label>
              <select
                value={sortBy}
                onChange={(e) => setSortBy(e.target.value)}
                className="w-full px-4 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-transparent"
              >
                <option value="success_rate">Success Rate</option>
                <option value="improvement">Improvement</option>
                <option value="applications">Applications</option>
                <option value="created_at">Recently Added</option>
              </select>
            </div>
          </div>

          {/* Active Filters */}
          {(selectedDatabase || selectedCategory || minSuccessRate > 0) && (
            <div className="flex items-center space-x-2 mt-4">
              <span className="text-sm text-gray-600">Active filters:</span>
              {selectedDatabase && (
                <span className="px-2 py-1 bg-blue-100 text-blue-700 rounded text-xs flex items-center space-x-1">
                  <span>{selectedDatabase}</span>
                  <button onClick={() => setSelectedDatabase('')}><X className="w-3 h-3" /></button>
                </span>
              )}
              {selectedCategory && (
                <span className="px-2 py-1 bg-purple-100 text-purple-700 rounded text-xs flex items-center space-x-1">
                  <span>{selectedCategory}</span>
                  <button onClick={() => setSelectedCategory('')}><X className="w-3 h-3" /></button>
                </span>
              )}
              <button
                onClick={() => {
                  setSelectedDatabase('');
                  setSelectedCategory('');
                  setMinSuccessRate(0);
                  setSearchQuery('');
                }}
                className="text-xs text-blue-600 hover:text-blue-700"
              >
                Clear all
              </button>
            </div>
          )}
        </div>

        {/* Error Message */}
        {error && (
          <div className="bg-red-50 border border-red-200 rounded-lg p-4 mb-8">
            <p className="text-red-700">{error}</p>
          </div>
        )}

        {/* Patterns Grid */}
        {loading ? (
          <div className="flex items-center justify-center py-12">
            <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
          </div>
        ) : patterns.length === 0 ? (
          <div className="bg-white rounded-lg shadow-md p-12 text-center">
            <BookOpen className="w-16 h-16 text-gray-400 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 mb-2">No Patterns Found</h3>
            <p className="text-gray-600">
              {searchQuery ? 'Try adjusting your search or filters' : 'No patterns available yet'}
            </p>
          </div>
        ) : (
          <>
            <div className="flex items-center justify-between mb-4">
              <p className="text-sm text-gray-600">
                Showing {patterns.length} pattern{patterns.length !== 1 ? 's' : ''}
              </p>
              <button
                onClick={loadPatterns}
                className="text-sm text-blue-600 hover:text-blue-700 flex items-center space-x-1"
              >
                <RefreshCw className="w-4 h-4" />
                <span>Refresh</span>
              </button>
            </div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
              {patterns.map((pattern) => (
                <PatternCard
                  key={pattern.id}
                  pattern={pattern}
                  onViewDetails={handleViewDetails}
                />
              ))}
            </div>
          </>
        )}

        {/* Pattern Detail Modal */}
        {showModal && selectedPattern && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50 p-4">
            <div className="bg-white rounded-lg max-w-4xl w-full max-h-[90vh] overflow-y-auto">
              <div className="p-6">
                <div className="flex items-start justify-between mb-4">
                  <h2 className="text-2xl font-bold text-gray-900">Pattern Details</h2>
                  <button
                    onClick={closeModal}
                    className="text-gray-400 hover:text-gray-600"
                  >
                    <X className="w-6 h-6" />
                  </button>
                </div>

                <div className="space-y-6">
                  {/* Metrics */}
                  <div className="grid grid-cols-4 gap-4">
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Success Rate</p>
                      <p className="text-2xl font-bold text-green-600">{selectedPattern.success_rate.toFixed(1)}%</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Improvement</p>
                      <p className="text-2xl font-bold text-blue-600">{selectedPattern.avg_improvement_pct.toFixed(1)}%</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Applied</p>
                      <p className="text-2xl font-bold text-purple-600">{selectedPattern.times_applied}</p>
                    </div>
                    <div className="bg-gray-50 p-4 rounded-lg">
                      <p className="text-sm text-gray-600 mb-1">Successful</p>
                      <p className="text-2xl font-bold text-orange-600">{selectedPattern.times_successful}</p>
                    </div>
                  </div>

                  {/* SQL Patterns */}
                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Original Pattern</h3>
                    <pre className="bg-gray-900 text-gray-100 p-4 rounded-lg overflow-x-auto text-sm">
                      {selectedPattern.original_pattern}
                    </pre>
                  </div>

                  <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-2">Optimized Pattern</h3>
                    <pre className="bg-gray-900 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                      {selectedPattern.optimized_pattern}
                    </pre>
                  </div>

                  {selectedPattern.description && (
                    <div>
                      <h3 className="text-lg font-semibold text-gray-900 mb-2">Description</h3>
                      <p className="text-gray-700">{selectedPattern.description}</p>
                    </div>
                  )}
                </div>
              </div>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default PatternLibrary;
