import { useState, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { GitBranch, ArrowRight, Calendar, Zap, BookOpen, Target } from 'lucide-react';

interface Learning {
  learning_id: string;
  topic: string;
  category: string | null;
  insight: string;
  confidence_level: number;
  times_reinforced: number;
  has_applied: boolean;
  created_at: string;
  last_reinforced_at: string | null;
}

interface KnowledgeNode {
  node_id: string;
  name: string;
  category: string | null;
  understanding: string | null;
  level: number;
  references: number;
  created_at: string;
}

interface PathNode {
  id: string;
  name: string;
  type: 'learning' | 'knowledge';
  category: string | null;
  date: string;
  confidence?: number;
  understanding?: number;
  connections: string[];
}

interface Props {
  learnings: Learning[];
  knowledgeNodes: KnowledgeNode[];
}

export default function KnowledgePathExplorer({ learnings, knowledgeNodes }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [timeRange, setTimeRange] = useState<'7d' | '30d' | '90d' | 'all'>('30d');

  // Build path data
  const pathData = useMemo(() => {
    const nodes: PathNode[] = [];

    // Add learnings
    learnings.forEach(l => {
      nodes.push({
        id: l.learning_id,
        name: l.topic,
        type: 'learning',
        category: l.category,
        date: l.created_at,
        confidence: l.confidence_level * 100,
        connections: []
      });
    });

    // Add knowledge nodes
    knowledgeNodes.forEach(k => {
      nodes.push({
        id: k.node_id,
        name: k.name,
        type: 'knowledge',
        category: k.category,
        date: k.created_at,
        understanding: k.level * 100,
        connections: []
      });
    });

    // Filter by time range
    const now = new Date();
    const cutoffDate = new Date();
    if (timeRange === '7d') cutoffDate.setDate(now.getDate() - 7);
    else if (timeRange === '30d') cutoffDate.setDate(now.getDate() - 30);
    else if (timeRange === '90d') cutoffDate.setDate(now.getDate() - 90);
    else cutoffDate.setFullYear(2000); // all

    let filtered = nodes.filter(n => new Date(n.date) >= cutoffDate);

    // Filter by category
    if (selectedCategory) {
      filtered = filtered.filter(n => n.category === selectedCategory);
    }

    // Sort by date
    return filtered.sort((a, b) => new Date(a.date).getTime() - new Date(b.date).getTime());
  }, [learnings, knowledgeNodes, timeRange, selectedCategory]);

  // Get categories
  const categories = useMemo(() => {
    const cats = new Set<string>();
    [...learnings, ...knowledgeNodes].forEach(item => {
      if (item.category) cats.add(item.category);
    });
    return Array.from(cats).sort();
  }, [learnings, knowledgeNodes]);

  // Group by month
  const pathByMonth = useMemo(() => {
    const grouped: Record<string, PathNode[]> = {};

    pathData.forEach(node => {
      const date = new Date(node.date);
      const monthKey = `${date.getFullYear()}-${String(date.getMonth() + 1).padStart(2, '0')}`;

      if (!grouped[monthKey]) {
        grouped[monthKey] = [];
      }
      grouped[monthKey].push(node);
    });

    return grouped;
  }, [pathData]);

  const formatMonthYear = (monthKey: string) => {
    const [year, month] = monthKey.split('-');
    const date = new Date(parseInt(year), parseInt(month) - 1);
    return date.toLocaleDateString('en-US', { month: 'long', year: 'numeric' });
  };

  const getNodeIcon = (type: 'learning' | 'knowledge') => {
    return type === 'learning' ? <Zap className="w-4 h-4" /> : <BookOpen className="w-4 h-4" />;
  };

  const getNodeColor = (type: 'learning' | 'knowledge') => {
    return type === 'learning'
      ? 'border-l-4 border-l-blue-500 bg-blue-50 dark:bg-blue-900/20'
      : 'border-l-4 border-l-purple-500 bg-purple-50 dark:bg-purple-900/20';
  };

  const stats = {
    totalNodes: pathData.length,
    learningNodes: pathData.filter(n => n.type === 'learning').length,
    knowledgeNodes: pathData.filter(n => n.type === 'knowledge').length,
    avgConfidence: pathData.filter(n => n.confidence).reduce((sum, n) => sum + (n.confidence || 0), 0) / pathData.filter(n => n.confidence).length || 0,
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <GitBranch className="w-5 h-5 text-green-500" />
            <CardTitle>Knowledge Path Explorer</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{stats.totalNodes} items</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-wrap gap-3 mb-6">
          {/* Time Range */}
          <div className="flex items-center gap-2">
            <Calendar className="w-4 h-4 text-gray-500" />
            <select
              value={timeRange}
              onChange={(e) => setTimeRange(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800"
            >
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
              <option value="90d">Last 90 days</option>
              <option value="all">All time</option>
            </select>
          </div>

          {/* Category Filter */}
          <div className="flex items-center gap-2">
            <Target className="w-4 h-4 text-gray-500" />
            <select
              value={selectedCategory || ''}
              onChange={(e) => setSelectedCategory(e.target.value || null)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800"
            >
              <option value="">All categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>
          </div>

          {/* Reset */}
          {(selectedCategory || timeRange !== '30d') && (
            <button
              onClick={() => {
                setSelectedCategory(null);
                setTimeRange('30d');
              }}
              className="px-3 py-1.5 text-sm text-gray-600 dark:text-gray-400 hover:text-gray-900 dark:hover:text-gray-200"
            >
              Reset filters
            </button>
          )}
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.totalNodes}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Items</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.learningNodes}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Learnings</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{stats.knowledgeNodes}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Knowledge</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg">
            <div className="text-2xl font-bold text-yellow-600">{stats.avgConfidence.toFixed(0)}%</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Avg Confidence</div>
          </div>
        </div>

        {/* Timeline Path */}
        <div className="space-y-6 max-h-[600px] overflow-y-auto pr-2">
          {Object.keys(pathByMonth).length === 0 ? (
            <div className="text-center py-12">
              <GitBranch className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">No learning path found for selected filters</p>
            </div>
          ) : (
            Object.entries(pathByMonth).map(([monthKey, nodes]) => (
              <div key={monthKey}>
                {/* Month Header */}
                <div className="flex items-center gap-3 mb-4">
                  <div className="flex-shrink-0 w-3 h-3 bg-green-500 rounded-full"></div>
                  <h3 className="text-lg font-semibold text-gray-900 dark:text-gray-100">
                    {formatMonthYear(monthKey)}
                  </h3>
                  <div className="flex-1 h-px bg-gray-200 dark:bg-gray-700"></div>
                  <Badge variant="outline" className="text-xs">
                    {nodes.length} items
                  </Badge>
                </div>

                {/* Nodes in this month */}
                <div className="ml-6 space-y-3">
                  {nodes.map((node, idx) => (
                    <div key={node.id} className="relative">
                      {/* Connector line */}
                      {idx < nodes.length - 1 && (
                        <div className="absolute left-0 top-12 w-px h-full bg-gray-200 dark:bg-gray-700"></div>
                      )}

                      {/* Node Card */}
                      <div className={`relative pl-6 ${getNodeColor(node.type)} rounded-lg p-4`}>
                        {/* Node Icon */}
                        <div className="absolute left-0 top-1/2 -translate-y-1/2 -translate-x-1/2 bg-white dark:bg-gray-900 rounded-full p-1 border-2 border-gray-200 dark:border-gray-700">
                          {getNodeIcon(node.type)}
                        </div>

                        {/* Content */}
                        <div className="flex items-start justify-between">
                          <div className="flex-1">
                            <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">
                              {node.name}
                            </h4>
                            <div className="flex items-center gap-2">
                              <Badge variant="secondary" className="text-xs">
                                {node.type}
                              </Badge>
                              {node.category && (
                                <Badge variant="outline" className="text-xs">
                                  {node.category}
                                </Badge>
                              )}
                              <span className="text-xs text-gray-500 dark:text-gray-400">
                                {new Date(node.date).toLocaleDateString()}
                              </span>
                            </div>
                          </div>

                          {/* Metrics */}
                          <div className="text-right">
                            {node.confidence !== undefined && (
                              <div className="text-sm">
                                <span className="text-gray-600 dark:text-gray-400">Confidence:</span>{' '}
                                <strong className="text-blue-600">{node.confidence.toFixed(0)}%</strong>
                              </div>
                            )}
                            {node.understanding !== undefined && (
                              <div className="text-sm">
                                <span className="text-gray-600 dark:text-gray-400">Understanding:</span>{' '}
                                <strong className="text-purple-600">{node.understanding.toFixed(0)}%</strong>
                              </div>
                            )}
                          </div>
                        </div>
                      </div>
                    </div>
                  ))}
                </div>
              </div>
            ))
          )}
        </div>

        {/* Legend */}
        <div className="mt-6 flex flex-wrap gap-3 pt-4 border-t border-gray-200 dark:border-gray-700">
          <div className="flex items-center gap-2">
            <Zap className="w-4 h-4 text-blue-600" />
            <span className="text-sm text-gray-600 dark:text-gray-400">Learning</span>
          </div>
          <div className="flex items-center gap-2">
            <BookOpen className="w-4 h-4 text-purple-600" />
            <span className="text-sm text-gray-600 dark:text-gray-400">Knowledge Node</span>
          </div>
          <div className="flex items-center gap-2">
            <ArrowRight className="w-4 h-4 text-gray-400" />
            <span className="text-sm text-gray-600 dark:text-gray-400">Chronological Flow</span>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
