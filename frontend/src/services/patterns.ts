/**
 * Pattern Library API Service
 * Handles all pattern-related API calls
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

export interface Pattern {
  id: number;
  pattern_type: string;
  pattern_signature: string;
  original_pattern: string;
  optimized_pattern: string;
  success_rate: number;
  avg_improvement_pct: number;
  times_applied: number;
  times_successful: number;
  database_type: string;
  category?: string;
  created_at: string;
  updated_at: string;
  description?: string;
}

export interface PatternStatistics {
  total_patterns: number;
  by_database: Record<string, number>;
  by_category: Record<string, number>;
  avg_success_rate: number;
  total_applications: number;
  total_successful: number;
  overall_success_rate: number;
}

export interface PatternCategory {
  name: string;
  display_name: string;
  count: number;
  avg_success_rate: number;
  description: string;
}

export interface PatternFilters {
  database_type?: string;
  pattern_type?: string;
  category?: string;
  min_success_rate?: number;
  min_applications?: number;
  sort_by?: string;
  limit?: number;
  offset?: number;
}

/**
 * Get all patterns with optional filters
 */
export const getAllPatterns = async (filters?: PatternFilters): Promise<Pattern[]> => {
  try {
    const params = new URLSearchParams();
    
    if (filters?.database_type) params.append('database_type', filters.database_type);
    if (filters?.pattern_type) params.append('pattern_type', filters.pattern_type);
    if (filters?.category) params.append('category', filters.category);
    if (filters?.min_success_rate !== undefined) params.append('min_success_rate', filters.min_success_rate.toString());
    if (filters?.min_applications !== undefined) params.append('min_applications', filters.min_applications.toString());
    if (filters?.sort_by) params.append('sort_by', filters.sort_by);
    if (filters?.limit) params.append('limit', filters.limit.toString());
    if (filters?.offset) params.append('offset', filters.offset.toString());
    
    const response = await client.get(`/api/patterns?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching patterns:', error);
    throw error;
  }
};

/**
 * Get pattern by ID
 */
export const getPatternById = async (patternId: number): Promise<Pattern> => {
  try {
    const response = await client.get(`/api/patterns/${patternId}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching pattern ${patternId}:`, error);
    throw error;
  }
};

/**
 * Search patterns
 */
export const searchPatterns = async (
  query: string,
  filters?: Omit<PatternFilters, 'sort_by' | 'limit' | 'offset'>
): Promise<Pattern[]> => {
  try {
    const params = new URLSearchParams({ q: query });
    
    if (filters?.database_type) params.append('database_type', filters.database_type);
    if (filters?.category) params.append('category', filters.category);
    
    const response = await client.get(`/api/patterns/search/query?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error searching patterns:', error);
    throw error;
  }
};

/**
 * Get all pattern categories
 */
export const getCategories = async (): Promise<PatternCategory[]> => {
  try {
    const response = await client.get('/api/patterns/categories/list');
    return response.data;
  } catch (error) {
    console.error('Error fetching categories:', error);
    throw error;
  }
};

/**
 * Get patterns by category
 */
export const getPatternsByCategory = async (
  category: string,
  databaseType?: string,
  limit?: number
): Promise<Pattern[]> => {
  try {
    const params = new URLSearchParams();
    if (databaseType) params.append('database_type', databaseType);
    if (limit) params.append('limit', limit.toString());
    
    const response = await client.get(`/api/patterns/category/${category}?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error(`Error fetching patterns for category ${category}:`, error);
    throw error;
  }
};

/**
 * Get pattern statistics
 */
export const getStatistics = async (): Promise<PatternStatistics> => {
  try {
    const response = await client.get('/api/patterns/statistics/overview');
    return response.data;
  } catch (error) {
    console.error('Error fetching pattern statistics:', error);
    throw error;
  }
};

/**
 * Get top performing patterns
 */
export const getTopPatterns = async (
  limit: number = 10,
  databaseType?: string
): Promise<Pattern[]> => {
  try {
    const params = new URLSearchParams({ limit: limit.toString() });
    if (databaseType) params.append('database_type', databaseType);
    
    const response = await client.get(`/api/patterns/top/performers?${params.toString()}`);
    return response.data;
  } catch (error) {
    console.error('Error fetching top patterns:', error);
    throw error;
  }
};

/**
 * Load common patterns into the library
 */
export const loadCommonPatterns = async (): Promise<{ success: boolean; patterns_loaded: number; message: string }> => {
  try {
    const response = await client.post('/api/patterns/load-common');
    return response.data;
  } catch (error) {
    console.error('Error loading common patterns:', error);
    throw error;
  }
};
