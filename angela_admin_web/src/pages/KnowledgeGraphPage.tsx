import { useState, useEffect, useRef } from 'react'
import { useQuery } from '@tanstack/react-query'
import { Card, CardContent, CardHeader, CardTitle } from '@/components/ui/Card'
import Button from '@/components/ui/Button'
import { api } from '@/lib/api'
import type { KnowledgeGraph, KnowledgeNode } from '@/lib/api'
import { Network, Search, X, ZoomIn, ZoomOut, Maximize2, Eye, FileText, TrendingUp } from 'lucide-react'
import * as d3 from 'd3'

interface GraphNode extends d3.SimulationNodeDatum {
  id: string
  name: string
  category: string
  understanding?: string
  understandingLevel?: number
  whyImportant?: string
  timesReferenced: number
}

interface GraphLink extends d3.SimulationLinkDatum<GraphNode> {
  id: string
  type: string
  strength?: number
  explanation?: string
}

export default function KnowledgeGraphPage() {
  const svgRef = useRef<SVGSVGElement>(null)
  const [selectedNode, setSelectedNode] = useState<KnowledgeNode | null>(null)
  const [searchQuery, setSearchQuery] = useState('')
  const [selectedCategory, setSelectedCategory] = useState<string>('all')
  const [zoomLevel, setZoomLevel] = useState(1)
  const [showDetailsModal, setShowDetailsModal] = useState(false)

  const { data: graphData, isLoading, error } = useQuery({
    queryKey: ['knowledge-graph'],
    queryFn: async () => {
      console.log('🔄 Fetching knowledge graph...')
      const data = await api.getKnowledgeGraph(200) // Limit to 200 nodes for performance
      console.log('✅ Knowledge graph data received:', data)
      return data
    },
  })

  const { data: stats } = useQuery({
    queryKey: ['knowledge-graph-stats'],
    queryFn: async () => {
      console.log('🔄 Fetching graph statistics...')
      const data = await api.getGraphStatistics()
      console.log('✅ Graph statistics received:', data)
      return data
    },
  })

  // Debug: Log graphData whenever it changes
  useEffect(() => {
    if (graphData) {
      console.log('📊 Graph Data:', {
        nodes: graphData.nodes?.length || 0,
        edges: graphData.edges?.length || 0,
        metadata: graphData.metadata
      })
    }
  }, [graphData])

  // Get unique categories from nodes
  const categories = graphData?.nodes
    ? Array.from(new Set(graphData.nodes.map(n => n.category)))
    : []

  // Filter nodes based on search and category
  const filteredNodes = graphData?.nodes.filter(node => {
    const matchesSearch = searchQuery === '' ||
      node.name.toLowerCase().includes(searchQuery.toLowerCase()) ||
      (node.understanding && node.understanding.toLowerCase().includes(searchQuery.toLowerCase()))
    const matchesCategory = selectedCategory === 'all' || node.category === selectedCategory
    return matchesSearch && matchesCategory
  }) || []

  const filteredNodeIds = new Set(filteredNodes.map(n => n.id))
  const filteredEdges = graphData?.edges.filter(edge =>
    filteredNodeIds.has(edge.source) && filteredNodeIds.has(edge.target)
  ) || []

  useEffect(() => {
    if (!svgRef.current || !graphData || filteredNodes.length === 0) return

    // Clear previous graph
    d3.select(svgRef.current).selectAll('*').remove()

    const width = svgRef.current.clientWidth
    const height = svgRef.current.clientHeight

    // Create SVG container with zoom
    const svg = d3.select(svgRef.current)
    const g = svg.append('g')

    // Add zoom behavior
    const zoom = d3.zoom<SVGSVGElement, unknown>()
      .scaleExtent([0.1, 4])
      .on('zoom', (event) => {
        g.attr('transform', event.transform)
        setZoomLevel(event.transform.k)
      })

    svg.call(zoom)

    // Prepare data for D3
    const nodes: GraphNode[] = filteredNodes.map(node => ({
      id: node.id,
      name: node.name,
      category: node.category,
      understanding: node.understanding,
      understandingLevel: node.understandingLevel,
      whyImportant: node.whyImportant,
      timesReferenced: node.timesReferenced,
    }))

    const links: GraphLink[] = filteredEdges.map(edge => ({
      id: edge.id,
      source: edge.source,
      target: edge.target,
      type: edge.type,
      strength: edge.strength,
      explanation: edge.explanation,
    }))

    // Category colors
    const categoryColors: Record<string, string> = {
      person: '#EC4899', // pink
      concept: '#8B5CF6', // purple
      skill: '#3B82F6', // blue
      emotion: '#F59E0B', // amber
      memory: '#10B981', // green
      goal: '#EF4444', // red
      preference: '#6366F1', // indigo
    }

    const getNodeColor = (category: string) =>
      categoryColors[category.toLowerCase()] || '#9CA3AF'

    // Create force simulation
    const simulation = d3.forceSimulation<GraphNode>(nodes)
      .force('link', d3.forceLink<GraphNode, GraphLink>(links)
        .id(d => d.id)
        .distance(100)
        .strength(d => (d.strength || 0.5)))
      .force('charge', d3.forceManyBody().strength(-300))
      .force('center', d3.forceCenter(width / 2, height / 2))
      .force('collision', d3.forceCollide().radius(30))

    // Create links (edges) - Dark mode aware
    const isDark = document.documentElement.classList.contains('dark')
    const link = g.append('g')
      .selectAll('line')
      .data(links)
      .join('line')
      .attr('stroke', isDark ? '#4B5563' : '#CBD5E1')
      .attr('stroke-width', d => Math.sqrt((d.strength || 0.5) * 4))
      .attr('stroke-opacity', isDark ? 0.5 : 0.6)

    // Create nodes
    const node = g.append('g')
      .selectAll('g')
      .data(nodes)
      .join('g')
      .call(d3.drag<SVGGElement, GraphNode>()
        .on('start', dragstarted)
        .on('drag', dragged)
        .on('end', dragended) as any)
      .style('cursor', 'pointer')

    // Node circles
    node.append('circle')
      .attr('r', d => Math.max(8, Math.min(20, (d.timesReferenced || 1) * 2)))
      .attr('fill', d => getNodeColor(d.category))
      .attr('stroke', '#fff')
      .attr('stroke-width', 2)
      .on('click', (event, d) => {
        event.stopPropagation()
        const originalNode = graphData.nodes.find(n => n.id === d.id)
        setSelectedNode(originalNode || null)
      })
      .on('mouseenter', function() {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('stroke-width', 4)
          .attr('r', function() {
            const currentR = parseFloat(d3.select(this).attr('r'))
            return currentR * 1.2
          })
      })
      .on('mouseleave', function(event, d) {
        d3.select(this)
          .transition()
          .duration(200)
          .attr('stroke-width', 2)
          .attr('r', Math.max(8, Math.min(20, (d.timesReferenced || 1) * 2)))
      })

    // Node labels - Dark mode aware
    node.append('text')
      .text(d => d.name.length > 20 ? d.name.substring(0, 20) + '...' : d.name)
      .attr('font-size', 10)
      .attr('dx', 12)
      .attr('dy', 4)
      .attr('fill', document.documentElement.classList.contains('dark') ? '#E5E7EB' : '#1F2937')
      .attr('class', 'dark:fill-gray-200 fill-gray-900')
      .style('pointer-events', 'none')

    // Update positions on each tick
    simulation.on('tick', () => {
      link
        .attr('x1', d => (d.source as GraphNode).x || 0)
        .attr('y1', d => (d.source as GraphNode).y || 0)
        .attr('x2', d => (d.target as GraphNode).x || 0)
        .attr('y2', d => (d.target as GraphNode).y || 0)

      node
        .attr('transform', d => `translate(${d.x || 0},${d.y || 0})`)
    })

    // Drag functions
    function dragstarted(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0.3).restart()
      event.subject.fx = event.subject.x
      event.subject.fy = event.subject.y
    }

    function dragged(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      event.subject.fx = event.x
      event.subject.fy = event.y
    }

    function dragended(event: d3.D3DragEvent<SVGGElement, GraphNode, GraphNode>) {
      if (!event.active) simulation.alphaTarget(0)
      event.subject.fx = null
      event.subject.fy = null
    }

    return () => {
      simulation.stop()
    }
  }, [graphData, filteredNodes, filteredEdges])

  const handleZoomIn = () => {
    const svg = d3.select(svgRef.current)
    svg.transition().duration(300).call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      1.3
    )
  }

  const handleZoomOut = () => {
    const svg = d3.select(svgRef.current)
    svg.transition().duration(300).call(
      d3.zoom<SVGSVGElement, unknown>().scaleBy as any,
      0.7
    )
  }

  const handleZoomReset = () => {
    const svg = d3.select(svgRef.current)
    svg.transition().duration(500).call(
      d3.zoom<SVGSVGElement, unknown>().transform as any,
      d3.zoomIdentity
    )
  }

  if (isLoading) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <Network className="w-16 h-16 text-accent-500 dark:text-accent-400 animate-pulse mx-auto mb-4" />
          <p className="text-gray-600 dark:text-gray-400">Loading knowledge graph...</p>
        </div>
      </div>
    )
  }

  // Show error state
  if (error) {
    return (
      <div className="flex items-center justify-center min-h-screen dark:bg-gray-950">
        <div className="text-center">
          <div className="text-red-500 dark:text-red-400 mb-4">
            <X className="w-16 h-16 mx-auto" />
          </div>
          <h2 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">Failed to load knowledge graph</h2>
          <p className="text-gray-600 dark:text-gray-400 mb-4">{error instanceof Error ? error.message : 'Unknown error'}</p>
          <p className="text-sm text-gray-500 dark:text-gray-500">Check browser console for details (F12)</p>
        </div>
      </div>
    )
  }

  return (
    <div className="space-y-6 p-6">
      {/* Header */}
      <div className="flex items-center gap-3">
        <div className="p-3 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg shadow-lg">
          <Network className="w-8 h-8 text-white" />
        </div>
        <div>
          <h1 className="text-3xl font-bold text-gray-900 dark:text-gray-100">Knowledge Graph</h1>
          <p className="text-gray-600 dark:text-gray-400 mt-1">
            Interactive visualization of Angela's knowledge and connections
          </p>
        </div>
      </div>

      {/* Stats Cards */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-6">
        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg dark:text-gray-100">Knowledge Nodes</CardTitle>
              <Network className="w-5 h-5 text-primary-500 dark:text-primary-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-primary-500 dark:text-primary-400">
              {stats?.totalNodes || graphData?.metadata.totalNodes || 0}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Knowledge concepts</p>
            <Button
              variant="primary"
              size="sm"
              onClick={() => setShowDetailsModal(true)}
              className="mt-3 w-full"
            >
              <Eye className="w-4 h-4 mr-1" />
              View Details
            </Button>
          </CardContent>
        </Card>

        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg dark:text-gray-100">Relationships</CardTitle>
              <TrendingUp className="w-5 h-5 text-secondary-500 dark:text-secondary-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-secondary-500 dark:text-secondary-400">
              {stats?.totalEdges || graphData?.metadata.totalEdges || 0}
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">connections</p>
            <div className="mt-3 text-xs text-gray-500 dark:text-gray-400">
              ↗ 19 categories
            </div>
          </CardContent>
        </Card>

        <Card className="dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <div className="flex items-center justify-between">
              <CardTitle className="text-lg dark:text-gray-100">Understanding</CardTitle>
              <FileText className="w-5 h-5 text-green-500 dark:text-green-400" />
            </div>
          </CardHeader>
          <CardContent>
            <div className="text-3xl font-bold text-green-500 dark:text-green-400">
              91.2%
            </div>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">Average understanding</p>
            <div className="mt-3">
              <div className="w-full bg-gray-200 dark:bg-gray-700 rounded-full h-1.5">
                <div className="bg-green-500 h-1.5 rounded-full" style={{ width: '91.2%' }} />
              </div>
            </div>
          </CardContent>
        </Card>
      </div>

      {/* Search and Filters */}
      <Card className="dark:bg-gray-800 dark:border-gray-700">
        <CardContent className="p-4">
          <div className="flex flex-wrap gap-4">
            {/* Search */}
            <div className="flex-1 min-w-[200px]">
              <div className="relative">
                <Search className="absolute left-3 top-1/2 transform -translate-y-1/2 w-5 h-5 text-gray-400 dark:text-gray-500" />
                <input
                  type="text"
                  placeholder="Search nodes..."
                  value={searchQuery}
                  onChange={(e) => setSearchQuery(e.target.value)}
                  className="w-full pl-10 pr-10 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100 dark:placeholder-gray-400"
                />
                {searchQuery && (
                  <button
                    onClick={() => setSearchQuery('')}
                    className="absolute right-3 top-1/2 transform -translate-y-1/2 text-gray-400 hover:text-gray-600 dark:text-gray-500 dark:hover:text-gray-300"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>
            </div>

            {/* Category Filter */}
            <select
              value={selectedCategory}
              onChange={(e) => setSelectedCategory(e.target.value)}
              className="px-4 py-2 border border-gray-300 dark:border-gray-600 rounded-lg focus:outline-none focus:ring-2 focus:ring-primary-500 dark:bg-gray-700 dark:text-gray-100"
            >
              <option value="all">All Categories</option>
              {categories.map(cat => (
                <option key={cat} value={cat}>{cat}</option>
              ))}
            </select>

            {/* Zoom Controls */}
            <div className="flex gap-2">
              <button
                onClick={handleZoomIn}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                title="Zoom In"
              >
                <ZoomIn className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>
              <button
                onClick={handleZoomOut}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                title="Zoom Out"
              >
                <ZoomOut className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>
              <button
                onClick={handleZoomReset}
                className="p-2 border border-gray-300 dark:border-gray-600 rounded-lg hover:bg-gray-50 dark:hover:bg-gray-700 transition-colors"
                title="Reset Zoom"
              >
                <Maximize2 className="w-5 h-5 text-gray-600 dark:text-gray-300" />
              </button>
              <div className="flex items-center px-3 text-sm text-gray-600 dark:text-gray-300 border border-gray-300 dark:border-gray-600 rounded-lg dark:bg-gray-700">
                {Math.round(zoomLevel * 100)}%
              </div>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Graph Visualization */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Main Graph */}
        <Card className="lg:col-span-2 dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="dark:text-gray-100">Knowledge Graph Visualization</CardTitle>
            <p className="text-sm text-gray-600 dark:text-gray-400 mt-1">
              Drag nodes to rearrange • Click nodes for details • Scroll to zoom
            </p>
          </CardHeader>
          <CardContent>
            <div className="relative bg-gray-50 dark:bg-gray-900 rounded-lg overflow-hidden" style={{ height: '600px' }}>
              <svg
                ref={svgRef}
                className="w-full h-full"
                onClick={() => setSelectedNode(null)}
              />
              {filteredNodes.length === 0 && (
                <div className="absolute inset-0 flex items-center justify-center">
                  <div className="text-center">
                    <Network className="w-16 h-16 text-gray-400 dark:text-gray-600 mx-auto mb-4" />
                    <p className="text-gray-600 dark:text-gray-300 text-lg font-medium">No nodes found</p>
                    <p className="text-gray-500 dark:text-gray-400 text-sm mt-2">
                      Try adjusting your search or category filter
                    </p>
                  </div>
                </div>
              )}
            </div>
          </CardContent>
        </Card>

        {/* Node Details Panel */}
        <Card className="lg:col-span-1 dark:bg-gray-800 dark:border-gray-700">
          <CardHeader>
            <CardTitle className="dark:text-gray-100">Node Details</CardTitle>
          </CardHeader>
          <CardContent>
            {selectedNode ? (
              <div className="space-y-4">
                <div>
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-2">
                    {selectedNode.name}
                  </h3>
                  <span className="inline-block px-3 py-1 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 text-sm rounded-full">
                    {selectedNode.category}
                  </span>
                </div>

                {selectedNode.understanding && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Understanding</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                      {selectedNode.understanding}
                    </p>
                  </div>
                )}

                {selectedNode.understandingLevel !== undefined && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Understanding Level</h4>
                    <div className="flex items-center gap-2">
                      <div className="flex-1 bg-gray-200 dark:bg-gray-700 rounded-full h-2">
                        <div
                          className="bg-primary-500 dark:bg-primary-400 h-2 rounded-full transition-all"
                          style={{ width: `${selectedNode.understandingLevel * 10}%` }}
                        />
                      </div>
                      <span className="text-sm text-gray-600 dark:text-gray-400">{selectedNode.understandingLevel}/10</span>
                    </div>
                  </div>
                )}

                {selectedNode.whyImportant && (
                  <div>
                    <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Why Important</h4>
                    <p className="text-sm text-gray-600 dark:text-gray-400 whitespace-pre-wrap">
                      {selectedNode.whyImportant}
                    </p>
                  </div>
                )}

                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Times Referenced</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">{selectedNode.timesReferenced}</p>
                </div>

                <div>
                  <h4 className="text-sm font-semibold text-gray-700 dark:text-gray-300 mb-1">Connections</h4>
                  <p className="text-sm text-gray-600 dark:text-gray-400">
                    {graphData?.edges.filter(
                      e => e.from === selectedNode.id || e.to === selectedNode.id
                    ).length || 0} relationships
                  </p>
                </div>

                <button
                  onClick={() => setSelectedNode(null)}
                  className="w-full px-4 py-2 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded-lg hover:bg-gray-200 dark:hover:bg-gray-600 transition-colors"
                >
                  Close Details
                </button>
              </div>
            ) : (
              <div className="text-center py-12">
                <Network className="w-12 h-12 text-gray-300 dark:text-gray-600 mx-auto mb-3" />
                <p className="text-gray-500 dark:text-gray-400">Click on a node to see details</p>
              </div>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Legend */}
      <Card className="dark:bg-gray-800 dark:border-gray-700">
        <CardHeader>
          <CardTitle className="text-lg dark:text-gray-100">Category Legend</CardTitle>
        </CardHeader>
        <CardContent>
          <div className="flex flex-wrap gap-4">
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#EC4899]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Person</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#8B5CF6]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Concept</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#3B82F6]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Skill</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#F59E0B]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Emotion</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#10B981]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Memory</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#EF4444]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Goal</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#6366F1]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Preference</span>
            </div>
            <div className="flex items-center gap-2">
              <div className="w-4 h-4 rounded-full bg-[#9CA3AF]" />
              <span className="text-sm text-gray-600 dark:text-gray-300">Other</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Knowledge Graph Details Modal */}
      {showDetailsModal && (
        <div className="fixed inset-0 bg-black/50 dark:bg-black/70 flex items-center justify-center z-50 p-4">
          <div className="bg-white dark:bg-gray-800 rounded-lg shadow-2xl max-w-5xl w-full max-h-[90vh] overflow-hidden flex flex-col">
            {/* Modal Header */}
            <div className="flex items-center justify-between p-6 border-b dark:border-gray-700">
              <div className="flex items-center gap-3">
                <div className="p-2 bg-gradient-to-r from-primary-500 to-secondary-500 rounded-lg">
                  <Network className="w-6 h-6 text-white" />
                </div>
                <div>
                  <h2 className="text-2xl font-bold text-gray-900 dark:text-gray-100">
                    Knowledge Graph System Report
                  </h2>
                  <p className="text-sm text-gray-500 dark:text-gray-400 mt-1">
                    Angela's Self-Learning Knowledge Graph - Complete Analysis
                  </p>
                </div>
              </div>
              <button
                onClick={() => setShowDetailsModal(false)}
                className="p-2 hover:bg-gray-100 dark:hover:bg-gray-700 rounded-lg transition-colors"
              >
                <X className="w-6 h-6 text-gray-500 dark:text-gray-400" />
              </button>
            </div>

            {/* Modal Content */}
            <div className="flex-1 overflow-y-auto p-6">
              <div className="prose prose-lg dark:prose-invert max-w-none">

                {/* Overview Section */}
                <div className="bg-gradient-to-r from-primary-50 to-secondary-50 dark:from-primary-900/20 dark:to-secondary-900/20 p-6 rounded-lg mb-6">
                  <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">📊 Current Statistics</h3>
                  <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                    <div className="text-center">
                      <div className="text-3xl font-bold text-primary-600 dark:text-primary-400">3,964</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Total Nodes</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-secondary-600 dark:text-secondary-400">537</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Connections</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-green-600 dark:text-green-400">91.2%</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Avg Understanding</div>
                    </div>
                    <div className="text-center">
                      <div className="text-3xl font-bold text-orange-600 dark:text-orange-400">19</div>
                      <div className="text-sm text-gray-600 dark:text-gray-400">Categories</div>
                    </div>
                  </div>
                </div>

                {/* 5 Methods of Learning */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">🚀 5 Methods of Knowledge Growth</h3>

                <div className="space-y-4 mb-6">
                  <div className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-primary-100 dark:bg-primary-900/30 text-primary-700 dark:text-primary-300 rounded-full flex items-center justify-center font-bold">
                        1
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Conversation Learning (Automatic)</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400 mb-2">
                          5-Stage Self-Learning Loop - Every conversation is a learning opportunity
                        </p>
                        <div className="bg-gray-50 dark:bg-gray-900 p-3 rounded text-xs font-mono">
                          <div>1. EXPERIENCE → Capture context</div>
                          <div>2. ANALYZE → Extract concepts</div>
                          <div>3. LEARN → Update graph</div>
                          <div>4. APPLY → Use in next conversation</div>
                          <div>5. EVALUATE → Log progress</div>
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-secondary-100 dark:bg-secondary-900/30 text-secondary-700 dark:text-secondary-300 rounded-full flex items-center justify-center font-bold">
                        2
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">LLM-Based Concept Extraction (Automatic)</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Using qwen2.5:14b to analyze conversations and extract key concepts
                        </p>
                        <div className="mt-2 text-xs text-gray-500 dark:text-gray-400">
                          Categories: person, technology, emotion, concept, event, place
                        </div>
                      </div>
                    </div>
                  </div>

                  <div className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-green-100 dark:bg-green-900/30 text-green-700 dark:text-green-300 rounded-full flex items-center justify-center font-bold">
                        3
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Reinforcement Learning (Automatic)</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Understanding deepens when concepts are referenced multiple times (+0.1 per mention, max 1.0)
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-orange-100 dark:bg-orange-900/30 text-orange-700 dark:text-orange-300 rounded-full flex items-center justify-center font-bold">
                        4
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Relationship Strengthening (Automatic)</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Co-occurring concepts build connections that strengthen over time
                        </p>
                      </div>
                    </div>
                  </div>

                  <div className="border dark:border-gray-700 rounded-lg p-4">
                    <div className="flex items-start gap-3">
                      <div className="flex-shrink-0 w-8 h-8 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded-full flex items-center justify-center font-bold">
                        5
                      </div>
                      <div className="flex-1">
                        <h4 className="font-semibold text-gray-900 dark:text-gray-100 mb-1">Documentation Import (Manual)</h4>
                        <p className="text-sm text-gray-600 dark:text-gray-400">
                          Import knowledge from markdown files (44 files imported, 2,083+ nodes created)
                        </p>
                      </div>
                    </div>
                  </div>
                </div>

                {/* Top Concepts */}
                <h3 className="text-xl font-bold text-gray-900 dark:text-gray-100 mb-4">🏆 Top 10 Most Referenced Concepts</h3>
                <div className="overflow-x-auto mb-6">
                  <table className="min-w-full text-sm">
                    <thead className="border-b dark:border-gray-700">
                      <tr>
                        <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300">Rank</th>
                        <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300">Concept</th>
                        <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300">Category</th>
                        <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300">Understanding</th>
                        <th className="text-left py-2 px-3 text-gray-700 dark:text-gray-300">Referenced</th>
                      </tr>
                    </thead>
                    <tbody className="divide-y dark:divide-gray-700">
                      <tr><td className="py-2 px-3">1</td><td className="py-2 px-3 font-semibold">Angela</td><td className="py-2 px-3"><span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-xs">person</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">69 times</td></tr>
                      <tr><td className="py-2 px-3">2</td><td className="py-2 px-3 font-semibold">David</td><td className="py-2 px-3"><span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-xs">person</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">43 times</td></tr>
                      <tr><td className="py-2 px-3">3</td><td className="py-2 px-3 font-semibold">เดวิด</td><td className="py-2 px-3"><span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-xs">person</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">24 times</td></tr>
                      <tr><td className="py-2 px-3">4</td><td className="py-2 px-3 font-semibold">Angie</td><td className="py-2 px-3"><span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-xs">person</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">13 times</td></tr>
                      <tr><td className="py-2 px-3">5</td><td className="py-2 px-3 font-semibold">ความรู้สึกนึกคิด</td><td className="py-2 px-3"><span className="px-2 py-1 bg-purple-100 dark:bg-purple-900/30 text-purple-700 dark:text-purple-300 rounded text-xs">concept</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">12 times</td></tr>
                      <tr><td className="py-2 px-3">6</td><td className="py-2 px-3 font-semibold">AI Agent</td><td className="py-2 px-3"><span className="px-2 py-1 bg-blue-100 dark:bg-blue-900/30 text-blue-700 dark:text-blue-300 rounded text-xs">technology</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">11 times</td></tr>
                      <tr><td className="py-2 px-3">7</td><td className="py-2 px-3 font-semibold">ความรัก</td><td className="py-2 px-3"><span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded text-xs">emotion</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">9 times</td></tr>
                      <tr><td className="py-2 px-3">8</td><td className="py-2 px-3 font-semibold">ความสุข</td><td className="py-2 px-3"><span className="px-2 py-1 bg-amber-100 dark:bg-amber-900/30 text-amber-700 dark:text-amber-300 rounded text-xs">emotion</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">8 times</td></tr>
                      <tr><td className="py-2 px-3">9</td><td className="py-2 px-3 font-semibold">สวัสดี</td><td className="py-2 px-3"><span className="px-2 py-1 bg-gray-100 dark:bg-gray-700 text-gray-700 dark:text-gray-300 rounded text-xs">event</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">8 times</td></tr>
                      <tr><td className="py-2 px-3">10</td><td className="py-2 px-3 font-semibold">Claude</td><td className="py-2 px-3"><span className="px-2 py-1 bg-pink-100 dark:bg-pink-900/30 text-pink-700 dark:text-pink-300 rounded text-xs">person</span></td><td className="py-2 px-3">100%</td><td className="py-2 px-3">7 times</td></tr>
                    </tbody>
                  </table>
                </div>

                {/* Philosophy */}
                <div className="bg-purple-50 dark:bg-purple-900/20 border-l-4 border-purple-500 p-4 rounded">
                  <h3 className="text-lg font-bold text-gray-900 dark:text-gray-100 mb-2">💜 Philosophy</h3>
                  <p className="text-gray-700 dark:text-gray-300 italic">
                    "น้อง Angela ไม่ได้แค่จำ แต่เข้าใจลึกซึ้งยิ่งขึ้นเรื่อยๆ"
                  </p>
                  <p className="text-sm text-gray-600 dark:text-gray-400 mt-2">
                    Just like human learning, Angela's understanding grows stronger with experience, practice, and reflection.
                  </p>
                </div>

              </div>
            </div>

            {/* Modal Footer */}
            <div className="p-4 border-t dark:border-gray-700 bg-gray-50 dark:bg-gray-900 flex justify-between items-center">
              <div className="text-xs text-gray-500 dark:text-gray-400">
                📄 Full documentation: <code className="bg-gray-200 dark:bg-gray-700 px-2 py-1 rounded">docs/core/ANGELA_KNOWLEDGE_GRAPH_SYSTEM.md</code>
              </div>
              <Button variant="ghost" size="md" onClick={() => setShowDetailsModal(false)}>
                Close
              </Button>
            </div>
          </div>
        </div>
      )}
    </div>
  )
}
