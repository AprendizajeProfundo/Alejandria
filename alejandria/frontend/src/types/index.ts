export interface SearchResult {
  title: string;
  link: string;
  description: string;
  type: 'academic' | 'blog' | 'code';
  relevance: number;
  visualizations: {
    type: string;
    data: {
      labels: string[];
      datasets: {
        data: number[];
        backgroundColor: string[];
      }[];
    };
  }[];
}

export interface WebSocketMessage {
  type: string;
  result?: SearchResult;
}

export interface SearchState {
  query: string;
  results: SearchResult[];
  loading: boolean;
  activeTab: string;
}
