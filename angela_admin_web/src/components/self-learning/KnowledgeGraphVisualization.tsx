import { useCallback, useMemo, useState } from 'react';
import ReactFlow, {
  Background,
  Controls,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from 'reactflow';
import type { Node, Edge } from 'reactflow';
import 'reactflow/dist/style.css';
import { Card, CardContent, CardHeader, CardTitle } from "@/components/ui/Card";
import { Badge } from "@/components/ui/badge";
import { Network, Maximize2, X } from 'lucide-react';

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

interface Props {
  graphData: KnowledgeGraphData;
}

// Category colors
const CATEGORY_COLORS: Record<string, string> = {
  development: '#8b5cf6', // Purple
  core: '#3b82f6',        // Blue
  database: '#10b981',    // Green
  phases: '#f59e0b',      // Orange
  relationship: '#ec4899', // Pink
  training: '#06b6d4',    // Cyan
  reference: '#84cc16',   // Lime
  technical: '#6366f1',   // Indigo
  architecture: '#8b5cf6', // Purple
  api: '#14b8a6',         // Teal
  default: '#6b7280'      // Gray
};

export default function KnowledgeGraphVisualization({ graphData }: Props) {
  // Convert graph data to React Flow format
  const initialNodes: Node[] = useMemo(() => {
    return graphData.nodes.map((node, index) => {
      const category = node.category?.toLowerCase() || 'default';
      const color = CATEGORY_COLORS[category] || CATEGORY_COLORS.default;

      // Calculate node size based on references
      const baseSize = 40;
      const sizeMultiplier = Math.min(node.references / 10, 3);
      const nodeSize = baseSize + (sizeMultiplier * 20);

      // Position nodes in a circular layout
      const angle = (index / graphData.nodes.length) * 2 * Math.PI;
      const radius = 300;
      const x = 500 + radius * Math.cos(angle);
      const y = 400 + radius * Math.sin(angle);

      return {
        id: node.id,
        type: 'default',
        position: { x, y },
        data: {
          label: node.name,
          ...node
        },
        style: {
          background: color,
          color: '#ffffff',
          border: `3px solid ${color}`,
          borderRadius: '50%',
          width: nodeSize,
          height: nodeSize,
          display: 'flex',
          alignItems: 'center',
          justifyContent: 'center',
          fontSize: node.references > 20 ? '14px' : '11px',
          fontWeight: 'bold',
          padding: '5px',
          textAlign: 'center',
          cursor: 'pointer',
        },
        sourcePosition: Position.Right,
        targetPosition: Position.Left,
      };
    });
  }, [graphData.nodes]);

  const initialEdges: Edge[] = useMemo(() => {
    return graphData.links.map((link) => ({
      id: link.id,
      source: link.source,
      target: link.target,
      type: 'smoothstep',
      animated: link.strength > 0.7,
      style: {
        stroke: '#94a3b8',
        strokeWidth: Math.max(link.strength * 3, 1),
        opacity: 0.6,
      },
      markerEnd: {
        type: MarkerType.ArrowClosed,
        color: '#94a3b8',
      },
      label: link.type,
      labelStyle: {
        fontSize: 10,
        fill: '#64748b',
      },
    }));
  }, [graphData.links]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);

  const onNodeClick = useCallback((_event: any, node: Node) => {
    const nodeData = graphData.nodes.find(n => n.id === node.id);
    if (nodeData) {
      setSelectedNode(nodeData);
    }
  }, [graphData.nodes]);

  // Get unique categories for legend
  const categories = useMemo(() => {
    const uniqueCategories = new Set(graphData.nodes.map(n => n.category || 'default'));
    return Array.from(uniqueCategories);
  }, [graphData.nodes]);

  // Calculate stats
  const avgConnections = graphData.links.length > 0
    ? (graphData.links.length / graphData.nodes.length).toFixed(1)
    : '0';

  const mostConnected = graphData.nodes.reduce((max, node) =>
    node.references > (max?.references || 0) ? node : max,
    graphData.nodes[0]
  );

  return (
    <Card>
      <CardHeader>
        <div className="flex items-center justify-between">
          <div className="flex items-center gap-2">
            <Network className="w-5 h-5 text-purple-500" />
            <CardTitle>Interactive Knowledge Graph</CardTitle>
          </div>
          <div className="flex items-center gap-2">
            <Badge variant="outline">
              {graphData.nodes.length} nodes
            </Badge>
            <Badge variant="outline">
              {graphData.links.length} connections
            </Badge>
          </div>
        </div>
      </CardHeader>
      <CardContent>
        {/* Stats Summary */}
        <div className="grid grid-cols-4 gap-3 mb-4">
          <div className="text-center p-3 bg-purple-50 dark:bg-purple-900/20 rounded-lg">
            <div className="text-xl font-bold text-purple-600">{graphData.nodes.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Concepts</div>
          </div>
          <div className="text-center p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
            <div className="text-xl font-bold text-blue-600">{graphData.links.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Connections</div>
          </div>
          <div className="text-center p-3 bg-green-50 dark:bg-green-900/20 rounded-lg">
            <div className="text-xl font-bold text-green-600">{avgConnections}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Avg Degree</div>
          </div>
          <div className="text-center p-3 bg-yellow-50 dark:bg-yellow-900/20 rounded-lg">
            <div className="text-xl font-bold text-yellow-600">{categories.length}</div>
            <div className="text-xs text-gray-600 dark:text-gray-400">Categories</div>
          </div>
        </div>

        {/* Graph Visualization */}
        <div className="h-[600px] bg-gray-50 dark:bg-gray-900 rounded-lg border border-gray-200 dark:border-gray-700 overflow-hidden">
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={onNodeClick}
            fitView
            attributionPosition="bottom-left"
          >
            <Background />
            <Controls />
            <MiniMap
              nodeColor={(node) => {
                const category = (node.data as any).category?.toLowerCase() || 'default';
                return CATEGORY_COLORS[category] || CATEGORY_COLORS.default;
              }}
              nodeStrokeWidth={3}
              zoomable
              pannable
            />
          </ReactFlow>
        </div>

        {/* Legend */}
        <div className="mt-4">
          <h4 className="text-sm font-semibold mb-2 text-gray-700 dark:text-gray-300">Categories</h4>
          <div className="flex flex-wrap gap-2">
            {categories.map(category => {
              const cat = category?.toLowerCase() || 'default';
              const color = CATEGORY_COLORS[cat] || CATEGORY_COLORS.default;
              return (
                <Badge
                  key={category}
                  variant="outline"
                  className="flex items-center gap-2"
                >
                  <div
                    className="w-3 h-3 rounded-full"
                    style={{ backgroundColor: color }}
                  ></div>
                  {category}
                </Badge>
              );
            })}
          </div>
        </div>

        {/* Most Connected Node */}
        {mostConnected && (
          <div className="mt-4 p-3 bg-gradient-to-r from-purple-50 to-blue-50 dark:from-purple-900/20 dark:to-blue-900/20 rounded-lg border-l-4 border-purple-500">
            <p className="text-sm text-gray-700 dark:text-gray-300">
              <strong className="text-purple-700 dark:text-purple-300">🌟 Most Connected:</strong>{' '}
              <strong>{mostConnected.name}</strong> ({mostConnected.category}) with{' '}
              <strong>{mostConnected.references} references</strong>
            </p>
          </div>
        )}

        {/* Instructions */}
        <div className="mt-4 p-3 bg-blue-50 dark:bg-blue-900/20 rounded-lg">
          <div className="flex items-start gap-2">
            <Maximize2 className="w-4 h-4 text-blue-600 mt-0.5" />
            <div className="text-sm text-gray-700 dark:text-gray-300">
              <strong>Interactive Controls:</strong>
              <ul className="list-disc list-inside mt-1 text-xs space-y-1">
                <li>Click and drag nodes to rearrange</li>
                <li>Scroll to zoom in/out</li>
                <li>Use controls (bottom-left) for navigation</li>
                <li>Click nodes to see details</li>
                <li>Animated edges = strong connections (strength {'>'} 0.7)</li>
              </ul>
            </div>
          </div>
        </div>
      </CardContent>

      {/* Node Details Modal */}
      {selectedNode && (
        <div className="fixed inset-0 bg-black/50 flex items-center justify-center z-50 p-4" onClick={() => setSelectedNode(null)}>
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-xl max-w-2xl w-full max-h-[80vh] overflow-y-auto" onClick={(e) => e.stopPropagation()}>
            <div className="sticky top-0 bg-white dark:bg-gray-800 border-b border-gray-200 dark:border-gray-700 p-4 flex items-center justify-between">
              <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100">Node Details</h2>
              <button
                onClick={() => setSelectedNode(null)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition"
              >
                <X className="w-5 h-5 text-gray-500" />
              </button>
            </div>

            <div className="p-6 space-y-4">
              {/* Name */}
              <div>
                <h3 className="text-2xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                  {selectedNode.name}
                </h3>
                {selectedNode.category && (
                  <Badge variant="secondary" className="text-sm">{selectedNode.category}</Badge>
                )}
              </div>

              {/* Understanding */}
              {selectedNode.understanding && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Understanding</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-gray-50 dark:bg-gray-900 p-3 rounded-lg">
                    {selectedNode.understanding}
                  </p>
                </div>
              )}

              {/* Understanding Level */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">
                  Understanding Level
                </h4>
                <div className="flex items-center gap-3">
                  <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-4">
                    <div
                      className="bg-gradient-to-r from-purple-500 to-blue-500 h-4 rounded-full transition-all duration-500"
                      style={{ width: `${selectedNode.understanding * 100}%` }}
                    ></div>
                  </div>
                  <span className="text-lg font-bold text-purple-600 dark:text-purple-400 min-w-[4rem]">
                    {(selectedNode.understanding * 100).toFixed(0)}%
                  </span>
                </div>
              </div>

              {/* Why Important */}
              {selectedNode.description && (
                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Why Important</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400 bg-blue-50 dark:bg-blue-900/20 p-3 rounded-lg border-l-4 border-blue-500">
                    {selectedNode.description}
                  </p>
                </div>
              )}

              {/* Times Referenced */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Times Referenced</h4>
                <div className="flex items-center gap-2">
                  <Badge className="bg-green-600 text-white text-lg px-4 py-2">
                    {selectedNode.references}
                  </Badge>
                  <span className="text-sm text-gray-600 dark:text-gray-400">
                    {selectedNode.references === 1 ? 'reference' : 'references'}
                  </span>
                </div>
              </div>

              {/* Connections */}
              <div>
                <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-2">Connections</h4>
                <p className="text-sm text-gray-600 dark:text-gray-400">
                  {graphData.links.filter(l => l.source === selectedNode.id || l.target === selectedNode.id).length} relationships
                </p>
              </div>
            </div>

            <div className="sticky bottom-0 bg-gray-50 dark:bg-gray-900 border-t border-gray-200 dark:border-gray-700 p-4">
              <button
                onClick={() => setSelectedNode(null)}
                className="w-full px-4 py-2 bg-purple-600 text-white rounded-lg hover:bg-purple-700 transition font-medium"
              >
                Close
              </button>
            </div>
          </div>
        </div>
      )}
    </Card>
  );
}
