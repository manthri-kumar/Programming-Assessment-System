import { useMemo, useState } from 'react'
import { Background, Controls, Handle, MarkerType, Position, ReactFlow, type Edge, type Node, type NodeProps } from '@xyflow/react'
import '@xyflow/react/dist/style.css'
import type { AssessmentResult, ConceptGraph, ConceptNode } from '../api/types'
import { Badge, Card } from '../components/ui'

type GraphNodeData = Record<string, unknown> & ConceptNode & { state: string }
function ConceptNodeView({ data }: NodeProps<Node<GraphNodeData>>) { return <div className={`graph-node graph-node-${data.state}`}><Handle type="target" position={Position.Top}/><strong>{data.label}</strong><small>{data.id}</small><Handle type="source" position={Position.Bottom}/></div> }
const nodeTypes = { concept: ConceptNodeView }

export default function KnowledgeGraphView({ graph, result }: { graph: ConceptGraph; result?: AssessmentResult }) {
  const [selected, setSelected] = useState(graph.nodes[0]?.id ?? '')
  const evidenceText = JSON.stringify({ analysis: result?.analysis, recommendations: result?.recommendations, evidence: result?.evidence }).toLowerCase()
  const recommendations = useMemo(() => new Set((result?.recommendations ?? []).map(item => item.concept_id).filter(Boolean)), [result?.recommendations])
  const stateFor = (id: string) => {
    const conceptEvidence = (result?.evidence ?? []).filter(item => item.concept_ids?.includes(id))
    const text = JSON.stringify(conceptEvidence).toLowerCase()
    if (text.includes('contradict')) return 'contradictory'
    if (recommendations.has(id) || text.includes('weak') || text.includes('missing')) return 'weak'
    if (text.includes('satisfied') || text.includes('demonstrated') || text.includes('present')) return 'satisfied'
    return evidenceText.includes(id.toLowerCase()) ? 'evidence' : 'unknown'
  }
  const nodes: Node<GraphNodeData>[] = graph.nodes.map((item, index) => ({ id: item.id, type: 'concept', position: { x: (index % 3) * 230, y: Math.floor(index / 3) * 150 }, data: { ...item, state: stateFor(item.id) } }))
  const edges = useMemo<Edge[]>(() => graph.edges.map(item => ({ id: item.id, source: item.source, target: item.target, label: item.type, markerEnd: { type: MarkerType.ArrowClosed }, style: { stroke: '#ffd600' }, labelStyle: { fill: '#b8c7d6' } })), [graph.edges])
  const active = graph.nodes.find(item => item.id === selected)
  const activeEvidence = (result?.evidence ?? []).filter(item => item.concept_ids?.includes(selected))
  const activeRecommendation = (result?.recommendations ?? []).find(item => item.concept_id === selected)
  return <div className="graph-layout"><Card><div className="section-title"><h2>Concept map</h2><Badge tone="gold">{graph.version}</Badge></div><div className="graph-canvas" aria-label="Interactive concept graph"><ReactFlow nodes={nodes} edges={edges} nodeTypes={nodeTypes} fitView onNodeClick={(_,node)=>setSelected(node.id)}><Background color="#243943"/><Controls/></ReactFlow></div></Card><Card><h2>Accessible concept list</h2><p className="muted">This list contains the same concepts and prerequisite relationships as the visual map.</p><div className="concept-list">{graph.nodes.map(item => { const parents=graph.edges.filter(edge=>edge.target===item.id).map(edge=>graph.nodes.find(node=>node.id===edge.source)?.label??edge.source); return <button className="concept-button" aria-pressed={selected===item.id} key={item.id} onClick={()=>setSelected(item.id)}><strong>{item.label}</strong><span className="muted">{parents.length?`Requires: ${parents.join(', ')}`:'No prerequisites'} · Evidence: {stateFor(item.id)}</span></button>})}</div>{active&&<div aria-live="polite"><h3>{active.label}</h3><p>{active.guidance}</p><div className="stack"><Badge tone={stateFor(active.id)==='contradictory'?'red':stateFor(active.id)==='satisfied'?'green':stateFor(active.id)==='weak'?'gold':'neutral'}>{stateFor(active.id)}</Badge>{activeRecommendation&&<Badge tone="red">Current recommendation</Badge>}</div>{activeEvidence.length>0&&<ul>{activeEvidence.map((item,index)=><li key={item.id??index}><strong>{item.id??`Evidence ${index+1}`}</strong>{item.message?`: ${item.message}`:''}</li>)}</ul>}{activeRecommendation&&<p>{activeRecommendation.guidance}{activeRecommendation.path?.length?` Path: ${activeRecommendation.path.join(' → ')}`:''}</p>}</div>}</Card></div>
}
