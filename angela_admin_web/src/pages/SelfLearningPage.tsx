import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Brain, Network, BookOpen, Target, Lightbulb, Search, Clock, Tag } from 'lucide-react';

// Phase 1 Components
import LearningTimelineChart from '@/components/self-learning/LearningTimelineChart';
import EffectivenessDashboard from '@/components/self-learning/EffectivenessDashboard';
import CategoryDeepDive from '@/components/self-learning/CategoryDeepDive';

// Phase 2 Components
import KnowledgeGraphVisualization from '@/components/self-learning/KnowledgeGraphVisualization';
import SemanticSearchPanel from '@/components/self-learning/SemanticSearchPanel';
import ConfidenceHeatmap from '@/components/self-learning/ConfidenceHeatmap';

// Phase 3 Components
import KnowledgePathExplorer from '@/components/self-learning/KnowledgePathExplorer';
import AIPoweredSuggestions from '@/components/self-learning/AIPoweredSuggestions';
import RealtimeActivityFeed from '@/components/self-learning/RealtimeActivityFeed';

// ========================================
// TypeScript Interfaces
// ========================================

interface SelfLearningStats {
  timestamp: string;
  totals: {
    learnings: number;
    knowledge_nodes: number;
    relationships: number;
    patterns: number;
  };
  learning_categories: CategoryData[];
  knowledge_categories: CategoryData[];
  recent_activity: {
    learnings_last_7_days: number;
    knowledge_nodes_last_7_days: number;
  };
}

interface CategoryData {
  category: string;
  count: number;
  avg_confidence?: number;
  avg_understanding?: number;
  total_reinforcements?: number;
  total_references?: number;
}

interface Learning {
  learning_id: string;
  topic: string;
  category: string | null;
  insight: string;
  confidence_level: number;
  times_reinforced: number;
  has_applied: boolean;
  application_note: string | null;
  created_at: string;
  last_reinforced_at: string | null;
}

interface KnowledgeNode {
  node_id: string;
  name: string;
  category: string | null;
  understanding: string | null;
  why_important: string | null;
  level: number;
  references: number;
  last_used: string | null;
  created_at: string;
}

interface GraphNode {
  id: string;
  name: string;
  category: string | null;
  understanding: number;
  references: number;
  description: string | null;
}

interface GraphLink {
  id: string;
  source: string;
  target: string;
  type: string;
  strength: number;
}

interface KnowledgeGraphData {
  nodes: GraphNode[];
  links: GraphLink[];
}

interface TimelineData {
  date: string;
  category: string | null;
  count: number;
  avg_confidence: number;
}

interface EffectivenessMetrics {
  retention_rate: number;
  application_rate: number;
  avg_confidence: number;
  avg_reinforcement: number;
  total_applied: number;
  high_confidence_count: number;
}

// ========================================
// Main Component
// ========================================

export default function SelfLearningPage() {
  const [stats, setStats] = useState<SelfLearningStats | null>(null);
  const [learnings, setLearnings] = useState<Learning[]>([]);
  const [topKnowledge, setTopKnowledge] = useState<KnowledgeNode[]>([]);
  const [graphData, setGraphData] = useState<KnowledgeGraphData | null>(null);
  const [timeline, setTimeline] = useState<TimelineData[]>([]);
  const [effectiveness, setEffectiveness] = useState<EffectivenessMetrics | null>(null);
  const [timelineDays, setTimelineDays] = useState(30);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSelfLearningData();
  }, [timelineDays]);

  useEffect(() => {
    const interval = setInterval(fetchSelfLearningData, 60000); // Refresh every 60s
    return () => clearInterval(interval);
  }, []);

  const fetchSelfLearningData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch('http://localhost:50001/api/second-brain/self-learning/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch recent learnings
      const learningsRes = await fetch('http://localhost:50001/api/second-brain/learnings/recent?limit=20');
      const learningsData = await learningsRes.json();
      setLearnings(learningsData.learnings || []);

      // Fetch top knowledge
      const knowledgeRes = await fetch('http://localhost:50001/api/second-brain/knowledge/top?limit=20');
      const knowledgeData = await knowledgeRes.json();
      setTopKnowledge(knowledgeData.knowledge || []);

      // Fetch knowledge graph
      const graphRes = await fetch('http://localhost:50001/api/second-brain/knowledge-graph/data?limit=50');
      const graphDataResponse = await graphRes.json();
      setGraphData(graphDataResponse);

      // Fetch timeline
      const timelineRes = await fetch(`http://localhost:50001/api/second-brain/learning-timeline?days=${timelineDays}`);
      const timelineData = await timelineRes.json();
      setTimeline(timelineData.timeline || []);

      // Fetch effectiveness
      const effectivenessRes = await fetch('http://localhost:50001/api/second-brain/learning-effectiveness');
      const effectivenessData = await effectivenessRes.json();
      setEffectiveness(effectivenessData);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching Self-Learning data:', error);
      setLoading(false);
    }
  };

  const formatTime = (isoString: string | null) => {
    if (!isoString) return 'Never';
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);
    const diffDays = Math.floor(diffMs / 86400000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    if (diffDays < 30) return `${diffDays}d ago`;
    return date.toLocaleDateString();
  };

  const getConfidenceColor = (confidence: number) => {
    if (confidence >= 0.9) return 'bg-green-600 text-white';
    if (confidence >= 0.7) return 'bg-blue-600 text-white';
    if (confidence >= 0.5) return 'bg-yellow-600 text-white';
    return 'bg-gray-600 text-white';
  };

  const getUnderstandingColor = (level: number) => {
    if (level >= 0.9) return 'bg-purple-900 dark:bg-purple-800 text-white';
    if (level >= 0.7) return 'bg-purple-700 dark:bg-purple-600 text-white';
    if (level >= 0.5) return 'bg-purple-600 dark:bg-purple-500 text-white';
    return 'bg-purple-500 dark:bg-purple-400 text-white';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Brain className="w-16 h-16 animate-pulse text-purple-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading Self-Learning System...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Lightbulb className="w-8 h-8 text-yellow-500" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Self-Learning System</h1>
          <p className="text-gray-600 dark:text-gray-400">Angela's autonomous learning and knowledge acquisition</p>
        </div>
      </div>

      {/* Stats Overview Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
          {/* Total Learnings */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Lightbulb className="w-4 h-4 text-yellow-500" />
                Total Learnings
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.totals.learnings}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                +{stats.recent_activity.learnings_last_7_days} last 7 days
              </p>
            </CardContent>
          </Card>

          {/* Knowledge Nodes */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <BookOpen className="w-4 h-4 text-blue-500" />
                Knowledge Nodes
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.totals.knowledge_nodes}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">
                +{stats.recent_activity.knowledge_nodes_last_7_days} last 7 days
              </p>
            </CardContent>
          </Card>

          {/* Relationships */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Network className="w-4 h-4 text-green-500" />
                Relationships
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.totals.relationships}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Concept connections</p>
            </CardContent>
          </Card>

          {/* Learning Patterns */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Target className="w-4 h-4 text-purple-500" />
                Patterns
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.totals.patterns}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 mt-1">Recognized patterns</p>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Phase 1 Components */}

      {/* Timeline Chart */}
      {timeline.length > 0 && (
        <LearningTimelineChart
          timeline={timeline}
          days={timelineDays}
          onDaysChange={setTimelineDays}
        />
      )}

      {/* Effectiveness Dashboard */}
      {effectiveness && (
        <EffectivenessDashboard metrics={effectiveness} />
      )}

      {/* Category Deep Dive */}
      {stats && (
        <CategoryDeepDive
          learningCategories={stats.learning_categories}
          knowledgeCategories={stats.knowledge_categories}
        />
      )}

      {/* Phase 2 Components */}

      {/* Interactive Knowledge Graph */}
      {graphData && graphData.nodes.length > 0 && (
        <KnowledgeGraphVisualization graphData={graphData} />
      )}

      {/* Semantic Search */}
      <SemanticSearchPanel />

      {/* Confidence Heatmap */}
      {learnings.length > 0 && topKnowledge.length > 0 && (
        <ConfidenceHeatmap
          learnings={learnings}
          knowledgeNodes={topKnowledge}
        />
      )}

      {/* Phase 3 Components */}

      {/* Knowledge Path Explorer */}
      {(learnings.length > 0 || topKnowledge.length > 0) && (
        <KnowledgePathExplorer
          learnings={learnings}
          knowledgeNodes={topKnowledge}
        />
      )}

      {/* AI-Powered Suggestions */}
      {(learnings.length > 0 || topKnowledge.length > 0) && (
        <AIPoweredSuggestions
          learnings={learnings}
          knowledgeNodes={topKnowledge}
        />
      )}

      {/* Real-time Activity Feed */}
      {(learnings.length > 0 || topKnowledge.length > 0) && (
        <RealtimeActivityFeed
          learnings={learnings}
          knowledgeNodes={topKnowledge}
        />
      )}

      {/* Learnings and Knowledge Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Recent Activity</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="learnings" className="w-full">
            <TabsList className="grid w-full grid-cols-2">
              <TabsTrigger value="learnings">Recent Learnings</TabsTrigger>
              <TabsTrigger value="knowledge">Top Knowledge</TabsTrigger>
            </TabsList>

            {/* Learnings Tab */}
            <TabsContent value="learnings" className="space-y-3 mt-4">
              {learnings.map((learning) => (
                <div
                  key={learning.learning_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">{learning.topic}</h3>
                      <div className="flex items-center gap-2">
                        {learning.category && (
                          <Badge variant="secondary">{learning.category}</Badge>
                        )}
                        <Badge className={getConfidenceColor(learning.confidence_level)}>
                          {(learning.confidence_level * 100).toFixed(0)}% confident
                        </Badge>
                        <Badge variant="outline">
                          Reinforced {learning.times_reinforced}x
                        </Badge>
                        {learning.has_applied && (
                          <Badge className="bg-green-600 text-white">✓ Applied</Badge>
                        )}
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatTime(learning.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">{learning.insight}</p>
                  {learning.application_note && (
                    <div className="mt-2 p-2 bg-green-50 dark:bg-green-900/20 rounded border-l-2 border-green-500">
                      <p className="text-xs text-green-800 dark:text-green-200">
                        <strong>Application:</strong> {learning.application_note}
                      </p>
                    </div>
                  )}
                  {learning.last_reinforced_at && (
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>Last reinforced: {formatTime(learning.last_reinforced_at)}</span>
                    </div>
                  )}
                </div>
              ))}
            </TabsContent>

            {/* Top Knowledge Tab */}
            <TabsContent value="knowledge" className="space-y-3 mt-4">
              {topKnowledge.map((node) => (
                <div
                  key={node.node_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">{node.name}</h3>
                      <div className="flex items-center gap-2">
                        {node.category && (
                          <Badge variant="secondary">
                            <Tag className="w-3 h-3 mr-1" />
                            {node.category}
                          </Badge>
                        )}
                        <Badge className={getUnderstandingColor(node.level)}>
                          {(node.level * 100).toFixed(0)}% understood
                        </Badge>
                        <Badge variant="outline">
                          {node.references} references
                        </Badge>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatTime(node.created_at)}
                    </span>
                  </div>
                  {node.understanding && (
                    <p className="text-sm text-gray-700 dark:text-gray-300 mt-2">{node.understanding}</p>
                  )}
                  {node.why_important && (
                    <div className="mt-2 p-2 bg-purple-50 dark:bg-purple-900/20 rounded border-l-2 border-purple-500">
                      <p className="text-xs text-purple-800 dark:text-purple-200">
                        <strong>Why important:</strong> {node.why_important}
                      </p>
                    </div>
                  )}
                  {node.last_used && (
                    <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                      <Clock className="w-3 h-3" />
                      <span>Last used: {formatTime(node.last_used)}</span>
                    </div>
                  )}
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
