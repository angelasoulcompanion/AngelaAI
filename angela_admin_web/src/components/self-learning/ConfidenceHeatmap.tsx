import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { ScatterChart, Scatter, XAxis, YAxis, ZAxis, CartesianGrid, Tooltip, ResponsiveContainer, Cell } from 'recharts';
import { Target, TrendingUp } from 'lucide-react';

interface DataPoint {
  id: string;
  name: string;
  category: string | null;
  confidence: number;
  understanding: number;
  references: number;
}

interface Props {
  learnings: Array<{
    learning_id: string;
    topic: string;
    category: string | null;
    confidence_level: number;
    times_reinforced: number;
  }>;
  knowledgeNodes: Array<{
    node_id: string;
    name: string;
    category: string | null;
    level: number;
    references: number;
  }>;
}

export default function ConfidenceHeatmap({ learnings, knowledgeNodes }: Props) {
  const scatterData = useMemo(() => {
    const data: DataPoint[] = [];

    // Add learnings
    learnings.forEach(l => {
      data.push({
        id: l.learning_id,
        name: l.topic,
        category: l.category,
        confidence: l.confidence_level * 100,
        understanding: Math.min(l.times_reinforced * 20, 100), // Estimate understanding from reinforcement
        references: l.times_reinforced
      });
    });

    // Add knowledge nodes
    knowledgeNodes.slice(0, 20).forEach(k => {
      data.push({
        id: k.node_id,
        name: k.name,
        category: k.category,
        confidence: 90, // Assume high confidence for knowledge nodes
        understanding: k.level * 100,
        references: k.references
      });
    });

    return data;
  }, [learnings, knowledgeNodes]);

  const quadrants = useMemo(() => {
    const mastered = scatterData.filter(d => d.confidence >= 90 && d.understanding >= 90);
    const needReview = scatterData.filter(d => d.confidence >= 70 && d.understanding < 70);
    const needPractice = scatterData.filter(d => d.confidence < 70 && d.understanding >= 70);
    const learning = scatterData.filter(d => d.confidence < 70 && d.understanding < 70);

    return { mastered, needReview, needPractice, learning };
  }, [scatterData]);

  const getColor = (confidence: number, understanding: number) => {
    if (confidence >= 90 && understanding >= 90) return '#10b981'; // Green - Mastered
    if (confidence >= 70 && understanding < 70) return '#f59e0b';  // Orange - Need Review
    if (confidence < 70 && understanding >= 70) return '#3b82f6';  // Blue - Need Practice
    return '#6b7280'; // Gray - Still Learning
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Target className="w-5 h-5 text-blue-500" />
          <CardTitle>Confidence vs Understanding Matrix</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {/* Quadrant Stats */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-3 mb-6">
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border border-green-200">
            <div className="text-2xl font-bold text-green-600">{quadrants.mastered.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">✅ Mastered</div>
          </div>
          <div className="text-center p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border border-orange-200">
            <div className="text-2xl font-bold text-orange-600">{quadrants.needReview.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">⚠️ Need Review</div>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border border-blue-200">
            <div className="text-2xl font-bold text-blue-600">{quadrants.needPractice.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">🔄 Need Practice</div>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200">
            <div className="text-2xl font-bold text-gray-600">{quadrants.learning.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">📚 Learning</div>
          </div>
        </div>

        {/* Scatter Plot */}
        <div className="h-96 bg-gray-50 dark:bg-gray-900 rounded-lg p-4">
          <ResponsiveContainer width="100%" height="100%">
            <ScatterChart margin={{ top: 20, right: 20, bottom: 20, left: 20 }}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                type="number"
                dataKey="understanding"
                name="Understanding"
                unit="%"
                domain={[0, 100]}
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
                label={{ value: 'Understanding Level →', position: 'bottom', fill: '#6b7280' }}
              />
              <YAxis
                type="number"
                dataKey="confidence"
                name="Confidence"
                unit="%"
                domain={[0, 100]}
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
                label={{ value: '← Confidence Level', angle: -90, position: 'left', fill: '#6b7280' }}
              />
              <ZAxis type="number" dataKey="references" range={[50, 400]} />
              <Tooltip
                cursor={{ strokeDasharray: '3 3' }}
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  padding: '8px'
                }}
                content={({ active, payload }) => {
                  if (active && payload && payload.length) {
                    const data = payload[0].payload as DataPoint;
                    return (
                      <div className="bg-white dark:bg-gray-800 p-3 rounded-lg border border-gray-200 dark:border-gray-700 shadow-lg">
                        <p className="font-semibold text-sm text-gray-900 dark:text-gray-100">{data.name}</p>
                        {data.category && (
                          <Badge variant="outline" className="mt-1 text-xs">{data.category}</Badge>
                        )}
                        <div className="mt-2 space-y-1 text-xs">
                          <p>Confidence: <strong>{data.confidence.toFixed(0)}%</strong></p>
                          <p>Understanding: <strong>{data.understanding.toFixed(0)}%</strong></p>
                          <p>References: <strong>{data.references}</strong></p>
                        </div>
                      </div>
                    );
                  }
                  return null;
                }}
              />
              <Scatter name="Concepts" data={scatterData}>
                {scatterData.map((entry, index) => (
                  <Cell key={`cell-${index}`} fill={getColor(entry.confidence, entry.understanding)} />
                ))}
              </Scatter>
            </ScatterChart>
          </ResponsiveContainer>
        </div>

        {/* Legend & Insights */}
        <div className="mt-6 space-y-3">
          <div className="flex flex-wrap gap-3">
            <Badge className="bg-green-600 text-white">✅ Mastered (High/High)</Badge>
            <Badge className="bg-orange-600 text-white">⚠️ Need Review (High Conf/Low Understand)</Badge>
            <Badge className="bg-blue-600 text-white">🔄 Need Practice (Low Conf/High Understand)</Badge>
            <Badge className="bg-gray-600 text-white">📚 Still Learning (Low/Low)</Badge>
          </div>

          {quadrants.needReview.length > 0 && (
            <div className="p-3 bg-orange-50 dark:bg-orange-900/20 rounded-lg border-l-4 border-orange-500">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong className="text-orange-700 dark:text-orange-300">⚠️ Attention:</strong> {quadrants.needReview.length} concepts have high confidence but low understanding - consider reviewing!
              </p>
            </div>
          )}

          {quadrants.mastered.length > 0 && (
            <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border-l-4 border-green-500">
              <p className="text-sm text-gray-700 dark:text-gray-300">
                <strong className="text-green-700 dark:text-green-300">🎉 Excellent:</strong> {quadrants.mastered.length} concepts fully mastered!
              </p>
            </div>
          )}
        </div>
      </CardContent>
    </Card>
  );
}
