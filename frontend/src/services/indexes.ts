/**
 * Index Management API Service
 * Handles all index-related API calls
 */
import axios from 'axios';

const API_URL = import.meta.env.VITE_API_URL || 'http://localhost:8000';

const client = axios.create({
  baseURL: API_URL,
  headers: {
    'Content-Type': 'application/json',
  },
  timeout: 30000,
});

const normalizeColumns = (value: unknown): string[] => {
  if (Array.isArray(value)) {
    return value
      .filter((v) => v !== null && v !== undefined)
      .map((v) => String(v).trim())
      .filter(Boolean);
  }

  if (typeof value === 'string') {
    const trimmed = value.trim();
    if (!trimmed) return [];

    // Some backends/DBs return JSON-encoded arrays.
    if (trimmed.startsWith('[') && trimmed.endsWith(']')) {
      try {
        const parsed = JSON.parse(trimmed);
        if (Array.isArray(parsed)) {
          return parsed
            .filter((v) => v !== null && v !== undefined)
            .map((v) => String(v).trim())
            .filter(Boolean);
        }
      } catch {
        // fall through
      }
    }

    // Fallback: comma-separated list.
    return trimmed
      .split(',')
      .map((s) => s.trim())
      .filter(Boolean);
  }

  return [];
};

const normalizeIndexRecommendation = (rec: any): IndexRecommendation => ({
  ...rec,
  columns: normalizeColumns(rec?.columns),
});

export interface IndexRecommendation {
  id: number;
  connection_id: number;
  table_name: string;
  index_name?: string;
  columns: string[];
  index_type: string;
  recommendation_type: string;
  reason: string;
  schema_name?: string;
  estimated_benefit?: number;
  estimated_cost?: number;
  usage_count: number;
  last_used_at?: string;
  status: string;
  created_at: string;
  applied_at?: string;
  size_bytes?: number;
  scans: number;
}

export interface IndexStatistics {
  total_indexes: number;
  unused_count: number;
  rarely_used_count: number;
  total_size_bytes: number;
  total_size: string;
  indexes: any[];
  unused_indexes: any[];
  rarely_used_indexes: any[];
}

export interface IndexCreateRequest {
  connection_id: number;
  table_name: string;
  index_name: string;
  columns: string[];
  index_type?: string;
  unique?: boolean;
  schema_name?: string;
}

export interface IndexDropRequest {
  connection_id: number;
  table_name: string;
  index_name: string;
  schema_name?: string;
}

export interface IndexAnalysisResponse {
  connection_id: number;
  analysis_type: string;
  results: any;
  analyzed_at: string;
}

/**
 * Get index recommendations for a connection
 */
export const getIndexRecommendations = async (connectionId: number): Promise<IndexRecommendation[]> => {
  try {
    const response = await client.get(`/api/indexes/recommendations/${connectionId}`);
    const data = Array.isArray(response.data) ? response.data : [];
    return data.map(normalizeIndexRecommendation);
  } catch (error) {
    console.error('Error fetching index recommendations:', error);
    throw error;
  }
};

/**
 * Get unused indexes for a connection
 */
export const getUnusedIndexes = async (
  connectionId: number,
  usageThreshold: number = 10
): Promise<any> => {
  try {
    const response = await client.get(`/api/indexes/unused/${connectionId}`, {
      params: { usage_threshold: usageThreshold }
    });
    return response.data;
  } catch (error) {
    console.error('Error fetching unused indexes:', error);
    throw error;
  }
};

/**
 * Get missing index suggestions for a connection
 */
export const getMissingIndexes = async (connectionId: number): Promise<any> => {
  try {
    const response = await client.get(`/api/indexes/missing/${connectionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching missing indexes:', error);
    throw error;
  }
};

/**
 * Get index statistics for a connection
 */
export const getIndexStatistics = async (connectionId: number): Promise<IndexStatistics> => {
  try {
    const response = await client.get(`/api/indexes/statistics/${connectionId}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching index statistics:', error);
    throw error;
  }
};

/**
 * Create a new index
 */
export const createIndex = async (request: IndexCreateRequest): Promise<any> => {
  try {
    const response = await client.post('/api/indexes/create', request);
    return response.data;
  } catch (error) {
    console.error('Error creating index:', error);
    throw error;
  }
};

/**
 * Drop an existing index
 */
export const dropIndex = async (request: IndexDropRequest): Promise<any> => {
  try {
    const response = await client.post('/api/indexes/drop', request);
    return response.data;
  } catch (error) {
    console.error('Error dropping index:', error);
    throw error;
  }
};

/**
 * Get index change history for a connection
 */
export const getIndexHistory = async (
  connectionId: number,
  limit: number = 50
): Promise<any> => {
  try {
    const response = await client.get(`/api/indexes/history/${connectionId}`, {
      params: { limit }
    });
    const data = response.data;
    if (data && Array.isArray(data.changes)) {
      data.changes = data.changes.map(normalizeIndexRecommendation);
    }
    return data;
  } catch (error) {
    console.error('Error fetching index history:', error);
    throw error;
  }
};

/**
 * Perform comprehensive index analysis
 */
export const analyzeIndexUsage = async (connectionId: number): Promise<IndexAnalysisResponse> => {
  try {
    const response = await client.post(`/api/indexes/analyze?connection_id=${connectionId}`);
    return response.data;
  } catch (error) {
    console.error('Error analyzing index usage:', error);
    throw error;
  }
};
