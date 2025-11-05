import { useMemo } from 'react';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Sparkles, TrendingUp, AlertTriangle, Lightbulb, Target, ArrowRight } from 'lucide-react';

interface Learning {
  learning_id: string;
  topic: string;
  category: string | null;
  confidence_level: number;
  times_reinforced: number;
  has_applied: boolean;
}

interface KnowledgeNode {
  node_id: string;
  name: string;
  category: string | null;
  level: number;
  references: number;
}

interface Suggestion {
  id: string;
  type: 'review' | 'learn_next' | 'practice' | 'reinforce';
  title: string;
  description: string;
  priority: 'high' | 'medium' | 'low';
  items: string[];
  category?: string;
  reason: string;
}

interface Props {
  learnings: Learning[];
  knowledgeNodes: KnowledgeNode[];
}

export default function AIPoweredSuggestions({ learnings, knowledgeNodes }: Props) {
  const suggestions = useMemo(() => {
    const suggestions: Suggestion[] = [];

    // 1. Find concepts that need review (high confidence but not applied)
    const needReview = learnings.filter(l =>
      l.confidence_level >= 0.7 && !l.has_applied
    );
    if (needReview.length > 0) {
      suggestions.push({
        id: 'review-1',
        type: 'review',
        title: 'Review High-Confidence Concepts',
        description: 'These concepts have high confidence but haven\'t been applied yet',
        priority: 'high',
        items: needReview.slice(0, 5).map(l => l.topic),
        reason: `${needReview.length} concepts need practical application to solidify understanding`,
      });
    }

    // 2. Find low confidence concepts
    const lowConfidence = learnings.filter(l =>
      l.confidence_level < 0.6 && l.times_reinforced < 3
    );
    if (lowConfidence.length > 0) {
      suggestions.push({
        id: 'reinforce-1',
        type: 'reinforce',
        title: 'Reinforce Low-Confidence Topics',
        description: 'These topics need more practice and reinforcement',
        priority: 'high',
        items: lowConfidence.slice(0, 5).map(l => l.topic),
        reason: `${lowConfidence.length} concepts have low confidence and need reinforcement`,
      });
    }

    // 3. Find knowledge gaps by category
    const categoryCounts: Record<string, number> = {};
    [...learnings, ...knowledgeNodes].forEach(item => {
      if (item.category) {
        categoryCounts[item.category] = (categoryCounts[item.category] || 0) + 1;
      }
    });

    const sortedCategories = Object.entries(categoryCounts)
      .sort((a, b) => a[1] - b[1])
      .slice(0, 3);

    if (sortedCategories.length > 0) {
      suggestions.push({
        id: 'learn-1',
        type: 'learn_next',
        title: 'Explore Underrepresented Categories',
        description: 'Balance your knowledge by learning more in these areas',
        priority: 'medium',
        items: sortedCategories.map(([cat, count]) => `${cat} (${count} items)`),
        reason: 'Diversifying knowledge across categories strengthens overall understanding',
      });
    }

    // 4. Find concepts with low understanding (knowledge nodes)
    const lowUnderstanding = knowledgeNodes.filter(k => k.level < 0.5);
    if (lowUnderstanding.length > 0) {
      suggestions.push({
        id: 'practice-1',
        type: 'practice',
        title: 'Practice Low-Understanding Concepts',
        description: 'These knowledge areas need more practical experience',
        priority: 'medium',
        items: lowUnderstanding.slice(0, 5).map(k => k.name),
        reason: `${lowUnderstanding.length} concepts have low understanding level`,
      });
    }

    // 5. Find rarely used knowledge nodes
    const rarelyUsed = knowledgeNodes.filter(k => k.references < 3);
    if (rarelyUsed.length > 0) {
      suggestions.push({
        id: 'practice-2',
        type: 'practice',
        title: 'Apply Rarely-Used Knowledge',
        description: 'These concepts are understood but rarely referenced',
        priority: 'low',
        items: rarelyUsed.slice(0, 5).map(k => k.name),
        reason: `${rarelyUsed.length} knowledge nodes have few references - applying them will strengthen retention`,
      });
    }

    // 6. Find highly reinforced learnings (success stories)
    const wellReinforced = learnings.filter(l =>
      l.times_reinforced >= 5 && l.confidence_level >= 0.8
    );
    if (wellReinforced.length > 0) {
      suggestions.push({
        id: 'learn-2',
        type: 'learn_next',
        title: 'Build on Strong Foundations',
        description: 'You\'ve mastered these - consider related advanced topics',
        priority: 'low',
        items: wellReinforced.slice(0, 5).map(l => l.topic),
        reason: 'These concepts are solid - good foundation for learning related advanced topics',
      });
    }

    // Sort by priority
    return suggestions.sort((a, b) => {
      const priorityOrder = { high: 0, medium: 1, low: 2 };
      return priorityOrder[a.priority] - priorityOrder[b.priority];
    });
  }, [learnings, knowledgeNodes]);

  const getSuggestionIcon = (type: Suggestion['type']) => {
    switch (type) {
      case 'review': return <AlertTriangle className="w-5 h-5" />;
      case 'learn_next': return <Lightbulb className="w-5 h-5" />;
      case 'practice': return <Target className="w-5 h-5" />;
      case 'reinforce': return <TrendingUp className="w-5 h-5" />;
    }
  };

  const getSuggestionColor = (type: Suggestion['type']) => {
    switch (type) {
      case 'review': return 'from-orange-500 to-red-500';
      case 'learn_next': return 'from-blue-500 to-purple-500';
      case 'practice': return 'from-green-500 to-teal-500';
      case 'reinforce': return 'from-yellow-500 to-orange-500';
    }
  };

  const getPriorityBadge = (priority: Suggestion['priority']) => {
    switch (priority) {
      case 'high':
        return <Badge className="bg-red-600 text-white">High Priority</Badge>;
      case 'medium':
        return <Badge className="bg-yellow-600 text-white">Medium Priority</Badge>;
      case 'low':
        return <Badge className="bg-gray-600 text-white">Low Priority</Badge>;
    }
  };

  const stats = {
    total: suggestions.length,
    high: suggestions.filter(s => s.priority === 'high').length,
    medium: suggestions.filter(s => s.priority === 'medium').length,
    low: suggestions.filter(s => s.priority === 'low').length,
  };

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Sparkles className="w-5 h-5 text-yellow-500" />
            <CardTitle>AI-Powered Learning Suggestions</CardTitle>
            <Badge variant="outline" className="ml-2">Smart Recommendations</Badge>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">{stats.total} suggestions</Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Priority Summary */}
        <div className="grid grid-cols-3 gap-3 mb-6">
          <div className="text-center p-3 bg-red-50 dark:bg-red-900/20 rounded-lg border border-red-200 dark:border-red-800">
            <div className="text-2xl font-bold text-red-600">{stats.high}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">High Priority</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg border border-yellow-200 dark:border-yellow-800">
            <div className="text-2xl font-bold text-yellow-600">{stats.medium}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Medium Priority</div>
          </div>
          <div className="text-center p-3 bg-gray-50 dark:bg-gray-800 rounded-lg border border-gray-200 dark:border-gray-700">
            <div className="text-2xl font-bold text-gray-600">{stats.low}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Low Priority</div>
          </div>
        </div>

        {/* Suggestions List */}
        <div className="space-y-4">
          {suggestions.length === 0 ? (
            <div className="text-center py-12">
              <Sparkles className="w-16 h-16 text-gray-300 dark:text-gray-600 mx-auto mb-4" />
              <p className="text-gray-600 dark:text-gray-400">
                No suggestions at this time - you're doing great! 🎉
              </p>
            </div>
          ) : (
            suggestions.map((suggestion) => (
              <div
                key={suggestion.id}
                className="border border-gray-200 dark:border-gray-700 rounded-lg overflow-hidden hover:shadow-lg transition"
              >
                {/* Header with gradient */}
                <div className={`bg-gradient-to-r ${getSuggestionColor(suggestion.type)} p-4 text-white`}>
                  <div className="flex items-start justify-between">
                    <div className="flex items-center gap-3">
                      {getSuggestionIcon(suggestion.type)}
                      <div>
                        <h3 className="font-semibold text-lg">{suggestion.title}</h3>
                        <p className="text-sm text-white/90 mt-1">{suggestion.description}</p>
                      </div>
                    </div>
                    {getPriorityBadge(suggestion.priority)}
                  </div>
                </div>

                {/* Content */}
                <div className="p-4 bg-white dark:bg-gray-800">
                  {/* Reason */}
                  <div className="mb-3 p-3 bg-gray-50 dark:bg-gray-900 rounded-lg border-l-4 border-l-blue-500">
                    <p className="text-sm text-gray-700 dark:text-gray-300">
                      <strong className="text-blue-600 dark:text-blue-400">Why this matters:</strong> {suggestion.reason}
                    </p>
                  </div>

                  {/* Items */}
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                      Suggested items:
                    </h4>
                    <div className="space-y-2">
                      {suggestion.items.map((item, idx) => (
                        <div
                          key={idx}
                          className="flex items-center gap-2 p-2 bg-gray-50 dark:bg-gray-900 rounded hover:bg-gray-100 dark:hover:bg-gray-800 transition"
                        >
                          <ArrowRight className="w-4 h-4 text-gray-400 flex-shrink-0" />
                          <span className="text-sm text-gray-800 dark:text-gray-200">{item}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                </div>
              </div>
            ))
          )}
        </div>

        {/* Info Box */}
        {suggestions.length > 0 && (
          <div className="mt-6 p-4 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border border-purple-200 dark:border-purple-800">
            <div className="flex items-start gap-2">
              <Sparkles className="w-5 h-5 text-purple-600 flex-shrink-0 mt-0.5" />
              <div className="text-sm text-gray-700 dark:text-gray-300">
                <strong className="text-purple-700 dark:text-purple-300">AI Analysis:</strong> These suggestions are generated based on your learning patterns, confidence levels, and knowledge gaps. Focus on high-priority items first for maximum learning efficiency.
              </div>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
  );
}
