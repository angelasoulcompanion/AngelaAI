import { useState, useEffect, useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Activity, Zap, BookOpen, Link2, Clock, Filter } from 'lucide-react';

interface Learning {
  learning_id: string;
  topic: string;
  category: string | null;
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
  level: number;
  references: number;
  created_at: string;
  last_used: string | null;
}

interface ActivityItem {
  id: string;
  type: 'learning_created' | 'learning_reinforced' | 'knowledge_created' | 'knowledge_used' | 'learning_applied';
  timestamp: string;
  title: string;
  description: string;
  category: string | null;
  metadata?: {
    confidence?: number;
    understanding?: number;
    reinforcement_count?: number;
  };
}

interface Props {
  learnings: Learning[];
  knowledgeNodes: KnowledgeNode[];
}

export default function RealtimeActivityFeed({ learnings, knowledgeNodes }: Props) {
  const [activityFilter, setActivityFilter] = useState<'all' | 'learning' | 'knowledge'>('all');
  const [timeFilter, setTimeFilter] = useState<'24h' | '7d' | '30d'>('7d');
  const [autoRefresh, setAutoRefresh] = useState(true);

  // Build activity feed
  const activities = useMemo(() => {
    const items: ActivityItem[] = [];

    // Add learning activities
    learnings.forEach(l => {
      // Learning created
      items.push({
        id: `learning-created-${l.learning_id}`,
        type: 'learning_created',
        timestamp: l.created_at,
        title: `New learning: ${l.topic}`,
        description: `Started learning about ${l.topic}`,
        category: l.category,
        metadata: {
          confidence: l.confidence_level * 100,
        },
      });

      // Learning reinforced
      if (l.last_reinforced_at && l.times_reinforced > 1) {
        items.push({
          id: `learning-reinforced-${l.learning_id}`,
          type: 'learning_reinforced',
          timestamp: l.last_reinforced_at,
          title: `Reinforced: ${l.topic}`,
          description: `Reinforced ${l.topic} (${l.times_reinforced}× total)`,
          category: l.category,
          metadata: {
            confidence: l.confidence_level * 100,
            reinforcement_count: l.times_reinforced,
          },
        });
      }

      // Learning applied
      if (l.has_applied) {
        items.push({
          id: `learning-applied-${l.learning_id}`,
          type: 'learning_applied',
          timestamp: l.last_reinforced_at || l.created_at,
          title: `Applied: ${l.topic}`,
          description: `Successfully applied knowledge of ${l.topic}`,
          category: l.category,
          metadata: {
            confidence: l.confidence_level * 100,
          },
        });
      }
    });

    // Add knowledge node activities
    knowledgeNodes.forEach(k => {
      // Knowledge created
      items.push({
        id: `knowledge-created-${k.node_id}`,
        type: 'knowledge_created',
        timestamp: k.created_at,
        title: `New knowledge: ${k.name}`,
        description: `Added ${k.name} to knowledge base`,
        category: k.category,
        metadata: {
          understanding: k.level * 100,
        },
      });

      // Knowledge used
      if (k.last_used) {
        items.push({
          id: `knowledge-used-${k.node_id}`,
          type: 'knowledge_used',
          timestamp: k.last_used,
          title: `Used: ${k.name}`,
          description: `Referenced ${k.name} (${k.references}× total)`,
          category: k.category,
          metadata: {
            understanding: k.level * 100,
          },
        });
      }
    });

    // Filter by type
    let filtered = items;
    if (activityFilter === 'learning') {
      filtered = items.filter(i => i.type.startsWith('learning_'));
    } else if (activityFilter === 'knowledge') {
      filtered = items.filter(i => i.type.startsWith('knowledge_'));
    }

    // Filter by time
    const now = new Date();
    const cutoffDate = new Date();
    if (timeFilter === '24h') cutoffDate.setHours(now.getHours() - 24);
    else if (timeFilter === '7d') cutoffDate.setDate(now.getDate() - 7);
    else if (timeFilter === '30d') cutoffDate.setDate(now.getDate() - 30);

    filtered = filtered.filter(i => new Date(i.timestamp) >= cutoffDate);

    // Sort by timestamp (most recent first)
    return filtered.sort((a, b) => new Date(b.timestamp).getTime() - new Date(a.timestamp).getTime());
  }, [learnings, knowledgeNodes, activityFilter, timeFilter]);

  // Auto-refresh every 60 seconds
  useEffect(() => {
    if (!autoRefresh) return;

    const interval = setInterval(() => {
      // In a real app, this would fetch new data
      console.log('Auto-refreshing activity feed...');
    }, 60000);

    return () => clearInterval(interval);
  }, [autoRefresh]);

  const getActivityIcon = (type: ActivityItem['type']) => {
    switch (type) {
      case 'learning_created':
      case 'learning_reinforced':
      case 'learning_applied':
        return <Zap className="w-4 h-4" />;
      case 'knowledge_created':
      case 'knowledge_used':
        return <BookOpen className="w-4 h-4" />;
    }
  };

  const getActivityColor = (type: ActivityItem['type']) => {
    switch (type) {
      case 'learning_created':
        return 'bg-blue-500';
      case 'learning_reinforced':
        return 'bg-yellow-500';
      case 'learning_applied':
        return 'bg-green-500';
      case 'knowledge_created':
        return 'bg-purple-500';
      case 'knowledge_used':
        return 'bg-indigo-500';
    }
  };

  const getActivityLabel = (type: ActivityItem['type']) => {
    switch (type) {
      case 'learning_created': return 'New';
      case 'learning_reinforced': return 'Reinforced';
      case 'learning_applied': return 'Applied';
      case 'knowledge_created': return 'Added';
      case 'knowledge_used': return 'Used';
    }
  };

  const formatTimeAgo = (timestamp: string) => {
    const now = new Date();
    const date = new Date(timestamp);
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 1) return 'Just now';
    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 7) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const stats = {
    total: activities.length,
    learning: activities.filter(a => a.type.startsWith('learning_')).length,
    knowledge: activities.filter(a => a.type.startsWith('knowledge_')).length,
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Activity className="w-5 h-5 text-green-500" />
            <CardTitle>Real-time Activity Feed</CardTitle>
            {autoRefresh && (
              <Badge variant="outline" className="ml-2 animate-pulse">
                Live
              </Badge>
            )}
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{stats.total} activities</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Filters */}
        <div className="flex flex-wrap items-center gap-3 mb-6">
          {/* Activity Type Filter */}
          <div className="flex items-center gap-2">
            <Filter className="w-4 h-4 text-gray-500" />
            <select
              value={activityFilter}
              onChange={(e) => setActivityFilter(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800"
            >
              <option value="all">All activities</option>
              <option value="learning">Learning only</option>
              <option value="knowledge">Knowledge only</option>
            </select>
          </div>

          {/* Time Filter */}
          <div className="flex items-center gap-2">
            <Clock className="w-4 h-4 text-gray-500" />
            <select
              value={timeFilter}
              onChange={(e) => setTimeFilter(e.target.value as any)}
              className="px-3 py-1.5 border border-gray-300 dark:border-gray-600 rounded-lg text-sm focus:outline-none focus:ring-2 focus:ring-green-500 dark:bg-gray-800"
            >
              <option value="24h">Last 24 hours</option>
              <option value="7d">Last 7 days</option>
              <option value="30d">Last 30 days</option>
            </select>
          </div>

          {/* Auto-refresh Toggle */}
          <label className="flex items-center gap-2 cursor-pointer">
            <input
              type="checkbox"
              checked={autoRefresh}
              onChange={(e) => setAutoRefresh(e.target.checked)}
              className="w-4 h-4 text-green-600 rounded focus:ring-2 focus:ring-green-500"
            />
            <span className="text-sm text-gray-700 dark:text-gray-300">Auto-refresh</span>
          </label>
        </div>

        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="text-center p-3 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">{stats.total}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Activities</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{stats.learning}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Learning</div>
          </div>
          <div className="text-center p-3 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{stats.knowledge}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Knowledge</div>
          </div>
        </div>

        {/* Activity Feed */}
        <div className="space-y-3 max-h-[600px] overflow-y-auto pr-2">
          {activities.length === 0 ? (
            <div className="text-center py-12">
              <Activity className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No activities found for selected filters
              </p>
            </div>
          ) : (
            activities.map((activity) => (
              <div
                key={activity.id}
                className="flex items-start gap-3 p-4 bg-white dark:bg-gray-800 border border-gray-200 dark:border-gray-700 rounded-lg hover:shadow-md transition"
              >
                {/* Icon */}
                <div className={`flex-shrink-0 p-2 ${getActivityColor(activity.type)} rounded-full text-white`}>
                  {getActivityIcon(activity.type)}
                </div>

                {/* Content */}
                <div className="flex-1 min-w-0">
                  <div className="flex items-start justify-between gap-2">
                    <div className="flex-1">
                      <h4 className="font-semibold text-gray-900 dark:text-gray-100 text-sm">
                        {activity.title}
                      </h4>
                      <p className="text-sm text-gray-600 dark:text-gray-400 mt-0.5">
                        {activity.description}
                      </p>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400 whitespace-nowrap">
                      {formatTimeAgo(activity.timestamp)}
                    </span>
                  </div>

                  {/* Metadata */}
                  <div className="flex items-center gap-2 mt-2">
                    <Badge variant="secondary" className="text-xs">
                      {getActivityLabel(activity.type)}
                    </Badge>
                    {activity.category && (
                      <Badge variant="outline" className="text-xs">
                        {activity.category}
                      </Badge>
                    )}
                    {activity.metadata?.confidence !== undefined && (
                      <Badge variant="outline" className="text-xs">
                        {activity.metadata.confidence.toFixed(0)}% confidence
                      </Badge>
                    )}
                    {activity.metadata?.understanding !== undefined && (
                      <Badge variant="outline" className="text-xs">
                        {activity.metadata.understanding.toFixed(0)}% understanding
                      </Badge>
                    )}
                    {activity.metadata?.reinforcement_count !== undefined && (
                      <Badge variant="outline" className="text-xs">
                        {activity.metadata.reinforcement_count}× reinforced
                      </Badge>
                    )}
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Info */}
        {activities.length > 0 && (
          <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-500">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong className="text-blue-700 dark:text-blue-300">💡 Tip:</strong> Activities are updated in real-time. Enable auto-refresh to see the latest changes automatically.
            </p>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
