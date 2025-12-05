/**
 * API client for marketplace
 */

import { API_BASE_URL } from '../config';

export interface MarketplaceListing {
  id: string;
  name: string;
  description?: string;
  author_name?: string;
  clone_count: number;
  average_rating: number;
  rating_count: number;
  created_at: string;
  category?: string;
  tags?: string[];
  rating?: number;
  downloads?: number;
  featured?: boolean;
  source?: string;
}

export interface MarketplaceSearchResponse {
  blueprints: MarketplaceListing[];  // API returns 'blueprints' not 'listings'
  total: number;
  page: number;
  page_size: number;
  total_pages: number;
}

/**
 * Search marketplace blueprints
 */
export async function searchMarketplace(
  query?: string,
  page: number = 1,
  pageSize: number = 20
): Promise<MarketplaceSearchResponse> {
  const params = new URLSearchParams({
    page: page.toString(),
    page_size: pageSize.toString(),
  });

  if (query) {
    params.append('q', query);
  }

  const response = await fetch(`${API_BASE_URL}/api/marketplace?${params}`);

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to search marketplace');
  }

  return response.json();
}

/**
 * Publish a blueprint to the marketplace
 */
export async function publishBlueprint(token: string, blueprintId: string): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/marketplace/publish`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ blueprint_id: blueprintId }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to publish blueprint');
  }
}

/**
 * Clone a marketplace blueprint
 */
export async function cloneBlueprint(token: string, blueprintId: string): Promise<any> {
  const response = await fetch(`${API_BASE_URL}/api/marketplace/blueprints/${blueprintId}/clone`, {
    method: 'POST',
    headers: {
      'Authorization': `Bearer ${token}`,
    },
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to clone blueprint');
  }

  return response.json();
}

/**
 * Rate a marketplace blueprint
 */
export async function rateBlueprint(
  token: string,
  blueprintId: string,
  rating: number
): Promise<void> {
  const response = await fetch(`${API_BASE_URL}/api/marketplace/blueprints/${blueprintId}/rate`, {
    method: 'POST',
    headers: {
      'Content-Type': 'application/json',
      'Authorization': `Bearer ${token}`,
    },
    body: JSON.stringify({ rating }),
  });

  if (!response.ok) {
    const error = await response.json().catch(() => ({ detail: response.statusText }));
    throw new Error(error.detail || 'Failed to rate blueprint');
  }
}
