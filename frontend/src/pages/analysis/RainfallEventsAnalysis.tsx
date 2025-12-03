import React, { useState } from 'react';
import "gantt-task-react/dist/index.css"; // Keeping css for now if needed elsewhere, or remove if specific to lib
import { format } from 'date-fns';
import { ChevronDown, ChevronUp, Play, AlertCircle, Loader2, Plus } from 'lucide-react';
import RainfallEventsGantt from './RainfallEventsGantt';
import CaptureEventModal from './CaptureEventModal';

interface RainfallEventsAnalysisProps {
    datasetIds: number[];
    projectId: number;
    onEventSaved?: () => void;
}

interface AnalysisParams {
    rainfallDepthTolerance: number;
    precedingDryDays: number;
    consecZero: number;
    interEventGap: number;
    requiredDepth: number;
    requiredIntensity: number;
    requiredIntensityDuration: number;
    partialPercent: number;
    useConsecutiveIntensities: boolean;
}

interface EventResult {
    event_id: number;
    dataset_id: number;
    dataset_name: string;
    start_time: string;
    end_time: string;
    total_mm: number;
    duration_hours: number;
    peak_intensity: number;
    status: string;
    passed: number;
}

interface DryDayResult {
    dataset_id: number;
    dataset_name: string;
    date: string;
    total_mm: number;
    duration_hours?: number;
}

interface AnalysisResult {
    events: EventResult[];
    dry_days: DryDayResult[];
}

const RainfallEventsAnalysis: React.FC<RainfallEventsAnalysisProps> = ({ datasetIds, projectId, onEventSaved }) => {
    const [params, setParams] = useState<AnalysisParams>({
        rainfallDepthTolerance: 0,
        precedingDryDays: 4,
        consecZero: 5,
        interEventGap: 10, // 6 hours default
        requiredDepth: 5,
        requiredIntensity: 6,
        requiredIntensityDuration: 4,
        partialPercent: 20,
        useConsecutiveIntensities: true
    });

    const [isLoading, setIsLoading] = useState(false);
    const [result, setResult] = useState<AnalysisResult | null>(null);
    const [error, setError] = useState<string | null>(null);
    const [isParamsOpen, setIsParamsOpen] = useState(true);

    // Modal state
    const [isModalOpen, setIsModalOpen] = useState(false);
    const [selectedEvent, setSelectedEvent] = useState<EventResult | null>(null);
    const [selectedDryDay, setSelectedDryDay] = useState<DryDayResult | null>(null);

    // Status filter
    const [statusFilter, setStatusFilter] = useState<string>('All');

    // Collapsible tables
    const [isEventsTableOpen, setIsEventsTableOpen] = useState(true);
    const [isDryDaysTableOpen, setIsDryDaysTableOpen] = useState(true);

    const handleParamChange = (key: keyof AnalysisParams, value: any) => {
        setParams(prev => ({ ...prev, [key]: value }));
    };

    const runAnalysis = async () => {
        setIsLoading(true);
        setError(null);
        try {
            const response = await fetch(`/api/fsa/rainfall/events`, {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    dataset_ids: datasetIds,
                    params: params
                })
            });

            if (!response.ok) throw new Error('Analysis failed');

            const data = await response.json();
            setResult(data);
            setIsParamsOpen(false);
        } catch (err) {
            setError('Failed to run analysis. Please try again.');
            console.error(err);
        } finally {
            setIsLoading(false);
        }
    };

    const handleCaptureEvent = (event: EventResult) => {
        setSelectedEvent(event);
        setSelectedDryDay(null);
        setIsModalOpen(true);
    };

    const handleCaptureDryDay = (dryDay: DryDayResult) => {
        setSelectedDryDay(dryDay);
        setSelectedEvent(null);
        setIsModalOpen(true);
    };

    const handleAddEvent = () => {
        setSelectedEvent(null);
        setSelectedDryDay(null);
        setIsModalOpen(true);
    };

    const handleSaveEvent = async (eventData: {
        name: string;
        event_type: string;
        start_time: string;
        end_time: string;
    }) => {
        const response = await fetch(`/api/fsa/projects/${projectId}/events`, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(eventData)
        });

        if (!response.ok) {
            throw new Error('Failed to save event');
        }

        const savedEvent = await response.json();
        if (onEventSaved) {
            onEventSaved();
        }
        return savedEvent;
    };

    // Filter events by status
    const filteredEvents = result?.events.filter(event => {
        if (statusFilter === 'All') return true;
        return event.status === statusFilter;
    }) || [];



    return (
        <div className="h-full flex flex-col space-y-4 p-4 overflow-y-auto">
            {/* Parameters Section */}
            <div className="bg-white rounded-lg border border-gray-200 shadow-sm">
                <button
                    onClick={() => setIsParamsOpen(!isParamsOpen)}
                    className="w-full px-4 py-3 flex items-center justify-between bg-gray-50 rounded-t-lg hover:bg-gray-100 transition-colors"
                >
                    <span className="font-semibold text-gray-700">Analysis Parameters</span>
                    {isParamsOpen ? <ChevronUp size={18} /> : <ChevronDown size={18} />}
                </button>

                {isParamsOpen && (
                    <div className="p-4 space-y-6">
                        {/* Storm Event Detection */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-1">Storm Event Detection</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Required Depth (mm)</label>
                                    <input
                                        type="number"
                                        value={params.requiredDepth}
                                        onChange={e => handleParamChange('requiredDepth', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Required Intensity (mm/hr)</label>
                                    <input
                                        type="number"
                                        value={params.requiredIntensity}
                                        onChange={e => handleParamChange('requiredIntensity', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Req. Intensity Duration (min)</label>
                                    <input
                                        type="number"
                                        value={params.requiredIntensityDuration}
                                        onChange={e => handleParamChange('requiredIntensityDuration', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Partial Event %</label>
                                    <input
                                        type="number"
                                        value={params.partialPercent}
                                        onChange={e => handleParamChange('partialPercent', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Inter-event Gap (min)</label>
                                    <input
                                        type="number"
                                        value={params.interEventGap}
                                        onChange={e => handleParamChange('interEventGap', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                            </div>
                        </div>

                        {/* Dry Day Detection */}
                        <div>
                            <h4 className="text-sm font-semibold text-gray-900 mb-3 border-b pb-1">Dry Day Detection</h4>
                            <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Rainfall Depth Tolerance (mm)</label>
                                    <input
                                        type="number"
                                        value={params.rainfallDepthTolerance}
                                        onChange={e => handleParamChange('rainfallDepthTolerance', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                                <div>
                                    <label className="block text-sm font-medium text-gray-700 mb-1">Preceding Dry Days</label>
                                    <input
                                        type="number"
                                        value={params.precedingDryDays}
                                        onChange={e => handleParamChange('precedingDryDays', parseFloat(e.target.value))}
                                        className="w-full px-3 py-2 border rounded-md focus:ring-purple-500 focus:border-purple-500"
                                    />
                                </div>
                            </div>
                        </div>

                        <div className="flex justify-end pt-2">
                            <button
                                onClick={runAnalysis}
                                disabled={isLoading}
                                className="bg-purple-600 text-white px-6 py-2 rounded-lg hover:bg-purple-700 transition-colors flex items-center disabled:opacity-50"
                            >
                                {isLoading ? <Loader2 className="animate-spin mr-2" /> : <Play size={18} className="mr-2" />}
                                Run Analysis
                            </button>
                        </div>
                    </div>
                )}
            </div>

            {error && (
                <div className="bg-red-50 text-red-600 p-4 rounded-lg flex items-center">
                    <AlertCircle size={20} className="mr-2" />
                    {error}
                </div>
            )}

            {/* Results */}
            {result && result.events.length > 0 && (
                <div className="space-y-6">
                    {/* Gantt Chart */}
                    <div className="bg-white p-4 rounded-lg border border-gray-200 shadow-sm">
                        <div className="flex justify-between items-center mb-4">
                            <h3 className="text-lg font-semibold">Rainfall Events Gantt Chart</h3>
                        </div>
                        <div className="overflow-x-auto">
                            <RainfallEventsGantt events={result.events} />
                        </div>
                        <div className="mt-4 flex gap-4 text-sm justify-center">
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-green-500 rounded"></div>
                                <span>Event</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-orange-500 rounded"></div>
                                <span>Partial Event</span>
                            </div>
                            <div className="flex items-center gap-2">
                                <div className="w-4 h-4 bg-red-500 rounded"></div>
                                <span>No Event</span>
                            </div>
                        </div>
                    </div>

                    {/* Add Event Button */}
                    <div className="flex justify-center py-4">
                        <button
                            onClick={handleAddEvent}
                            className="px-4 py-2 bg-green-600 text-white rounded-lg hover:bg-green-700 transition-colors flex items-center"
                        >
                            <Plus size={18} className="mr-2" />
                            Add Event
                        </button>
                    </div>

                    {/* Event Table */}
                    <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                        <button
                            onClick={() => setIsEventsTableOpen(!isEventsTableOpen)}
                            className="w-full px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center justify-between hover:bg-gray-100 transition-colors"
                        >
                            <div className="flex items-center gap-2">
                                <ChevronDown
                                    size={20}
                                    className={`transition-transform ${isEventsTableOpen ? 'rotate-180' : ''}`}
                                />
                                <h3 className="font-semibold text-gray-700">Detected Events ({filteredEvents.length})</h3>
                            </div>
                            {/* Status Filter */}
                            <div className="flex gap-2" onClick={(e) => e.stopPropagation()}>
                                {['All', 'Event', 'Partial Event', 'No Event'].map((status) => (
                                    <button
                                        key={status}
                                        onClick={() => setStatusFilter(status)}
                                        className={`px-3 py-1 text-sm rounded-md transition-colors ${statusFilter === status
                                            ? 'bg-purple-600 text-white'
                                            : 'bg-gray-100 text-gray-700 hover:bg-gray-200'
                                            }`}
                                    >
                                        {status}
                                    </button>
                                ))}
                            </div>
                        </button>
                        {isEventsTableOpen && (
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50 sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Start Time</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Duration (hr)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total (mm)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Peak (mm/hr)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {filteredEvents.map((event, idx) => (
                                        <tr key={`${event.dataset_id}-${event.event_id}-${idx}`} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {event.dataset_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <span className={`px-2 py-1 rounded-full text-xs font-semibold ${event.status === 'Event' ? 'bg-green-100 text-green-800' :
                                                    event.status === 'Partial Event' ? 'bg-orange-100 text-orange-800' :
                                                        'bg-red-100 text-red-800'
                                                    }`}>
                                                    {event.status}
                                                </span>
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {format(new Date(event.start_time), 'MMM d HH:mm')}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {event.duration_hours}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {event.total_mm}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {event.peak_intensity}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <button
                                                    onClick={() => handleCaptureEvent(event)}
                                                    className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors"
                                                >
                                                    Capture
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        )}
                    </div>
                </div>
            )}

            {/* Dry Days Table */}
            {result && result.dry_days && result.dry_days.length > 0 && (
                <div className="bg-white rounded-lg border border-gray-200 shadow-sm overflow-hidden">
                    <button
                        onClick={() => setIsDryDaysTableOpen(!isDryDaysTableOpen)}
                        className="w-full px-4 py-3 border-b border-gray-200 bg-gray-50 flex items-center gap-2 hover:bg-gray-100 transition-colors"
                    >
                        <ChevronDown
                            size={20}
                            className={`transition-transform ${isDryDaysTableOpen ? 'rotate-180' : ''}`}
                        />
                        <h3 className="font-semibold text-gray-700">Dry Days ({result.dry_days.length})</h3>
                    </button>
                    {isDryDaysTableOpen && (
                        <div className="overflow-x-auto max-h-96">
                            <table className="min-w-full divide-y divide-gray-200">
                                <thead className="bg-gray-50 sticky top-0">
                                    <tr>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Dataset</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Total (mm)</th>
                                        <th className="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Actions</th>
                                    </tr>
                                </thead>
                                <tbody className="bg-white divide-y divide-gray-200">
                                    {result.dry_days.map((day, idx) => (
                                        <tr key={`${day.dataset_id}-${day.date}-${idx}`} className="hover:bg-gray-50">
                                            <td className="px-6 py-4 whitespace-nowrap text-sm font-medium text-gray-900">
                                                {day.dataset_name}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-500">
                                                {day.date}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm text-gray-900">
                                                {day.total_mm}
                                            </td>
                                            <td className="px-6 py-4 whitespace-nowrap text-sm">
                                                <button
                                                    onClick={() => handleCaptureDryDay(day)}
                                                    className="px-3 py-1 bg-purple-600 text-white text-xs rounded hover:bg-purple-700 transition-colors"
                                                >
                                                    Capture
                                                </button>
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    )}
                </div>
            )}


            {/* Capture Event Modal */}
            <CaptureEventModal
                isOpen={isModalOpen}
                onClose={() => setIsModalOpen(false)}
                onSave={handleSaveEvent}
                sourceEvent={selectedEvent}
                sourceDryDay={selectedDryDay}
                projectId={projectId}
            />
        </div >
    );
};

export default RainfallEventsAnalysis;
