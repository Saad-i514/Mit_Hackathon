"use client";

import React, { useCallback, useMemo } from "react";
import {
  ReactFlow,
  Node,
  Edge,
  Controls,
  Background,
  MiniMap,
  useNodesState,
  useEdgesState,
  MarkerType,
  Position,
} from "@xyflow/react";
import "@xyflow/react/dist/style.css";
import { Card, CardContent, CardDescription, CardHeader, CardTitle } from "@/components/ui/card";
import { Protocol, ProtocolStep } from "@/lib/types";

interface ProtocolFlowchartProps {
  protocol: Protocol;
  onNodeClick?: (stepNumber: number) => void;
}

export function ProtocolFlowchart({ protocol, onNodeClick }: ProtocolFlowchartProps) {
  // Convert protocol steps to React Flow nodes and edges
  const { nodes: initialNodes, edges: initialEdges } = useMemo(() => {
    return convertProtocolToFlow(protocol);
  }, [protocol]);

  const [nodes, setNodes, onNodesChange] = useNodesState(initialNodes);
  const [edges, setEdges, onEdgesChange] = useEdgesState(initialEdges);

  const handleNodeClick = useCallback(
    (_event: React.MouseEvent, node: Node) => {
      const stepNumber = Number((node.data as any)?.stepNumber);
      if (onNodeClick && Number.isFinite(stepNumber) && stepNumber > 0) {
        onNodeClick(stepNumber);
      }
    },
    [onNodeClick]
  );

  return (
    <Card className="w-full">
      <CardHeader>
        <CardTitle>Protocol Flowchart</CardTitle>
        <CardDescription>
          Visual representation of experimental protocol steps
        </CardDescription>
      </CardHeader>
      <CardContent>
        <div style={{ height: "600px", width: "100%", borderRadius: "12px", overflow: "hidden", background: "#0f172a" }}>
          <ReactFlow
            nodes={nodes}
            edges={edges}
            onNodesChange={onNodesChange}
            onEdgesChange={onEdgesChange}
            onNodeClick={handleNodeClick}
            fitView
            fitViewOptions={{ padding: 0.3 }}
            attributionPosition="bottom-left"
          >
            <Background color="#334155" gap={20} size={1} />
            <Controls style={{ background: "#1e293b", border: "1px solid #334155", borderRadius: "8px" }} />
            <MiniMap
              nodeColor={(node) => {
                if ((node.data as any)?.isDecision) return "#eab308";
                return "#3b82f6";
              }}
              style={{ background: "#1e293b", border: "1px solid #334155" }}
              maskColor="rgba(15, 23, 42, 0.6)"
            />
          </ReactFlow>
        </div>
      </CardContent>
    </Card>
  );
}

// Helper function to convert protocol to React Flow format
function convertProtocolToFlow(protocol: Protocol): { nodes: Node[]; edges: Edge[] } {
  const nodes: Node[] = [];
  const edges: Edge[] = [];

  const nodeWidth = 200;
  const nodeHeight = 80;
  const horizontalSpacing = 300;
  const verticalSpacing = 150;

  let currentX = 100;
  let currentY = 50;
  let maxX = currentX;

  protocol.steps.forEach((step, index) => {
    const isDecision = step.description.toLowerCase().includes("if ") || 
                      step.description.toLowerCase().includes("decide") ||
                      step.description.toLowerCase().includes("choose");

    // Create node
    const node: Node = {
      id: `step-${step.step_number}`,
      type: "default",
      position: { x: currentX, y: currentY },
      data: {
        label: (
          <div style={{ textAlign: "center", padding: "4px" }}>
            <div style={{ fontWeight: 700, fontSize: "11px", marginBottom: "4px", color: "#1e293b" }}>
              Step {step.step_number}
            </div>
            <div style={{
              fontSize: "10px",
              color: "#334155",
              overflow: "hidden",
              display: "-webkit-box",
              WebkitLineClamp: 2,
              WebkitBoxOrient: "vertical",
              lineHeight: "1.3",
            }}>
              {step.description}
            </div>
            <div style={{ fontSize: "9px", color: "#64748b", marginTop: "3px" }}>
              ⏱ {step.duration}
            </div>
          </div>
        ),
        stepNumber: step.step_number,
        isDecision,
      },
      style: {
        width: nodeWidth,
        height: nodeHeight,
        background: isDecision ? "#fef9c3" : "#eff6ff",
        border: isDecision ? "2px solid #eab308" : "2px solid #3b82f6",
        borderRadius: "10px",
        padding: 0,
        boxShadow: "0 2px 8px rgba(0,0,0,0.15)",
      },
      sourcePosition: Position.Bottom,
      targetPosition: Position.Top,
    };

    nodes.push(node);

    // Create edge from previous step
    if (index > 0) {
      const edge: Edge = {
        id: `edge-${index}`,
        source: `step-${protocol.steps[index - 1].step_number}`,
        target: `step-${step.step_number}`,
        type: "smoothstep",
        animated: false,
        markerEnd: {
          type: MarkerType.ArrowClosed,
          width: 20,
          height: 20,
        },
        style: {
          strokeWidth: 2,
          stroke: "#3b82f6",
        },
      };
      edges.push(edge);
    }

    // Position next node
    if (isDecision) {
      // Decision nodes branch horizontally
      currentY += verticalSpacing;
      currentX = maxX - horizontalSpacing / 2;
    } else {
      // Regular nodes go vertically
      currentY += verticalSpacing;
    }

    maxX = Math.max(maxX, currentX);
  });

  return { nodes, edges };
}

// Custom node component for decision points (diamond shape)
export function DecisionNode({ data }: { data: any }) {
  return (
    <div
      style={{
        width: "100%",
        height: "100%",
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        transform: "rotate(45deg)",
        background: "#fef3c7",
        border: "2px solid #f59e0b",
      }}
    >
      <div style={{ transform: "rotate(-45deg)", textAlign: "center", padding: "8px" }}>
        <div className="font-bold text-sm mb-1">Step {data.stepNumber}</div>
        <div className="text-xs">{data.label}</div>
      </div>
    </div>
  );
}
