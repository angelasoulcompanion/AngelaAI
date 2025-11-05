import { useState } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Tabs, TabsContent, TabsList, TabsTrigger } from "@/components/ui/tabs";
import { FolderOpen, TrendingUp, BookOpen, ChevronRight } from 'lucide-react';

interface CategoryData {
  category: string;
  count: number;
  avg_confidence?: number;
  avg_understanding?: number;
  total_reinforcements?: number;
  total_references?: number;
}

interface Props {
  learningCategories: CategoryData[];
  knowledgeCategories: CategoryData[];
}

export default function CategoryDeepDive({ learningCategories, knowledgeCategories }: Props) {
  const [selectedCategory, setSelectedCategory] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'learning' | 'knowledge'>('learning');

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

  const getCategoryIcon = (category: string) => {
    const icons: Record<string, string> = {
      development: '💻',
      core: '🎯',
      database: '🗄️',
      phases: '📊',
      relationship: '❤️',
      training: '🎓',
      reference: '📚',
      technical: '⚙️',
      architecture: '🏗️',
      api: '🔌'
    };
    return icons[category.toLowerCase()] || '📁';
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center gap-2">
          <FolderOpen className="w-5 h-5 text-blue-500" />
          <CardTitle>Knowledge Categories Deep Dive</CardTitle>
        </div>
      </CardHeader>
      <CardContent>
        <Tabs value={activeTab} onValueChange={(v: string) => setActiveTab(v as 'learning' | 'knowledge')}>
          <TabsList className="grid w-full grid-cols-2 mb-6">
            <TabsTrigger value="learning">
              <BookOpen className="w-4 h-4 mr-2" />
              Learning Categories
            </TabsTrigger>
            <TabsTrigger value="knowledge">
              <TrendingUp className="w-4 h-4 mr-2" />
              Knowledge Categories
            </TabsTrigger>
          </TabsList>

          {/* Learning Categories Tab */}
          <TabsContent value="learning" className="space-y-3">
            {learningCategories.map((category, idx) => (
              <div
                key={category.category}
                className={`border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition cursor-pointer ${
                  selectedCategory === category.category
                    ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
                onClick={() => setSelectedCategory(
                  selectedCategory === category.category ? null : category.category
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-2xl">{getCategoryIcon(category.category)}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                          {category.category}
                        </h3>
                        <Badge variant="outline">#{idx + 1}</Badge>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary">{category.count} learnings</Badge>
                        {category.avg_confidence !== undefined && (
                          <Badge className={getConfidenceColor(category.avg_confidence)}>
                            {(category.avg_confidence * 100).toFixed(0)}% confident
                          </Badge>
                        )}
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Reinforced {category.total_reinforcements || 0}× total
                        </span>
                      </div>
                    </div>
                  </div>
                  <ChevronRight
                    className={`w-5 h-5 text-gray-400 transition-transform ${
                      selectedCategory === category.category ? 'rotate-90' : ''
                    }`}
                  />
                </div>

                {/* Expanded Details */}
                {selectedCategory === category.category && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-purple-600">{category.count}</div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Total Items</div>
                      </div>
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-blue-600">
                          {category.avg_confidence ? (category.avg_confidence * 100).toFixed(1) : 0}%
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Avg Confidence</div>
                      </div>
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-green-600">
                          {category.total_reinforcements || 0}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Reinforcements</div>
                      </div>
                    </div>
                    <div className="p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        <strong>Insight:</strong> This category contains {category.count} learnings
                        with an average confidence of {category.avg_confidence ? (category.avg_confidence * 100).toFixed(1) : 0}%.
                        {(category.avg_confidence || 0) >= 0.9 && ' Excellent mastery! 🎉'}
                        {(category.avg_confidence || 0) >= 0.7 && (category.avg_confidence || 0) < 0.9 && ' Good progress! Keep it up! 💪'}
                        {(category.avg_confidence || 0) < 0.7 && ' Room for improvement. Consider reviewing! 📚'}
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </TabsContent>

          {/* Knowledge Categories Tab */}
          <TabsContent value="knowledge" className="space-y-3">
            {knowledgeCategories.map((category, idx) => (
              <div
                key={category.category}
                className={`border border-gray-200 dark:border-gray-700 rounded-lg p-4 transition cursor-pointer ${
                  selectedCategory === category.category
                    ? 'bg-purple-50 dark:bg-purple-900/20 border-purple-500'
                    : 'hover:bg-gray-50 dark:hover:bg-gray-800'
                }`}
                onClick={() => setSelectedCategory(
                  selectedCategory === category.category ? null : category.category
                )}
              >
                <div className="flex items-center justify-between">
                  <div className="flex items-center gap-3 flex-1">
                    <span className="text-2xl">{getCategoryIcon(category.category)}</span>
                    <div className="flex-1">
                      <div className="flex items-center gap-2 mb-1">
                        <h3 className="font-semibold text-gray-900 dark:text-gray-100">
                          {category.category}
                        </h3>
                        <Badge variant="outline">#{idx + 1}</Badge>
                      </div>
                      <div className="flex items-center gap-3">
                        <Badge variant="secondary">{category.count} nodes</Badge>
                        {category.avg_understanding !== undefined && (
                          <Badge className={getUnderstandingColor(category.avg_understanding)}>
                            {(category.avg_understanding * 100).toFixed(0)}% understood
                          </Badge>
                        )}
                        <span className="text-xs text-gray-500 dark:text-gray-400">
                          Referenced {category.total_references || 0}× total
                        </span>
                      </div>
                    </div>
                  </div>
                  <ChevronRight
                    className={`w-5 h-5 text-gray-400 transition-transform ${
                      selectedCategory === category.category ? 'rotate-90' : ''
                    }`}
                  />
                </div>

                {/* Expanded Details */}
                {selectedCategory === category.category && (
                  <div className="mt-4 pt-4 border-t border-gray-200 dark:border-gray-700 space-y-2">
                    <div className="grid grid-cols-3 gap-4">
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-purple-600">{category.count}</div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Knowledge Nodes</div>
                      </div>
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-blue-600">
                          {category.avg_understanding ? (category.avg_understanding * 100).toFixed(1) : 0}%
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Avg Understanding</div>
                      </div>
                      <div className="text-center p-3 bg-white dark:bg-gray-800 rounded-lg">
                        <div className="text-lg font-bold text-green-600">
                          {category.total_references || 0}
                        </div>
                        <div className="text-xs text-gray-600 dark:text-gray-400">Total References</div>
                      </div>
                    </div>
                    <div className="p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
                      <p className="text-sm text-gray-700 dark:text-gray-300">
                        <strong>Insight:</strong> This category contains {category.count} knowledge nodes
                        with an average understanding of {category.avg_understanding ? (category.avg_understanding * 100).toFixed(1) : 0}%.
                        Referenced {category.total_references || 0} times across conversations.
                      </p>
                    </div>
                  </div>
                )}
              </div>
            ))}
          </TabsContent>
        </Tabs>
      </CardContent>
    </Card>
  );
}
