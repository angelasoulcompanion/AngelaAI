import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { AreaChart, Area, XAxis, YAxis, CartesianGrid, Tooltip, Legend, ResponsiveContainer } from 'recharts';
import { Calendar, TrendingUp } from 'lucide-react';

interface TimelineData {
  date: string;
  category: string | null;
  count: number;
  avg_confidence: number;
}

interface Props {
  timeline: TimelineData[];
  days: number;
  onDaysChange: (days: number) => void;
}

const COLORS = {
  development: '#8b5cf6',
  core: '#3b82f6',
  database: '#10b981',
  phases: '#f59e0b',
  relationship: '#ec4899',
  training: '#06b6d4',
  reference: '#84cc16',
  default: '#6b7280'
};

export default function LearningTimelineChart({ timeline, days, onDaysChange }: Props) {
  // Group timeline data by date for stacked area chart
  const processTimelineData = () => {
    const dateMap: Record<string, any> = {};

    timeline.forEach(item => {
      if (!item.date) return;

      const date = new Date(item.date).toLocaleDateString('en-US', { month: 'short', day: 'numeric' });

      if (!dateMap[date]) {
        dateMap[date] = { date, total: 0 };
      }

      const category = item.category || 'other';
      dateMap[date][category] = (dateMap[date][category] || 0) + item.count;
      dateMap[date].total += item.count;
    });

    return Object.values(dateMap).reverse(); // Reverse to show oldest first
  };

  const chartData = processTimelineData();

  // Get unique categories for legend
  const categories = Array.from(new Set(timeline.map(t => t.category || 'other')));

  // Calculate stats
  const totalLearnings = timeline.reduce((sum, t) => sum + t.count, 0);
  const avgConfidence = timeline.length > 0
    ? (timeline.reduce((sum, t) => sum + t.avg_confidence, 0) / timeline.length)
    : 0;
  const mostActiveDay = chartData.reduce((max, d) => d.total > (max?.total || 0) ? d : max, chartData[0]);

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Calendar className="w-5 h-5 text-purple-500" />
            <CardTitle>Learning Progress Timeline</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            {[7, 14, 30, 60, 90].map(d => (
              <Badge
                key={d}
                variant={days === d ? "default" : "outline"}
                className={`cursor-pointer ${days === d ? 'bg-purple-600' : ''}`}
                onClick={() => onDaysChange(d)}
              >
                {d}d
              </Badge>
            ))}
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Stats Summary */}
        <div className="grid grid-cols-3 gap-4 mb-6">
          <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="text-2xl font-bold text-purple-600">{totalLearnings}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Total Learnings</div>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-2xl font-bold text-blue-600">{(avgConfidence * 100).toFixed(0)}%</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Avg Confidence</div>
          </div>
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-2xl font-bold text-green-600">
              {mostActiveDay ? mostActiveDay.total : 0}
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Most Active Day</div>
          </div>
        </div>

        {/* Area Chart */}
        <div className="h-80">
          <ResponsiveContainer width="100%" height="100%">
            <AreaChart data={chartData}>
              <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
              <XAxis
                dataKey="date"
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
              />
              <YAxis
                tick={{ fill: '#6b7280', fontSize: 12 }}
                stroke="#9ca3af"
              />
              <Tooltip
                contentStyle={{
                  backgroundColor: '#ffffff',
                  border: '1px solid #e5e7eb',
                  borderRadius: '8px',
                  boxShadow: '0 4px 6px rgba(0, 0, 0, 0.1)'
                }}
              />
              <Legend
                wrapperStyle={{ paddingTop: '20px' }}
                iconType="circle"
              />
              {categories.map(category => (
                <Area
                  key={category}
                  type="monotone"
                  dataKey={category}
                  stackId="1"
                  stroke={COLORS[category as keyof typeof COLORS] || COLORS.default}
                  fill={COLORS[category as keyof typeof COLORS] || COLORS.default}
                  fillOpacity={0.6}
                  name={category}
                />
              ))}
            </AreaChart>
          </ResponsiveContainer>
        </div>

        {/* Trend Insight */}
        <div className="mt-4 flex items-center gap-2 p-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg">
          <TrendingUp className="w-5 h-5 text-purple-600" />
          <p className="text-sm text-gray-700 dark:text-gray-300">
            <strong>Insight:</strong> You learned {totalLearnings} new concepts in the last {days} days
            with an average confidence of {(avgConfidence * 100).toFixed(1)}%
          </p>
        </div>
      </CardContent>
    </Card>
  );
}
