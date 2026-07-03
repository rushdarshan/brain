import GraphView from '@/components/GraphView';

export default function Home() {
  return (
    <div className="min-h-screen bg-gray-950 text-gray-100 p-8 font-[family-name:var(--font-geist-sans)]">
      <main className="max-w-6xl mx-auto flex flex-col gap-8">
        <header className="border-b border-gray-800 pb-4">
          <h1 className="text-3xl font-semibold tracking-tight">ProjectBrain <span className="text-gray-500">Memory Graph</span></h1>
          <p className="text-sm text-gray-400 mt-1">A self-improving project memory that documents its own creation.</p>
        </header>

        <section className="flex flex-col gap-4">
          <div className="flex gap-4 text-xs">
            <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-green-500"></span> Decision</span>
            <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-blue-500"></span> File</span>
            <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-red-500"></span> Incident</span>
            <span className="flex items-center gap-2"><span className="w-3 h-3 rounded-full bg-yellow-500"></span> Metric</span>
          </div>
          
          {/* Graph Visualization */}
          <GraphView />
        </section>
      </main>
    </div>
  );
}
