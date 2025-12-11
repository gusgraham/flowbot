import { useState, useEffect } from 'react';
import { Grid3X3, CheckCircle, AlertTriangle, XCircle, Minus, Play, Loader2, ChevronRight, Search } from 'lucide-react';
import { useVerificationMatrix, useRunVerification } from '../../../api/hooks';
import type { VerificationEvent } from '../../../api/hooks';
import VerificationWorkspace from './VerificationWorkspace';

interface ReviewTabProps {
    projectId: number;
}

export default function ReviewTab({ projectId }: ReviewTabProps) {
    const { data: matrix, isLoading } = useVerificationMatrix(projectId);
    const runVerification = useRunVerification();

    const [selectedEventId, setSelectedEventId] = useState<number | null>(null);
    const [selectedMonitorId, setSelectedMonitorId] = useState<number | null>(null);
    const [searchTerm, setSearchTerm] = useState('');
    const [runResults, setRunResults] = useState<string | null>(null);

    // Auto-select first event if available and none selected
    useEffect(() => {
        if (matrix?.events?.length && !selectedEventId) {
            setSelectedEventId(matrix.events[0].id);
        }
    }, [matrix, selectedEventId]);

    const handleRunVerification = async () => {
        if (!selectedEventId) return;

        try {
            const eventName = matrix?.events?.find(e => e.id === selectedEventId)?.name;
            const result = await runVerification.mutateAsync({
                eventId: selectedEventId,
                projectId
            });
            setRunResults(`Created ${result.runs_created} verification runs for ${eventName || 'Event'}`);
            setTimeout(() => setRunResults(null), 5000);
        } catch (error) {
            setRunResults('Error running verification');
            setTimeout(() => setRunResults(null), 5000);
        }
    };

    if (isLoading) {
        return (
            <div className="flex justify-center items-center h-64">
                <Loader2 className="animate-spin text-green-500" size={32} />
            </div>
        );
    }

    if (!matrix || !matrix.monitors || matrix.monitors.length === 0 || !matrix.events || matrix.events.length === 0) {
        return (
            <div className="text-center py-12 bg-gray-50 rounded-lg border-2 border-dashed border-gray-200">
                <Grid3X3 className="mx-auto text-gray-400 mb-3" size={48} />
                <p className="text-gray-500 mb-2">No verification data yet</p>
                <p className="text-sm text-gray-400">
                    Create events and import traces to see the verification review.
                </p>
            </div>
        );
    }

    const selectedEvent = matrix.events.find((e: VerificationEvent) => e.id === selectedEventId);

    // Filter monitors
    const filteredMonitors = matrix.monitors.filter((m: any) =>
        m.name.toLowerCase().includes(searchTerm.toLowerCase())
    );

    const getStatusColor = (status: string) => {
        switch (status) {
            case 'VERIFIED': return 'text-green-600 bg-green-50 border-green-200';
            case 'MARGINAL': return 'text-amber-600 bg-amber-50 border-amber-200';
            case 'NOT_VERIFIED': return 'text-red-600 bg-red-50 border-red-200';
            default: return 'text-gray-500 bg-gray-50 border-gray-200';
        }
    };

    const getStatusIcon = (status: string) => {
        switch (status) {
            case 'VERIFIED': return <CheckCircle size={16} />;
            case 'MARGINAL': return <AlertTriangle size={16} />;
            case 'NOT_VERIFIED': return <XCircle size={16} />;
            default: return <Minus size={16} />;
        }
    };

    // Find run ID for selected monitor/event
    const getRunId = (monitorName: string, eventName: string) => {
        return matrix.matrix[monitorName]?.[eventName]?.run_id;
    };

    const selectedMonitor = selectedMonitorId ? matrix.monitors.find((m: any) => m.id === selectedMonitorId) : null;

    const activeRunId = (selectedMonitor?.name && selectedEvent?.name)
        ? getRunId(selectedMonitor.name, selectedEvent.name)
        : null;

    return (
        <div className="flex flex-col h-[calc(100vh-200px)] min-h-[600px]">
            {/* Top Bar: Event Selection and Run Verification */}
            <div className="flex flex-wrap items-center justify-between gap-4 p-4 mb-4 bg-white border border-gray-200 rounded-lg shadow-sm">
                <div className="flex items-center gap-4 flex-1">
                    <label className="text-sm font-medium text-gray-700 whitespace-nowrap">
                        Verification Event:
                    </label>
                    <select
                        value={selectedEventId || ''}
                        onChange={(e) => setSelectedEventId(e.target.value ? Number(e.target.value) : null)}
                        className="flex-1 max-w-xs border-gray-300 rounded-md text-sm focus:ring-green-500 focus:border-green-500"
                    >
                        {matrix.events.map((event: VerificationEvent) => (
                            <option key={event.id} value={event.id}>
                                {event.name} ({event.event_type})
                            </option>
                        ))}
                    </select>

                    <button
                        onClick={handleRunVerification}
                        disabled={!selectedEventId || runVerification.isPending}
                        className="flex items-center gap-2 px-3 py-1.5 bg-blue-600 text-white text-sm font-medium rounded-lg hover:bg-blue-700 disabled:opacity-50 disabled:cursor-not-allowed ml-auto"
                    >
                        {runVerification.isPending ? (
                            <Loader2 size={16} className="animate-spin" />
                        ) : (
                            <Play size={16} />
                        )}
                        Run Score
                    </button>
                </div>
            </div>

            {/* Run Results Notification */}
            {runResults && (
                <div className="mb-4 p-3 bg-green-50 border border-green-200 rounded-lg text-green-700 text-sm animate-fade-in">
                    {runResults}
                </div>
            )}

            {/* Main Content Area - Split Pane */}
            <div className="flex flex-1 gap-6 overflow-hidden">
                {/* Left Pane: Monitor List */}
                <div className="w-1/3 min-w-[300px] max-w-[400px] flex flex-col bg-white border border-gray-200 rounded-lg shadow-sm">
                    {/* Search/Filter */}
                    <div className="p-3 border-b border-gray-200">
                        <div className="relative">
                            <Search className="absolute left-3 top-1/2 -translate-y-1/2 text-gray-400" size={16} />
                            <input
                                type="text"
                                placeholder="Search monitors..."
                                value={searchTerm}
                                onChange={(e) => setSearchTerm(e.target.value)}
                                className="w-full pl-9 pr-3 py-2 text-sm border-gray-300 rounded-md focus:ring-green-500 focus:border-green-500"
                            />
                        </div>
                    </div>

                    {/* Monitor List */}
                    <div className="flex-1 overflow-y-auto p-2 space-y-2">
                        {filteredMonitors.map((monitor: any) => {
                            const eventName = selectedEvent?.name;
                            const cell = eventName ? matrix.matrix[monitor.name]?.[eventName] : null;
                            const isSelected = selectedMonitorId === monitor.id;

                            return (
                                <button
                                    key={monitor.id}
                                    onClick={() => setSelectedMonitorId(monitor.id)}
                                    className={`w-full text-left p-3 rounded-lg border transition-all ${isSelected
                                        ? 'border-green-500 bg-green-50 shadow-sm ring-1 ring-green-500'
                                        : 'border-gray-200 hover:border-green-300 hover:bg-gray-50'
                                        }`}
                                >
                                    <div className="flex justify-between items-start mb-1">
                                        <span className="font-semibold text-gray-900">{monitor.name}</span>
                                        {cell && (
                                            <div className={`flex items-center gap-1 px-1.5 py-0.5 rounded text-xs font-medium border ${getStatusColor(cell.status)}`}>
                                                {getStatusIcon(cell.status)}
                                                <span>{cell.status === 'NOT_VERIFIED' ? 'NO VER' : cell.status}</span>
                                            </div>
                                        )}
                                        {!cell && (
                                            <span className="text-xs text-gray-400">No Data</span>
                                        )}
                                    </div>
                                    <div className="flex items-center gap-2 text-xs text-gray-500">
                                        {monitor.is_critical && (
                                            <span className="text-red-600 font-medium">Critical</span>
                                        )}
                                        {monitor.is_surcharged && (
                                            <span className="text-purple-600 font-medium">Surcharged</span>
                                        )}
                                        {cell?.nse !== undefined && (
                                            <span className="ml-auto font-mono">NSE: {cell.nse.toFixed(2)}</span>
                                        )}
                                    </div>
                                </button>
                            );
                        })}
                    </div>

                    <div className="p-3 border-t border-gray-200 text-xs text-gray-500 text-center">
                        {filteredMonitors.length} monitors
                    </div>
                </div>

                {/* Right Pane: Workspace Details */}
                <div className="flex-1 bg-white border border-gray-200 rounded-lg shadow-sm overflow-hidden flex flex-col">
                    {selectedMonitorId && activeRunId ? (
                        <div className="flex-1 overflow-y-auto">
                            <VerificationWorkspace runId={activeRunId} embedded={true} />
                        </div>
                    ) : (
                        <div className="flex-1 flex flex-col items-center justify-center text-gray-400 p-8">
                            {selectedMonitorId && !activeRunId ? (
                                <>
                                    <AlertTriangle size={48} className="mb-4 text-amber-300" />
                                    <p className="text-lg font-medium text-gray-500">Not Scored</p>
                                    <p className="text-sm">No verification run found for this monitor and event.</p>
                                    <button
                                        onClick={handleRunVerification}
                                        className="mt-4 px-4 py-2 bg-blue-600 text-white rounded-lg hover:bg-blue-700 text-sm"
                                    >
                                        Run Scoring for {selectedEvent?.name}
                                    </button>
                                </>
                            ) : (
                                <>
                                    <div className="p-4 bg-gray-50 rounded-full mb-4">
                                        <ChevronRight size={32} />
                                    </div>
                                    <p className="text-lg font-medium text-gray-500">Select a monitor</p>
                                    <p className="text-sm">Choose a monitor from the list to view detailed verification analysis.</p>
                                </>
                            )}
                        </div>
                    )}
                </div>
            </div>
        </div>
    );
}
