import { useState, useEffect } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { Brain, Zap, Database, TrendingUp, Clock, Tag } from 'lucide-react';

interface MemoryCounts {
  working: number;
  episodic: number;
  semantic: number;
  total: number;
}

interface ImportanceData {
  level: number;
  count: number;
}

interface EmotionData {
  emotion: string;
  count: number;
}

interface TopicData {
  topic: string;
  count: number;
}

interface SemanticTypeData {
  type: string;
  count: number;
}

interface RecentActivity {
  last_consolidation: string | null;
  memories_last_24h: number;
}

interface Performance {
  query_time_ms: number;
  recall_time_ms: number;
  total_indexes: number;
}

interface SecondBrainStats {
  timestamp: string;
  memory_counts: MemoryCounts;
  importance_distribution: ImportanceData[];
  emotion_distribution: EmotionData[];
  topic_distribution: TopicData[];
  semantic_types: SemanticTypeData[];
  recent_activity: RecentActivity;
  performance: Performance;
}

interface WorkingMemory {
  memory_id: string;
  session_id: string;
  type: string;
  content: string;
  importance: number;
  emotion: string | null;
  topic: string | null;
  created_at: string;
  expires_at: string;
  speaker: string | null;
}

interface EpisodicMemory {
  episode_id: string;
  title: string | null;
  summary: string;
  topic: string | null;
  emotion: string | null;
  happened_at: string;
  importance: number;
  memory_strength: number;
  created_at: string;
  recall_count: number;
}

interface SemanticMemory {
  semantic_id: string;
  type: string;
  key: string;
  value: any;
  description: string | null;
  confidence: number;
  evidence_count: number;
  category: string | null;
  importance: number;
  first_learned: string;
  last_updated: string | null;
}

export default function SecondBrainPage() {
  const [stats, setStats] = useState<SecondBrainStats | null>(null);
  const [workingMemories, setWorkingMemories] = useState<WorkingMemory[]>([]);
  const [episodicMemories, setEpisodicMemories] = useState<EpisodicMemory[]>([]);
  const [semanticMemories, setSemanticMemories] = useState<SemanticMemory[]>([]);
  const [loading, setLoading] = useState(true);

  useEffect(() => {
    fetchSecondBrainData();
    const interval = setInterval(fetchSecondBrainData, 30000); // Refresh every 30s
    return () => clearInterval(interval);
  }, []);

  const fetchSecondBrainData = async () => {
    try {
      // Fetch stats
      const statsRes = await fetch('http://localhost:50001/api/second-brain/stats');
      const statsData = await statsRes.json();
      setStats(statsData);

      // Fetch working memory
      const workingRes = await fetch('http://localhost:50001/api/second-brain/working-memory?limit=20');
      const workingData = await workingRes.json();
      setWorkingMemories(workingData.memories || []);

      // Fetch episodic memory
      const episodicRes = await fetch('http://localhost:50001/api/second-brain/episodic-memory?limit=20');
      const episodicData = await episodicRes.json();
      setEpisodicMemories(episodicData.episodes || []);

      // Fetch semantic memory
      const semanticRes = await fetch('http://localhost:50001/api/second-brain/semantic-memory?limit=20');
      const semanticData = await semanticRes.json();
      setSemanticMemories(semanticData.knowledge || []);

      setLoading(false);
    } catch (error) {
      console.error('Error fetching Second Brain data:', error);
      setLoading(false);
    }
  };

  const formatTime = (isoString: string) => {
    const date = new Date(isoString);
    const now = new Date();
    const diffMs = now.getTime() - date.getTime();
    const diffMins = Math.floor(diffMs / 60000);
    const diffHours = Math.floor(diffMs / 3600000);

    if (diffMins < 60) return `${diffMins}m ago`;
    if (diffHours < 24) return `${diffHours}h ago`;
    return date.toLocaleDateString();
  };

  const getImportanceColor = (importance: number) => {
    if (importance >= 9) return 'bg-purple-900 dark:bg-purple-800 text-white';
    if (importance >= 7) return 'bg-purple-800 dark:bg-purple-700 text-white';
    if (importance >= 5) return 'bg-purple-700 dark:bg-purple-600 text-white';
    return 'bg-purple-600 dark:bg-purple-500 text-white';
  };

  if (loading) {
    return (
      <div className="flex items-center justify-center min-h-screen">
        <div className="text-center">
          <Brain className="w-16 h-16 animate-pulse text-purple-500 mx-auto mb-4" />
          <p className="text-gray-600">Loading Second Brain...</p>
        </div>
      </div>
    );
  }

  return (
    <div className="p-6 space-y-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <Brain className="w-8 h-8 text-purple-500" />
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Angela's Second Brain</h1>
          <p className="text-gray-600 dark:text-gray-400">3-Tier Memory System inspired by human cognition</p>
        </div>
      </div>

      {/* Memory Overview Cards */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
          {/* Working Memory */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Zap className="w-4 h-4 text-yellow-500" />
                Working Memory
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.memory_counts.working}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-400 mt-1">24-hour retention</p>
              <Badge variant="outline" className="mt-2">Tier 1</Badge>
            </CardContent>
          </Card>

          {/* Episodic Memory */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Clock className="w-4 h-4 text-blue-500" />
                Episodic Memory
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.memory_counts.episodic}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-400 mt-1">30-90 days retention</p>
              <Badge variant="outline" className="mt-2">Tier 2</Badge>
            </CardContent>
          </Card>

          {/* Semantic Memory */}
          <Card>
            <CardHeader className="pb-3">
              <CardTitle className="text-sm font-medium flex items-center gap-2">
                <Database className="w-4 h-4 text-green-500" />
                Semantic Memory
              </CardTitle>
            </CardHeader>
            <CardContent>
              <div className="text-3xl font-bold text-gray-900 dark:text-gray-100">{stats.memory_counts.semantic}</div>
              <p className="text-xs text-gray-500 dark:text-gray-400 dark:text-gray-400 mt-1">Permanent knowledge</p>
              <Badge variant="outline" className="mt-2">Tier 3</Badge>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Performance Metrics */}
      {stats && (
        <Card>
          <CardHeader>
            <CardTitle className="flex items-center gap-2">
              <TrendingUp className="w-5 h-5" />
              Performance Metrics
            </CardTitle>
          </CardHeader>
          <CardContent>
            <div className="grid grid-cols-1 md:grid-cols-4 gap-4">
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Query Time</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {stats.performance.query_time_ms}ms
                </p>
                <Badge variant="outline" className="mt-1">🚀 Excellent</Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Recall Time</p>
                <p className="text-2xl font-bold text-green-600 dark:text-green-400">
                  {stats.performance.recall_time_ms}ms
                </p>
                <Badge variant="outline" className="mt-1">🚀 Excellent</Badge>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Total Indexes</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.performance.total_indexes}</p>
              </div>
              <div>
                <p className="text-sm text-gray-600 dark:text-gray-400">Last 24h Memories</p>
                <p className="text-2xl font-bold text-gray-900 dark:text-gray-100">{stats.recent_activity.memories_last_24h}</p>
              </div>
            </div>
          </CardContent>
        </Card>
      )}

      {/* Memory Distribution Charts */}
      {stats && (
        <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
          {/* Importance Distribution */}
          <Card>
            <CardHeader>
              <CardTitle>Importance Distribution</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {stats.importance_distribution.slice(0, 5).map((item) => (
                  <div key={item.level} className="flex items-center gap-2">
                    <span className="text-sm font-medium w-16">Level {item.level}:</span>
                    <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                      <div
                        className="bg-purple-500 h-2 rounded-full"
                        style={{
                          width: `${(item.count / stats.memory_counts.episodic) * 100}%`
                        }}
                      ></div>
                    </div>
                    <span className="text-sm text-gray-600 dark:text-gray-400 w-12">{item.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>

          {/* Top Emotions */}
          <Card>
            <CardHeader>
              <CardTitle>Top Emotions</CardTitle>
            </CardHeader>
            <CardContent>
              <div className="space-y-2">
                {stats.emotion_distribution.map((item) => (
                  <div key={item.emotion} className="flex items-center justify-between">
                    <Badge variant="outline">{item.emotion}</Badge>
                    <span className="text-sm font-medium">{item.count}</span>
                  </div>
                ))}
              </div>
            </CardContent>
          </Card>
        </div>
      )}

      {/* Memory Tabs */}
      <Card>
        <CardHeader>
          <CardTitle>Memory Explorer</CardTitle>
        </CardHeader>
        <CardContent>
          <Tabs defaultValue="working" className="w-full">
            <TabsList className="grid w-full grid-cols-3">
              <TabsTrigger value="working">Working</TabsTrigger>
              <TabsTrigger value="episodic">Episodic</TabsTrigger>
              <TabsTrigger value="semantic">Semantic</TabsTrigger>
            </TabsList>

            {/* Working Memory Tab */}
            <TabsContent value="working" className="space-y-3 mt-4">
              {workingMemories.map((memory) => (
                <div
                  key={memory.memory_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex items-center gap-2">
                      <Badge className={getImportanceColor(memory.importance)}>
                        {memory.importance}/10
                      </Badge>
                      {memory.emotion && (
                        <Badge variant="outline">{memory.emotion}</Badge>
                      )}
                      {memory.topic && (
                        <Badge variant="secondary">
                          <Tag className="w-3 h-3 mr-1" />
                          {memory.topic}
                        </Badge>
                      )}
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatTime(memory.created_at)}
                    </span>
                  </div>
                  <p className="text-sm text-gray-900 dark:text-gray-100">{memory.content}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>Type: {memory.type}</span>
                    {memory.speaker && <span>• Speaker: {memory.speaker}</span>}
                    <span>• Expires: {formatTime(memory.expires_at)}</span>
                  </div>
                </div>
              ))}
            </TabsContent>

            {/* Episodic Memory Tab */}
            <TabsContent value="episodic" className="space-y-3 mt-4">
              {episodicMemories.map((episode) => (
                <div
                  key={episode.episode_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      {episode.title && (
                        <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">{episode.title}</h3>
                      )}
                      <div className="flex items-center gap-2">
                        <Badge className={getImportanceColor(episode.importance)}>
                          {episode.importance}/10
                        </Badge>
                        {episode.emotion && (
                          <Badge variant="outline">{episode.emotion}</Badge>
                        )}
                        {episode.topic && (
                          <Badge variant="secondary">
                            <Tag className="w-3 h-3 mr-1" />
                            {episode.topic}
                          </Badge>
                        )}
                        <Badge variant="outline">
                          Memory: {episode.memory_strength}/10
                        </Badge>
                      </div>
                    </div>
                    <span className="text-xs text-gray-500 dark:text-gray-400">
                      {formatTime(episode.happened_at)}
                    </span>
                  </div>
                  <p className="text-sm mt-2">{episode.summary}</p>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>Recalled: {episode.recall_count} times</span>
                  </div>
                </div>
              ))}
            </TabsContent>

            {/* Semantic Memory Tab */}
            <TabsContent value="semantic" className="space-y-3 mt-4">
              {semanticMemories.map((knowledge) => (
                <div
                  key={knowledge.semantic_id}
                  className="border border-gray-200 dark:border-gray-700 rounded-lg bg-white dark:bg-gray-800 p-4 hover:bg-gray-50 dark:hover:bg-gray-700 transition"
                >
                  <div className="flex items-start justify-between mb-2">
                    <div className="flex-1">
                      <h3 className="font-semibold mb-1 text-gray-900 dark:text-gray-100">{knowledge.key}</h3>
                      <div className="flex items-center gap-2">
                        <Badge variant="outline">{knowledge.type}</Badge>
                        {knowledge.category && (
                          <Badge variant="secondary">{knowledge.category}</Badge>
                        )}
                        <Badge className="bg-green-100 text-green-800">
                          Confidence: {(knowledge.confidence * 100).toFixed(0)}%
                        </Badge>
                        <Badge variant="outline">
                          Evidence: {knowledge.evidence_count}
                        </Badge>
                      </div>
                    </div>
                  </div>
                  {knowledge.description && (
                    <p className="text-sm mt-2">{knowledge.description}</p>
                  )}
                  <details className="mt-2">
                    <summary className="text-xs text-gray-600 cursor-pointer">
                      View value
                    </summary>
                    <pre className="text-xs bg-gray-100 p-2 rounded mt-1 overflow-x-auto">
                      {JSON.stringify(knowledge.value, null, 2)}
                    </pre>
                  </details>
                  <div className="flex items-center gap-2 mt-2 text-xs text-gray-500 dark:text-gray-400">
                    <span>First learned: {formatTime(knowledge.first_learned)}</span>
                    {knowledge.last_updated && (
                      <span>• Last updated: {formatTime(knowledge.last_updated)}</span>
                    )}
                  </div>
                </div>
              ))}
            </TabsContent>
          </Tabs>
        </CardContent>
      </Card>
    </div>
  );
}
