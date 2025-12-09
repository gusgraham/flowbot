import React from 'react';
import { BarChart2 } from 'lucide-react';

interface SpillEvent {
    start_time: string;
    end_time: string;
    duration_hours: number;
    volume_m3: number;
    peak_flow_m3s: number;
    is_bathing_season: boolean;
}

interface SSDAnalysisResult {
    success: boolean;
    cso_name: string;
    converged: boolean;
    iterations: number;
    final_storage_m3: number;
    spill_count: number;
    bathing_spill_count: number;
    total_spill_volume_m3: number;
    bathing_spill_volume_m3: number;
    total_spill_duration_hours: number;
    spill_events: SpillEvent[];
    error?: string;
}

interface ResultsTabProps {
    result: SSDAnalysisResult | null;
}

const ResultsTab: React.FC<ResultsTabProps> = ({ result }) => {
    if (!result) {
        return (
            <div className="text-center py-16 text-gray-400">
                <BarChart2 size={64} className="mx-auto mb-4 opacity-50" />
                <p className="text-lg">No analysis results yet</p>
                <p className="text-sm mt-2">Run an analysis from the Analysis tab to see results here.</p>
            </div>
        );
    }

    if (!result.success) {
        return (
            <div className="bg-red-50 border border-red-200 rounded-xl p-6">
                <h3 className="text-lg font-semibold text-red-800 mb-2">Analysis Failed</h3>
                <p className="text-red-700">{result.error || 'Unknown error occurred'}</p>
            </div>
        );
    }

    return (
        <div className="space-y-8">
            {/* Summary Cards */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-orange-50 border border-orange-200 rounded-xl p-5 text-center">
                    <p className="text-3xl font-bold text-orange-700">{result.final_storage_m3.toLocaleString()}</p>
                    <p className="text-sm text-orange-600 mt-1">Required Storage (m³)</p>
                </div>
                <div className="bg-blue-50 border border-blue-200 rounded-xl p-5 text-center">
                    <p className="text-3xl font-bold text-blue-700">{result.spill_count}</p>
                    <p className="text-sm text-blue-600 mt-1">Total Spills</p>
                </div>
                <div className="bg-cyan-50 border border-cyan-200 rounded-xl p-5 text-center">
                    <p className="text-3xl font-bold text-cyan-700">{result.bathing_spill_count}</p>
                    <p className="text-sm text-cyan-600 mt-1">Bathing Season Spills</p>
                </div>
                <div className={`${result.converged ? 'bg-green-50 border-green-200' : 'bg-amber-50 border-amber-200'} border rounded-xl p-5 text-center`}>
                    <p className={`text-3xl font-bold ${result.converged ? 'text-green-700' : 'text-amber-700'}`}>
                        {result.converged ? '✓' : '○'}
                    </p>
                    <p className={`text-sm mt-1 ${result.converged ? 'text-green-600' : 'text-amber-600'}`}>
                        {result.converged ? 'Converged' : 'Not Converged'}
                    </p>
                </div>
            </div>

            {/* Additional Stats */}
            <div className="grid grid-cols-2 md:grid-cols-4 gap-4">
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">CSO Name</p>
                    <p className="font-semibold text-gray-900">{result.cso_name}</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Total Spill Volume</p>
                    <p className="font-semibold text-gray-900">{result.total_spill_volume_m3.toLocaleString()} m³</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Total Spill Duration</p>
                    <p className="font-semibold text-gray-900">{result.total_spill_duration_hours.toFixed(1)} hours</p>
                </div>
                <div className="bg-gray-50 rounded-lg p-4">
                    <p className="text-sm text-gray-500">Iterations</p>
                    <p className="font-semibold text-gray-900">{result.iterations}</p>
                </div>
            </div>

            {/* Spill Events Table */}
            {result.spill_events.length > 0 && (
                <div>
                    <h3 className="text-lg font-semibold text-gray-900 mb-4">
                        Spill Events ({result.spill_events.length})
                    </h3>
                    <div className="border border-gray-200 rounded-xl overflow-hidden">
                        <div className="overflow-auto max-h-96">
                            <table className="min-w-full text-sm">
                                <thead className="bg-gray-50 sticky top-0">
                                    <tr>
                                        <th className="px-4 py-3 text-left text-gray-600 font-medium">Start Time</th>
                                        <th className="px-4 py-3 text-left text-gray-600 font-medium">End Time</th>
                                        <th className="px-4 py-3 text-right text-gray-600 font-medium">Duration (h)</th>
                                        <th className="px-4 py-3 text-right text-gray-600 font-medium">Volume (m³)</th>
                                        <th className="px-4 py-3 text-right text-gray-600 font-medium">Peak Flow (m³/s)</th>
                                        <th className="px-4 py-3 text-center text-gray-600 font-medium">Bathing</th>
                                    </tr>
                                </thead>
                                <tbody className="divide-y divide-gray-100">
                                    {result.spill_events.map((event, idx) => (
                                        <tr key={idx} className={event.is_bathing_season ? 'bg-cyan-50/50' : 'hover:bg-gray-50'}>
                                            <td className="px-4 py-3 text-gray-700">
                                                {new Date(event.start_time).toLocaleString()}
                                            </td>
                                            <td className="px-4 py-3 text-gray-700">
                                                {new Date(event.end_time).toLocaleString()}
                                            </td>
                                            <td className="px-4 py-3 text-right text-gray-700">
                                                {event.duration_hours.toFixed(2)}
                                            </td>
                                            <td className="px-4 py-3 text-right text-gray-700">
                                                {event.volume_m3.toFixed(1)}
                                            </td>
                                            <td className="px-4 py-3 text-right text-gray-700">
                                                {event.peak_flow_m3s.toFixed(4)}
                                            </td>
                                            <td className="px-4 py-3 text-center">
                                                {event.is_bathing_season && (
                                                    <span className="inline-block w-3 h-3 bg-cyan-500 rounded-full" title="Bathing Season" />
                                                )}
                                            </td>
                                        </tr>
                                    ))}
                                </tbody>
                            </table>
                        </div>
                    </div>
                </div>
            )}

            {result.spill_events.length === 0 && (
                <div className="bg-green-50 border border-green-200 rounded-xl p-6 text-center">
                    <p className="text-green-700 font-medium">No spill events recorded</p>
                    <p className="text-green-600 text-sm mt-1">The storage solution eliminates all spills for this configuration.</p>
                </div>
            )}
        </div>
    );
};

export default ResultsTab;
