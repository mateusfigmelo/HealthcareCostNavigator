import React, { useState, useCallback, useRef, useEffect } from 'react';
import axios from 'axios';
import { 
  Hospital, 
  AIResponse, 
  HealthStatus, 
  ProviderSearchForm, 
  TextSearchForm, 
  TabType,
  PaginationInfo,
  SearchResult
} from './types';

// Constants for result limiting
const DEFAULT_PAGE_SIZE = 10; // Reduced from 20 to 10
const MAX_PAGE_SIZE = 50; // Reduced from 100 to 50
const SEARCH_DEBOUNCE_MS = 500;
const INFINITE_SCROLL_THRESHOLD = 50; // Reduced from 100 to 50 pixels

// Configure axios base URL for different environments
const getApiBaseUrl = (): string => {
  // In Docker, use the proxy (relative URLs)
  // In development, use localhost
  return window.location.hostname === 'localhost' ? 'http://localhost:8000' : '';
};

axios.defaults.baseURL = getApiBaseUrl();
console.log('API Base URL:', axios.defaults.baseURL);

const App: React.FC = (): JSX.Element => {
  const [activeTab, setActiveTab] = useState<TabType>('providers');
  const [loading, setLoading] = useState<boolean>(false);
  const [loadingMore, setLoadingMore] = useState<boolean>(false);
  const [error, setError] = useState<string>('');
  const [success, setSuccess] = useState<string>('');

  // Provider search state
  const [providerSearch, setProviderSearch] = useState<ProviderSearchForm>({
    drg: '',
    zip_code: '',
    radius_km: '',
    sort_by: 'cost',
    page: 1,
    page_size: DEFAULT_PAGE_SIZE
  });
  const [providerResults, setProviderResults] = useState<SearchResult>({
    hospitals: [],
    total_count: 0
  });
  const [providerHasMore, setProviderHasMore] = useState<boolean>(true);

  // Text search state
  const [textSearch, setTextSearch] = useState<TextSearchForm>({
    q: '',
    zip_code: '',
    radius_km: '',
    page: 1,
    page_size: DEFAULT_PAGE_SIZE
  });
  const [textResults, setTextResults] = useState<SearchResult>({
    hospitals: [],
    total_count: 0
  });
  const [textHasMore, setTextHasMore] = useState<boolean>(true);

  // AI Assistant state
  const [aiQuestion, setAiQuestion] = useState<string>('');
  const [aiResponse, setAiResponse] = useState<AIResponse | null>(null);

  // Health check state
  const [healthStatus, setHealthStatus] = useState<HealthStatus | null>(null);

  // Refs for infinite scrolling
  const providerResultsRef = useRef<HTMLDivElement>(null);
  const textResultsRef = useRef<HTMLDivElement>(null);

  // Debounced search function
  const debouncedSearch = useCallback(
    (searchFunction: () => Promise<void>) => {
      const timeoutId = setTimeout(searchFunction, SEARCH_DEBOUNCE_MS);
      return () => clearTimeout(timeoutId);
    },
    []
  );

  // Infinite scroll handler for provider results
  const handleProviderScroll = useCallback(() => {
    if (!providerResultsRef.current || loadingMore || !providerHasMore) return;

    const { scrollTop, scrollHeight, clientHeight } = providerResultsRef.current;
    if (scrollHeight - scrollTop - clientHeight < INFINITE_SCROLL_THRESHOLD) {
      loadMoreProviderResults();
    }
  }, [loadingMore, providerHasMore]);

  // Infinite scroll handler for text results
  const handleTextScroll = useCallback(() => {
    if (!textResultsRef.current || loadingMore || !textHasMore) return;

    const { scrollTop, scrollHeight, clientHeight } = textResultsRef.current;
    if (scrollHeight - scrollTop - clientHeight < INFINITE_SCROLL_THRESHOLD) {
      loadMoreTextResults();
    }
  }, [loadingMore, textHasMore]);

  // Load more provider results
  const loadMoreProviderResults = async (): Promise<void> => {
    if (loadingMore || !providerHasMore) return;

    setLoadingMore(true);
    try {
      const nextPage = Math.floor(providerResults.hospitals.length / providerSearch.page_size) + 1;
      const params = new URLSearchParams();
      if (providerSearch.drg) params.append('drg', providerSearch.drg);
      if (providerSearch.zip_code) params.append('zip_code', providerSearch.zip_code);
      if (providerSearch.radius_km) params.append('radius_km', providerSearch.radius_km);
      params.append('sort_by', providerSearch.sort_by);
      params.append('page', nextPage.toString());
      params.append('page_size', providerSearch.page_size.toString());

      const response = await axios.get<Hospital[]>(`/providers/?${params.toString()}`);
      const newHospitals = response.data;

      if (newHospitals.length === 0) {
        setProviderHasMore(false);
      } else {
        setProviderResults(prev => ({
          ...prev,
          hospitals: [...prev.hospitals, ...newHospitals],
          total_count: prev.total_count + newHospitals.length
        }));
      }
    } catch (err: any) {
      console.error('Load more provider results error:', err);
      setError('Failed to load more results');
    } finally {
      setLoadingMore(false);
    }
  };

  // Load more text results
  const loadMoreTextResults = async (): Promise<void> => {
    if (loadingMore || !textHasMore) return;

    setLoadingMore(true);
    try {
      const nextPage = Math.floor(textResults.hospitals.length / textSearch.page_size) + 1;
      const params = new URLSearchParams();
      params.append('q', textSearch.q);
      if (textSearch.zip_code) params.append('zip_code', textSearch.zip_code);
      if (textSearch.radius_km) params.append('radius_km', textSearch.radius_km);
      params.append('page', nextPage.toString());
      params.append('page_size', textSearch.page_size.toString());

      const response = await axios.get<Hospital[]>(`/providers/search?${params.toString()}`);
      const newHospitals = response.data;

      if (newHospitals.length === 0) {
        setTextHasMore(false);
      } else {
        setTextResults(prev => ({
          ...prev,
          hospitals: [...prev.hospitals, ...newHospitals],
          total_count: prev.total_count + newHospitals.length
        }));
      }
    } catch (err: any) {
      console.error('Load more text results error:', err);
      setError('Failed to load more results');
    } finally {
      setLoadingMore(false);
    }
  };

  const handleProviderSearch = async (reset: boolean = true): Promise<void> => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    if (reset) {
      setProviderResults({ hospitals: [], total_count: 0 });
      setProviderHasMore(true);
    }
    
    try {
      const params = new URLSearchParams();
      if (providerSearch.drg) params.append('drg', providerSearch.drg);
      if (providerSearch.zip_code) params.append('zip_code', providerSearch.zip_code);
      if (providerSearch.radius_km) params.append('radius_km', providerSearch.radius_km);
      params.append('sort_by', providerSearch.sort_by);
      params.append('page', '1');
      params.append('page_size', providerSearch.page_size.toString());

      console.log('Making provider search request to:', `/providers/?${params.toString()}`);
      const response = await axios.get<Hospital[]>(`/providers/?${params.toString()}`);
      console.log('Provider search response:', response.data);
      
      const hospitals = response.data;
      setProviderResults({
        hospitals,
        total_count: hospitals.length,
        search_time_ms: Date.now(),
        query_info: `DRG: ${providerSearch.drg || 'All'}, Location: ${providerSearch.zip_code || 'All'}`
      });
      
      setProviderHasMore(hospitals.length >= providerSearch.page_size);
      
      if (hospitals.length === 0) {
        setSuccess('No hospitals found matching your criteria');
      } else {
        setSuccess(`Found ${hospitals.length} hospitals (scroll to load more)`);
      }
    } catch (err: any) {
      console.error('Provider search error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to search providers';
      setError(`Provider search failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleTextSearch = async (reset: boolean = true): Promise<void> => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    if (reset) {
      setTextResults({ hospitals: [], total_count: 0 });
      setTextHasMore(true);
    }
    
    try {
      const params = new URLSearchParams();
      params.append('q', textSearch.q);
      if (textSearch.zip_code) params.append('zip_code', textSearch.zip_code);
      if (textSearch.radius_km) params.append('radius_km', textSearch.radius_km);
      params.append('page', '1');
      params.append('page_size', textSearch.page_size.toString());

      console.log('Making text search request to:', `/providers/search?${params.toString()}`);
      const response = await axios.get<Hospital[]>(`/providers/search?${params.toString()}`);
      console.log('Text search response:', response.data);
      
      const hospitals = response.data;
      setTextResults({
        hospitals,
        total_count: hospitals.length,
        search_time_ms: Date.now(),
        query_info: `Search: "${textSearch.q}", Location: ${textSearch.zip_code || 'All'}`
      });
      
      setTextHasMore(hospitals.length >= textSearch.page_size);
      
      if (hospitals.length === 0) {
        setSuccess('No hospitals found matching your search');
      } else {
        setSuccess(`Found ${hospitals.length} hospitals (scroll to load more)`);
      }
    } catch (err: any) {
      console.error('Text search error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to search by text';
      setError(`Text search failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleAiQuestion = async (): Promise<void> => {
    if (!aiQuestion.trim()) {
      setError('Please enter a question');
      return;
    }

    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      console.log('Making AI request to:', '/ask/', { question: aiQuestion });
      const response = await axios.post<AIResponse>('/ask/', {
        question: aiQuestion
      });
      console.log('AI response:', response.data);
      setAiResponse(response.data);
      setSuccess('AI response received');
    } catch (err: any) {
      console.error('AI request error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'Failed to get AI response';
      setError(`AI request failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  const handleHealthCheck = async (): Promise<void> => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      console.log('Making health check request to:', '/health');
      const response = await axios.get<HealthStatus>('/health');
      console.log('Health check response:', response.data);
      setHealthStatus(response.data);
      setSuccess('Health check completed');
    } catch (err: any) {
      console.error('Health check error:', err);
      const errorMessage = err.message || 'Health check failed';
      setError(`Health check failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  // Debug function to test API connectivity
  const testApiConnection = async (): Promise<void> => {
    setLoading(true);
    setError('');
    setSuccess('');
    
    try {
      console.log('Testing API connection...');
      
      // Test 1: Health endpoint
      console.log('Testing health endpoint...');
      const healthResponse = await axios.get('/health');
      console.log('Health response:', healthResponse.data);
      
      // Test 2: Root endpoint
      console.log('Testing root endpoint...');
      const rootResponse = await axios.get('/');
      console.log('Root response:', rootResponse.data);
      
      // Test 3: Simple provider search
      console.log('Testing provider search...');
      const providerResponse = await axios.get('/providers/?drg=291&sort_by=cost&page_size=5');
      console.log('Provider response:', providerResponse.data);
      
      setSuccess('All API tests passed! Check console for details.');
    } catch (err: any) {
      console.error('API test error:', err);
      const errorMessage = err.response?.data?.detail || err.message || 'API test failed';
      setError(`API test failed: ${errorMessage}`);
    } finally {
      setLoading(false);
    }
  };

  // Pagination handlers (now using infinite scroll instead)
  const handleProviderPageChange = (newPage: number) => {
    setProviderSearch(prev => ({ ...prev, page: newPage }));
    handleProviderSearch(true); // Reset results and hasMore
  };

  const handleTextPageChange = (newPage: number) => {
    setTextSearch(prev => ({ ...prev, page: newPage }));
    handleTextSearch(true); // Reset results and hasMore
  };

  // Page size handlers
  const handleProviderPageSizeChange = (newPageSize: number) => {
    setProviderSearch(prev => ({ ...prev, page_size: newPageSize, page: 1 }));
    handleProviderSearch(true); // Reset results and hasMore
  };

  const handleTextPageSizeChange = (newPageSize: number) => {
    setTextSearch(prev => ({ ...prev, page_size: newPageSize, page: 1 }));
    handleTextSearch(true); // Reset results and hasMore
  };

  // Render pagination controls
  const renderPagination = (
    currentPage: number,
    pageSize: number,
    totalResults: number,
    onPageChange: (page: number) => void,
    onPageSizeChange: (pageSize: number) => void
  ): JSX.Element | null => {
    if (totalResults === 0) return null;

    const totalPages = Math.ceil(totalResults / pageSize);
    const startResult = (currentPage - 1) * pageSize + 1;
    const endResult = Math.min(currentPage * pageSize, totalResults);

    return (
      <div className="mt-6 p-4 bg-gray-50 rounded-lg">
        <div className="flex flex-col sm:flex-row justify-between items-center space-y-4 sm:space-y-0">
          {/* Results info */}
          <div className="text-sm text-gray-600">
            Showing {startResult}-{endResult} of {totalResults} results
          </div>

          {/* Page size selector */}
          <div className="flex items-center space-x-2">
            <label className="text-sm text-gray-600">Show:</label>
            <select
              className="border border-gray-300 rounded px-2 py-1 text-sm"
              value={pageSize}
              onChange={(e) => onPageSizeChange(Number(e.target.value))}
            >
              <option value={5}>5</option>
              <option value={10}>10</option>
              <option value={20}>20</option>
              <option value={50}>50</option>
            </select>
            <span className="text-sm text-gray-600">per page</span>
          </div>

          {/* Pagination buttons */}
          <div className="flex items-center space-x-2">
            <button
              className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              onClick={() => onPageChange(currentPage - 1)}
              disabled={currentPage <= 1}
            >
              Previous
            </button>
            
            <span className="text-sm text-gray-600">
              Page {currentPage} of {totalPages}
            </span>
            
            <button
              className="px-3 py-1 text-sm border border-gray-300 rounded disabled:opacity-50 disabled:cursor-not-allowed hover:bg-gray-50"
              onClick={() => onPageChange(currentPage + 1)}
              disabled={currentPage >= totalPages}
            >
              Next
            </button>
          </div>
        </div>
      </div>
    );
  };

  // Render loading skeleton for hospital results
  const renderLoadingSkeleton = (count: number = 3): JSX.Element => {
    return (
      <div className="space-y-4">
        {Array.from({ length: count }).map((_, index) => (
          <div key={index} className="bg-gray-50 border border-gray-200 rounded-lg p-6 animate-pulse">
            <div className="h-6 bg-gray-200 rounded mb-3 w-3/4"></div>
            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
              {Array.from({ length: 6 }).map((_, i) => (
                <div key={i} className="h-4 bg-gray-200 rounded w-full"></div>
              ))}
            </div>
          </div>
        ))}
      </div>
    );
  };

  // Render error state
  const renderErrorState = (error: string): JSX.Element => {
    return (
      <div className="mt-8">
        <div className="bg-red-50 border border-red-200 rounded-lg p-6">
          <div className="flex items-center">
            <div className="flex-shrink-0">
              <svg className="h-5 w-5 text-red-400" viewBox="0 0 20 20" fill="currentColor">
                <path fillRule="evenodd" d="M10 18a8 8 0 100-16 8 8 0 000 16zM8.707 7.293a1 1 0 00-1.414 1.414L8.586 10l-1.293 1.293a1 1 0 101.414 1.414L10 11.414l1.293 1.293a1 1 0 001.414-1.414L11.414 10l1.293-1.293a1 1 0 00-1.414-1.414L10 8.586 8.707 7.293z" clipRule="evenodd" />
              </svg>
            </div>
            <div className="ml-3">
              <h3 className="text-sm font-medium text-red-800">Error occurred</h3>
              <div className="mt-2 text-sm text-red-700">
                <p>{error}</p>
              </div>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Render empty state
  const renderEmptyState = (message: string): JSX.Element => {
    return (
      <div className="mt-8">
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-8 text-center">
          <div className="mx-auto h-12 w-12 text-gray-400">
            <svg fill="none" viewBox="0 0 24 24" stroke="currentColor">
              <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M9.172 16.172a4 4 0 015.656 0M9 12h6m-6-4h6m2 5.291A7.962 7.962 0 0112 15c-2.34 0-4.47-.881-6.08-2.33" />
            </svg>
          </div>
          <h3 className="mt-2 text-sm font-medium text-gray-900">No results found</h3>
          <p className="mt-1 text-sm text-gray-500">{message}</p>
        </div>
      </div>
    );
  };

  // Render warning for large result sets
  const renderLargeResultWarning = (count: number): JSX.Element | null => {
    if (count < 100) return null;
    
    return (
      <div className="mb-4 p-4 bg-yellow-50 border border-yellow-200 rounded-lg">
        <div className="flex items-center">
          <div className="flex-shrink-0">
            <svg className="h-5 w-5 text-yellow-400" viewBox="0 0 20 20" fill="currentColor">
              <path fillRule="evenodd" d="M8.257 3.099c.765-1.36 2.722-1.36 3.486 0l5.58 9.92c.75 1.334-.213 2.98-1.742 2.98H4.42c-1.53 0-2.493-1.646-1.743-2.98l5.58-9.92zM11 13a1 1 0 11-2 0 1 1 0 012 0zm-1-8a1 1 0 00-1 1v3a1 1 0 002 0V6a1 1 0 00-1-1z" clipRule="evenodd" />
            </svg>
          </div>
          <div className="ml-3">
            <h3 className="text-sm font-medium text-yellow-800">Large result set</h3>
            <div className="mt-2 text-sm text-yellow-700">
              <p>Found {count} results. Consider adding more specific filters to narrow down your search.</p>
            </div>
          </div>
        </div>
      </div>
    );
  };

  // Add scroll event listeners
  useEffect(() => {
    const providerElement = providerResultsRef.current;
    const textElement = textResultsRef.current;

    if (providerElement) {
      providerElement.addEventListener('scroll', handleProviderScroll);
    }
    if (textElement) {
      textElement.addEventListener('scroll', handleTextScroll);
    }

    return () => {
      if (providerElement) {
        providerElement.removeEventListener('scroll', handleProviderScroll);
      }
      if (textElement) {
        textElement.removeEventListener('scroll', handleTextScroll);
      }
    };
  }, [handleProviderScroll, handleTextScroll]);

  // Render infinite scroll loading indicator
  const renderInfiniteScrollLoader = (): JSX.Element | null => {
    if (!loadingMore) return null;

    return (
      <div className="flex justify-center items-center py-4">
        <div className="animate-spin rounded-full h-8 w-8 border-b-2 border-primary-600"></div>
        <span className="ml-2 text-gray-600">Loading more results...</span>
      </div>
    );
  };

  // Render end of results indicator
  const renderEndOfResults = (): JSX.Element | null => {
    if (loadingMore || (providerHasMore && textHasMore)) return null;

    return (
      <div className="text-center py-4 text-gray-500">
        <p>No more results to load</p>
      </div>
    );
  };

  const renderProviderResults = (): JSX.Element | null => {
    if (loading) {
      return (
        <div className="mt-8">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Search Results</h3>
          {renderLoadingSkeleton(5)}
        </div>
      );
    }

    if (error) {
      return renderErrorState(error);
    }

    if (providerResults.hospitals.length === 0) {
      return renderEmptyState("No hospitals found matching your criteria. Try adjusting your search parameters.");
    }

    return (
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-800">
            Search Results ({providerResults.total_count} hospitals loaded)
          </h3>
          {providerResults.search_time_ms && (
            <span className="text-sm text-gray-500">
              Search completed in {Date.now() - providerResults.search_time_ms}ms
            </span>
          )}
        </div>
        
        {providerResults.query_info && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Query:</strong> {providerResults.query_info}
            </p>
          </div>
        )}

        {/* Large result warning */}
        {renderLargeResultWarning(providerResults.total_count)}

        <div 
          className="space-y-4 max-h-80 overflow-y-auto" 
          ref={providerResultsRef}
          style={{ scrollBehavior: 'smooth' }}
        >
          {providerResults.hospitals.map((hospital, index) => (
            <div key={`${hospital.provider_id}-${index}`} className="bg-gray-50 border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">{hospital.provider_name}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4 text-sm">
                <p><span className="font-medium text-gray-600">Location:</span> {hospital.provider_city}, {hospital.provider_state} {hospital.provider_zip_code}</p>
                <p><span className="font-medium text-gray-600">DRG Code:</span> {hospital.ms_drg_code}</p>
                <p><span className="font-medium text-gray-600">Procedure:</span> {hospital.ms_drg_definition}</p>
                <p><span className="font-medium text-gray-600">Average Covered Charges:</span> ${hospital.average_covered_charges?.toLocaleString() || 'N/A'}</p>
                <p><span className="font-medium text-gray-600">Average Total Payments:</span> ${hospital.average_total_payments?.toLocaleString() || 'N/A'}</p>
                <p><span className="font-medium text-gray-600">Average Medicare Payments:</span> ${hospital.average_medicare_payments?.toLocaleString() || 'N/A'}</p>
                <p><span className="font-medium text-gray-600">Total Discharges:</span> {hospital.total_discharges || 'N/A'}</p>
                <p><span className="font-medium text-gray-600">Rating:</span> {hospital.average_rating || hospital.rating || 'N/A'}/10</p>
              </div>
            </div>
          ))}
          
          {/* Infinite scroll loading indicator */}
          {renderInfiniteScrollLoader()}
          
          {/* End of results indicator */}
          {!providerHasMore && providerResults.hospitals.length > 0 && renderEndOfResults()}
        </div>

        {/* Load more button for manual loading */}
        {providerHasMore && !loadingMore && (
          <div className="mt-4 text-center">
            <button
              className="btn-secondary"
              onClick={loadMoreProviderResults}
              disabled={loadingMore}
            >
              Load More Results
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderTextResults = (): JSX.Element | null => {
    if (loading) {
      return (
        <div className="mt-8">
          <h3 className="text-xl font-semibold text-gray-800 mb-4">Search Results</h3>
          {renderLoadingSkeleton(5)}
        </div>
      );
    }

    if (error) {
      return renderErrorState(error);
    }

    if (textResults.hospitals.length === 0) {
      return renderEmptyState("No hospitals found matching your search. Try different keywords or location.");
    }

    return (
      <div className="mt-8">
        <div className="flex justify-between items-center mb-4">
          <h3 className="text-xl font-semibold text-gray-800">
            Search Results ({textResults.total_count} hospitals loaded)
          </h3>
          {textResults.search_time_ms && (
            <span className="text-sm text-gray-500">
              Search completed in {Date.now() - textResults.search_time_ms}ms
            </span>
          )}
        </div>
        
        {textResults.query_info && (
          <div className="mb-4 p-3 bg-blue-50 border border-blue-200 rounded-lg">
            <p className="text-sm text-blue-800">
              <strong>Query:</strong> {textResults.query_info}
            </p>
          </div>
        )}

        {/* Large result warning */}
        {renderLargeResultWarning(textResults.total_count)}

        <div 
          className="space-y-4 max-h-80 overflow-y-auto" 
          ref={textResultsRef}
          style={{ scrollBehavior: 'smooth' }}
        >
          {textResults.hospitals.map((hospital, index) => (
            <div key={`${hospital.provider_id}-${index}`} className="bg-gray-50 border border-gray-200 rounded-lg p-6 hover:shadow-md transition-shadow">
              <h3 className="text-lg font-semibold text-gray-800 mb-3">{hospital.provider_name}</h3>
              <div className="grid grid-cols-1 md:grid-cols-2 gap-4 text-sm">
                <p><span className="font-medium text-gray-600">Location:</span> {hospital.provider_city}, {hospital.provider_state} {hospital.provider_zip_code}</p>
                <p><span className="font-medium text-gray-600">DRG Code:</span> {hospital.ms_drg_code}</p>
                <p><span className="font-medium text-gray-600">Procedure:</span> {hospital.ms_drg_definition}</p>
                <p><span className="font-medium text-gray-600">Average Covered Charges:</span> ${hospital.average_covered_charges?.toLocaleString() || 'N/A'}</p>
                <p><span className="font-medium text-gray-600">Rating:</span> {hospital.average_rating || hospital.rating || 'N/A'}/10</p>
              </div>
            </div>
          ))}
          
          {/* Infinite scroll loading indicator */}
          {renderInfiniteScrollLoader()}
          
          {/* End of results indicator */}
          {!textHasMore && textResults.hospitals.length > 0 && renderEndOfResults()}
        </div>

        {/* Load more button for manual loading */}
        {textHasMore && !loadingMore && (
          <div className="mt-4 text-center">
            <button
              className="btn-secondary"
              onClick={loadMoreTextResults}
              disabled={loadingMore}
            >
              Load More Results
            </button>
          </div>
        )}
      </div>
    );
  };

  const renderAiResponse = (): JSX.Element | null => {
    if (!aiResponse) return null;

    return (
      <div className="mt-8">
        <h3 className="text-xl font-semibold text-gray-800 mb-4">AI Assistant Response</h3>
        <div className="bg-gray-50 border border-gray-200 rounded-lg p-6">
          <h4 className="font-semibold text-gray-800 mb-3">Answer:</h4>
          <p className="text-gray-700 mb-4">{aiResponse.answer}</p>
          
          {aiResponse.out_of_scope && (
            <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-4">
              <strong>Note:</strong> This question is outside the scope of healthcare pricing and quality information.
            </div>
          )}
          
          {aiResponse.sql_query && (
            <div className="mb-4">
              <h4 className="font-semibold text-gray-800 mb-2">Generated SQL Query:</h4>
              <pre className="bg-gray-800 text-green-400 p-4 rounded-lg overflow-x-auto text-sm">
                {aiResponse.sql_query}
              </pre>
            </div>
          )}
          
          {aiResponse.results && aiResponse.results.length > 0 && (
            <div>
              <h4 className="font-semibold text-gray-800 mb-3">Results ({aiResponse.results.length} hospitals):</h4>
              <div className="space-y-3">
                {aiResponse.results.map((hospital, index) => (
                  <div key={`${hospital.provider_id}-${index}`} className="bg-white border border-gray-200 rounded-lg p-4">
                    <p className="font-semibold text-gray-800">{hospital.provider_name}</p>
                    <p className="text-gray-600">Location: {hospital.provider_city}, {hospital.provider_state}</p>
                    {hospital.average_covered_charges && (
                      <p className="text-gray-600">Average Cost: ${hospital.average_covered_charges.toLocaleString()}</p>
                    )}
                    {hospital.rating && (
                      <p className="text-gray-600">Rating: {hospital.rating}/10</p>
                    )}
                  </div>
                ))}
              </div>
            </div>
          )}
        </div>
      </div>
    );
  };

  const tabs: { id: TabType; label: string; icon: string }[] = [
    { id: 'providers', label: 'Provider Search', icon: '🔍' },
    { id: 'text', label: 'Text Search', icon: '📝' },
    { id: 'ai', label: 'AI Assistant', icon: '🤖' },
    { id: 'health', label: 'Health Check', icon: '💚' }
  ];

  return (
    <div className="min-h-screen bg-gradient-to-br from-blue-50 via-indigo-50 to-purple-50">
      <div className="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 py-8">
        {/* Header */}
        <div className="text-center mb-12">
          <h1 className="text-4xl md:text-5xl font-bold text-gray-900 mb-4">
            🏥 Healthcare Cost Navigator
          </h1>
          <p className="text-xl text-gray-600 max-w-3xl mx-auto">
            Find hospitals, compare costs, and get AI-powered insights for medical procedures
          </p>
        </div>

        {/* Tabs */}
        <div className="bg-white rounded-2xl shadow-lg p-2 mb-8">
          <div className="flex flex-col sm:flex-row">
            {tabs.map((tab) => (
              <button
                key={tab.id}
                className={`tab ${activeTab === tab.id ? 'active' : ''}`}
                onClick={() => setActiveTab(tab.id)}
              >
                <span className="mr-2">{tab.icon}</span>
                {tab.label}
              </button>
            ))}
          </div>
        </div>

        {/* Messages */}
        {error && (
          <div className="bg-red-50 border border-red-200 text-red-700 px-4 py-3 rounded-lg mb-6">
            {error}
          </div>
        )}
        {success && (
          <div className="bg-green-50 border border-green-200 text-green-700 px-4 py-3 rounded-lg mb-6">
            {success}
          </div>
        )}

        {/* Tab Content */}
        <div className="space-y-8">
          {/* Provider Search Tab */}
          {activeTab === 'providers' && (
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b-2 border-primary-500 pb-3">
                🔍 Search Hospitals by DRG Code
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    DRG Code (e.g., 291, 193, 280):
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={providerSearch.drg}
                    onChange={(e) => setProviderSearch({...providerSearch, drg: e.target.value})}
                    placeholder="Enter DRG code"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ZIP Code (e.g., 36301, 36401):
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={providerSearch.zip_code}
                    onChange={(e) => setProviderSearch({...providerSearch, zip_code: e.target.value})}
                    placeholder="Enter ZIP code"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Radius (km):
                  </label>
                  <input
                    type="number"
                    className="input-field"
                    value={providerSearch.radius_km}
                    onChange={(e) => setProviderSearch({...providerSearch, radius_km: e.target.value})}
                    placeholder="Enter radius in km"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Sort By:
                  </label>
                  <select
                    className="input-field"
                    value={providerSearch.sort_by}
                    onChange={(e) => setProviderSearch({...providerSearch, sort_by: e.target.value as 'cost' | 'rating'})}
                  >
                    <option value="cost">Cost (Lowest First)</option>
                    <option value="rating">Rating (Highest First)</option>
                  </select>
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={() => handleProviderSearch(true)}
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search Hospitals'}
              </button>
              {renderProviderResults()}
            </div>
          )}

          {/* Text Search Tab */}
          {activeTab === 'text' && (
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b-2 border-primary-500 pb-3">
                📝 Search by Text Description
              </h2>
              <div className="grid grid-cols-1 md:grid-cols-3 gap-6 mb-6">
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Search Text:
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={textSearch.q}
                    onChange={(e) => setTextSearch({...textSearch, q: e.target.value})}
                    placeholder="e.g., heart failure, pneumonia, joint replacement"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    ZIP Code:
                  </label>
                  <input
                    type="text"
                    className="input-field"
                    value={textSearch.zip_code}
                    onChange={(e) => setTextSearch({...textSearch, zip_code: e.target.value})}
                    placeholder="Enter ZIP code"
                  />
                </div>
                <div>
                  <label className="block text-sm font-medium text-gray-700 mb-2">
                    Radius (km):
                  </label>
                  <input
                    type="number"
                    className="input-field"
                    value={textSearch.radius_km}
                    onChange={(e) => setTextSearch({...textSearch, radius_km: e.target.value})}
                    placeholder="Enter radius in km"
                  />
                </div>
              </div>
              <button 
                className="btn-primary"
                onClick={() => handleTextSearch(true)}
                disabled={loading}
              >
                {loading ? 'Searching...' : 'Search by Text'}
              </button>
              {renderTextResults()}
            </div>
          )}

          {/* AI Assistant Tab */}
          {activeTab === 'ai' && (
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b-2 border-primary-500 pb-3">
                🤖 AI Assistant
              </h2>
              <p className="text-gray-600 mb-6">
                Ask natural language questions about hospital pricing and quality. Examples:
              </p>
              <div className="bg-blue-50 border border-blue-200 rounded-lg p-4 mb-6">
                <p className="font-medium text-blue-800 mb-2">Examples:</p>
                <ul className="text-blue-700 space-y-1 ml-4">
                  <li>• "Who is cheapest for DRG 291 within 25 miles of 36301?"</li>
                  <li>• "What hospitals have the best ratings for heart failure near 36401?"</li>
                  <li>• "What is the average cost of pneumonia treatment in Alabama?"</li>
                  <li>• "Show me top 3 hospitals by rating for DRG 193 within 50 km of 36301"</li>
                </ul>
              </div>
              <div className="mb-6">
                <label className="block text-sm font-medium text-gray-700 mb-2">
                  Your Question:
                </label>
                <textarea
                  className="input-field"
                  value={aiQuestion}
                  onChange={(e) => setAiQuestion(e.target.value)}
                  placeholder="Ask about hospital pricing, quality, or procedures..."
                  rows={4}
                />
              </div>
              <button 
                className="btn-success"
                onClick={handleAiQuestion}
                disabled={loading}
              >
                {loading ? 'Processing...' : 'Ask AI Assistant'}
              </button>
              {renderAiResponse()}
            </div>
          )}

          {/* Health Check Tab */}
          {activeTab === 'health' && (
            <div className="card">
              <h2 className="text-2xl font-bold text-gray-800 mb-6 border-b-2 border-primary-500 pb-3">
                💚 API Health Check
              </h2>
              <p className="text-gray-600 mb-6">
                Check if the backend API is running and healthy.
              </p>
              <div className="space-x-4">
                <button 
                  className="btn-secondary"
                  onClick={handleHealthCheck}
                  disabled={loading}
                >
                  {loading ? 'Checking...' : 'Check API Health'}
                </button>
                <button 
                  className="bg-yellow-600 hover:bg-yellow-700 text-white font-semibold py-3 px-6 rounded-lg transition-all duration-200 transform hover:scale-105 hover:shadow-lg focus:outline-none focus:ring-2 focus:ring-yellow-500 focus:ring-offset-2"
                  onClick={testApiConnection}
                  disabled={loading}
                >
                  {loading ? 'Testing...' : 'Debug API Connection'}
                </button>
              </div>
              {healthStatus && (
                <div className="mt-8">
                  <h3 className="text-xl font-semibold text-gray-800 mb-4">Health Status</h3>
                  <div className="bg-green-50 border border-green-200 rounded-lg p-6">
                    <p className="text-green-800"><span className="font-medium">Status:</span> {healthStatus.status}</p>
                    <p className="text-green-800"><span className="font-medium">Service:</span> {healthStatus.service}</p>
                  </div>
                </div>
              )}
            </div>
          )}
        </div>

        {/* Loading Overlay */}
        {loading && (
          <div className="fixed inset-0 bg-black bg-opacity-50 flex items-center justify-center z-50">
            <div className="bg-white rounded-lg p-8 text-center">
              <div className="animate-spin rounded-full h-12 w-12 border-b-2 border-primary-600 mx-auto mb-4"></div>
              <p className="text-gray-600">Loading...</p>
            </div>
          </div>
        )}
      </div>
    </div>
  );
};

export default App; 
