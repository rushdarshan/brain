"use client";

import { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import dynamic from 'next/dynamic';

const ForceGraph2D = dynamic(() => import('react-force-graph-2d'), { ssr: false });

// Use relative path in production so the browser connects to the Railway domain, not localhost.
const API = typeof window !== 'undefined' && window.location.hostname === '127.0.0.1' ? 'http://127.0.0.1:8000' : '';

const GROUP_COLORS: Record<string, string> = {
  decision: '#22c55e',
  file: '#3b82f6',
  incident: '#ef4444',
  metric: '#eab308',
};

export default function GraphView() {
  const [graphData, setGraphData] = useState({ nodes: [], links: [] });
  const graphRef = useRef<any>(null);
  const [searchMode, setSearchMode] = useState('GRAPH_COMPLETION');
  const [searchQuery, setSearchQuery] = useState('');
  const [searchResults, setSearchResults] = useState<any[]>([]);
  const [isSearching, setIsSearching] = useState(false);
  const [modes, setModes] = useState<{id: string, name: string}[]>([]);
  const [modesError, setModesError] = useState(false);
  const [sseError, setSseError] = useState(false);
  const [metrics, setMetrics] = useState<any>(null);
  const [edgeFilter, setEdgeFilter] = useState('ALL');
  const [selectedNode, setSelectedNode] = useState<any>(null);
  const [week, setWeek] = useState<number | null>(null);
  const [weekOptions, setWeekOptions] = useState<{weeks: number[], current: number} | null>(null);
  const [improveLoading, setImproveLoading] = useState(false);
  const [improveDelta, setImproveDelta] = useState<string | null>(null);
  const [historyData, setHistoryData] = useState<any[]>([]);
  const [activePanel, setActivePanel] = useState<'add' | 'activity' | 'metrics'>('metrics');
  const [addTitle, setAddTitle] = useState('');
  const [addRationale, setAddRationale] = useState('');
  const [addFiles, setAddFiles] = useState('');
  const [addTags, setAddTags] = useState('');
  const [addSupersedes, setAddSupersedes] = useState('');
  const [addLoading, setAddLoading] = useState(false);
  const [addMsg, setAddMsg] = useState<string | null>(null);
  const [activityLog, setActivityLog] = useState<{type: string; text: string; time: number}[]>([]);

  useEffect(() => {
    const es = new EventSource(`${API}/api/stream`);
    es.onmessage = (event) => {
      try {
        setGraphData(JSON.parse(event.data));
        setSseError(false);
      } catch (err) {
        console.error("Failed to parse SSE data", err);
      }
    };
    es.onerror = () => {
      setSseError(true);
    };
    return () => es.close();
  }, []);

  const fetchMetrics = useCallback(async () => {
    try {
      const r = await fetch(`${API}/api/metrics`);
      setMetrics(await r.json());
    } catch {}
  }, []);

  useEffect(() => {
    fetch(`${API}/api/search/modes`)
      .then(r => r.json())
      .then(d => setModes(d.modes))
      .catch(() => setModesError(true));
    fetchMetrics();
  }, [fetchMetrics]);

  const logActivity = useCallback((type: string, text: string) => {
    setActivityLog(prev => [{type, text, time: Date.now()}, ...prev].slice(0, 20));
  }, []);

  useEffect(() => {
    fetch(`${API}/api/graph/weeks`)
      .then(r => r.json())
      .then(d => { setWeekOptions(d); setWeek(d.current); })
      .catch(() => {});
  }, []);

  useEffect(() => {
    fetch(`${API}/api/metrics/history`)
      .then(r => r.json())
      .then(setHistoryData)
      .catch(() => {});
  }, []);

  useEffect(() => {
    if (week == null) return;
    if (week === (weekOptions?.current ?? 8)) {
      setGraphData(prev => prev);
      return;
    }
    fetch(`${API}/api/graph?week=${week}`)
      .then(r => r.json())
      .then(d => setGraphData(d))
      .catch(() => {});
  }, [week, weekOptions?.current]);

  const doImprove = useCallback(async () => {
    setImproveLoading(true);
    const oldRecall = metrics?.recall_precision;
    try {
      const r = await fetch(`${API}/api/improve`, { method: 'POST' });
      const m = await r.json();
      setMetrics(m);
      if (oldRecall != null && m.recall_precision != null) {
        const delta = ((m.recall_precision - oldRecall) * 100).toFixed(1);
        setImproveDelta(delta.startsWith('-') ? delta : `+${delta}`);
        setTimeout(() => setImproveDelta(null), 5000);
      }
      logActivity('improve', 'Memory strengthened');
      fetch(`${API}/api/metrics/history`).then(r => r.json()).then(setHistoryData).catch(() => {});
    } catch {}
    setImproveLoading(false);
  }, [metrics, logActivity]);

  const doSubmitDecision = useCallback(async () => {
    if (!addTitle.trim()) return;
    setAddLoading(true);
    setAddMsg(null);
    try {
      const r = await fetch(`${API}/api/webhook/remember`, {
        method: 'POST',
        headers: {'Content-Type': 'application/json'},
        body: JSON.stringify({
          title: addTitle,
          rationale: addRationale,
          files: addFiles.split(',').map(s => s.trim()).filter(Boolean),
          tags: addTags.split(',').map(s => s.trim()).filter(Boolean),
          supersedes: addSupersedes.trim() || null,
        }),
      });
      if (r.ok) {
        setAddMsg('Decision remembered!');
        setAddTitle(''); setAddRationale(''); setAddFiles(''); setAddTags(''); setAddSupersedes('');
        logActivity('add', addTitle);
        setTimeout(() => setAddMsg(null), 3000);
      } else {
        setAddMsg('Failed to remember. Check console.');
      }
    } catch { setAddMsg('Network error.'); }
    setAddLoading(false);
  }, [addTitle, addRationale, addFiles, addTags, addSupersedes, logActivity]);

  const doSearch = useCallback(async (q: string, mode: string) => {
    if (!q.trim()) { setSearchResults([]); return; }
    setIsSearching(true);
    try {
      const r = await fetch(`${API}/api/search?q=${encodeURIComponent(q)}&mode=${mode}`);
      const d = await r.json();
      setSearchResults(d.results);
      logActivity('search', `${q} (${mode})`);
    } catch {
      setSearchResults([]);
    }
    setIsSearching(false);
  }, [logActivity]);

  const modeRef = useRef(searchMode);
  modeRef.current = searchMode;

  useEffect(() => {
    if (!searchQuery.trim()) { setSearchResults([]); return; }
    const timer = setTimeout(() => doSearch(searchQuery, modeRef.current), 300);
    return () => clearTimeout(timer);
  }, [searchQuery, doSearch]);

  useEffect(() => {
    if (searchQuery.trim()) doSearch(searchQuery, searchMode);
  }, [searchMode]);

  const edgeTypes = useMemo(() => {
    const types = new Set<string>();
    for (const link of graphData.links as any[]) {
      if (link.name) types.add(link.name);
    }
    return Array.from(types).sort();
  }, [graphData.links]);

  const filteredData = useMemo(() => {
    if (edgeFilter === 'ALL') return graphData;
    const filteredLinks = (graphData.links as any[]).filter(l => l.name === edgeFilter);
    const nodeIds = new Set<string>();
    for (const l of filteredLinks) {
      const src = typeof l.source === 'object' ? l.source.id : l.source;
      const tgt = typeof l.target === 'object' ? l.target.id : l.target;
      nodeIds.add(src);
      nodeIds.add(tgt);
    }
    const filteredNodes = (graphData.nodes as any[]).filter(n => nodeIds.has(n.id));
    return { nodes: filteredNodes as any, links: filteredLinks as any };
  }, [graphData, edgeFilter]);

  const groupCounts = useMemo(() => {
    const counts: Record<string, number> = {};
    for (const n of graphData.nodes as any[]) {
      const g = n.group || 'other';
      counts[g] = (counts[g] || 0) + 1;
    }
    return counts;
  }, [graphData.nodes]);

  const nodeConnections = useMemo(() => {
    if (!selectedNode) return [];
    const connected: any[] = [];
    for (const link of graphData.links as any[]) {
      const srcId = typeof link.source === 'object' ? link.source.id : link.source;
      const tgtId = typeof link.target === 'object' ? link.target.id : link.target;
      if (srcId === selectedNode.id) {
        const tgt = (graphData.nodes as any[]).find(n => n.id === tgtId);
        connected.push({ node: tgt, relation: link.name, dir: 'out' });
      } else if (tgtId === selectedNode.id) {
        const src = (graphData.nodes as any[]).find(n => n.id === srcId);
        connected.push({ node: src, relation: link.name, dir: 'in' });
      }
    }
    return connected;
  }, [selectedNode, graphData]);

  useEffect(() => {
    const handler = (e: KeyboardEvent) => {
      if (e.key === 'Escape') setSelectedNode(null);
    };
    window.addEventListener('keydown', handler);
    return () => window.removeEventListener('keydown', handler);
  }, []);

  const getNodeColor = useCallback((node: any) => {
    const opacity = node.hotness ? Math.max(0.2, node.hotness) : 1;
    const base = GROUP_COLORS[node.group] || '#9ca3af';
    return base.replace(')', `, ${opacity})`).replace('rgb', 'rgba');
  }, []);

  const getLinkColor = useCallback((link: any) => {
    const opacity = link.decay ? Math.max(0.1, link.decay) : 1.0;
    if (link.name === 'SUPERSEDES') return `rgba(239, 68, 68, ${opacity})`;
    if (link.name === 'IMPACTS') return `rgba(168, 85, 247, ${opacity})`;
    return `rgba(75, 85, 99, ${opacity})`;
  }, []);

  const handleNodeClick = useCallback((node: any) => {
    setSelectedNode(node);
  }, []);

  const handleCanvasClick = useCallback(() => {
    setSelectedNode(null);
  }, []);

  return (
    <div className="flex flex-col gap-4">
      {/* Search controls row */}
      <div className="flex gap-3 items-end">
        <div className="flex-1">
          <label className="text-xs text-gray-500 mb-1 block">Search Mode</label>
          <select
            value={searchMode}
            onChange={e => setSearchMode(e.target.value)}
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 focus:outline-none focus:border-gray-500"
          >
            {modesError ? (
              <option value="GRAPH_COMPLETION">Backend unavailable — using default</option>
            ) : modes.length === 0 ? (
              <option value="GRAPH_COMPLETION">Loading modes...</option>
            ) : modes.map(m => (
              <option key={m.id} value={m.id}>{m.name}</option>
            ))}
          </select>
        </div>
        <div className="flex-[2]">
          <label className="text-xs text-gray-500 mb-1 block">Query</label>
          <input
            type="text"
            value={searchQuery}
            onChange={e => setSearchQuery(e.target.value)}
            placeholder="Search the knowledge graph..."
            className="w-full bg-gray-900 border border-gray-700 rounded px-3 py-2 text-sm text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500"
          />
        </div>
      </div>

      {/* Metrics row */}
      {metrics && (
        <div className="flex gap-4 text-xs text-gray-500 font-mono flex-wrap items-center">
          <span>{metrics.nodes} nodes</span>
          <span>{metrics.edges} edges</span>
          <span>recall: {(metrics.recall_precision * 100).toFixed(0)}%</span>
          {metrics.search_latency_ms != null && <span>{metrics.search_latency_ms}ms latency</span>}
          {metrics.memory_composition && (Object.entries(metrics.memory_composition) as [string, number][]).map(([g, c]) => (
            <span key={g} className="capitalize">{g}: {c}</span>
          ))}
          <button
            onClick={doImprove}
            disabled={improveLoading}
            className="ml-auto px-3 py-1 rounded text-xs font-medium bg-indigo-700 hover:bg-indigo-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
          >
            {improveLoading ? 'Improving...' : 'Strengthen Memory'}
          </button>
          {improveDelta && (
            <span className="text-green-400 font-bold text-xs animate-pulse">{improveDelta}pp recall</span>
          )}
        </div>
      )}

      {/* Legend row */}
      <div className="flex gap-6 text-xs text-gray-400 items-center flex-wrap">
        <span className="text-gray-500 font-medium">Legend</span>
        {Object.entries(GROUP_COLORS).map(([group, color]) => (
          <span key={group} className="flex items-center gap-1.5">
            <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: color }}></span>
            {group} <span className="text-gray-600">({groupCounts[group] || 0})</span>
          </span>
        ))}
        <span className="text-gray-500 mx-1">|</span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-0.5 bg-red-500"></span> SUPERSEDES
        </span>
        <span className="flex items-center gap-1.5">
          <span className="w-5 h-0.5 bg-gray-500"></span> LINKS_TO
        </span>
        <span className="flex items-center gap-1.5 text-gray-600 ml-2">
          size = relevance
        </span>
      </div>

      {/* Week slider */}
      {weekOptions && week != null && (
        <div className="flex items-center gap-3 text-xs text-gray-500">
          <span className="font-medium">Timeline</span>
          <input
            type="range"
            min={Math.min(...weekOptions.weeks)}
            max={weekOptions.current}
            value={week}
            onChange={e => setWeek(Number(e.target.value))}
            className="flex-1 h-1.5 bg-gray-800 rounded-full appearance-none cursor-pointer accent-indigo-500"
          />
          <span className="font-mono w-16 text-right">Week {week}/{weekOptions.current}</span>
        </div>
      )}

      {/* Graph + SSE warning + Results */}
      <div className="flex gap-4">
        <div className="relative flex-1 min-w-0">
          {sseError && (
            <div className="absolute top-0 left-0 right-0 z-20 bg-yellow-900/80 border-b border-yellow-700 text-yellow-200 text-xs px-4 py-2 text-center">
              SSE disconnected — graph data may be stale. Retrying...
            </div>
          )}

          {/* Controls toolbar */}
          <div className="flex gap-2 mb-2">
            <div className="flex items-center gap-2">
              <label className="text-xs text-gray-500">Edge type:</label>
              <select
                value={edgeFilter}
                onChange={e => setEdgeFilter(e.target.value)}
                className="bg-gray-900 border border-gray-700 rounded px-2 py-1 text-xs text-gray-200 focus:outline-none focus:border-gray-500"
              >
                <option value="ALL">All edges ({graphData.links.length})</option>
                {edgeTypes.map(t => (
                  <option key={t} value={t}>{t}</option>
                ))}
              </select>
            </div>
          </div>

          <div className="w-full h-[400px] border border-gray-800 rounded-lg overflow-hidden bg-gray-950 relative">
            <ForceGraph2D
              ref={graphRef}
              graphData={filteredData}
              nodeLabel="name"
              nodeColor={getNodeColor}
              nodeRelSize={6}
              nodeVal={(node: any) => node.hotness ? node.val * node.hotness : node.val}
              linkColor={getLinkColor}
              linkWidth={(link: any) => link.name === 'SUPERSEDES' ? 2 : 1}
              linkDirectionalArrowLength={3.5}
              linkDirectionalArrowRelPos={1}
              d3VelocityDecay={0.3}
              backgroundColor="#030712"
              onNodeClick={handleNodeClick}
              onBackgroundClick={handleCanvasClick}
            />
          </div>

          {/* Search results */}
          {searchQuery.trim() && (
            <div className="border border-gray-800 rounded-lg bg-gray-900 max-h-48 overflow-y-auto mt-2">
              {isSearching ? (
                <div className="p-4 text-sm text-gray-500 text-center">Searching...</div>
              ) : searchResults.length === 0 ? (
                <div className="p-4 text-sm text-gray-500 text-center">No results found.</div>
              ) : (
                <div className="divide-y divide-gray-800">
                  {searchResults.map((r, i) => (
                    <div key={i} className="p-3 text-sm text-gray-300 hover:bg-gray-800 cursor-pointer" onClick={() => {
                      const node = (graphData.nodes as any[]).find(n => n.id === r.node_id);
                      if (node) setSelectedNode(node);
                    }}>
                      <p className="line-clamp-3">{r.text}</p>
                      {r.score != null && (
                        <span className="text-xs text-gray-600 mt-1 block">score: {r.score.toFixed(3)}</span>
                      )}
                      {r.node_id && <span className="text-[10px] text-gray-700 mt-0.5 block truncate">{r.node_id}</span>}
                    </div>
                  ))}
                </div>
              )}
            </div>
          )}
        </div>

        {/* Right panel — control tabs or node detail */}
        <div className="w-72 shrink-0 border border-gray-700 rounded-lg bg-gray-900 h-fit max-h-[500px] overflow-y-auto">
          {selectedNode ? (
            <div className="p-4">
              <div className="flex items-center justify-between mb-3">
                <h3 className="text-sm font-medium text-gray-200 truncate">{selectedNode.name}</h3>
                <button
                  onClick={() => setSelectedNode(null)}
                  className="text-gray-500 hover:text-gray-300 text-lg leading-none ml-2"
                >
                  &times;
                </button>
              </div>
              <div className="space-y-2 text-xs">
                <div className="flex items-center gap-2">
                  <span className="w-2.5 h-2.5 rounded-full" style={{ backgroundColor: GROUP_COLORS[selectedNode.group] || '#9ca3af' }}></span>
                  <span className="text-gray-400 capitalize">{selectedNode.group || 'unknown'}</span>
                </div>
                <div className="text-gray-500 font-mono text-[10px] break-all">{selectedNode.id}</div>

                {nodeConnections.length > 0 && (
                  <div className="pt-2 border-t border-gray-800">
                    <p className="text-gray-500 mb-1.5 font-medium">Connections ({nodeConnections.length})</p>
                    <div className="space-y-1">
                      {nodeConnections.map((c, i) => (
                        <div key={i} className="flex items-center gap-1.5 text-gray-400">
                          <span className="text-[10px] text-gray-600">{c.dir === 'out' ? '→' : '←'}</span>
                          <span className="truncate">{c.node?.name || 'unknown'}</span>
                          <span className="text-gray-600 ml-auto text-[10px]">{c.relation}</span>
                        </div>
                      ))}
                    </div>
                  </div>
                )}
              </div>
            </div>
          ) : (
            <div className="p-3">
              {/* Tabs */}
              <div className="flex gap-1 mb-3 border-b border-gray-800 pb-2">
                {(['metrics', 'add', 'activity'] as const).map(tab => (
                  <button
                    key={tab}
                    onClick={() => setActivePanel(tab)}
                    className={`text-xs px-2 py-1 rounded capitalize transition-colors ${
                      activePanel === tab
                        ? 'bg-indigo-700 text-white'
                        : 'text-gray-400 hover:text-gray-200'
                    }`}
                  >
                    {tab}
                  </button>
                ))}
              </div>

              {/* Add tab */}
              {activePanel === 'add' && (
                <div className="space-y-2 text-xs">
                  <input type="text" placeholder="Title" value={addTitle}
                    onChange={e => setAddTitle(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500" />
                  <textarea placeholder="Rationale" value={addRationale} rows={2}
                    onChange={e => setAddRationale(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500 resize-none" />
                  <input type="text" placeholder="Files (comma-separated)" value={addFiles}
                    onChange={e => setAddFiles(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500" />
                  <input type="text" placeholder="Tags (comma-separated)" value={addTags}
                    onChange={e => setAddTags(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500" />
                  <input type="text" placeholder="Supersedes (optional)" value={addSupersedes}
                    onChange={e => setAddSupersedes(e.target.value)}
                    className="w-full bg-gray-800 border border-gray-700 rounded px-2 py-1.5 text-gray-200 placeholder-gray-600 focus:outline-none focus:border-gray-500" />
                  <button
                    onClick={doSubmitDecision}
                    disabled={addLoading || !addTitle.trim()}
                    className="w-full px-3 py-1.5 rounded text-xs font-medium bg-indigo-700 hover:bg-indigo-600 disabled:bg-gray-700 disabled:text-gray-500 text-white transition-colors"
                  >
                    {addLoading ? 'Saving...' : 'Remember Decision'}
                  </button>
                  {addMsg && <p className="text-center text-gray-400">{addMsg}</p>}
                </div>
              )}

              {/* Activity tab */}
              {activePanel === 'activity' && (
                <div className="space-y-1 text-xs max-h-64 overflow-y-auto">
                  {activityLog.length === 0 ? (
                    <p className="text-gray-600 text-center py-4">No activity yet.</p>
                  ) : activityLog.map((a, i) => (
                    <div key={i} className="flex items-start gap-2 text-gray-400 py-1.5 border-b border-gray-800/50 last:border-0">
                      <span className={`shrink-0 text-[10px] font-medium px-1 rounded ${
                        a.type === 'improve' ? 'bg-indigo-900/50 text-indigo-400' :
                        a.type === 'add' ? 'bg-green-900/50 text-green-400' :
                        'bg-gray-800 text-gray-500'
                      }`}>{a.type}</span>
                      <span className="truncate">{a.text}</span>
                    </div>
                  ))}
                </div>
              )}

              {/* Metrics tab */}
              {activePanel === 'metrics' && (
                <div className="space-y-2 text-xs">
                  {historyData.length === 0 ? (
                    <p className="text-gray-600 text-center py-4">No metrics history yet. Click "Strengthen Memory" to record snapshots.</p>
                  ) : (
                    <div className="space-y-1 max-h-64 overflow-y-auto">
                      {historyData.map((h, i) => (
                        <div key={i} className="flex justify-between text-gray-400 py-1 border-b border-gray-800/50 last:border-0">
                          <span>{new Date(h.t * 1000).toLocaleTimeString()}</span>
                          <span className="font-mono">{h.metrics.nodes} nodes / {h.metrics.edges} edges / {(h.metrics.recall_precision * 100).toFixed(0)}% recall</span>
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
}
