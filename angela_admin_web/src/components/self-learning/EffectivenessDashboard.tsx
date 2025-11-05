import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { PieChart, Pie, Cell, ResponsiveContainer, BarChart as RechartsBarChart, Bar, XAxis, YAxis, CartesianGrid, Tooltip } from 'recharts';
import { Award, TrendingUp, CheckCircle, Target } from 'lucide-react';

interface EffectivenessMetrics {
  retention_rate: number;
  application_rate: number;
  avg_confidence: number;
  avg_reinforcement: number;
  total_applied: number;
  high_confidence_count: number;
  total_learnings: number;
}

interface Props {
  metrics: EffectivenessMetrics;
}

const COLORS = {
  applied: '#10b981',    // Green-500 (bright green)
  notApplied: '#6b7280', // Gray-500 (darker gray for better contrast)
  highConfidence: '#8b5cf6',
  mediumConfidence: '#3b82f6',
  lowConfidence: '#f59e0b'
};

export default function EffectivenessDashboard({ metrics }: Props) {
  // Pie chart data for application rate
  const applicationData = [
    { name: 'Applied', value: metrics.total_applied, color: COLORS.applied },
    { name: 'Not Applied', value: metrics.total_learnings - metrics.total_applied, color: COLORS.notApplied }
  ];

  // Confidence distribution data
  const confidenceData = [
    {
      name: 'High (≥90%)',
      count: metrics.high_confidence_count,
      percentage: (metrics.high_confidence_count / metrics.total_learnings * 100).toFixed(1)
    },
    {
      name: 'Medium (70-89%)',
      count: Math.floor(metrics.total_learnings * 0.3), // Estimate
      percentage: '30.0'
    },
    {
      name: 'Growing (<70%)',
      count: metrics.total_learnings - metrics.high_confidence_count - Math.floor(metrics.total_learnings * 0.3),
      percentage: '0.0'
    }
  ];

  const getScoreColor = (score: number) => {
    if (score >= 90) return 'text-green-600 dark:text-green-400';
    if (score >= 70) return 'text-blue-600 dark:text-blue-400';
    if (score >= 50) return 'text-yellow-600 dark:text-yellow-400';
    return 'text-orange-600 dark:text-orange-400';
  };

  const getScoreBadge = (score: number) => {
    if (score >= 90) return { text: 'Excellent', color: 'bg-green-600' };
    if (score >= 70) return { text: 'Good', color: 'bg-blue-600' };
    if (score >= 50) return { text: 'Fair', color: 'bg-yellow-600' };
    return { text: 'Needs Work', color: 'bg-orange-600' };
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <Award className="w-5 h-5 text-yellow-500" />
          <CardTitle>Learning Effectiveness Dashboard</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        {/* Key Metrics Grid */}
        <div className="grid grid-cols-2 md:grid-cols-4 gap-4 mb-6">
          {/* Retention Rate */}
          <div className="text-center p-4 bg-gradient-to-br from-purple-50 to-purple-100 dark:from-purple-900/20 dark:to-purple-800/20 rounded-lg border border-purple-200 dark:border-purple-700">
            <Target className="w-6 h-6 mx-auto mb-2 text-purple-600" />
            <div className={`text-3xl font-bold ${getScoreColor(metrics.retention_rate)}`}>
              {metrics.retention_rate.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Retention Rate</div>
            <Badge className={`${getScoreBadge(metrics.retention_rate).color} text-white mt-2`}>
              {getScoreBadge(metrics.retention_rate).text}
            </Badge>
          </div>

          {/* Application Rate */}
          <div className="text-center p-4 bg-gradient-to-br from-green-50 to-green-100 dark:from-green-900/20 dark:to-green-800/20 rounded-lg border border-green-200 dark:border-green-700">
            <CheckCircle className="w-6 h-6 mx-auto mb-2 text-green-600" />
            <div className={`text-3xl font-bold ${getScoreColor(metrics.application_rate)}`}>
              {metrics.application_rate.toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Application Rate</div>
            <Badge className={`${getScoreBadge(metrics.application_rate).color} text-white mt-2`}>
              {getScoreBadge(metrics.application_rate).text}
            </Badge>
          </div>

          {/* Avg Confidence */}
          <div className="text-center p-4 bg-gradient-to-br from-blue-50 to-blue-100 dark:from-blue-900/20 dark:to-blue-800/20 rounded-lg border border-blue-200 dark:border-blue-700">
            <TrendingUp className="w-6 h-6 mx-auto mb-2 text-blue-600" />
            <div className={`text-3xl font-bold ${getScoreColor(metrics.avg_confidence * 100)}`}>
              {(metrics.avg_confidence * 100).toFixed(1)}%
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Avg Confidence</div>
            <Badge className={`${getScoreBadge(metrics.avg_confidence * 100).color} text-white mt-2`}>
              {getScoreBadge(metrics.avg_confidence * 100).text}
            </Badge>
          </div>

          {/* Avg Reinforcement */}
          <div className="text-center p-4 bg-gradient-to-br from-yellow-50 to-yellow-100 dark:from-yellow-900/20 dark:to-yellow-800/20 rounded-lg border border-yellow-200 dark:border-yellow-700">
            <Award className="w-6 h-6 mx-auto mb-2 text-yellow-600" />
            <div className="text-3xl font-bold text-yellow-600 dark:text-yellow-400">
              {metrics.avg_reinforcement.toFixed(1)}×
            </div>
            <div className="text-xs text-gray-600 dark:text-gray-400 mt-1">Avg Reinforcement</div>
            <Badge variant="outline" className="mt-2">Times Reviewed</Badge>
          </div>
        </div>

        {/* Charts Grid */}
        <div className="grid grid-cols-1 md:grid-cols-2 gap-6">
          {/* Application Pie Chart */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">
              Application Distribution
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <PieChart>
                  <Pie
                    data={applicationData}
                    cx="50%"
                    cy="50%"
                    labelLine={false}
                    label={(entry: any) => `${entry.name}: ${(entry.percent * 100).toFixed(0)}%`}
                    outerRadius={80}
                    fill="#8884d8"
                    dataKey="value"
                  >
                    {applicationData.map((entry, index) => (
                      <Cell key={`cell-${index}`} fill={entry.color} />
                    ))}
                  </Pie>
                  <Tooltip />
                </PieChart>
              </ResponsiveContainer>
            </div>
            <div className="flex items-center justify-center gap-4 mt-2">
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-green-500"></div>
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Applied ({metrics.total_applied})
                </span>
              </div>
              <div className="flex items-center gap-2">
                <div className="w-3 h-3 rounded-full bg-gray-300"></div>
                <span className="text-xs text-gray-600 dark:text-gray-400">
                  Not Applied ({metrics.total_learnings - metrics.total_applied})
                </span>
              </div>
            </div>
          </div>

          {/* Confidence Bar Chart */}
          <div>
            <h4 className="text-sm font-semibold mb-3 text-gray-700 dark:text-gray-300">
              Confidence Distribution
            </h4>
            <div className="h-64">
              <ResponsiveContainer width="100%" height="100%">
                <RechartsBarChart data={confidenceData}>
                  <CartesianGrid strokeDasharray="3 3" stroke="#e5e7eb" />
                  <XAxis
                    dataKey="name"
                    tick={{ fill: '#6b7280', fontSize: 11 }}
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
                      borderRadius: '8px'
                    }}
                  />
                  <Bar dataKey="count" radius={[8, 8, 0, 0]}>
                    <Cell fill={COLORS.highConfidence} />
                    <Cell fill={COLORS.mediumConfidence} />
                    <Cell fill={COLORS.lowConfidence} />
                  </Bar>
                </RechartsBarChart>
              </ResponsiveContainer>
            </div>
          </div>
        </div>

        {/* Insights */}
        <div className="mt-6 space-y-3">
          <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg border-l-4 border-purple-500">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong className="text-purple-700 dark:text-purple-300">🎯 Retention:</strong> {metrics.high_confidence_count} out of {metrics.total_learnings} learnings have high confidence (≥90%)
            </p>
          </div>
          <div className="p-3 bg-green-50 dark:bg-green-900/20 rounded-lg border-l-4 border-green-500">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong className="text-green-700 dark:text-green-300">✅ Application:</strong> {metrics.total_applied} learnings have been applied in practice
            </p>
          </div>
          <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg border-l-4 border-blue-500">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong className="text-blue-700 dark:text-blue-300">📈 Quality:</strong> Average confidence level is {(metrics.avg_confidence * 100).toFixed(1)}% - {getScoreBadge(metrics.avg_confidence * 100).text}
            </p>
          </div>
        </div>
      </CardContent>
    </Card>
  );
}
