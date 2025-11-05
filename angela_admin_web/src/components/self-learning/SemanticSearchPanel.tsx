import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Search, Sparkles, ArrowRight, TrendingUp, BookOpen } from 'lucide-react';

interface SearchResult {
  knowledge_nodes: Array<{
    id: string;
    name: string;
    category: string | null;
    understanding: string | null;
    level: number;
    references: number;
    similarity: number;
    type: string;
  }>;
  learnings: Array<{
    id: string;
    topic: string;
    category: string | null;
    insight: string;
    confidence: number;
    reinforced: number;
    applied: boolean;
    similarity: number;
    type: string;
  }>;
  related_concepts: Array<{
    id: string;
    name: string;
    category: string | null;
    relationship: string;
    strength: number;
  }>;
}

export default function SemanticSearchPanel() {
  const [query, setQuery] = useState('');
  const [results, setResults] = useState<SearchResult | null>(null);
  const [loading, setLoading] = useState(false);
  const [searched, setSearched] = useState(false);

  const handleSearch = async () => {
    if (!query.trim()) return;

    setLoading(true);
    setSearched(true);

    try {
      const res = await fetch(
        `http://localhost:50001/api/second-brain/semantic-search/vector?query=${encodeURIComponent(query)}&limit=10`,
        { method: 'POST' }
      );
      const data = await res.json();
      setResults(data);
    } catch (error) {
      console.error('Search error:', error);
    } finally {
      setLoading(false);
    }
  };

  const getSimilarityColor = (similarity: number) => {
    if (similarity >= 0.9) return 'bg-green-600 text-white';
    if (similarity >= 0.7) return 'bg-blue-600 text-white';
    if (similarity >= 0.5) return 'bg-yellow-600 text-white';
    return 'bg-gray-600 text-white';
  };

  const getSimilarityLabel = (similarity: number) => {
    if (similarity >= 0.9) return 'Exact Match';
    if (similarity >= 0.7) return 'High Match';
    if (similarity >= 0.5) return 'Good Match';
    return 'Partial Match';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Sparkles className="w-5 h-5 text-purple-500" />
          <CardTitle>Semantic Search</CardTitle>
          <Badge variant="outline" className="ml-2">AI-Powered</Badge>
        </div>
      </CardHeader>
      <CardContent>
        {/* Search Bar */}
        <div className="flex gap-2 mb-6">
          <div className="flex-1 relative">
            <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400" />
            <input
              type="text"
              value={query}
              onChange={(e) => setQuery(e.target.value)}
              onKeyPress={(e) => e.key === 'Enter' && handleSearch()}
              placeholder="Search knowledge and learnings... (e.g., 'database', 'FastAPI', 'memory')"
              className="w-full pl-10 pr-4 py-3 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-purple-500 dark:bg-gray-800 dark:text-gray-100"
              disabled={loading}
            />
          </div>
          <button
            onClick={handleSearch}
            disabled={loading || !query.trim()}
            className="px-8 py-3 bg-gradient-to-r from-purple-600 to-blue-600 text-white rounded-lg hover:from-purple-700 hover:to-blue-700 transition disabled:opacity-50 disabled:cursor-not-allowed font-medium"
          >
            {loading ? 'Searching...' : 'Search'}
          </button>
        </div>

        {/* Results */}
        {searched && results && (
          <div className="space-y-6">
            {/* Summary */}
            <div className="flex items-center justify-between p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                Found <strong>{results.knowledge_nodes.length + results.learnings.length}</strong> results
                for "<strong>{query}</strong>"
              </p>
              {results.related_concepts.length > 0 && (
                <Badge className="bg-blue-600 text-white">
                  +{results.related_concepts.length} related
                </Badge>
              )}
            </div>

            {/* Knowledge Nodes */}
            {results.knowledge_nodes.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-900 dark:text-gray-100">
                  <BookOpen className="w-5 h-5 text-purple-600" />
                  Knowledge Nodes
                  <Badge variant="outline">{results.knowledge_nodes.length}</Badge>
                </h3>
                <div className="space-y-3">
                  {results.knowledge_nodes.map((node) => (
                    <div
                      key={node.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                            {node.name}
                          </h4>
                          <div className="flex items-center gap-2">
                            {node.category && (
                              <Badge variant="secondary">{node.category}</Badge>
                            )}
                            <Badge className={getSimilarityColor(node.similarity)}>
                              {(node.similarity * 100).toFixed(0)}% - {getSimilarityLabel(node.similarity)}
                            </Badge>
                            <Badge variant="outline">
                              {node.references} refs
                            </Badge>
                          </div>
                        </div>
                      </div>
                      {node.understanding && (
                        <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                          {node.understanding.length > 200
                            ? node.understanding.substring(0, 200) + '...'
                            : node.understanding}
                        </p>
                      )}
                      <div className="mt-2 flex items-center gap-2">
                        <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                          <div
                            className="bg-purple-600 h-2 rounded-full"
                            style={{ width: `${node.level * 100}%` }}
                          ></div>
                        </div>
                        <span className="text-xs text-gray-600 dark:text-gray-400">
                          {(node.level * 100).toFixed(0)}% understood
                        </span>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Learnings */}
            {results.learnings.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-900 dark:text-gray-100">
                  <TrendingUp className="w-5 h-5 text-blue-600" />
                  Learnings
                  <Badge variant="outline">{results.learnings.length}</Badge>
                </h3>
                <div className="space-y-3">
                  {results.learnings.map((learning) => (
                    <div
                      key={learning.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-4 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    >
                      <div className="flex items-start justify-between mb-2">
                        <div className="flex-1">
                          <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                            {learning.topic}
                          </h4>
                          <div className="flex items-center gap-2">
                            {learning.category && (
                              <Badge variant="secondary">{learning.category}</Badge>
                            )}
                            <Badge className={getSimilarityColor(learning.similarity)}>
                              {(learning.similarity * 100).toFixed(0)}% - {getSimilarityLabel(learning.similarity)}
                            </Badge>
                            <Badge variant="outline">
                              {(learning.confidence * 100).toFixed(0)}% confident
                            </Badge>
                            {learning.applied && (
                              <Badge className="bg-green-600 text-white">✓ Applied</Badge>
                            )}
                          </div>
                        </div>
                      </div>
                      <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">
                        {learning.insight}
                      </p>
                      <p className="text-xs text-gray-500 dark:text-gray-400 mt-2">
                        Reinforced {learning.reinforced}× times
                      </p>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* Related Concepts */}
            {results.related_concepts.length > 0 && (
              <div>
                <h3 className="text-lg font-semibold mb-3 flex items-center gap-2 text-gray-900 dark:text-gray-100">
                  <ArrowRight className="w-5 h-5 text-green-600" />
                  Related Concepts
                  <Badge variant="outline">{results.related_concepts.length}</Badge>
                </h3>
                <div className="grid grid-cols-1 md:grid-cols-2 gap-3">
                  {results.related_concepts.map((concept) => (
                    <div
                      key={concept.id}
                      className="border border-gray-200 dark:border-gray-700 rounded-lg p-3 hover:bg-gray-50 dark:hover:bg-gray-800 transition"
                    >
                      <div className="flex items-center justify-between">
                        <div className="flex-1">
                          <h4 className="font-medium text-sm text-gray-900 dark:text-gray-100">
                            {concept.name}
                          </h4>
                          {concept.category && (
                            <Badge variant="outline" className="mt-1 text-xs">
                              {concept.category}
                            </Badge>
                          )}
                        </div>
                        <div className="text-right">
                          <Badge className="bg-purple-600 text-white text-xs">
                            {concept.relationship}
                          </Badge>
                          <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                            {(concept.strength * 100).toFixed(0)}% strength
                          </p>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            )}

            {/* No Results */}
            {results.knowledge_nodes.length === 0 && results.learnings.length === 0 && (
              <div className="text-center py-12">
                <Search className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
                <p className="text-gray-600 dark:text-gray-400">
                  No results found for "<strong>{query}</strong>"
                </p>
                <p className="text-sm text-gray-500 dark:text-gray-500 mt-2">
                  Try different keywords or browse categories above
                </p>
              </div>
            )}
          </div>
        )}

        {/* Initial State */}
        {!searched && (
          <div className="text-center py-12">
            <Sparkles className="w-16 h-16 text-purple-300 dark:text-purple-600 mx-auto mb-4" />
            <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100 mb-2">
              Intelligent Semantic Search
            </h3>
            <p className="text-gray-600 dark:text-gray-400 mb-4">
              Search through Angela's knowledge and learnings with AI-powered matching
            </p>
            <div className="flex flex-wrap justify-center gap-2">
              {['FastAPI', 'Database', 'Memory System', 'React', 'PostgreSQL'].map(suggestion => (
                <Badge
                  key={suggestion}
                  variant="outline"
                  className="cursor-pointer hover:bg-purple-50 dark:hover:bg-purple-900/20"
                  onClick={() => {
                    setQuery(suggestion);
                    setTimeout(handleSearch, 100);
                  }}
                >
                  Try "{suggestion}"
                </Badge>
              ))}
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
